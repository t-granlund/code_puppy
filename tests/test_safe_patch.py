"""Tests for Safe Patch module.

AUDIT-1.1 Part H test coverage.
"""

import ast
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from code_puppy.tools.safe_patch import (
    # Enums
    UnsafePatternType,
    # Data classes
    UnsafePatternMatch,
    FileBackup,
    SafeEditResult,
    # Functions
    detect_unsafe_patterns,
    is_command_safe,
    format_unsafe_warning,
    validate_syntax,
    create_backup,
    get_backup,
    restore_from_backup,
    safe_write_file,
    safe_edit_lines,
    detect_syntax_explosion,
    get_safe_patch_instructions,
    # Classes
    SyntaxChecker,
)


class TestUnsafePatternDetection:
    """Test detection of unsafe shell patterns."""
    
    def test_detect_heredoc(self):
        """Detect heredoc patterns."""
        cmd = "cat > config.py << EOF\nprint('hello')\nEOF"
        matches = detect_unsafe_patterns(cmd)
        assert len(matches) > 0
        assert any(m.pattern_type == UnsafePatternType.HEREDOC for m in matches)
    
    def test_detect_sed_inplace(self):
        """Detect sed -i patterns."""
        cmd = "sed -i 's/old/new/g' file.py"
        matches = detect_unsafe_patterns(cmd)
        assert len(matches) > 0
        assert any(m.pattern_type == UnsafePatternType.SED_INPLACE for m in matches)
    
    def test_detect_echo_redirect(self):
        """Detect echo redirect to source files."""
        cmd = "echo 'print(1)' > main.py"
        matches = detect_unsafe_patterns(cmd)
        assert len(matches) > 0
        assert any(m.pattern_type == UnsafePatternType.ECHO_REDIRECT for m in matches)
    
    def test_detect_cat_redirect(self):
        """Detect cat redirect patterns."""
        cmd = "cat > script.js"
        matches = detect_unsafe_patterns(cmd)
        assert len(matches) > 0
    
    def test_detect_perl_inplace(self):
        """Detect perl -i patterns."""
        cmd = "perl -i -pe 's/foo/bar/' file.py"
        matches = detect_unsafe_patterns(cmd)
        assert len(matches) > 0
        assert any(m.pattern_type == UnsafePatternType.PERL_INPLACE for m in matches)
    
    def test_safe_command(self):
        """Safe commands have no matches."""
        cmd = "cat file.py | grep pattern"
        matches = detect_unsafe_patterns(cmd)
        assert len(matches) == 0
    
    def test_is_command_safe(self):
        """Test is_command_safe helper."""
        safe, matches = is_command_safe("ls -la")
        assert safe
        assert len(matches) == 0
        
        safe, matches = is_command_safe("sed -i 's/x/y/' file.py")
        assert not safe
        assert len(matches) > 0
    
    def test_format_unsafe_warning(self):
        """Test warning formatting."""
        matches = [
            UnsafePatternMatch(
                pattern_type=UnsafePatternType.HEREDOC,
                matched_text="cat > file << EOF",
                explanation="Heredoc is unsafe",
                safe_alternative="Use edit_file",
            )
        ]
        warning = format_unsafe_warning(matches)
        
        assert "UNSAFE" in warning
        assert "heredoc" in warning
        assert "edit_file" in warning
    
    def test_empty_warning(self):
        """Empty matches returns empty string."""
        warning = format_unsafe_warning([])
        assert warning == ""


class TestSyntaxValidation:
    """Test syntax validation for various languages."""
    
    def test_valid_python(self):
        """Valid Python passes."""
        code = """
def hello():
    print("Hello, World!")
    return True
"""
        is_valid, error = SyntaxChecker.check_python(code)
        assert is_valid
        assert error is None
    
    def test_invalid_python(self):
        """Invalid Python fails."""
        code = """
def hello(
    print("Missing paren")
"""
        is_valid, error = SyntaxChecker.check_python(code)
        assert not is_valid
        assert error is not None
    
    def test_valid_json(self):
        """Valid JSON passes."""
        code = '{"key": "value", "number": 42}'
        is_valid, error = SyntaxChecker.check_json(code)
        assert is_valid
    
    def test_invalid_json(self):
        """Invalid JSON fails."""
        code = '{"key": "value",}'  # Trailing comma
        is_valid, error = SyntaxChecker.check_json(code)
        assert not is_valid
    
    def test_validate_by_extension(self):
        """Validation based on extension."""
        # Python
        is_valid, _ = validate_syntax("x = 1", "test.py")
        assert is_valid
        
        # JSON
        is_valid, _ = validate_syntax('{"a": 1}', "config.json")
        assert is_valid
        
        # Unknown extension (passes by default)
        is_valid, _ = validate_syntax("anything", "file.xyz")
        assert is_valid


class TestFileBackup:
    """Test file backup functionality."""
    
    def test_create_backup(self):
        """Create backup of file."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False
        ) as f:
            f.write("original content")
            temp_path = f.name
        
        try:
            backup = create_backup(temp_path)
            assert backup is not None
            assert backup.original_path == temp_path
            assert os.path.exists(backup.backup_path)
            
            # Cleanup
            backup.cleanup()
        finally:
            os.unlink(temp_path)
    
    def test_restore_backup(self):
        """Restore file from backup."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False
        ) as f:
            f.write("original content")
            temp_path = f.name
        
        try:
            # Create backup
            backup = create_backup(temp_path)
            
            # Modify original
            with open(temp_path, 'w') as f:
                f.write("modified content")
            
            # Restore
            success = backup.restore()
            assert success
            
            with open(temp_path, 'r') as f:
                assert f.read() == "original content"
            
            backup.cleanup()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_get_backup(self):
        """Get backup for file."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False
        ) as f:
            f.write("content")
            temp_path = f.name
        
        try:
            create_backup(temp_path)
            backup = get_backup(temp_path)
            assert backup is not None
            backup.cleanup()
        finally:
            os.unlink(temp_path)
    
    def test_backup_nonexistent_file(self):
        """Backup of nonexistent file returns None."""
        backup = create_backup("/nonexistent/path/file.py")
        assert backup is None


class TestSafeWriteFile:
    """Test safe file writing."""
    
    def test_safe_write_new_file(self):
        """Write new file safely."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "new_file.py")
            content = "x = 1\nprint(x)\n"
            
            result = safe_write_file(path, content)
            
            assert result.success
            assert os.path.exists(path)
            with open(path) as f:
                assert f.read() == content
    
    def test_safe_write_with_backup(self):
        """Write file creates backup."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False
        ) as f:
            f.write("original")
            temp_path = f.name
        
        try:
            result = safe_write_file(
                temp_path,
                "x = 1\n",
                create_backup_flag=True,
            )
            
            assert result.success
            assert result.backup is not None
            result.backup.cleanup()
        finally:
            os.unlink(temp_path)
    
    def test_safe_write_syntax_validation(self):
        """Write rejects invalid syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "invalid.py")
            content = "def broken(\n"  # Invalid Python
            
            result = safe_write_file(
                path,
                content,
                validate_syntax_flag=True,
            )
            
            assert not result.success
            assert not result.syntax_valid
            assert result.syntax_error is not None
    
    def test_safe_write_skip_validation(self):
        """Write can skip validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "skip.py")
            content = "def broken(\n"  # Invalid but we skip
            
            result = safe_write_file(
                path,
                content,
                validate_syntax_flag=False,
            )
            
            # Writes even with bad syntax
            assert result.success


class TestSafeEditLines:
    """Test safe line-based editing."""
    
    def test_edit_lines_success(self):
        """Edit lines successfully."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False
        ) as f:
            f.write("line1\nline2\nline3\nline4\n")
            temp_path = f.name
        
        try:
            result = safe_edit_lines(
                temp_path,
                start_line=2,
                end_line=3,
                new_content="new_line2\nnew_line3",
                validate_syntax_flag=False,  # Skip for plain text
            )
            
            assert result.success
            
            with open(temp_path) as f:
                content = f.read()
            
            assert "new_line2" in content
            assert "new_line3" in content
            assert "line1" in content
            assert "line4" in content
        finally:
            os.unlink(temp_path)
    
    def test_edit_lines_invalid_range(self):
        """Edit with invalid range fails."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False
        ) as f:
            f.write("line1\nline2\n")
            temp_path = f.name
        
        try:
            result = safe_edit_lines(
                temp_path,
                start_line=5,  # Out of range
                end_line=10,
                new_content="new",
            )
            
            assert not result.success
            assert "Invalid line range" in result.message
        finally:
            os.unlink(temp_path)
    
    def test_edit_lines_syntax_check(self):
        """Edit validates resulting syntax."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False
        ) as f:
            f.write("def foo():\n    pass\n")
            temp_path = f.name
        
        try:
            # This would break syntax
            result = safe_edit_lines(
                temp_path,
                start_line=2,
                end_line=2,
                new_content="    invalid syntax here(",
                validate_syntax_flag=True,
            )
            
            assert not result.success
            assert "syntax error" in result.message.lower()
        finally:
            os.unlink(temp_path)


class TestSyntaxExplosion:
    """Test syntax explosion detection."""
    
    def test_detect_broke_valid_code(self):
        """Detect when edit breaks valid code."""
        original = "def foo():\n    pass\n"
        new = "def foo(\n    pass\n"  # Missing closing paren
        
        is_explosion, explanation = detect_syntax_explosion(
            original, new, "test.py"
        )
        
        assert is_explosion
        assert "broke" in explanation.lower()
    
    def test_detect_line_explosion(self):
        """Detect dramatic line increase."""
        original = "x = 1\n" * 100
        new = "x = 1\n" * 500  # 5x increase
        
        is_explosion, explanation = detect_syntax_explosion(
            original, new, "test.txt"
        )
        
        assert is_explosion
        assert "explosion" in explanation.lower()
    
    def test_detect_truncation(self):
        """Detect potential truncation."""
        original = "x = 1\n" * 100
        new = "x = 1\n" * 10  # Dramatic decrease
        
        is_explosion, explanation = detect_syntax_explosion(
            original, new, "test.txt"
        )
        
        assert is_explosion
        assert "truncation" in explanation.lower()
    
    def test_no_explosion(self):
        """Normal edit is not explosion."""
        original = "def foo():\n    pass\n"
        new = "def foo():\n    return 1\n"
        
        is_explosion, explanation = detect_syntax_explosion(
            original, new, "test.py"
        )
        
        assert not is_explosion


class TestSafeEditResult:
    """Test SafeEditResult data class."""
    
    def test_success_result(self):
        """Successful result properties."""
        result = SafeEditResult(
            success=True,
            file_path="test.py",
            message="OK",
            syntax_valid=True,
        )
        assert result.success
        assert result.syntax_valid
        assert not result.rolled_back
    
    def test_failure_result(self):
        """Failed result properties."""
        result = SafeEditResult(
            success=False,
            file_path="test.py",
            message="Syntax error",
            syntax_valid=False,
            syntax_error="Line 1: invalid",
        )
        assert not result.success
        assert not result.syntax_valid
        assert result.syntax_error is not None


class TestSafePatchInstructions:
    """Test safe patch instructions."""
    
    def test_instructions_content(self):
        """Instructions contain key rules."""
        instructions = get_safe_patch_instructions()
        
        assert "BANNED" in instructions
        assert "heredoc" in instructions.lower()
        assert "sed -i" in instructions
        assert "edit_file" in instructions
        assert "Syntax Error" in instructions or "syntax" in instructions.lower()
    
    def test_instructions_alternatives(self):
        """Instructions provide alternatives."""
        instructions = get_safe_patch_instructions()
        
        assert "Safe Alternative" in instructions or "safe" in instructions.lower()
        assert "micro-patch" in instructions.lower() or "Micro-Patch" in instructions
