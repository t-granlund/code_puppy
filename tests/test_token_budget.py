"""Tests for core/token_budget.py - Token Budget Manager."""

import asyncio
import time
from unittest.mock import patch

import pytest

from code_puppy.core.token_budget import (
    BudgetCheckResult,
    ProviderBudget,
    TokenBudgetManager,
    smart_retry,
)


class TestProviderBudget:
    """Tests for ProviderBudget dataclass."""
    
    def test_reset_minute_if_needed(self):
        """Should reset minute counter after window passes."""
        budget = ProviderBudget(
            tokens_per_minute=100_000,
            tokens_per_day=1_000_000,
            reset_window_seconds=60,
        )
        budget.tokens_used_this_minute = 50_000
        budget.last_minute_reset = time.time() - 61  # Window passed
        
        budget.reset_minute_if_needed()
        
        assert budget.tokens_used_this_minute == 0
    
    def test_no_reset_within_window(self):
        """Should not reset if still within window."""
        budget = ProviderBudget(
            tokens_per_minute=100_000,
            tokens_per_day=1_000_000,
            reset_window_seconds=60,
        )
        budget.tokens_used_this_minute = 50_000
        budget.last_minute_reset = time.time() - 30  # Within window
        
        budget.reset_minute_if_needed()
        
        assert budget.tokens_used_this_minute == 50_000
    
    def test_remaining_minute_calculation(self):
        """Should calculate remaining tokens correctly."""
        budget = ProviderBudget(
            tokens_per_minute=100_000,
            tokens_per_day=1_000_000,
        )
        budget.tokens_used_this_minute = 30_000
        
        assert budget.remaining_minute == 70_000
    
    def test_usage_percent_minute(self):
        """Should calculate usage percentage correctly."""
        budget = ProviderBudget(
            tokens_per_minute=100_000,
            tokens_per_day=1_000_000,
        )
        budget.tokens_used_this_minute = 50_000
        
        assert budget.usage_percent_minute == 0.5


class TestTokenBudgetManager:
    """Tests for TokenBudgetManager singleton."""
    
    def test_singleton_pattern(self):
        """Should return same instance."""
        mgr1 = TokenBudgetManager()
        mgr2 = TokenBudgetManager()
        
        assert mgr1 is mgr2
    
    def test_check_budget_within_limits(self):
        """Should allow request within limits."""
        mgr = TokenBudgetManager()
        mgr.reset_provider("cerebras")
        
        result = mgr.check_budget("cerebras", 10_000)
        
        assert result.can_proceed
        assert result.provider == "cerebras"
    
    def test_check_budget_exceeds_minute_limit(self):
        """Should block when exceeding minute limit."""
        mgr = TokenBudgetManager()
        mgr.reset_provider("cerebras")
        
        # Use up most of the budget
        mgr._budgets["cerebras"].tokens_used_this_minute = 290_000
        
        result = mgr.check_budget("cerebras", 20_000)
        
        assert not result.can_proceed
        assert result.wait_seconds > 0 or result.failover_to is not None
    
    def test_normalize_provider(self):
        """Should normalize model names to providers."""
        mgr = TokenBudgetManager()
        
        assert mgr._normalize_provider("cerebras-glm-4.7") == "cerebras"
        assert mgr._normalize_provider("gemini-3-flash") == "gemini_flash"
        assert mgr._normalize_provider("claude-opus-4.5") == "claude_opus"
    
    def test_record_usage(self):
        """Should record token usage."""
        mgr = TokenBudgetManager()
        mgr.reset_provider("cerebras")
        
        initial = mgr._budgets["cerebras"].tokens_used_this_minute
        mgr.record_usage("cerebras", 5_000)
        
        assert mgr._budgets["cerebras"].tokens_used_this_minute == initial + 5_000
    
    def test_record_429_exponential_backoff(self):
        """Should increase wait time on consecutive 429s."""
        mgr = TokenBudgetManager()
        mgr.reset_provider("cerebras")
        
        wait1, _ = mgr.record_429("cerebras")
        wait2, _ = mgr.record_429("cerebras")
        wait3, failover = mgr.record_429("cerebras")
        
        # Wait times should increase
        assert wait2 > wait1
        assert wait3 > wait2
        # Should suggest failover after 3 429s
        assert failover == "gemini_flash"
    
    def test_failover_chain(self):
        """Should suggest failover when budget exceeded."""
        mgr = TokenBudgetManager()
        mgr.reset_provider("cerebras")
        
        # Exhaust cerebras daily budget
        mgr._budgets["cerebras"].tokens_used_today = 24_000_000
        
        result = mgr.check_budget("cerebras", 10_000, allow_failover=True)
        
        assert not result.can_proceed
        assert result.failover_to == "gemini_flash"


class TestSmartRetry:
    """Tests for smart_retry decorator."""
    
    @pytest.mark.asyncio
    async def test_successful_call(self):
        """Should return result on success."""
        @smart_retry("cerebras", max_retries=3)
        async def mock_call():
            return "success"
        
        result = await mock_call()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_on_429(self):
        """Should retry on 429 error."""
        call_count = 0
        
        @smart_retry("gemini", max_retries=3, max_wait=0.1)
        async def mock_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("429 Too Many Requests")
            return "success"
        
        result = await mock_call()
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_no_retry_on_other_errors(self):
        """Should not retry on non-rate-limit errors."""
        @smart_retry("cerebras", max_retries=3)
        async def mock_call():
            raise ValueError("Something else broke")
        
        with pytest.raises(ValueError):
            await mock_call()
