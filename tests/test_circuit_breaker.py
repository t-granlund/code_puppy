"""Tests for Circuit Breaker module."""

import asyncio
import pytest
import time

from code_puppy.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerManager,
    CircuitState,
    CircuitOpenError,
    ProviderHealthChecker,
    get_circuit_manager,
    check_circuit,
    with_circuit_breaker,
)


class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""
    
    def test_initial_state_is_closed(self):
        """Circuit starts in CLOSED state."""
        cb = CircuitBreaker("test-provider")
        assert cb.state == CircuitState.CLOSED
        assert cb.is_available
    
    @pytest.mark.asyncio
    async def test_can_execute_when_closed(self):
        """Requests allowed when circuit is closed."""
        cb = CircuitBreaker("test-provider")
        assert await cb.can_execute()
    
    @pytest.mark.asyncio
    async def test_opens_after_failure_threshold(self):
        """Circuit opens after consecutive failures."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test-provider", config=config)
        
        # Record failures
        for _ in range(3):
            await cb.record_failure("test error")
        
        assert cb.state == CircuitState.OPEN
        assert not cb.is_available
    
    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self):
        """Success resets consecutive failure counter."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test-provider", config=config)
        
        # Two failures
        await cb.record_failure()
        await cb.record_failure()
        assert cb.stats.consecutive_failures == 2
        
        # Success resets
        await cb.record_success()
        assert cb.stats.consecutive_failures == 0
        assert cb.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self):
        """Circuit transitions to half-open after recovery timeout."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1,  # 100ms for fast test
        )
        cb = CircuitBreaker("test-provider", config=config)
        
        # Open the circuit
        await cb.record_failure()
        await cb.record_failure()
        assert cb.state == CircuitState.OPEN
        
        # Wait for recovery
        await asyncio.sleep(0.15)
        
        # Should transition to half-open
        assert await cb.can_execute()
        assert cb.state == CircuitState.HALF_OPEN
    
    @pytest.mark.asyncio
    async def test_closes_after_success_in_half_open(self):
        """Circuit closes after successes in half-open state."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1,
            success_threshold=2,
        )
        cb = CircuitBreaker("test-provider", config=config)
        
        # Open and wait for half-open
        await cb.record_failure()
        await cb.record_failure()
        await asyncio.sleep(0.15)
        await cb.can_execute()
        
        # Record successes
        await cb.record_success()
        await cb.record_success()
        
        assert cb.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_reopens_on_failure_in_half_open(self):
        """Circuit reopens if failure occurs in half-open state."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1,
        )
        cb = CircuitBreaker("test-provider", config=config)
        
        # Open and wait for half-open
        await cb.record_failure()
        await cb.record_failure()
        await asyncio.sleep(0.15)
        await cb.can_execute()
        assert cb.state == CircuitState.HALF_OPEN
        
        # Failure in half-open
        await cb.record_failure()
        assert cb.state == CircuitState.OPEN
    
    def test_get_status(self):
        """Status dict contains expected fields."""
        cb = CircuitBreaker("test-provider")
        status = cb.get_status()
        
        assert "name" in status
        assert "state" in status
        assert "total_requests" in status
        assert "success_rate" in status
        assert status["name"] == "test-provider"
        assert status["state"] == "closed"
    
    def test_reset(self):
        """Reset returns circuit to initial state."""
        cb = CircuitBreaker("test-provider")
        cb.state = CircuitState.OPEN
        cb.stats.total_requests = 100
        cb.stats.failed_requests = 50
        
        cb.reset()
        
        assert cb.state == CircuitState.CLOSED
        assert cb.stats.total_requests == 0


class TestCircuitBreakerManager:
    """Tests for CircuitBreakerManager class."""
    
    @pytest.mark.asyncio
    async def test_get_breaker_creates_new(self):
        """Manager creates new breaker if not exists."""
        manager = CircuitBreakerManager()
        breaker = await manager.get_breaker("new-provider")
        
        assert breaker is not None
        assert breaker.name == "new-provider"
    
    @pytest.mark.asyncio
    async def test_get_breaker_returns_same(self):
        """Manager returns same breaker for same name."""
        manager = CircuitBreakerManager()
        breaker1 = await manager.get_breaker("provider-a")
        breaker2 = await manager.get_breaker("provider-a")
        
        assert breaker1 is breaker2
    
    @pytest.mark.asyncio
    async def test_is_available(self):
        """Manager checks availability correctly."""
        manager = CircuitBreakerManager()
        breaker = await manager.get_breaker("test-provider")
        
        assert await manager.is_available("test-provider")
        
        # Open the circuit
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker.config = config
        await manager.record_failure("test-provider")
        
        assert not await manager.is_available("test-provider")
    
    def test_get_all_status(self):
        """Manager returns status for all breakers."""
        manager = CircuitBreakerManager()
        # Create some breakers synchronously
        manager._breakers["provider-1"] = CircuitBreaker("provider-1")
        manager._breakers["provider-2"] = CircuitBreaker("provider-2")
        
        all_status = manager.get_all_status()
        
        assert "provider-1" in all_status
        assert "provider-2" in all_status
    
    def test_get_available_providers(self):
        """Manager returns set of available providers."""
        manager = CircuitBreakerManager()
        manager._breakers["available"] = CircuitBreaker("available")
        
        unavailable = CircuitBreaker("unavailable")
        unavailable.state = CircuitState.OPEN
        manager._breakers["unavailable"] = unavailable
        
        available = manager.get_available_providers()
        assert "available" in available
        assert "unavailable" not in available


class TestWithCircuitBreaker:
    """Tests for with_circuit_breaker decorator."""
    
    @pytest.mark.asyncio
    async def test_successful_call_records_success(self):
        """Successful function call records success."""
        # Reset singleton
        CircuitBreakerManager._instance = None
        manager = CircuitBreakerManager.get_instance()
        
        async def success_func():
            return "ok"
        
        result = await with_circuit_breaker("test", success_func)
        assert result == "ok"
        
        breaker = await manager.get_breaker("test")
        assert breaker.stats.successful_requests >= 1
    
    @pytest.mark.asyncio
    async def test_failed_call_records_failure(self):
        """Failed function call records failure."""
        CircuitBreakerManager._instance = None
        manager = CircuitBreakerManager.get_instance()
        
        async def fail_func():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            await with_circuit_breaker("test-fail", fail_func)
        
        breaker = await manager.get_breaker("test-fail")
        assert breaker.stats.failed_requests >= 1
    
    @pytest.mark.asyncio
    async def test_rejects_when_open(self):
        """Raises CircuitOpenError when circuit is open."""
        CircuitBreakerManager._instance = None
        manager = CircuitBreakerManager.get_instance()
        
        # Create and open a circuit
        breaker = await manager.get_breaker("open-circuit")
        breaker.state = CircuitState.OPEN
        breaker._last_state_change = time.time()  # Recent, so no half-open
        
        async def any_func():
            return "ok"
        
        with pytest.raises(CircuitOpenError):
            await with_circuit_breaker("open-circuit", any_func)
