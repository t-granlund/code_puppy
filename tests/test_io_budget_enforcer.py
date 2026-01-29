"""Tests for IO Budget Enforcer module.

AUDIT-1.1 Part D test coverage.
"""

import pytest
from unittest.mock import patch, MagicMock

from code_puppy.tools.io_budget_enforcer import (
    # Constants
    PROVIDER_BUDGETS,
    DEFAULT_MAX_FILE_LINES,
    DEFAULT_MAX_FILE_TOKENS,
    SLICE_REQUIRED_THRESHOLD,
    # Enums
    BudgetViolation,
    NarrowingMode,
    # Data classes
    BudgetCheckResult,
    IterationTracker,
    FileReadPolicy,
    CompactionSummary,
    # Functions
    get_provider_budget,
    get_max_input_tokens,
    get_hard_fail_threshold,
    is_hard_fail_enabled,
    estimate_tokens,
    estimate_message_tokens,
    check_budget,
    check_iteration_compaction,
    get_narrowing_instructions,
    get_file_read_policy,
    check_file_read,
    extract_compaction_summary,
    get_iteration_tracker,
    reset_iteration_tracker,
)


class TestProviderBudgets:
    """Test provider budget configuration."""
    
    def test_cerebras_budget_exists(self):
        """Cerebras has specific budget config."""
        budget = get_provider_budget("cerebras")
        assert budget["max_input_tokens"] == 50000
        assert budget["max_output_tokens"] == 8192
    
    def test_default_budget_fallback(self):
        """Unknown providers get default budget."""
        budget = get_provider_budget("unknown_provider")
        assert budget == PROVIDER_BUDGETS["default"]
    
    def test_case_insensitive_lookup(self):
        """Provider lookup is case-insensitive."""
        budget_lower = get_provider_budget("cerebras")
        budget_upper = get_provider_budget("CEREBRAS")
        assert budget_lower == budget_upper
    
    def test_get_max_input_tokens(self):
        """Get max input tokens for provider."""
        assert get_max_input_tokens("cerebras") == 50000
        assert get_max_input_tokens("anthropic") == 180000
    
    def test_get_hard_fail_threshold(self):
        """Get hard fail threshold."""
        threshold = get_hard_fail_threshold("cerebras")
        assert 0 < threshold <= 1.0
        assert threshold == 0.95


class TestTokenEstimation:
    """Test token estimation functions."""
    
    def test_estimate_tokens_empty(self):
        """Empty string returns 0."""
        assert estimate_tokens("") == 0
    
    def test_estimate_tokens_short_text(self):
        """Short text estimation."""
        text = "Hello world"
        tokens = estimate_tokens(text)
        assert tokens > 0
        assert tokens < len(text)  # Should be less than char count
    
    def test_estimate_tokens_code(self):
        """Code estimation is conservative."""
        code = """
def hello_world():
    print("Hello, World!")
    return True
"""
        tokens = estimate_tokens(code)
        # Should produce some reasonable token count
        assert tokens > 0
        # The formula is len//2 + len//5, roughly 0.7 * len
        # For code, this should be less than the raw character count
        assert tokens < len(code)
    
    def test_estimate_message_tokens(self):
        """Estimate tokens for message list."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        tokens = estimate_message_tokens(messages)
        assert tokens > 0
        # Should include overhead
        assert tokens > estimate_tokens("Hello") + estimate_tokens("Hi there!")
    
    def test_estimate_message_tokens_multipart(self):
        """Handle multipart content."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Hello"},
                    {"type": "image", "url": "..."},
                ],
            }
        ]
        tokens = estimate_message_tokens(messages)
        assert tokens > 0


class TestBudgetChecking:
    """Test budget checking logic."""
    
    def test_check_budget_under_limit(self):
        """Check budget under all thresholds."""
        result = check_budget(10000, "cerebras")
        assert result.violation == BudgetViolation.NONE
        assert not result.should_refuse
        assert not result.should_compact
        assert not result.should_warn
    
    def test_check_budget_warning(self):
        """Check budget at warning threshold."""
        # 70% of 50000 = 35000
        result = check_budget(36000, "cerebras")
        assert result.violation in (BudgetViolation.WARNING, BudgetViolation.COMPACTION_NEEDED)
        assert result.should_warn
        assert not result.should_refuse
    
    def test_check_budget_compaction_needed(self):
        """Check budget at compaction threshold."""
        # 70% threshold
        result = check_budget(36000, "cerebras")
        assert result.violation == BudgetViolation.COMPACTION_NEEDED
        assert result.should_compact
    
    @patch("code_puppy.tools.io_budget_enforcer.is_hard_fail_enabled")
    def test_check_budget_hard_fail(self, mock_enabled):
        """Check budget at hard fail threshold."""
        mock_enabled.return_value = True
        # 95% of 50000 = 47500
        result = check_budget(48000, "cerebras")
        assert result.violation == BudgetViolation.HARD_FAIL
        assert result.should_refuse
    
    @patch("code_puppy.tools.io_budget_enforcer.is_hard_fail_enabled")
    def test_hard_fail_disabled(self, mock_enabled):
        """Hard fail can be disabled."""
        mock_enabled.return_value = False
        result = check_budget(48000, "cerebras")
        # Should still warn but not refuse
        assert result.violation != BudgetViolation.HARD_FAIL
        assert not result.should_refuse
    
    def test_budget_check_result_properties(self):
        """Test BudgetCheckResult properties."""
        result = BudgetCheckResult(
            violation=BudgetViolation.HARD_FAIL,
            current_tokens=48000,
            max_tokens=50000,
            usage_percent=0.96,
            message="Test",
        )
        assert result.should_refuse
        assert result.usage_percent == 0.96


class TestIterationTracker:
    """Test iteration tracking for auto-compaction."""
    
    def test_iteration_increment(self):
        """Test iteration counter."""
        tracker = IterationTracker()
        assert tracker.iteration_count == 0
        
        tracker.increment(input_tokens=1000, output_tokens=500)
        assert tracker.iteration_count == 1
        assert tracker.total_input_tokens == 1000
        assert tracker.total_output_tokens == 500
    
    def test_compaction_trigger(self):
        """Test compaction trigger after iterations."""
        tracker = IterationTracker()
        
        assert not tracker.should_trigger_compaction(2)
        
        tracker.increment()
        tracker.increment()
        
        assert tracker.should_trigger_compaction(2)
    
    def test_compaction_recording(self):
        """Test recording compaction resets counter."""
        tracker = IterationTracker()
        tracker.increment()
        tracker.increment()
        
        tracker.record_compaction()
        assert not tracker.should_trigger_compaction(2)
        
        # But after 2 more, should trigger again
        tracker.increment()
        tracker.increment()
        assert tracker.should_trigger_compaction(2)
    
    def test_global_tracker(self):
        """Test global tracker access."""
        reset_iteration_tracker()
        tracker = get_iteration_tracker()
        assert tracker.iteration_count == 0


class TestNarrowingInstructions:
    """Test context narrowing instructions."""
    
    def test_diff_only_instructions(self):
        """Get diff-only mode instructions."""
        instructions = get_narrowing_instructions(NarrowingMode.DIFF_ONLY)
        assert "DIFF ONLY" in instructions
        assert "git diff" in instructions
    
    def test_file_slice_instructions(self):
        """Get file slice mode instructions."""
        instructions = get_narrowing_instructions(NarrowingMode.FILE_SLICE)
        assert "FILE SLICE" in instructions
        assert "line ranges" in instructions
    
    def test_log_tail_instructions(self):
        """Get log tail mode instructions."""
        instructions = get_narrowing_instructions(NarrowingMode.LOG_TAIL)
        assert "LOG TAIL" in instructions
        assert "tail" in instructions
    
    def test_error_only_instructions(self):
        """Get error-only mode instructions."""
        instructions = get_narrowing_instructions(NarrowingMode.ERROR_ONLY)
        assert "ERROR ONLY" in instructions
        assert "error" in instructions.lower()


class TestFileReadPolicy:
    """Test file read guardrails."""
    
    def test_default_policy(self):
        """Default policy values."""
        policy = FileReadPolicy()
        assert policy.max_lines == DEFAULT_MAX_FILE_LINES
        assert policy.max_tokens == DEFAULT_MAX_FILE_TOKENS
        assert policy.require_slice_above == SLICE_REQUIRED_THRESHOLD
    
    def test_check_small_file_allowed(self):
        """Small files are allowed without slice."""
        allowed, message, suggested = check_file_read(
            file_path="test.py",
            line_count=100,
        )
        assert allowed
        assert message == ""
    
    def test_check_large_file_blocked(self):
        """Large files without slice are blocked."""
        allowed, message, suggested = check_file_read(
            file_path="big.py",
            line_count=1000,  # Above threshold
        )
        assert not allowed
        assert "blocked" in message.lower()
        assert suggested is not None
    
    def test_check_explicit_slice_allowed(self):
        """Explicit slice within limits is allowed."""
        allowed, message, suggested = check_file_read(
            file_path="big.py",
            line_count=1000,
            start_line=100,
            end_line=200,  # 101 lines, within limit
        )
        assert allowed
    
    def test_check_large_slice_rejected(self):
        """Too-large slice is rejected."""
        allowed, message, suggested = check_file_read(
            file_path="big.py",
            line_count=1000,
            start_line=1,
            end_line=500,  # 500 lines, above 300 default
        )
        assert not allowed
        assert suggested is not None
        assert suggested[1] - suggested[0] < 500


class TestCompactionSummary:
    """Test compaction summary generation."""
    
    def test_empty_summary(self):
        """Empty summary produces valid markdown."""
        summary = CompactionSummary()
        markdown = summary.to_markdown()
        assert "Session Summary" in markdown
    
    def test_summary_with_data(self):
        """Summary with data formats correctly."""
        summary = CompactionSummary(
            goals=["Fix bug", "Add feature"],
            current_branch="feature/test",
            changed_files=["file1.py", "file2.py"],
            failing_commands=["pytest test_x.py"],
            current_hypothesis="The issue is in the config",
            next_actions=["Check config", "Add logging"],
        )
        markdown = summary.to_markdown()
        
        assert "feature/test" in markdown
        assert "Fix bug" in markdown
        assert "file1.py" in markdown
        assert "pytest" in markdown
    
    def test_summary_to_dict(self):
        """Summary converts to dict."""
        summary = CompactionSummary(
            goals=["Test"],
            current_branch="main",
        )
        data = summary.to_dict()
        
        assert data["goals"] == ["Test"]
        assert data["current_branch"] == "main"
        assert "timestamp" in data
    
    def test_extract_summary_from_messages(self):
        """Extract summary from message history."""
        messages = [
            {"role": "user", "content": "Working on branch: `feature/audit`"},
            {"role": "assistant", "content": "I'll edit `config.py` and `main.py`"},
            {"role": "user", "content": "I got an error running `pytest`"},
        ]
        summary = extract_compaction_summary(messages)
        
        assert summary.current_branch == "feature/audit"
        assert "config.py" in summary.changed_files or "main.py" in summary.changed_files


class TestIntegration:
    """Integration tests for IO budget enforcer."""
    
    def test_full_budget_flow(self):
        """Test complete budget checking flow."""
        # Start fresh
        reset_iteration_tracker()
        tracker = get_iteration_tracker()
        
        # Simulate iterations
        tracker.increment(input_tokens=15000, output_tokens=2000)
        result1 = check_budget(15000, "cerebras")
        assert result1.violation == BudgetViolation.NONE
        
        tracker.increment(input_tokens=20000, output_tokens=3000)
        # Now at iteration 2, should trigger compaction check
        should_compact, reason = check_iteration_compaction()
        assert should_compact
    
    def test_budget_with_provider_override(self):
        """Test budget with config override."""
        with patch("code_puppy.tools.io_budget_enforcer.get_value") as mock_get:
            mock_get.return_value = "30000"  # Override cerebras budget
            budget = get_provider_budget("cerebras")
            # Still uses default structure but with overridden value
            assert budget["max_input_tokens"] == 30000
