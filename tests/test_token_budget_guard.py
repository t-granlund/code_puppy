"""Tests for token budget guard utilities."""

import pytest

from code_puppy.tools.token_budget_guard import (
    calculate_remaining_budget,
    estimate_file_tokens,
    estimate_tokens,
    format_token_warning,
    limit_diff_output,
    limit_output,
    suggest_narrow_request,
)


class TestEstimateTokens:
    """Tests for token estimation functions."""

    def test_empty_string(self):
        """Empty string returns 0 tokens."""
        assert estimate_tokens("") == 0

    def test_short_string(self):
        """Short strings return at least 1 token."""
        assert estimate_tokens("hi") >= 1

    def test_typical_code(self):
        """Typical code line estimates reasonably."""
        code = "def hello_world():\n    print('Hello, World!')"
        tokens = estimate_tokens(code)
        # ~2.5 chars per token, so variable estimate for 45 chars
        assert 5 <= tokens <= 50

    def test_estimate_file_tokens(self):
        """File token estimation works."""
        content = "line1\nline2\nline3\n" * 100
        tokens = estimate_file_tokens(content)
        assert tokens > 0


class TestLimitOutput:
    """Tests for output limiting function."""

    def test_short_output_unchanged(self):
        """Short output is not truncated."""
        output = "line1\nline2\nline3"
        result, truncated = limit_output(output, max_lines=10)
        assert result == output
        assert truncated is False

    def test_long_output_truncated(self):
        """Long output is truncated with header."""
        lines = [f"line{i}" for i in range(100)]
        output = "\n".join(lines)
        result, truncated = limit_output(output, max_lines=10)
        
        assert truncated is True
        assert "[... 90 lines truncated ...]" in result
        assert "line99" in result  # Last line preserved
        assert "line0" not in result  # First line removed

    def test_empty_output(self):
        """Empty output returns empty."""
        result, truncated = limit_output("", max_lines=10)
        assert result == ""
        assert truncated is False


class TestLimitDiffOutput:
    """Tests for diff output limiting."""

    def test_short_diff_unchanged(self):
        """Short diff is not truncated."""
        diff = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 line1
+new line
 line2"""
        result, truncated = limit_diff_output(diff, max_lines=20)
        assert result == diff
        assert truncated is False

    def test_long_diff_truncated(self):
        """Long diff is truncated with notice."""
        lines = ["--- a/file.py", "+++ b/file.py", "@@ -1,100 +1,100 @@"]
        lines.extend([f" line{i}" for i in range(200)])
        diff = "\n".join(lines)
        
        result, truncated = limit_diff_output(diff, max_lines=20)
        
        assert truncated is True
        assert "--- a/file.py" in result  # Header preserved
        assert "+++ b/file.py" in result
        assert "more lines in diff" in result


class TestFormatTokenWarning:
    """Tests for token warning formatting."""

    def test_no_warning_under_70_percent(self):
        """No warning when under 70% usage."""
        assert format_token_warning(30000, 50000) == ""

    def test_warning_at_80_percent(self):
        """Warning shown at 80% usage."""
        result = format_token_warning(40000, 50000)
        assert "⚠️" in result
        assert "80%" in result

    def test_critical_at_95_percent(self):
        """Critical warning at 95% usage."""
        result = format_token_warning(47500, 50000)
        assert "🚨" in result
        assert "CRITICAL" in result


class TestSuggestNarrowRequest:
    """Tests for request narrowing suggestions."""

    def test_file_read_suggestion(self):
        """File read suggestions include head/sed/grep."""
        result = suggest_narrow_request("file_read")
        assert "head" in result
        assert "sed" in result or "grep" in result

    def test_command_suggestion(self):
        """Command suggestions include tail and pytest flags."""
        result = suggest_narrow_request("command")
        assert "tail" in result
        assert "pytest" in result

    def test_unknown_type_fallback(self):
        """Unknown type returns generic suggestion."""
        result = suggest_narrow_request("unknown_type")
        assert "narrow" in result.lower()


class TestCalculateRemainingBudget:
    """Tests for remaining budget calculation."""

    def test_remaining_budget_calculation(self):
        """Remaining budget is calculated correctly."""
        result = calculate_remaining_budget(30000, 50000)
        
        assert result["remaining_tokens"] == 20000
        assert result["approx_chars"] == 40000
        assert result["is_critical"] is False
        assert result["is_warning"] is False

    def test_critical_threshold(self):
        """Critical is set when under 10% remaining."""
        result = calculate_remaining_budget(46000, 50000)
        
        assert result["remaining_tokens"] == 4000
        assert result["is_critical"] is True

    def test_warning_threshold(self):
        """Warning is set when under 30% remaining."""
        result = calculate_remaining_budget(40000, 50000)
        
        assert result["remaining_tokens"] == 10000
        assert result["is_warning"] is True
        assert result["is_critical"] is False
