"""Tests for rate limit failover system."""

import asyncio
import pytest
from unittest.mock import patch, MagicMock

from code_puppy.core.rate_limit_failover import (
    RateLimitFailover,
    FailoverTarget,
    FailoverPriority,
    get_failover_manager,
    with_rate_limit_failover,
    enhanced_failover_chain,
)


class TestRateLimitFailover:
    """Tests for RateLimitFailover class."""

    def setup_method(self):
        """Reset singleton for each test."""
        RateLimitFailover._instance = None

    def test_singleton_pattern(self):
        """Should return same instance."""
        mgr1 = RateLimitFailover()
        mgr2 = RateLimitFailover()
        assert mgr1 is mgr2

    def test_get_failover_manager(self):
        """Should return global singleton."""
        mgr = get_failover_manager()
        assert isinstance(mgr, RateLimitFailover)

    def test_detect_tier_opus(self):
        """Should detect Opus as Architect tier."""
        mgr = RateLimitFailover()
        assert mgr._detect_tier("claude-opus-4.5") == 1

    def test_detect_tier_sonnet(self):
        """Should detect Sonnet as Builder Mid tier."""
        mgr = RateLimitFailover()
        assert mgr._detect_tier("claude-sonnet-4.5") == 3

    def test_detect_tier_gemini(self):
        """Should detect Gemini as Librarian tier."""
        mgr = RateLimitFailover()
        assert mgr._detect_tier("gemini-3-flash") == 4

    def test_detect_tier_cerebras(self):
        """Should detect Cerebras as Sprinter tier."""
        mgr = RateLimitFailover()
        assert mgr._detect_tier("cerebras-glm-4.7") == 5

    def test_detect_tier_unknown(self):
        """Should default to Librarian for unknown."""
        mgr = RateLimitFailover()
        assert mgr._detect_tier("unknown-model") == 4

    def test_detect_tier_antigravity_opus(self):
        """Should detect Antigravity Opus as Architect tier."""
        mgr = RateLimitFailover()
        assert mgr._detect_tier("antigravity-claude-opus-4-5-thinking-high") == 1

    def test_detect_tier_antigravity_sonnet(self):
        """Should detect Antigravity Sonnet as Builder tier."""
        mgr = RateLimitFailover()
        # High thinking = Builder High (tier 2)
        assert mgr._detect_tier("antigravity-claude-sonnet-4-5-thinking-high") == 2
        # Regular sonnet = Builder Mid (tier 3)
        assert mgr._detect_tier("antigravity-claude-sonnet-4-5") == 3

    def test_detect_tier_antigravity_gemini(self):
        """Should detect Antigravity Gemini as Librarian tier."""
        mgr = RateLimitFailover()
        assert mgr._detect_tier("antigravity-gemini-3-flash") == 4
        assert mgr._detect_tier("antigravity-gemini-3-pro-high") == 4

    def test_detect_provider_antigravity(self):
        """Should detect Antigravity provider correctly."""
        mgr = RateLimitFailover()
        assert mgr._detect_provider("antigravity-gemini-3-flash", {}) == "antigravity_gemini"
        assert mgr._detect_provider("antigravity-claude-sonnet-4-5", {}) == "antigravity_claude"

    def test_load_fallback_models(self):
        """Should load fallback models when factory fails."""
        mgr = RateLimitFailover()
        mgr._load_fallback_models()
        assert "gemini-3-flash" in mgr._available_models
        assert "claude-sonnet-4.5" in mgr._available_models

    def test_build_failover_chains(self):
        """Should build chains preferring same tier."""
        mgr = RateLimitFailover()
        mgr._load_fallback_models()
        
        # Check that chains exist
        assert len(mgr._failover_chains) > 0
        
        # Check cerebras has failover
        if "cerebras-glm-4.7" in mgr._failover_chains:
            chain = mgr._failover_chains["cerebras-glm-4.7"]
            assert len(chain) > 0

    def test_get_failover_chain(self):
        """Should return ordered failover list."""
        mgr = RateLimitFailover()
        mgr._load_fallback_models()
        mgr._loaded = True
        
        chain = mgr.get_failover_chain("cerebras-glm-4.7")
        assert isinstance(chain, list)

    def test_record_rate_limit(self):
        """Should mark model as rate-limited and return failover."""
        mgr = RateLimitFailover()
        mgr._load_fallback_models()
        mgr._loaded = True
        
        # Create a mock event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            failover = mgr.record_rate_limit("cerebras-glm-4.7", 0.1)
            
            # Should be marked as rate-limited
            assert mgr.is_rate_limited("cerebras-glm-4.7")
            
            # Should have suggested a failover
            assert failover != "cerebras-glm-4.7"
        finally:
            loop.close()

    def test_is_rate_limited(self):
        """Should track rate-limited models."""
        mgr = RateLimitFailover()
        mgr._load_fallback_models()
        
        assert not mgr.is_rate_limited("test-model")
        mgr._rate_limited.add("test-model")
        assert mgr.is_rate_limited("test-model")

    def test_get_available_models_excludes_rate_limited(self):
        """Should exclude rate-limited models by default."""
        mgr = RateLimitFailover()
        mgr._load_fallback_models()
        mgr._loaded = True
        
        all_models = mgr.get_available_models(exclude_rate_limited=False)
        mgr._rate_limited.add(all_models[0])
        
        available = mgr.get_available_models(exclude_rate_limited=True)
        assert all_models[0] not in available


class TestEnhancedFailoverChain:
    """Tests for enhanced_failover_chain function."""

    def setup_method(self):
        """Reset singleton for each test."""
        RateLimitFailover._instance = None

    def test_returns_dict(self):
        """Should return a dict mapping models to failovers."""
        chain = enhanced_failover_chain()
        assert isinstance(chain, dict)


class TestWithRateLimitFailoverDecorator:
    """Tests for with_rate_limit_failover decorator."""

    def setup_method(self):
        """Reset singleton for each test."""
        RateLimitFailover._instance = None

    @pytest.mark.asyncio
    async def test_successful_call_no_failover(self):
        """Should pass through on successful calls."""
        @with_rate_limit_failover(model_param="model")
        async def mock_api(prompt: str, model: str = "test") -> str:
            return f"result from {model}"
        
        result = await mock_api("hello", model="cerebras")
        assert result == "result from cerebras"

    @pytest.mark.asyncio
    async def test_failover_on_429(self):
        """Should failover on 429 error."""
        mgr = RateLimitFailover()
        mgr._load_fallback_models()
        mgr._loaded = True
        
        call_count = 0
        
        @with_rate_limit_failover(model_param="model", max_failovers=2)
        async def mock_api(prompt: str, model: str = "cerebras-glm-4.7") -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("429 Too Many Requests")
            return f"result from {model}"
        
        result = await mock_api("hello", model="cerebras-glm-4.7")
        
        # Should have retried
        assert call_count >= 2
        # Result should be from a different model
        assert "result from" in result

    @pytest.mark.asyncio
    async def test_non_rate_limit_error_not_retried(self):
        """Should not retry non-rate-limit errors."""
        @with_rate_limit_failover(model_param="model")
        async def mock_api(prompt: str, model: str = "test") -> str:
            raise ValueError("Some other error")
        
        with pytest.raises(ValueError):
            await mock_api("hello")


class TestTokenBudgetFailoverIntegration:
    """Tests for integration with TokenBudgetManager."""

    def test_failover_chain_includes_more_models(self):
        """FAILOVER_CHAIN should have comprehensive mappings."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        mgr = TokenBudgetManager()
        
        # Check that key models have failovers
        assert "cerebras" in mgr.FAILOVER_CHAIN
        assert "claude_sonnet" in mgr.FAILOVER_CHAIN
        assert "claude_opus" in mgr.FAILOVER_CHAIN

    def test_get_failover_method(self):
        """TokenBudgetManager should have get_failover method."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        # Reset singleton
        TokenBudgetManager._instance = None
        mgr = TokenBudgetManager()
        
        failover = mgr.get_failover("cerebras")
        assert failover == "gemini_flash"


class TestModelRouterFailoverIntegration:
    """Tests for integration with ModelRouter."""

    def test_get_failover_for_model(self):
        """ModelRouter should provide failover for models."""
        from code_puppy.core.model_router import ModelRouter
        
        router = ModelRouter(load_from_factory=False)
        
        # Should return a failover for known models
        failover = router.get_failover_for_model("cerebras-glm-4.7")
        # May be None if no other models in same tier, but shouldn't crash
        assert failover is None or isinstance(failover, str)

    def test_record_rate_limit(self):
        """ModelRouter should record rate limits and suggest failover."""
        from code_puppy.core.model_router import ModelRouter
        
        router = ModelRouter(load_from_factory=False)
        
        # Should not crash
        failover = router.record_rate_limit("gemini-3-flash")
        assert failover is None or isinstance(failover, str)
