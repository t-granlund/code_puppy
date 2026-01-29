"""Safe Patch Application Rules for Code Puppy.

AUDIT-1.1 Part H compliance:
- Ban unsafe heredoc/sed patterns in agent instructions
- Safe edit helper preferring VS Code edits
- "Restore first" workflow on syntax explosion
- Validation of patch safety before application

This module provides:
1. Detection and blocking of unsafe editing patterns
2. Safe alternatives for file modifications
3. Pre-edit validation and post-edit syntax checking
4. Rollback capabilities for failed edits
"""

import ast
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# ============================================================================
# Unsafe Pattern Detection
# ============================================================================

class UnsafePatternType(Enum):
    """Types of unsafe patterns."""
    HEREDOC = "heredoc"
    SED_INPLACE = "sed_inplace"
    AWK_INPLACE = "awk_inplace"
    ECHO_REDIRECT = "echo_redirect"
    CAT_REDIRECT = "cat_redirect"
    PERL_INPLACE = "perl_inplace"
    DD_WRITE = "dd_write"
    TEE_OVERWRITE = "tee_overwrite"
    TRUNCATE = "truncate"


@dataclass
class UnsafePatternMatch:
    """A detected unsafe pattern."""
    pattern_type: UnsafePatternType
    matched_text: str
    explanation: str
    safe_alternative: str


# Patterns to detect in shell commands
UNSAFE_PATTERNS = [
    # Heredoc patterns
    (
        r'cat\s*>\s*\S+\s*<<[<\s]*[\'"]?(\w+)',
        UnsafePatternType.HEREDOC,
        "Heredoc file creation can corrupt files if interrupted",
        "Use the edit_file tool or write content atomically",
    ),
    (
        r'<<\s*[\'"]?EOF[\'"]?\s*>',
        UnsafePatternType.HEREDOC,
        "Heredoc with redirect is unsafe for file modifications",
        "Use the edit_file tool for file modifications",
    ),
    # Sed in-place
    (
        r"sed\s+(-i|--in-place)",
        UnsafePatternType.SED_INPLACE,
        "sed -i modifies files in place without backup",
        "Use 'sed -i.bak' for backup or edit_file tool",
    ),
    (
        r"sed\s+['\"][^'\"]+['\"]\s+.*\s*>\s*\S+",
        UnsafePatternType.SED_INPLACE,
        "sed with redirect can corrupt files",
        "Use edit_file tool for precise replacements",
    ),
    # Awk in-place
    (
        r"awk\s+(-i\s+inplace|--inplace)",
        UnsafePatternType.AWK_INPLACE,
        "awk inplace can corrupt files on error",
        "Prefer edit_file tool or awk to temp file then mv",
    ),
    # Echo redirect (dangerous for code)
    (
        r"echo\s+['\"].+['\"]\s*>\s*\S+\.(py|js|ts|java|go|rs|cpp|c|h)",
        UnsafePatternType.ECHO_REDIRECT,
        "echo redirect overwrites entire file",
        "Use edit_file tool to modify specific lines",
    ),
    # Cat redirect overwrite
    (
        r"cat\s*>\s*\S+\.(py|js|ts|java|go|rs|cpp|c|h)\s*$",
        UnsafePatternType.CAT_REDIRECT,
        "cat > file overwrites without confirmation",
        "Use edit_file tool for safe modifications",
    ),
    # Perl in-place
    (
        r"perl\s+(-i|-pie)",
        UnsafePatternType.PERL_INPLACE,
        "perl -i modifies in place without safety net",
        "Use edit_file tool or perl -i.bak",
    ),
    # dd write
    (
        r"dd\s+.*of=\S+\.(py|js|ts|java|go|rs|cpp|c|h)",
        UnsafePatternType.DD_WRITE,
        "dd of= can corrupt source files",
        "Use edit_file tool for text file modifications",
    ),
    # Tee overwrite
    (
        r"tee\s+\S+\.(py|js|ts|java|go|rs|cpp|c|h)\s*$",
        UnsafePatternType.TEE_OVERWRITE,
        "tee without -a overwrites the file",
        "Use edit_file tool or 'tee -a' for append",
    ),
    # Truncate
    (
        r"truncate\s+.*\S+\.(py|js|ts|java|go|rs|cpp|c|h)",
        UnsafePatternType.TRUNCATE,
        "truncate can destroy file contents",
        "Avoid truncate on source files",
    ),
]


def detect_unsafe_patterns(command: str) -> List[UnsafePatternMatch]:
    """Detect unsafe patterns in a shell command.
    
    Args:
        command: Shell command to analyze.
        
    Returns:
        List of detected unsafe patterns.
    """
    matches = []
    
    for pattern, pattern_type, explanation, alternative in UNSAFE_PATTERNS:
        for match in re.finditer(pattern, command, re.IGNORECASE | re.MULTILINE):
            matches.append(UnsafePatternMatch(
                pattern_type=pattern_type,
                matched_text=match.group(0)[:100],  # Truncate long matches
                explanation=explanation,
                safe_alternative=alternative,
            ))
    
    return matches


def is_command_safe(command: str) -> Tuple[bool, List[UnsafePatternMatch]]:
    """Check if a command is safe to execute.
    
    Args:
        command: Shell command to check.
        
    Returns:
        Tuple of (is_safe, list of unsafe patterns found).
    """
    matches = detect_unsafe_patterns(command)
    return len(matches) == 0, matches


def format_unsafe_warning(matches: List[UnsafePatternMatch]) -> str:
    """Format unsafe pattern matches as a warning message.
    
    Args:
        matches: List of unsafe patterns found.
        
    Returns:
        Formatted warning string.
    """
    if not matches:
        return ""
    
    lines = ["⚠️ UNSAFE SHELL PATTERNS DETECTED:", ""]
    
    for match in matches:
        lines.append(f"  🚫 {match.pattern_type.value}: {match.matched_text}")
        lines.append(f"     Problem: {match.explanation}")
        lines.append(f"     Alternative: {match.safe_alternative}")
        lines.append("")
    
    lines.append("Prefer using edit_file tool for safe file modifications.")
    return "\n".join(lines)


# ============================================================================
# Syntax Validation
# ============================================================================

class SyntaxChecker:
    """Validates syntax for various file types."""
    
    @staticmethod
    def check_python(content: str) -> Tuple[bool, Optional[str]]:
        """Check Python syntax.
        
        Args:
            content: Python source code.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            ast.parse(content)
            return True, None
        except SyntaxError as e:
            return False, f"Line {e.lineno}: {e.msg}"
    
    @staticmethod
    def check_json(content: str) -> Tuple[bool, Optional[str]]:
        """Check JSON syntax.
        
        Args:
            content: JSON content.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        import json
        try:
            json.loads(content)
            return True, None
        except json.JSONDecodeError as e:
            return False, f"Line {e.lineno}: {e.msg}"
    
    @staticmethod
    def check_yaml(content: str) -> Tuple[bool, Optional[str]]:
        """Check YAML syntax (if PyYAML available).
        
        Args:
            content: YAML content.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            import yaml
            yaml.safe_load(content)
            return True, None
        except ImportError:
            return True, None  # Can't check, assume OK
        except yaml.YAMLError as e:
            return False, str(e)
    
    @staticmethod
    def check_javascript(content: str, file_path: str) -> Tuple[bool, Optional[str]]:
        """Check JavaScript/TypeScript syntax using external tool.
        
        Args:
            content: JS/TS source code.
            file_path: Path for temp file extension.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        # Try node --check for JS
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ('.ts', '.tsx'):
            # TypeScript - try tsc
            try:
                with tempfile.NamedTemporaryFile(
                    mode='w', suffix=ext, delete=False
                ) as f:
                    f.write(content)
                    temp_path = f.name
                try:
                    result = subprocess.run(
                        ['npx', 'tsc', '--noEmit', temp_path],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if result.returncode != 0:
                        return False, result.stderr[:500]
                    return True, None
                finally:
                    os.unlink(temp_path)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return True, None  # Can't check
        else:
            # JavaScript - use node
            try:
                with tempfile.NamedTemporaryFile(
                    mode='w', suffix='.js', delete=False
                ) as f:
                    f.write(content)
                    temp_path = f.name
                try:
                    result = subprocess.run(
                        ['node', '--check', temp_path],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode != 0:
                        return False, result.stderr[:500]
                    return True, None
                finally:
                    os.unlink(temp_path)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return True, None  # Can't check
    
    @classmethod
    def check_file(cls, content: str, file_path: str) -> Tuple[bool, Optional[str]]:
        """Check syntax based on file extension.
        
        Args:
            content: File content.
            file_path: File path (for extension detection).
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.py':
            return cls.check_python(content)
        elif ext == '.json':
            return cls.check_json(content)
        elif ext in ('.yaml', '.yml'):
            return cls.check_yaml(content)
        elif ext in ('.js', '.jsx', '.ts', '.tsx'):
            return cls.check_javascript(content, file_path)
        else:
            return True, None  # Unknown type, assume OK


def validate_syntax(content: str, file_path: str) -> Tuple[bool, Optional[str]]:
    """Validate syntax of file content.
    
    Args:
        content: File content to validate.
        file_path: File path for extension detection.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    return SyntaxChecker.check_file(content, file_path)


# ============================================================================
# Safe Edit Operations
# ============================================================================

@dataclass
class FileBackup:
    """Backup of a file before editing."""
    original_path: str
    backup_path: str
    content_hash: str
    timestamp: str
    
    def restore(self) -> bool:
        """Restore the backed up file.
        
        Returns:
            True if restore succeeded.
        """
        try:
            shutil.copy2(self.backup_path, self.original_path)
            return True
        except IOError:
            return False
    
    def cleanup(self):
        """Remove the backup file."""
        try:
            os.unlink(self.backup_path)
        except IOError:
            pass


# Track active backups (for rollback capability)
_active_backups: Dict[str, FileBackup] = {}


def create_backup(file_path: str) -> Optional[FileBackup]:
    """Create a backup of a file before editing.
    
    Args:
        file_path: Path to file to backup.
        
    Returns:
        FileBackup object, or None if file doesn't exist.
    """
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create backup in temp directory
        backup_dir = os.path.join(tempfile.gettempdir(), "codepuppy_backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        base_name = os.path.basename(file_path)
        backup_name = f"{base_name}.{timestamp}.{content_hash}.bak"
        backup_path = os.path.join(backup_dir, backup_name)
        
        shutil.copy2(file_path, backup_path)
        
        backup = FileBackup(
            original_path=file_path,
            backup_path=backup_path,
            content_hash=content_hash,
            timestamp=timestamp,
        )
        
        _active_backups[file_path] = backup
        return backup
        
    except IOError:
        return None


def get_backup(file_path: str) -> Optional[FileBackup]:
    """Get the active backup for a file.
    
    Args:
        file_path: Path to check.
        
    Returns:
        FileBackup if one exists.
    """
    return _active_backups.get(file_path)


def restore_from_backup(file_path: str) -> Tuple[bool, str]:
    """Restore a file from its backup.
    
    Args:
        file_path: Path to restore.
        
    Returns:
        Tuple of (success, message).
    """
    backup = _active_backups.get(file_path)
    if not backup:
        return False, f"No backup found for {file_path}"
    
    if backup.restore():
        return True, f"Restored {file_path} from backup"
    else:
        return False, f"Failed to restore {file_path}"


def cleanup_old_backups(max_age_hours: int = 24):
    """Clean up old backup files.
    
    Args:
        max_age_hours: Maximum age in hours before cleanup.
    """
    backup_dir = os.path.join(tempfile.gettempdir(), "codepuppy_backups")
    if not os.path.exists(backup_dir):
        return
    
    cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
    
    try:
        for filename in os.listdir(backup_dir):
            file_path = os.path.join(backup_dir, filename)
            if os.path.isfile(file_path):
                if os.path.getmtime(file_path) < cutoff:
                    os.unlink(file_path)
    except IOError:
        pass


@dataclass
class SafeEditResult:
    """Result of a safe edit operation."""
    success: bool
    file_path: str
    message: str
    backup: Optional[FileBackup] = None
    syntax_valid: bool = True
    syntax_error: Optional[str] = None
    rolled_back: bool = False


def safe_write_file(
    file_path: str,
    content: str,
    validate_syntax_flag: bool = True,
    create_backup_flag: bool = True,
) -> SafeEditResult:
    """Safely write content to a file.
    
    This function:
    1. Creates a backup of the original file
    2. Validates syntax of the new content
    3. Writes atomically (via temp file)
    4. Rolls back on syntax errors if requested
    
    Args:
        file_path: Path to write to.
        content: Content to write.
        validate_syntax_flag: Whether to validate syntax.
        create_backup_flag: Whether to create a backup.
        
    Returns:
        SafeEditResult with operation status.
    """
    # Create backup if file exists
    backup = None
    if create_backup_flag and os.path.exists(file_path):
        backup = create_backup(file_path)
    
    # Validate syntax before writing
    if validate_syntax_flag:
        is_valid, syntax_error = validate_syntax(content, file_path)
        if not is_valid:
            return SafeEditResult(
                success=False,
                file_path=file_path,
                message=f"Syntax error in new content: {syntax_error}",
                backup=backup,
                syntax_valid=False,
                syntax_error=syntax_error,
            )
    
    # Write atomically via temp file
    try:
        dir_path = os.path.dirname(file_path) or "."
        os.makedirs(dir_path, exist_ok=True)
        
        # Write to temp file first
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=dir_path,
            delete=False,
            suffix=os.path.splitext(file_path)[1],
        ) as f:
            f.write(content)
            temp_path = f.name
        
        # Atomic move
        shutil.move(temp_path, file_path)
        
        return SafeEditResult(
            success=True,
            file_path=file_path,
            message=f"Successfully wrote {file_path}",
            backup=backup,
            syntax_valid=True,
        )
        
    except IOError as e:
        return SafeEditResult(
            success=False,
            file_path=file_path,
            message=f"Failed to write {file_path}: {e}",
            backup=backup,
        )


def safe_edit_lines(
    file_path: str,
    start_line: int,
    end_line: int,
    new_content: str,
    validate_syntax_flag: bool = True,
) -> SafeEditResult:
    """Safely replace a range of lines in a file.
    
    Args:
        file_path: Path to edit.
        start_line: First line to replace (1-indexed).
        end_line: Last line to replace (1-indexed, inclusive).
        new_content: New content for the line range.
        validate_syntax_flag: Whether to validate syntax.
        
    Returns:
        SafeEditResult with operation status.
    """
    if not os.path.exists(file_path):
        return SafeEditResult(
            success=False,
            file_path=file_path,
            message=f"File does not exist: {file_path}",
        )
    
    # Create backup
    backup = create_backup(file_path)
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Validate line range
        if start_line < 1 or end_line > len(lines) or start_line > end_line:
            return SafeEditResult(
                success=False,
                file_path=file_path,
                message=f"Invalid line range: {start_line}-{end_line} (file has {len(lines)} lines)",
                backup=backup,
            )
        
        # Build new content
        new_lines = new_content.splitlines(keepends=True)
        if new_content and not new_content.endswith('\n'):
            if new_lines:
                new_lines[-1] += '\n'
            else:
                new_lines = [new_content + '\n']
        
        # Replace lines (convert to 0-indexed)
        result_lines = lines[:start_line - 1] + new_lines + lines[end_line:]
        result_content = ''.join(result_lines)
        
        # Validate syntax
        if validate_syntax_flag:
            is_valid, syntax_error = validate_syntax(result_content, file_path)
            if not is_valid:
                return SafeEditResult(
                    success=False,
                    file_path=file_path,
                    message=f"Edit would create syntax error: {syntax_error}",
                    backup=backup,
                    syntax_valid=False,
                    syntax_error=syntax_error,
                )
        
        # Write result
        with open(file_path, 'w') as f:
            f.write(result_content)
        
        return SafeEditResult(
            success=True,
            file_path=file_path,
            message=f"Successfully edited lines {start_line}-{end_line} in {file_path}",
            backup=backup,
            syntax_valid=True,
        )
        
    except IOError as e:
        return SafeEditResult(
            success=False,
            file_path=file_path,
            message=f"Failed to edit {file_path}: {e}",
            backup=backup,
        )


# ============================================================================
# Syntax Explosion Detection
# ============================================================================

def detect_syntax_explosion(
    original_content: str,
    new_content: str,
    file_path: str,
    threshold_ratio: float = 3.0,
) -> Tuple[bool, str]:
    """Detect if an edit caused a "syntax explosion".
    
    A syntax explosion is when an edit dramatically increases
    errors or changes the file structure unexpectedly.
    
    Args:
        original_content: Original file content.
        new_content: New file content.
        file_path: File path for syntax checking.
        threshold_ratio: Error count increase ratio to trigger.
        
    Returns:
        Tuple of (is_explosion, explanation).
    """
    # Check original syntax errors
    original_valid, original_error = validate_syntax(original_content, file_path)
    new_valid, new_error = validate_syntax(new_content, file_path)
    
    # If original was valid and new is not, that's a problem
    if original_valid and not new_valid:
        return True, f"Edit broke valid code: {new_error}"
    
    # Check for dramatic size changes (potential truncation or explosion)
    original_lines = len(original_content.splitlines())
    new_lines = len(new_content.splitlines())
    
    if original_lines > 10:  # Only check for non-trivial files
        if new_lines > original_lines * 2:
            return True, f"Line count explosion: {original_lines} -> {new_lines}"
        if new_lines < original_lines * 0.25:
            return True, f"Potential truncation: {original_lines} -> {new_lines}"
    
    return False, ""


# ============================================================================
# Agent Instructions
# ============================================================================

SAFE_PATCH_INSTRUCTIONS = """
## Safe File Editing Rules

### BANNED Patterns (Never Use):
- `cat > file << EOF` (heredoc) - Use edit_file tool instead
- `sed -i` without backup - Use edit_file or `sed -i.bak`
- `echo "..." > file.py` - Never overwrite source files with echo
- `dd of=source.py` - Never use dd on source files
- Piping content directly to source files

### Safe Alternatives:
1. Use edit_file tool for line-based edits
2. Use read_file first to understand context
3. Make small, targeted changes (micro-patches)
4. Always check syntax after edits

### On Syntax Errors After Edit:
1. STOP immediately
2. Restore from backup if available
3. Re-read the original file
4. Identify the minimal fix needed
5. Apply a smaller, targeted patch

### Micro-Patch Guidelines:
- Change ≤10 lines per edit when possible
- Include 3+ lines of context for replacements
- Verify imports/dependencies exist
- Test after each significant change
"""


def get_safe_patch_instructions() -> str:
    """Get safe patch instructions for agent prompts.
    
    Returns:
        Instructions string.
    """
    return SAFE_PATCH_INSTRUCTIONS
