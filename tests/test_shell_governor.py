"""Tests for Shell Output Governor module.

AUDIT-1.1 Part E test coverage.
"""

import asyncio
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from code_puppy.tools.shell_governor import (
    # Constants
    DEFAULT_OUTPUT_LINES,
    DEFAULT_OUTPUT_CHARS,
    DEFAULT_TIMEOUT,
    QUICK_COMMAND_TIMEOUT,
    LONG_COMMAND_TIMEOUT,
    LONG_RUNNING_PATTERNS,
    SECRET_PATTERNS,
    # Enums
    OutputTruncation,
    # Data classes
    CommandResult,
    GovernorConfig,
    # Functions
    redact_secrets,
    truncate_output,
    detect_timeout,
    run_governed_command,
    run_quick,
    run_build,
    run_with_tail,
    format_for_llm,
    get_command_history,
    clear_command_history,
)


class TestSecretRedaction:
    """Test secret redaction functionality."""
    
    def test_redact_api_key(self):
        """Redact API key patterns."""
        text = "api_key=sk-1234567890abcdefghijklmnop"
        result, count = redact_secrets(text)
        assert "sk-1234567890" not in result
        assert "[REDACTED-" in result
        assert count >= 1
    
    def test_redact_bearer_token(self):
        """Redact bearer tokens."""
        text = 'authorization=Bearer_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
        result, count = redact_secrets(text)
        assert "eyJhbGci" not in result
        assert count >= 1
    
    def test_redact_github_token(self):
        """Redact GitHub tokens."""
        text = "GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        result, count = redact_secrets(text)
        assert "ghp_" not in result
        assert count >= 1
    
    def test_redact_password(self):
        """Redact password patterns."""
        text = "password=mysecretpassword123"
        result, count = redact_secrets(text)
        assert "mysecretpassword" not in result
        assert count >= 1
    
    def test_no_redaction_needed(self):
        """No redaction for clean text."""
        text = "This is just normal log output"
        result, count = redact_secrets(text)
        assert result == text
        assert count == 0
    
    def test_empty_text(self):
        """Handle empty text."""
        result, count = redact_secrets("")
        assert result == ""
        assert count == 0
    
    def test_multiple_secrets(self):
        """Redact multiple secrets."""
        text = """
        API_KEY=abc123456789012345678901234
        TOKEN=def123456789012345678901234
        """
        result, count = redact_secrets(text)
        assert count >= 2


class TestOutputTruncation:
    """Test output truncation functionality."""
    
    def test_no_truncation_needed(self):
        """Short output is not truncated."""
        output = "Line 1\nLine 2\nLine 3"
        result, truncation, lines, chars = truncate_output(output)
        assert result == output
        assert truncation == OutputTruncation.NONE
        assert lines == 0
        assert chars == 0
    
    def test_truncate_by_lines(self):
        """Truncate long output by lines."""
        lines = [f"Line {i}" for i in range(500)]
        output = "\n".join(lines)
        
        result, truncation, lines_trunc, chars_trunc = truncate_output(
            output, max_lines=100
        )
        
        assert truncation in (OutputTruncation.LINES, OutputTruncation.BOTH)
        assert lines_trunc > 0
        assert "omitted" in result
        # Should keep last N lines (tail)
        assert "Line 499" in result
    
    def test_truncate_by_chars(self):
        """Truncate by character count."""
        output = "x" * 50000
        
        result, truncation, _, chars_trunc = truncate_output(
            output, max_chars=10000
        )
        
        assert len(result) <= 10100  # Allow for header
        assert chars_trunc > 0
    
    def test_truncate_both(self):
        """Truncate by both lines and chars."""
        lines = [f"Line {i} " + "x" * 100 for i in range(1000)]
        output = "\n".join(lines)
        
        result, truncation, lines_trunc, chars_trunc = truncate_output(
            output, max_lines=100, max_chars=5000
        )
        
        assert truncation == OutputTruncation.BOTH
        assert lines_trunc > 0
        assert chars_trunc > 0
    
    def test_empty_output(self):
        """Handle empty output."""
        result, truncation, _, _ = truncate_output("")
        assert result == ""
        assert truncation == OutputTruncation.NONE


class TestTimeoutDetection:
    """Test timeout detection for commands."""
    
    def test_quick_command(self):
        """Simple commands get short timeout."""
        timeout = detect_timeout("ls -la")
        assert timeout == QUICK_COMMAND_TIMEOUT
    
    def test_npm_install(self):
        """npm install gets long timeout."""
        timeout = detect_timeout("npm install")
        assert timeout == LONG_COMMAND_TIMEOUT
    
    def test_pytest(self):
        """pytest gets long timeout."""
        timeout = detect_timeout("pytest tests/")
        assert timeout == LONG_COMMAND_TIMEOUT
    
    def test_docker_build(self):
        """docker build gets long timeout."""
        timeout = detect_timeout("docker build -t myimage .")
        assert timeout == LONG_COMMAND_TIMEOUT
    
    def test_pip_install(self):
        """pip install gets long timeout."""
        timeout = detect_timeout("pip install -r requirements.txt")
        assert timeout == LONG_COMMAND_TIMEOUT
    
    def test_complex_command_default(self):
        """Complex command gets default timeout."""
        timeout = detect_timeout("cat file.txt | grep pattern && echo done")
        assert timeout == DEFAULT_TIMEOUT


class TestCommandResult:
    """Test CommandResult data class."""
    
    def test_successful_result(self):
        """Test successful command result."""
        result = CommandResult(
            command="echo hello",
            exit_code=0,
            stdout="hello\n",
            stderr="",
            elapsed_ms=50,
            truncation=OutputTruncation.NONE,
        )
        assert result.succeeded
        assert "hello" in result.combined_output
    
    def test_failed_result(self):
        """Test failed command result."""
        result = CommandResult(
            command="false",
            exit_code=1,
            stdout="",
            stderr="error",
            elapsed_ms=10,
            truncation=OutputTruncation.NONE,
        )
        assert not result.succeeded
    
    def test_timed_out_result(self):
        """Test timed out command result."""
        result = CommandResult(
            command="sleep 1000",
            exit_code=-1,
            stdout="",
            stderr="",
            elapsed_ms=30000,
            truncation=OutputTruncation.NONE,
            timed_out=True,
        )
        assert not result.succeeded
        assert result.timed_out
    
    def test_to_dict(self):
        """Test serialization to dict."""
        result = CommandResult(
            command="echo test",
            exit_code=0,
            stdout="test",
            stderr="",
            elapsed_ms=100,
            truncation=OutputTruncation.LINES,
            lines_truncated=50,
        )
        data = result.to_dict()
        
        assert data["command"] == "echo test"
        assert data["exit_code"] == 0
        assert data["truncation"] == "lines"
        assert data["lines_truncated"] == 50


class TestGovernorConfig:
    """Test GovernorConfig loading."""
    
    def test_default_config(self):
        """Default config values."""
        config = GovernorConfig()
        assert config.max_output_lines == DEFAULT_OUTPUT_LINES
        assert config.max_output_chars == DEFAULT_OUTPUT_CHARS
        assert config.default_timeout == DEFAULT_TIMEOUT
        assert config.redact_secrets is True
    
    def test_config_from_settings(self):
        """Load config from settings."""
        with patch("code_puppy.tools.shell_governor.get_value") as mock_get:
            mock_get.side_effect = lambda k: {
                "shell_max_output_lines": "100",
                "shell_max_output_chars": "20000",
                "shell_default_timeout": "60",
                "shell_redact_secrets": "false",
            }.get(k)
            
            config = GovernorConfig.from_config()
            assert config.max_output_lines == 100
            assert config.max_output_chars == 20000
            assert config.default_timeout == 60
            assert config.redact_secrets is False


class TestRunGovernedCommand:
    """Test governed command execution."""
    
    def test_run_simple_command(self):
        """Run a simple echo command."""
        result = run_governed_command("echo 'hello world'")
        assert result.succeeded
        assert "hello world" in result.stdout
    
    def test_run_failing_command(self):
        """Run a failing command."""
        result = run_governed_command("exit 1")
        assert not result.succeeded
        assert result.exit_code == 1
    
    def test_run_with_cwd(self):
        """Run command in specific directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_governed_command("pwd", cwd=tmpdir)
            assert result.succeeded
            assert tmpdir in result.stdout or os.path.basename(tmpdir) in result.stdout
    
    def test_output_truncation(self):
        """Test output is truncated."""
        # Generate lots of output
        result = run_governed_command(
            "seq 1 1000",
            max_lines=50,
        )
        assert result.truncation != OutputTruncation.NONE
        assert result.lines_truncated > 0
    
    def test_secret_redaction(self):
        """Test secrets are redacted."""
        result = run_governed_command(
            "echo 'API_KEY=sk-1234567890abcdefghijklmnopqrstuvwxyz'",
            redact=True,
        )
        assert "sk-1234567890" not in result.stdout
        assert result.secrets_redacted > 0


class TestConvenienceWrappers:
    """Test convenience wrapper functions."""
    
    def test_run_quick(self):
        """Test quick command wrapper."""
        result = run_quick("echo quick")
        assert result.succeeded
    
    def test_run_with_tail(self):
        """Test tail wrapper."""
        result = run_with_tail("seq 1 500", tail_lines=50)
        # Should only show last 50 lines
        assert "500" in result.stdout
        assert result.lines_truncated > 0


class TestFormatForLLM:
    """Test LLM-friendly formatting."""
    
    def test_format_success(self):
        """Format successful result."""
        result = CommandResult(
            command="echo test",
            exit_code=0,
            stdout="test output",
            stderr="",
            elapsed_ms=50,
            truncation=OutputTruncation.NONE,
        )
        formatted = format_for_llm(result)
        
        assert "echo test" in formatted
        assert "✓" in formatted
        assert "test output" in formatted
    
    def test_format_failure(self):
        """Format failed result."""
        result = CommandResult(
            command="bad command",
            exit_code=1,
            stdout="",
            stderr="command not found",
            elapsed_ms=10,
            truncation=OutputTruncation.NONE,
        )
        formatted = format_for_llm(result)
        
        assert "✗" in formatted
        assert "stderr" in formatted.lower()
    
    def test_format_with_truncation(self):
        """Format result with truncation warning."""
        result = CommandResult(
            command="seq 1 1000",
            exit_code=0,
            stdout="output",
            stderr="",
            elapsed_ms=100,
            truncation=OutputTruncation.LINES,
            lines_truncated=900,
        )
        formatted = format_for_llm(result)
        
        assert "truncated" in formatted.lower()
        assert "900" in formatted
    
    def test_format_with_redaction(self):
        """Format result with redaction notice."""
        result = CommandResult(
            command="echo secret",
            exit_code=0,
            stdout="[REDACTED-abc123]",
            stderr="",
            elapsed_ms=50,
            truncation=OutputTruncation.NONE,
            secrets_redacted=1,
        )
        formatted = format_for_llm(result)
        
        assert "🔒" in formatted
        assert "1 secrets redacted" in formatted.lower() or "1 secret" in formatted.lower()


class TestCommandHistory:
    """Test command history tracking."""
    
    def test_history_tracking(self):
        """Commands are tracked in history."""
        clear_command_history()
        
        run_governed_command("echo test1")
        run_governed_command("echo test2")
        
        history = get_command_history()
        assert len(history) >= 2
    
    def test_history_clear(self):
        """History can be cleared."""
        run_governed_command("echo test")
        clear_command_history()
        
        history = get_command_history()
        assert len(history) == 0
