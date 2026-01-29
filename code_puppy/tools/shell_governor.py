"""Shell Output Governor for Code Puppy.

Central module for governing all shell command execution with:
- Automatic output truncation (default: tail -n 160)
- Configurable timeouts with sensible defaults
- Secret redaction for sensitive output
- Command metadata persistence for auditing/telemetry

AUDIT-1.1 Part E compliance.
"""

import asyncio
import hashlib
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import threading

from code_puppy.config import get_value


# ============================================================================
# Configuration Constants
# ============================================================================

# Default output limits
DEFAULT_OUTPUT_LINES = 160
DEFAULT_OUTPUT_CHARS = 40000  # ~10K tokens max
MAX_OUTPUT_CHARS = 100000    # Absolute ceiling

# Timeout defaults (seconds)
DEFAULT_TIMEOUT = 120        # 2 minutes
QUICK_COMMAND_TIMEOUT = 30   # For simple commands
LONG_COMMAND_TIMEOUT = 600   # 10 minutes for builds, tests

# Commands that typically need longer timeouts
LONG_RUNNING_PATTERNS = [
    r'\bnpm\s+install\b',
    r'\byarn\s+install\b',
    r'\bpip\s+install\b',
    r'\bcargo\s+build\b',
    r'\bgo\s+build\b',
    r'\bmake\b',
    r'\bcmake\b',
    r'\bpytest\b',
    r'\bunittest\b',
    r'\bnpx\s+playwright\b',
    r'\bdocker\s+build\b',
    r'\bgit\s+clone\b',
]

# Patterns that indicate secrets (case-insensitive)
SECRET_PATTERNS = [
    r'(api[_-]?key|apikey)\s*[=:]\s*["\']?([a-zA-Z0-9_-]{20,})',
    r'(token|auth[_-]?token)\s*[=:]\s*["\']?([a-zA-Z0-9_.-]{20,})',
    r'(password|passwd|pwd)\s*[=:]\s*["\']?([^\s"\',]+)',
    r'(secret|private[_-]?key)\s*[=:]\s*["\']?([a-zA-Z0-9_+/=-]{20,})',
    r'(bearer|authorization)\s*[=:]\s*["\']?([a-zA-Z0-9_.-]{20,})',
    r'(aws[_-]?access|aws[_-]?secret)\s*[=:]\s*["\']?([A-Z0-9]{16,})',
    r'(github[_-]?token|gh[_-]?token)\s*[=:]\s*["\']?([a-zA-Z0-9_-]{30,})',
    r'sk-[a-zA-Z0-9]{32,}',  # OpenAI API keys
    r'ghp_[a-zA-Z0-9]{36}',  # GitHub personal tokens
    r'gho_[a-zA-Z0-9]{36}',  # GitHub OAuth tokens
]


class OutputTruncation(Enum):
    """How output was truncated."""
    NONE = "none"
    LINES = "lines"
    CHARS = "chars"
    BOTH = "both"


@dataclass
class CommandResult:
    """Result of a governed shell command execution."""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    elapsed_ms: int
    truncation: OutputTruncation
    lines_truncated: int = 0
    chars_truncated: int = 0
    secrets_redacted: int = 0
    timed_out: bool = False
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0 and not self.timed_out
    
    @property
    def combined_output(self) -> str:
        """Combined stdout and stderr."""
        parts = []
        if self.stdout:
            parts.append(self.stdout)
        if self.stderr:
            parts.append(f"[stderr]\n{self.stderr}")
        return "\n".join(parts) if parts else "(no output)"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "command": self.command[:500],  # Truncate very long commands
            "exit_code": self.exit_code,
            "elapsed_ms": self.elapsed_ms,
            "truncation": self.truncation.value,
            "lines_truncated": self.lines_truncated,
            "chars_truncated": self.chars_truncated,
            "secrets_redacted": self.secrets_redacted,
            "timed_out": self.timed_out,
            "timestamp": self.timestamp,
            "output_preview": self.combined_output[:200],  # Short preview only
        }


@dataclass
class GovernorConfig:
    """Configuration for the shell governor."""
    max_output_lines: int = DEFAULT_OUTPUT_LINES
    max_output_chars: int = DEFAULT_OUTPUT_CHARS
    default_timeout: int = DEFAULT_TIMEOUT
    redact_secrets: bool = True
    persist_metadata: bool = True
    
    @classmethod
    def from_config(cls) -> "GovernorConfig":
        """Load configuration from code_puppy config."""
        config = cls()
        
        max_lines = get_value("shell_max_output_lines")
        if max_lines:
            try:
                config.max_output_lines = int(max_lines)
            except (ValueError, TypeError):
                pass
        
        max_chars = get_value("shell_max_output_chars")
        if max_chars:
            try:
                config.max_output_chars = min(int(max_chars), MAX_OUTPUT_CHARS)
            except (ValueError, TypeError):
                pass
        
        timeout = get_value("shell_default_timeout")
        if timeout:
            try:
                config.default_timeout = int(timeout)
            except (ValueError, TypeError):
                pass
        
        redact = get_value("shell_redact_secrets")
        if redact is not None:
            config.redact_secrets = str(redact).lower() in ("true", "1", "yes")
        
        persist = get_value("shell_persist_metadata")
        if persist is not None:
            config.persist_metadata = str(persist).lower() in ("true", "1", "yes")
        
        return config


# Global command history buffer (for telemetry)
_command_history: List[Dict[str, Any]] = []
_history_lock = threading.Lock()
MAX_HISTORY_SIZE = 100


def _add_to_history(result: CommandResult):
    """Add a command result to history buffer."""
    with _history_lock:
        _command_history.append(result.to_dict())
        # Trim if too large
        while len(_command_history) > MAX_HISTORY_SIZE:
            _command_history.pop(0)


def get_command_history() -> List[Dict[str, Any]]:
    """Get copy of command history."""
    with _history_lock:
        return list(_command_history)


def clear_command_history():
    """Clear command history."""
    global _command_history
    with _history_lock:
        _command_history = []


# ============================================================================
# Secret Redaction
# ============================================================================

def redact_secrets(text: str) -> Tuple[str, int]:
    """Redact potential secrets from text.
    
    Args:
        text: Text to scan for secrets.
        
    Returns:
        Tuple of (redacted_text, count_of_redactions).
    """
    if not text:
        return text, 0
    
    count = 0
    result = text
    
    for pattern in SECRET_PATTERNS:
        matches = list(re.finditer(pattern, result, re.IGNORECASE))
        for match in reversed(matches):  # Reverse to preserve indices
            # Compute hash of secret for debugging
            secret_hash = hashlib.sha256(match.group(0).encode()).hexdigest()[:8]
            replacement = f"[REDACTED-{secret_hash}]"
            result = result[:match.start()] + replacement + result[match.end():]
            count += 1
    
    return result, count


# ============================================================================
# Output Truncation
# ============================================================================

def truncate_output(
    output: str,
    max_lines: int = DEFAULT_OUTPUT_LINES,
    max_chars: int = DEFAULT_OUTPUT_CHARS,
) -> Tuple[str, OutputTruncation, int, int]:
    """Truncate output to limits.
    
    Prefers tail (last N lines) to preserve recent output
    which is usually more relevant.
    
    Args:
        output: Raw output text.
        max_lines: Maximum lines to keep.
        max_chars: Maximum characters to keep.
        
    Returns:
        Tuple of (truncated_output, truncation_type, lines_truncated, chars_truncated).
    """
    if not output:
        return output, OutputTruncation.NONE, 0, 0
    
    lines = output.split('\n')
    original_line_count = len(lines)
    original_char_count = len(output)
    
    lines_truncated = 0
    chars_truncated = 0
    truncation = OutputTruncation.NONE
    
    # First: truncate by lines (tail)
    if len(lines) > max_lines:
        # Keep last N lines (more relevant for debugging)
        omitted = len(lines) - max_lines
        lines = lines[-max_lines:]
        lines.insert(0, f"... ({omitted} lines omitted, showing last {max_lines}) ...")
        lines_truncated = omitted
        truncation = OutputTruncation.LINES
    
    result = '\n'.join(lines)
    
    # Second: truncate by characters if still too long
    if len(result) > max_chars:
        # Keep last N chars
        chars_omitted = len(result) - max_chars
        result = f"... ({chars_omitted} chars omitted) ...\n" + result[-max_chars:]
        chars_truncated = chars_omitted
        truncation = OutputTruncation.BOTH if lines_truncated > 0 else OutputTruncation.CHARS
    
    return result, truncation, lines_truncated, chars_truncated


# ============================================================================
# Timeout Detection
# ============================================================================

def detect_timeout(command: str) -> int:
    """Detect appropriate timeout for a command.
    
    Args:
        command: Command string.
        
    Returns:
        Timeout in seconds.
    """
    # Check for long-running patterns
    for pattern in LONG_RUNNING_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return LONG_COMMAND_TIMEOUT
    
    # Short commands
    if len(command) < 50 and not ('|' in command or '&&' in command):
        return QUICK_COMMAND_TIMEOUT
    
    return DEFAULT_TIMEOUT


# ============================================================================
# Main Execution Functions
# ============================================================================

def run_governed_command(
    command: str,
    cwd: Optional[str] = None,
    timeout: Optional[int] = None,
    env: Optional[Dict[str, str]] = None,
    max_lines: Optional[int] = None,
    max_chars: Optional[int] = None,
    redact: Optional[bool] = None,
) -> CommandResult:
    """Run a shell command with governance.
    
    This is the synchronous version for simple use cases.
    
    Args:
        command: Shell command to execute.
        cwd: Working directory.
        timeout: Timeout in seconds (auto-detected if None).
        env: Environment variables to add.
        max_lines: Max output lines (uses config default if None).
        max_chars: Max output chars (uses config default if None).
        redact: Whether to redact secrets (uses config default if None).
        
    Returns:
        CommandResult with governed output.
    """
    config = GovernorConfig.from_config()
    
    # Apply defaults
    effective_timeout = timeout if timeout is not None else detect_timeout(command)
    effective_max_lines = max_lines if max_lines is not None else config.max_output_lines
    effective_max_chars = max_chars if max_chars is not None else config.max_output_chars
    effective_redact = redact if redact is not None else config.redact_secrets
    
    # Prepare environment
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    
    # Execute
    start_time = time.time()
    timed_out = False
    error_message = None
    
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            env=full_env,
            capture_output=True,
            text=True,
            timeout=effective_timeout,
        )
        exit_code = proc.returncode
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
    except subprocess.TimeoutExpired as e:
        exit_code = -1
        stdout = e.stdout.decode() if e.stdout else ""
        stderr = e.stderr.decode() if e.stderr else ""
        timed_out = True
        error_message = f"Command timed out after {effective_timeout}s"
    except Exception as e:
        exit_code = -1
        stdout = ""
        stderr = str(e)
        error_message = str(e)
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    # Truncate output
    stdout, trunc_type, lines_trunc, chars_trunc = truncate_output(
        stdout, effective_max_lines, effective_max_chars
    )
    stderr, _, _, _ = truncate_output(
        stderr, effective_max_lines // 2, effective_max_chars // 2
    )
    
    # Redact secrets
    secrets_redacted = 0
    if effective_redact:
        stdout, stdout_redactions = redact_secrets(stdout)
        stderr, stderr_redactions = redact_secrets(stderr)
        secrets_redacted = stdout_redactions + stderr_redactions
    
    result = CommandResult(
        command=command,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        elapsed_ms=elapsed_ms,
        truncation=trunc_type,
        lines_truncated=lines_trunc,
        chars_truncated=chars_trunc,
        secrets_redacted=secrets_redacted,
        timed_out=timed_out,
        error_message=error_message,
    )
    
    # Persist to history
    if config.persist_metadata:
        _add_to_history(result)
    
    return result


async def run_governed_command_async(
    command: str,
    cwd: Optional[str] = None,
    timeout: Optional[int] = None,
    env: Optional[Dict[str, str]] = None,
    max_lines: Optional[int] = None,
    max_chars: Optional[int] = None,
    redact: Optional[bool] = None,
) -> CommandResult:
    """Run a shell command with governance (async version).
    
    Args:
        command: Shell command to execute.
        cwd: Working directory.
        timeout: Timeout in seconds (auto-detected if None).
        env: Environment variables to add.
        max_lines: Max output lines (uses config default if None).
        max_chars: Max output chars (uses config default if None).
        redact: Whether to redact secrets (uses config default if None).
        
    Returns:
        CommandResult with governed output.
    """
    config = GovernorConfig.from_config()
    
    # Apply defaults
    effective_timeout = timeout if timeout is not None else detect_timeout(command)
    effective_max_lines = max_lines if max_lines is not None else config.max_output_lines
    effective_max_chars = max_chars if max_chars is not None else config.max_output_chars
    effective_redact = redact if redact is not None else config.redact_secrets
    
    # Prepare environment
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    
    # Execute
    start_time = time.time()
    timed_out = False
    error_message = None
    
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=cwd,
            env=full_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=effective_timeout,
            )
            exit_code = proc.returncode or 0
            stdout = stdout_bytes.decode(errors='replace')
            stderr = stderr_bytes.decode(errors='replace')
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            exit_code = -1
            stdout = ""
            stderr = ""
            timed_out = True
            error_message = f"Command timed out after {effective_timeout}s"
            
    except Exception as e:
        exit_code = -1
        stdout = ""
        stderr = str(e)
        error_message = str(e)
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    # Truncate output
    stdout, trunc_type, lines_trunc, chars_trunc = truncate_output(
        stdout, effective_max_lines, effective_max_chars
    )
    stderr, _, _, _ = truncate_output(
        stderr, effective_max_lines // 2, effective_max_chars // 2
    )
    
    # Redact secrets
    secrets_redacted = 0
    if effective_redact:
        stdout, stdout_redactions = redact_secrets(stdout)
        stderr, stderr_redactions = redact_secrets(stderr)
        secrets_redacted = stdout_redactions + stderr_redactions
    
    result = CommandResult(
        command=command,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        elapsed_ms=elapsed_ms,
        truncation=trunc_type,
        lines_truncated=lines_trunc,
        chars_truncated=chars_trunc,
        secrets_redacted=secrets_redacted,
        timed_out=timed_out,
        error_message=error_message,
    )
    
    # Persist to history
    if config.persist_metadata:
        _add_to_history(result)
    
    return result


# ============================================================================
# Convenience Wrappers
# ============================================================================

def run_quick(command: str, cwd: Optional[str] = None) -> CommandResult:
    """Run a quick command with short timeout.
    
    Args:
        command: Command to run.
        cwd: Working directory.
        
    Returns:
        CommandResult.
    """
    return run_governed_command(command, cwd=cwd, timeout=QUICK_COMMAND_TIMEOUT)


def run_build(command: str, cwd: Optional[str] = None) -> CommandResult:
    """Run a build command with long timeout.
    
    Args:
        command: Build command to run.
        cwd: Working directory.
        
    Returns:
        CommandResult.
    """
    return run_governed_command(command, cwd=cwd, timeout=LONG_COMMAND_TIMEOUT)


def run_with_tail(
    command: str,
    tail_lines: int = 120,
    cwd: Optional[str] = None,
) -> CommandResult:
    """Run a command and limit output to last N lines.
    
    Useful for log-heavy commands.
    
    Args:
        command: Command to run.
        tail_lines: Number of lines to keep.
        cwd: Working directory.
        
    Returns:
        CommandResult with tailed output.
    """
    return run_governed_command(command, cwd=cwd, max_lines=tail_lines)


def format_for_llm(result: CommandResult, include_stderr: bool = True) -> str:
    """Format command result for LLM consumption.
    
    Creates a compact representation suitable for agent context.
    
    Args:
        result: Command result to format.
        include_stderr: Whether to include stderr.
        
    Returns:
        Formatted string.
    """
    parts = []
    
    # Header
    status = "✓" if result.succeeded else "✗"
    parts.append(f"$ {result.command}")
    parts.append(f"[{status} exit={result.exit_code}, {result.elapsed_ms}ms]")
    
    # Warnings
    if result.timed_out:
        parts.append("⚠️ TIMED OUT")
    if result.truncation != OutputTruncation.NONE:
        parts.append(f"⚠️ Output truncated ({result.lines_truncated} lines omitted)")
    if result.secrets_redacted > 0:
        parts.append(f"🔒 {result.secrets_redacted} secrets redacted")
    
    # Output
    if result.stdout:
        parts.append("")
        parts.append(result.stdout)
    
    if include_stderr and result.stderr:
        parts.append("")
        parts.append("[stderr]")
        parts.append(result.stderr)
    
    return "\n".join(parts)
