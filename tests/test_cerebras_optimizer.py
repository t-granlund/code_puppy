"""Tests for cerebras_optimizer module.

Tests the Cerebras-specific token optimization strategies:
- Task type detection
- Optimal max_tokens calculation
- Budget checking
- Sliding window compaction
- Auto-compaction triggers
"""

import pytest
from unittest.mock import MagicMock
from dataclasses import dataclass
from typing import List, Any


# Import the module under test
from code_puppy.tools.cerebras_optimizer import (
    TaskType,
    CEREBRAS_LIMITS,
    CompactionResult,
    TokenBudgetCheck,
    SlidingWindowConfig,
    detect_task_type,
    get_optimal_max_tokens,
    check_cerebras_budget,
    apply_sliding_window,
    should_auto_compact,
    get_cerebras_model_settings_override,
    cerebras_pre_request_hook,
    count_exchanges,
)


# Helper to create mock messages
@dataclass
class MockPart:
    content: str
    tool_call_id: str = None
    tool_name: str = None
    part_kind: str = "text"  # 'text', 'tool-call', or 'tool-return'


@dataclass
class MockMessage:
    parts: List[MockPart]
    kind: str = "request"  # 'request', 'response', or 'system-prompt'


def create_mock_messages(exchanges: int, tokens_per_msg: int = 1000) -> List[MockMessage]:
    """Create mock message history with N exchange pairs."""
    messages = []
    for i in range(exchanges):
        # User message
        user_content = "x" * (tokens_per_msg * 4)  # Approx tokens_per_msg tokens
        messages.append(MockMessage(
            parts=[MockPart(content=f"User query {i}: {user_content}")],
            kind="request"
        ))
        # Assistant response
        asst_content = "y" * (tokens_per_msg * 4)
        messages.append(MockMessage(
            parts=[MockPart(content=f"Response {i}: {asst_content}")],
            kind="response"
        ))
    return messages


class TestTaskTypeDetection:
    """Tests for detect_task_type function."""
    
    def test_detect_tool_call(self):
        """Should detect tool call patterns."""
        messages = [MockMessage(parts=[MockPart("Please read the file config.py")])]
        assert detect_task_type(messages) == TaskType.TOOL_CALL
        
        messages = [MockMessage(parts=[MockPart("list all files in src/")])]
        assert detect_task_type(messages) == TaskType.TOOL_CALL
        
        messages = [MockMessage(parts=[MockPart("grep for 'TODO' in the codebase")])]
        assert detect_task_type(messages) == TaskType.TOOL_CALL
    
    def test_detect_code_generation(self):
        """Should detect code generation patterns."""
        messages = [MockMessage(parts=[MockPart("Create a function to parse JSON")])]
        assert detect_task_type(messages) == TaskType.CODE_GENERATION
        
        messages = [MockMessage(parts=[MockPart("Implement a new feature for auth")])]
        assert detect_task_type(messages) == TaskType.CODE_GENERATION
        
        messages = [MockMessage(parts=[MockPart("Fix the bug in user.py")])]
        assert detect_task_type(messages) == TaskType.CODE_GENERATION
    
    def test_detect_explanation(self):
        """Should detect explanation patterns."""
        messages = [MockMessage(parts=[MockPart("Explain how async/await works")])]
        assert detect_task_type(messages) == TaskType.EXPLANATION
        
        messages = [MockMessage(parts=[MockPart("Why is this pattern used?")])]
        assert detect_task_type(messages) == TaskType.EXPLANATION
    
    def test_detect_planning(self):
        """Should detect planning patterns."""
        messages = [MockMessage(parts=[MockPart("Plan the architecture for this feature")])]
        assert detect_task_type(messages) == TaskType.PLANNING
        
        messages = [MockMessage(parts=[MockPart("What approach should we take?")])]
        assert detect_task_type(messages) == TaskType.PLANNING
    
    def test_detect_review(self):
        """Should detect review patterns."""
        messages = [MockMessage(parts=[MockPart("Review this code for issues")])]
        assert detect_task_type(messages) == TaskType.REVIEW
        
        messages = [MockMessage(parts=[MockPart("Audit the security of this module")])]
        assert detect_task_type(messages) == TaskType.REVIEW
    
    def test_empty_messages_returns_unknown(self):
        """Should return UNKNOWN for empty messages."""
        assert detect_task_type([]) == TaskType.UNKNOWN
    
    def test_ambiguous_returns_unknown(self):
        """Should return UNKNOWN for ambiguous queries."""
        messages = [MockMessage(parts=[MockPart("hello")])]
        assert detect_task_type(messages) == TaskType.UNKNOWN


class TestOptimalMaxTokens:
    """Tests for get_optimal_max_tokens function."""
    
    def test_tool_call_gets_low_limit(self):
        """Tool calls should get low max_tokens."""
        messages = [MockMessage(parts=[MockPart("read file config.py")])]
        max_tokens = get_optimal_max_tokens(messages, "cerebras")
        assert max_tokens == 225  # Scaled: 300 * 0.75 (standard diet for Code Pro plan)
    
    def test_code_gen_gets_high_limit(self):
        """Code generation should get higher max_tokens."""
        messages = [MockMessage(parts=[MockPart("build a new module for auth")])]
        max_tokens = get_optimal_max_tokens(messages, "cerebras")
        assert max_tokens == 3000  # Scaled: 4000 * 0.75 (standard diet for Code Pro plan)
    
    def test_non_cerebras_gets_provider_limit(self):
        """Non-Cerebras providers get their own limits (OpenAI uses 1.0 scale)."""
        messages = [MockMessage(parts=[MockPart("read file")])]
        max_tokens = get_optimal_max_tokens(messages, "openai")
        # OpenAI uses _scale_output_limits(1.0), so tool_call = 300
        assert max_tokens == 300  # Full scale for maintenance tier


class TestBudgetCheck:
    """Tests for check_cerebras_budget function."""
    
    def test_healthy_budget(self):
        """Should report healthy when well under 30% (Code Pro tier)."""
        result = check_cerebras_budget(10_000)  # ~12.5% of 80K - well under threshold
        assert not result.should_compact
        assert not result.should_block
        # At low usage, should not trigger hard limits
        assert "🚫" not in result.recommended_action
    
    def test_should_compact_at_30_percent(self):
        """Should trigger compaction at 30% usage (Code Pro tier)."""
        # 30% of 80K = 24K
        result = check_cerebras_budget(24_001)
        assert result.should_compact
        assert not result.should_block
    
    def test_should_block_at_50_percent(self):
        """Should block at 50% usage (Code Pro tier)."""
        # 50% of 80K = 40K
        result = check_cerebras_budget(40_001)
        assert result.should_compact
        assert result.should_block
        assert "🚫" in result.recommended_action or "HARD LIMIT" in result.recommended_action
    
    def test_usage_percent_calculated_correctly(self):
        """Usage percent should be relative to max tokens."""
        result = check_cerebras_budget(24_000)
        assert result.usage_percent == 0.3  # 24K / 80K = 30%


class TestCountExchanges:
    """Tests for count_exchanges function."""
    
    def test_counts_exchange_pairs(self):
        """Should count user-assistant pairs."""
        messages = create_mock_messages(5)
        assert count_exchanges(messages) == 5
    
    def test_empty_messages(self):
        """Empty messages should return 0."""
        assert count_exchanges([]) == 0
    
    def test_unbalanced_returns_min(self):
        """Unbalanced exchanges should return min count."""
        # 3 user, 2 assistant
        messages = [
            MockMessage(parts=[MockPart("q1")], kind="request"),
            MockMessage(parts=[MockPart("a1")], kind="response"),
            MockMessage(parts=[MockPart("q2")], kind="request"),
            MockMessage(parts=[MockPart("a2")], kind="response"),
            MockMessage(parts=[MockPart("q3")], kind="request"),
        ]
        assert count_exchanges(messages) == 2


class TestSlidingWindow:
    """Tests for apply_sliding_window function."""
    
    def test_keeps_last_n_exchanges(self):
        """Should keep only the last N exchanges."""
        messages = create_mock_messages(10)
        config = SlidingWindowConfig(max_exchanges=3)
        
        def estimate(msg):
            return sum(len(p.content) // 4 for p in msg.parts)
        
        compacted, result = apply_sliding_window(messages, config, estimate)
        
        # Should have 3 exchanges = 6 messages
        assert count_exchanges(compacted) == 3
        assert result.savings_percent > 0
    
    def test_no_compaction_when_under_limit(self):
        """Should not compact when under max_exchanges."""
        messages = create_mock_messages(3)
        config = SlidingWindowConfig(max_exchanges=4)  # Updated to match new limit
        
        def estimate(msg):
            return sum(len(p.content) // 4 for p in msg.parts)
        
        compacted, result = apply_sliding_window(messages, config, estimate)
        
        assert len(compacted) == len(messages)
        assert result.strategy_used == "none_needed"
        assert result.savings_percent == 0.0
    
    def test_preserves_system_messages(self):
        """Should preserve system messages when configured."""
        messages = [
            MockMessage(parts=[MockPart("System instructions")], kind="system-prompt"),
        ] + create_mock_messages(10)
        
        config = SlidingWindowConfig(max_exchanges=2, preserve_system=True)
        
        def estimate(msg):
            return sum(len(p.content) // 4 for p in msg.parts)
        
        compacted, result = apply_sliding_window(messages, config, estimate)
        
        # Should have system + 2 exchanges
        assert compacted[0].kind == "system-prompt"
        assert result.savings_percent > 0
    
    def test_drops_orphaned_tool_results(self):
        """Should drop tool results whose tool_call was dropped."""
        # Simulate pydantic-ai message structure:
        # - ModelResponse (kind='response') contains ToolCallPart (part_kind='tool-call')
        # - ModelRequest (kind='request') contains ToolReturnPart (part_kind='tool-return')
        messages = [
            # Exchange 1 (will be dropped) - user request
            MockMessage(parts=[MockPart("user request 1")], kind="request"),
            # Assistant response with tool call
            MockMessage(parts=[MockPart("calling read_file", tool_call_id="tc_dropped", tool_name="read_file", part_kind="tool-call")], kind="response"),
            # Tool result in a request message (this is how pydantic-ai works)
            MockMessage(parts=[MockPart("file contents", tool_call_id="tc_dropped", tool_name="read_file", part_kind="tool-return")], kind="request"),
            # Assistant response after tool
            MockMessage(parts=[MockPart("here is the file")], kind="response"),
            # Exchange 2 (kept) - user request  
            MockMessage(parts=[MockPart("user request 2")], kind="request"),
            MockMessage(parts=[MockPart("response 2")], kind="response"),
            # Exchange 3 (kept)
            MockMessage(parts=[MockPart("user request 3")], kind="request"),
            MockMessage(parts=[MockPart("final response")], kind="response"),
        ]
        
        config = SlidingWindowConfig(max_exchanges=2)
        
        def estimate(msg):
            return sum(len(p.content) // 4 for p in msg.parts)
        
        compacted, result = apply_sliding_window(messages, config, estimate)
        
        # Should have dropped the orphaned tool-return (the one referencing tc_dropped)
        orphaned_results = [
            m for m in compacted 
            if hasattr(m, 'parts') and any(
                getattr(p, 'part_kind', '') == 'tool-return' and
                getattr(p, 'tool_call_id', '') == 'tc_dropped'
                for p in m.parts
            )
        ]
        assert len(orphaned_results) == 0, "Orphaned tool results should be dropped"
        
        # Should have kept the 2 exchanges (4 messages)
        assert count_exchanges(compacted) == 2


class TestShouldAutoCompact:
    """Tests for should_auto_compact function."""
    
    def test_non_cerebras_never_compacts(self):
        """Non-Cerebras providers should not trigger auto-compact."""
        messages = create_mock_messages(20)  # Many exchanges
        should, reason = should_auto_compact(messages, "openai")
        assert not should
        assert "Not Cerebras" in reason
    
    def test_compacts_on_high_tokens(self):
        """Should compact when tokens exceed threshold."""
        # Create messages with lots of tokens
        messages = create_mock_messages(10, tokens_per_msg=3000)
        
        def estimate(msg):
            return sum(len(p.content) // 4 for p in msg.parts)
        
        should, reason = should_auto_compact(messages, "cerebras", estimate)
        assert should
        assert "usage" in reason.lower() or "%" in reason
    
    def test_compacts_on_high_exchange_count(self):
        """Should compact when exchange count exceeds max."""
        messages = create_mock_messages(10, tokens_per_msg=100)  # Low tokens, many exchanges
        
        def estimate(msg):
            return sum(len(p.content) // 4 for p in msg.parts)
        
        should, reason = should_auto_compact(messages, "cerebras", estimate)
        assert should
        assert "exchange" in reason.lower() or "exceeds" in reason.lower()


class TestModelSettingsOverride:
    """Tests for get_cerebras_model_settings_override function."""
    
    def test_returns_max_tokens(self):
        """Should return max_tokens in override dict."""
        messages = [MockMessage(parts=[MockPart("read file")])]
        overrides = get_cerebras_model_settings_override(messages)
        assert "max_tokens" in overrides
        assert overrides["max_tokens"] <= 4000
    
    def test_respects_base_limit(self):
        """Should not exceed base_max_tokens."""
        messages = [MockMessage(parts=[MockPart("write code")])]
        overrides = get_cerebras_model_settings_override(messages, base_max_tokens=1000)
        assert overrides["max_tokens"] <= 1000


class TestPreRequestHook:
    """Tests for cerebras_pre_request_hook function."""
    
    def test_returns_processed_messages(self):
        """Should return processed messages."""
        messages = create_mock_messages(3)
        processed, settings, status = cerebras_pre_request_hook(messages)
        assert processed is not None
        assert len(processed) > 0
    
    def test_returns_settings_override(self):
        """Should return settings with max_tokens."""
        messages = create_mock_messages(3)
        processed, settings, status = cerebras_pre_request_hook(messages)
        assert "max_tokens" in settings
    
    def test_returns_status_message(self):
        """Should return status message."""
        messages = create_mock_messages(3)
        processed, settings, status = cerebras_pre_request_hook(messages)
        assert isinstance(status, str)
        assert len(status) > 0
    
    def test_compacts_when_needed(self):
        """Should compact when over threshold."""
        # Create messages that will trigger compaction
        messages = create_mock_messages(10, tokens_per_msg=3000)
        
        def estimate(msg):
            return sum(len(p.content) // 4 for p in msg.parts)
        
        processed, settings, status = cerebras_pre_request_hook(messages, estimate)
        
        # Should have compacted
        assert "compact" in status.lower() or "saved" in status.lower()


class TestCerebrasLimits:
    """Tests for CEREBRAS_LIMITS constants (Code Pro tier - relaxed from free tier)."""
    
    def test_compaction_threshold_is_30_percent(self):
        """Compaction threshold should be 30% (Code Pro: $50/month tier)."""
        assert CEREBRAS_LIMITS["compaction_threshold"] == 0.30
    
    def test_hard_limit_is_50_percent(self):
        """Hard limit should be 50% (Code Pro: $50/month tier)."""
        assert CEREBRAS_LIMITS["hard_limit_threshold"] == 0.50
    
    def test_max_exchanges_is_5(self):
        """Max exchanges should be 5 (Code Pro: $50/month tier)."""
        assert CEREBRAS_LIMITS["max_exchanges"] == 5
    
    def test_target_input_is_15k(self):
        """Target input tokens should be 15K (Code Pro: $50/month tier)."""
        assert CEREBRAS_LIMITS["target_input_tokens"] == 15_000
    
    def test_max_input_is_80k(self):
        """Max input tokens should be 80K (Code Pro: $50/month tier)."""
        assert CEREBRAS_LIMITS["max_input_tokens"] == 80_000


class TestCompactionResult:
    """Tests for CompactionResult dataclass."""
    
    def test_tokens_saved_calculation(self):
        """Should correctly calculate tokens saved."""
        result = CompactionResult(
            original_tokens=10000,
            compacted_tokens=4000,
            original_messages=20,
            compacted_messages=8,
            strategy_used="sliding_window",
            savings_percent=60.0
        )
        assert result.tokens_saved == 6000
    
    def test_zero_savings(self):
        """Should handle zero savings."""
        result = CompactionResult(
            original_tokens=1000,
            compacted_tokens=1000,
            original_messages=4,
            compacted_messages=4,
            strategy_used="none_needed",
            savings_percent=0.0
        )
        assert result.tokens_saved == 0
