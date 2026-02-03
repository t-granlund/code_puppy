"""Tests for Intelligent Model Router and Capacity Management.

Tests the comprehensive rate limiting, capacity tracking, and intelligent
routing system that ensures work never stops due to rate limits.
"""

import asyncio
import time
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from code_puppy.core.model_capacity import (
    ModelLimits,
    ModelUsage,
    ModelCapacity,
    CapacityStatus,
    CapacityRegistry,
    get_capacity_registry,
    record_model_usage,
    record_model_rate_limit,
)
from code_puppy.core.intelligent_router import (
    IntelligentModelRouter,
    RoutingDecision,
    RoutingStats,
    get_router,
    select_model,
    record_usage,
    handle_rate_limit,
)


class TestModelLimits:
    """Tests for ModelLimits dataclass."""
    
    def test_default_values(self):
        """Should have sensible defaults."""
        limits = ModelLimits()
        assert limits.context_window == 128_000
        assert limits.max_output == 8_000
        assert limits.tokens_per_minute == 100_000
        assert limits.requests_per_minute == 50
        assert limits.tier == 3
    
    def test_custom_values(self):
        """Should accept custom values."""
        limits = ModelLimits(
            context_window=200_000,
            tokens_per_minute=1_000_000,
            provider="cerebras",
            tier=5,
            cost_per_month=50.0,
        )
        assert limits.context_window == 200_000
        assert limits.tokens_per_minute == 1_000_000
        assert limits.provider == "cerebras"
        assert limits.tier == 5
        assert limits.cost_per_month == 50.0


class TestModelUsage:
    """Tests for ModelUsage tracking."""
    
    def test_initial_state(self):
        """Should start with zero usage."""
        usage = ModelUsage()
        assert usage.tokens_used_minute == 0
        assert usage.requests_used_minute == 0
        assert not usage.is_in_cooldown()
    
    def test_record_request(self):
        """Should track token usage."""
        usage = ModelUsage()
        usage.record_request(input_tokens=1000, output_tokens=500)
        assert usage.tokens_used_minute == 1500
        assert usage.requests_used_minute == 1
        assert usage.tokens_used_day == 1500
        assert usage.requests_used_day == 1
    
    def test_record_multiple_requests(self):
        """Should accumulate usage."""
        usage = ModelUsage()
        usage.record_request(1000, 500)
        usage.record_request(2000, 1000)
        usage.record_request(500, 250)
        assert usage.tokens_used_minute == 5250
        assert usage.requests_used_minute == 3
    
    def test_record_rate_limit(self):
        """Should set cooldown on rate limit."""
        usage = ModelUsage()
        usage.record_rate_limit(cooldown_seconds=60)
        assert usage.is_in_cooldown()
        assert usage.consecutive_429s == 1
        assert usage.seconds_until_cooldown_end() > 0
    
    def test_exponential_backoff(self):
        """Should increase cooldown on consecutive 429s."""
        usage = ModelUsage()
        usage.record_rate_limit(60)  # 60s
        first_cooldown = usage.seconds_until_cooldown_end()
        
        usage.record_rate_limit(60)  # 120s
        second_cooldown = usage.seconds_until_cooldown_end()
        
        usage.record_rate_limit(60)  # 240s
        third_cooldown = usage.seconds_until_cooldown_end()
        
        assert usage.consecutive_429s == 3
        # Each should be roughly double (exponential backoff)
        assert second_cooldown > first_cooldown
        assert third_cooldown > second_cooldown
    
    def test_clear_cooldown(self):
        """Should clear cooldown on success."""
        usage = ModelUsage()
        usage.record_rate_limit(60)
        usage.record_rate_limit(60)
        assert usage.consecutive_429s == 2
        
        usage.clear_cooldown()
        assert usage.consecutive_429s == 0
        assert not usage.is_in_cooldown()
    
    def test_minute_window_reset(self):
        """Should reset minute counters after window expires."""
        usage = ModelUsage()
        usage.record_request(10000, 5000)
        usage.minute_window_start = time.time() - 61  # Simulate expired window
        
        usage.record_request(1000, 500)
        # Should have reset and only have new request
        assert usage.tokens_used_minute == 1500
        assert usage.requests_used_minute == 1
        # Daily should still accumulate
        assert usage.tokens_used_day == 16500


class TestModelCapacity:
    """Tests for ModelCapacity state management."""
    
    def test_status_available(self):
        """Should report AVAILABLE when under thresholds."""
        capacity = ModelCapacity(
            model_name="test-model",
            limits=ModelLimits(tokens_per_minute=100_000),
        )
        capacity.usage.tokens_used_minute = 10_000  # 10% used
        assert capacity.get_status() == CapacityStatus.AVAILABLE
    
    def test_status_approaching(self):
        """Should report APPROACHING at 50% capacity."""
        capacity = ModelCapacity(
            model_name="test-model",
            limits=ModelLimits(tokens_per_minute=100_000),
        )
        capacity.usage.tokens_used_minute = 55_000  # 55% used
        assert capacity.get_status() == CapacityStatus.APPROACHING
    
    def test_status_low(self):
        """Should report LOW at 80% capacity."""
        capacity = ModelCapacity(
            model_name="test-model",
            limits=ModelLimits(tokens_per_minute=100_000),
        )
        capacity.usage.tokens_used_minute = 85_000  # 85% used
        assert capacity.get_status() == CapacityStatus.LOW
    
    def test_status_exhausted(self):
        """Should report EXHAUSTED at 95% capacity."""
        capacity = ModelCapacity(
            model_name="test-model",
            limits=ModelLimits(tokens_per_minute=100_000),
        )
        capacity.usage.tokens_used_minute = 96_000  # 96% used
        assert capacity.get_status() == CapacityStatus.EXHAUSTED
    
    def test_status_cooldown(self):
        """Should report COOLDOWN when in cooldown."""
        capacity = ModelCapacity(
            model_name="test-model",
            limits=ModelLimits(),
        )
        capacity.usage.record_rate_limit(60)
        assert capacity.get_status() == CapacityStatus.COOLDOWN
    
    def test_available_tokens(self):
        """Should calculate available tokens correctly."""
        capacity = ModelCapacity(
            model_name="test-model",
            limits=ModelLimits(tokens_per_minute=100_000),
        )
        capacity.usage.tokens_used_minute = 30_000
        assert capacity.get_available_tokens() == 70_000
    
    def test_can_handle_prompt(self):
        """Should correctly check if prompt fits."""
        capacity = ModelCapacity(
            model_name="test-model",
            limits=ModelLimits(
                context_window=128_000,
                tokens_per_minute=100_000,
            ),
        )
        capacity.usage.tokens_used_minute = 30_000
        
        assert capacity.can_handle_prompt(50_000)  # 50K fits
        assert not capacity.can_handle_prompt(80_000)  # 80K exceeds rate limit
        assert not capacity.can_handle_prompt(150_000)  # Exceeds context
    
    def test_update_from_headers(self):
        """Should parse rate limit headers."""
        capacity = ModelCapacity(
            model_name="test-model",
            limits=ModelLimits(),
        )
        headers = {
            "x-ratelimit-remaining-tokens": "50000",
            "x-ratelimit-remaining-requests": "25",
        }
        
        updated = capacity.update_from_headers(headers)
        assert updated
        assert capacity.usage.remaining_tokens_minute == 50_000
        assert capacity.usage.remaining_requests_minute == 25
    
    def test_disabled_model(self):
        """Should report EXHAUSTED when disabled."""
        capacity = ModelCapacity(
            model_name="test-model",
            limits=ModelLimits(),
            enabled=False,
        )
        assert capacity.get_status() == CapacityStatus.EXHAUSTED


class TestCapacityRegistry:
    """Tests for CapacityRegistry singleton."""
    
    def setup_method(self):
        """Reset singleton for each test."""
        CapacityRegistry._instance = None
    
    def test_singleton(self):
        """Should return same instance."""
        reg1 = get_capacity_registry()
        reg2 = get_capacity_registry()
        assert reg1 is reg2
    
    def test_record_request(self):
        """Should track requests across models."""
        registry = get_capacity_registry()
        # Add a test model
        registry._models["test-model"] = ModelCapacity(
            model_name="test-model",
            limits=ModelLimits(),
        )
        
        registry.record_request("test-model", 1000, 500)
        capacity = registry.get_capacity("test-model")
        assert capacity.usage.tokens_used_minute == 1500
    
    def test_record_rate_limit(self):
        """Should track rate limits."""
        registry = get_capacity_registry()
        registry._models["test-model"] = ModelCapacity(
            model_name="test-model",
            limits=ModelLimits(),
        )
        
        registry.record_rate_limit("test-model")
        capacity = registry.get_capacity("test-model")
        assert capacity.usage.consecutive_429s == 1
        assert capacity.usage.is_in_cooldown()


class TestRoutingStats:
    """Tests for RoutingStats tracking."""
    
    def test_record_route(self):
        """Should track routing decisions."""
        stats = RoutingStats()
        stats.record_route("model-a")
        stats.record_route("model-a")
        stats.record_route("model-b")
        
        assert stats.total_requests == 3
        assert stats.successful_routes == 3
        assert stats.models_used["model-a"] == 2
        assert stats.models_used["model-b"] == 1
    
    def test_record_proactive_switch(self):
        """Should track proactive switches."""
        stats = RoutingStats()
        stats.record_route("model-a", is_proactive_switch=True)
        stats.record_route("model-b", is_proactive_switch=True)
        stats.record_route("model-a", is_proactive_switch=False)
        
        assert stats.proactive_switches == 2
    
    def test_record_rate_limit(self):
        """Should track rate limit events."""
        stats = RoutingStats()
        stats.record_rate_limit("model-a")
        stats.record_rate_limit("model-a")
        stats.record_rate_limit("model-b")
        
        assert stats.reactive_switches == 3
        assert stats.rate_limits_hit["model-a"] == 2
        assert stats.rate_limits_hit["model-b"] == 1


class TestIntelligentModelRouter:
    """Tests for IntelligentModelRouter."""
    
    def setup_method(self):
        """Reset singletons for each test."""
        IntelligentModelRouter._instance = None
        CapacityRegistry._instance = None
    
    def test_singleton(self):
        """Should return same instance."""
        router1 = get_router()
        router2 = get_router()
        assert router1 is router2
    
    def test_configure(self):
        """Should accept configuration."""
        router = get_router()
        router.configure(
            proactive_threshold=0.7,
            prefer_same_tier=False,
            emit_telemetry=False,
        )
        assert router._proactive_threshold == 0.7
        assert router._prefer_same_tier is False
        assert router._emit_telemetry is False
    
    def test_select_model_with_available(self):
        """Should select available model."""
        router = get_router()
        # Manually add test model to registry
        router._capacity_registry._models["test-coding-model"] = ModelCapacity(
            model_name="test-coding-model",
            limits=ModelLimits(tier=5),
            workloads=["coding"],
        )
        router._capacity_registry._initialized = True
        
        decision = router.select_model("coding", estimated_tokens=5000)
        assert decision is not None
        assert decision.model_name == "test-coding-model"
        assert decision.workload == "coding"
    
    def test_keeps_current_model_if_healthy(self):
        """Should keep current model if capacity is healthy."""
        router = get_router()
        router._capacity_registry._models["current-model"] = ModelCapacity(
            model_name="current-model",
            limits=ModelLimits(tokens_per_minute=100_000),
            workloads=["coding"],
        )
        router._capacity_registry._models["current-model"].usage.tokens_used_minute = 10_000  # 10%
        router._capacity_registry._initialized = True
        
        decision = router.select_model("coding", current_model="current-model")
        assert decision is not None
        assert decision.model_name == "current-model"
        assert decision.is_fallback is False
    
    @patch('code_puppy.core.credential_availability.get_credential_checker')
    def test_switches_when_low_capacity(self, mock_cred_checker):
        """Should switch model when capacity is low."""
        # Mock credential checker to return True for all models
        mock_checker = MagicMock()
        mock_checker.has_credentials.return_value = True
        mock_cred_checker.return_value = mock_checker
        
        router = get_router()
        
        # Add two models
        router._capacity_registry._models["exhausted-model"] = ModelCapacity(
            model_name="exhausted-model",
            limits=ModelLimits(tokens_per_minute=100_000, tier=5),
            workloads=["coding"],
        )
        router._capacity_registry._models["exhausted-model"].usage.tokens_used_minute = 96_000  # Exhausted
        
        router._capacity_registry._models["available-model"] = ModelCapacity(
            model_name="available-model",
            limits=ModelLimits(tokens_per_minute=100_000, tier=5),
            workloads=["coding"],
        )
        router._capacity_registry._initialized = True
        
        decision = router.select_model("coding", current_model="exhausted-model")
        assert decision is not None
        # Should NOT be exhausted model
        assert decision.model_name != "exhausted-model" or decision.capacity_status != CapacityStatus.EXHAUSTED
    
    def test_record_success(self):
        """Should record successful requests."""
        router = get_router()
        router._capacity_registry._models["test-model"] = ModelCapacity(
            model_name="test-model",
            limits=ModelLimits(),
        )
        
        router.record_success("test-model", 1000, 500)
        capacity = router._capacity_registry.get_capacity("test-model")
        assert capacity.usage.tokens_used_minute == 1500
    
    def test_record_rate_limit_returns_new_model(self):
        """Should return new model after rate limit."""
        router = get_router()
        
        router._capacity_registry._models["rate-limited"] = ModelCapacity(
            model_name="rate-limited",
            limits=ModelLimits(),
            workloads=["coding"],
        )
        router._capacity_registry._models["alternative"] = ModelCapacity(
            model_name="alternative",
            limits=ModelLimits(),
            workloads=["coding"],
        )
        router._capacity_registry._initialized = True
        
        decision = router.record_rate_limit("rate-limited")
        # Should get a new model (rate-limited is now in cooldown)
        assert decision is not None
    
    def test_should_switch_when_capacity_low(self):
        """Should recommend switch when capacity is low."""
        router = get_router()
        router._capacity_registry._models["low-model"] = ModelCapacity(
            model_name="low-model",
            limits=ModelLimits(tokens_per_minute=100_000),
        )
        router._capacity_registry._models["low-model"].usage.tokens_used_minute = 85_000
        
        should_switch, reason = router.should_switch("low-model")
        assert should_switch
        assert "Low capacity" in reason or "capacity" in reason.lower()
    
    def test_get_failover_chain(self):
        """Should return workload-appropriate chain."""
        router = get_router()
        chain = router.get_failover_chain("orchestrator")
        # Should return a list (even if empty)
        assert isinstance(chain, list)


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    def setup_method(self):
        """Reset singletons."""
        IntelligentModelRouter._instance = None
        CapacityRegistry._instance = None
    
    def test_select_model(self):
        """select_model should work."""
        # Will return None if no models configured, which is fine for test
        result = select_model("coding", estimated_tokens=5000)
        # Just verify it doesn't crash
        assert result is None or isinstance(result, str)
    
    def test_record_usage(self):
        """record_usage should not crash."""
        # Just verify it doesn't crash
        record_usage("any-model", 1000, 500)
    
    def test_handle_rate_limit(self):
        """handle_rate_limit should return model or None."""
        result = handle_rate_limit("any-model")
        assert result is None or isinstance(result, str)


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""
    
    def setup_method(self):
        """Reset singletons."""
        IntelligentModelRouter._instance = None
        CapacityRegistry._instance = None
    
    def test_scenario_high_volume_coding(self):
        """Simulate high-volume coding workload."""
        router = get_router()
        
        # Add multiple coding models with different capacities
        models = [
            ("cerebras-glm", 1_000_000, 5),
            ("synthetic-glm", 800_000, 5),
            ("chatgpt-codex", 200_000, 2),
        ]
        
        for name, tpm, tier in models:
            router._capacity_registry._models[name] = ModelCapacity(
                model_name=name,
                limits=ModelLimits(tokens_per_minute=tpm, tier=tier),
                workloads=["coding", "sprinter"],
            )
        router._capacity_registry._initialized = True
        
        # Simulate many requests
        last_model = None
        for i in range(100):
            decision = router.select_model("coding", estimated_tokens=10_000, current_model=last_model)
            if decision:
                # Simulate usage
                router.record_success(decision.model_name, 5000, 5000)
                last_model = decision.model_name
        
        # Verify stats
        stats = router.get_stats()
        assert stats.total_requests > 0
        assert len(stats.models_used) > 0
    
    def test_scenario_rate_limit_cascade(self):
        """Simulate rate limit cascade across providers."""
        router = get_router()
        
        # Add models
        router._capacity_registry._models["primary"] = ModelCapacity(
            model_name="primary",
            limits=ModelLimits(tokens_per_minute=100_000),
            workloads=["coding"],
        )
        router._capacity_registry._models["fallback1"] = ModelCapacity(
            model_name="fallback1",
            limits=ModelLimits(tokens_per_minute=100_000),
            workloads=["coding"],
        )
        router._capacity_registry._models["fallback2"] = ModelCapacity(
            model_name="fallback2",
            limits=ModelLimits(tokens_per_minute=100_000),
            workloads=["coding"],
        )
        router._capacity_registry._initialized = True
        
        # Hit rate limit on primary
        router.record_rate_limit("primary")
        decision1 = router.select_model("coding")
        assert decision1 is not None
        assert decision1.model_name != "primary"  # Should not use rate-limited model
        
        # Hit rate limit on fallback1
        if decision1.model_name == "fallback1":
            router.record_rate_limit("fallback1")
            decision2 = router.select_model("coding")
            assert decision2 is not None
            # Should use fallback2
            assert decision2.model_name not in ["primary", "fallback1"]
    
    def test_scenario_proactive_switching(self):
        """Test proactive switching before hitting limits."""
        router = get_router()
        router.configure(proactive_threshold=0.8)
        
        # Add model at 75% capacity (should still be usable)
        router._capacity_registry._models["model-75"] = ModelCapacity(
            model_name="model-75",
            limits=ModelLimits(tokens_per_minute=100_000),
            workloads=["coding"],
        )
        router._capacity_registry._models["model-75"].usage.tokens_used_minute = 75_000
        
        # Add model at 85% capacity (should be avoided)
        router._capacity_registry._models["model-85"] = ModelCapacity(
            model_name="model-85",
            limits=ModelLimits(tokens_per_minute=100_000),
            workloads=["coding"],
        )
        router._capacity_registry._models["model-85"].usage.tokens_used_minute = 85_000
        
        # Add fresh model
        router._capacity_registry._models["model-fresh"] = ModelCapacity(
            model_name="model-fresh",
            limits=ModelLimits(tokens_per_minute=100_000),
            workloads=["coding"],
        )
        router._capacity_registry._initialized = True
        
        # Should prefer fresh model over stressed ones
        decision = router.select_model("coding")
        assert decision is not None
        # Fresh model should be available
        assert decision.capacity_status in (CapacityStatus.AVAILABLE, CapacityStatus.APPROACHING)
