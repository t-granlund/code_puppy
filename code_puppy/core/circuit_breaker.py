"""Circuit Breaker Pattern - Protect Against Cascading Failures.

Implements the circuit breaker pattern to prevent repeated calls to failing services:
1. CLOSED: Normal operation, requests flow through
2. OPEN: Service is failing, requests are rejected immediately
3. HALF_OPEN: Testing if service has recovered

Includes health check functionality for proactive monitoring.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional, Set, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class CircuitState(Enum):
    """States of the circuit breaker."""
    
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitStats:
    """Statistics for a circuit breaker."""
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0  # Rejected while OPEN
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100


@dataclass
class CircuitBreakerConfig:
    """Configuration for a circuit breaker."""
    
    failure_threshold: int = 5  # Consecutive failures to open
    success_threshold: int = 3  # Consecutive successes to close from half-open
    recovery_timeout: float = 30.0  # Seconds before trying half-open
    half_open_max_requests: int = 1  # Max requests in half-open state
    failure_rate_threshold: float = 50.0  # Failure rate % to open
    min_requests_for_rate: int = 10  # Min requests before using failure rate


class CircuitBreaker:
    """Circuit breaker for a single provider/model.
    
    Protects against cascading failures by:
    1. Tracking consecutive failures
    2. Opening circuit after threshold exceeded
    3. Allowing recovery testing after timeout
    4. Closing circuit on successful recovery
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self._half_open_requests = 0
        self._last_state_change = time.time()
        self._lock = asyncio.Lock()
    
    @property
    def is_available(self) -> bool:
        """Check if circuit allows requests."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self._last_state_change >= self.config.recovery_timeout:
                return True  # Will transition to half-open
            return False
        else:  # HALF_OPEN
            return self._half_open_requests < self.config.half_open_max_requests
    
    async def can_execute(self) -> bool:
        """Check if a request can be executed and update state if needed."""
        async with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            
            elif self.state == CircuitState.OPEN:
                # Check recovery timeout
                if time.time() - self._last_state_change >= self.config.recovery_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
                    self._half_open_requests = 1
                    return True
                else:
                    self.stats.rejected_requests += 1
                    return False
            
            else:  # HALF_OPEN
                if self._half_open_requests < self.config.half_open_max_requests:
                    self._half_open_requests += 1
                    return True
                else:
                    self.stats.rejected_requests += 1
                    return False
    
    async def record_success(self) -> None:
        """Record a successful request."""
        async with self._lock:
            self.stats.total_requests += 1
            self.stats.successful_requests += 1
            self.stats.last_success_time = time.time()
            self.stats.consecutive_successes += 1
            self.stats.consecutive_failures = 0
            
            if self.state == CircuitState.HALF_OPEN:
                if self.stats.consecutive_successes >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
    
    async def record_failure(self, error: Optional[str] = None) -> None:
        """Record a failed request."""
        async with self._lock:
            self.stats.total_requests += 1
            self.stats.failed_requests += 1
            self.stats.last_failure_time = time.time()
            self.stats.consecutive_failures += 1
            self.stats.consecutive_successes = 0
            
            if error:
                logger.warning(f"Circuit {self.name} failure: {error}")
            
            # Check if we should open the circuit
            if self.state == CircuitState.CLOSED:
                should_open = False
                
                # Check consecutive failures
                if self.stats.consecutive_failures >= self.config.failure_threshold:
                    should_open = True
                    logger.warning(
                        f"Circuit {self.name}: Opening due to {self.stats.consecutive_failures} "
                        f"consecutive failures"
                    )
                
                # Check failure rate (if enough requests)
                elif self.stats.total_requests >= self.config.min_requests_for_rate:
                    if self.stats.failure_rate >= self.config.failure_rate_threshold:
                        should_open = True
                        logger.warning(
                            f"Circuit {self.name}: Opening due to {self.stats.failure_rate:.1f}% "
                            f"failure rate"
                        )
                
                if should_open:
                    self._transition_to(CircuitState.OPEN)
            
            elif self.state == CircuitState.HALF_OPEN:
                # Any failure in half-open reopens the circuit
                self._transition_to(CircuitState.OPEN)
                logger.warning(f"Circuit {self.name}: Reopening after half-open failure")
    
    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        old_state = self.state
        self.state = new_state
        self._last_state_change = time.time()
        
        if new_state == CircuitState.HALF_OPEN:
            self._half_open_requests = 0
            self.stats.consecutive_successes = 0
        elif new_state == CircuitState.CLOSED:
            self.stats.consecutive_failures = 0
        
        logger.info(f"Circuit {self.name}: {old_state.value} -> {new_state.value}")
    
    def reset(self) -> None:
        """Reset the circuit breaker to initial state."""
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self._half_open_requests = 0
        self._last_state_change = time.time()
        logger.info(f"Circuit {self.name}: Reset to CLOSED")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the circuit breaker."""
        return {
            "name": self.name,
            "state": self.state.value,
            "total_requests": self.stats.total_requests,
            "successful_requests": self.stats.successful_requests,
            "failed_requests": self.stats.failed_requests,
            "rejected_requests": self.stats.rejected_requests,
            "success_rate": f"{self.stats.success_rate:.1f}%",
            "failure_rate": f"{self.stats.failure_rate:.1f}%",
            "consecutive_failures": self.stats.consecutive_failures,
            "seconds_in_state": time.time() - self._last_state_change,
        }


class CircuitBreakerManager:
    """Manages circuit breakers for all providers/models.
    
    Provides centralized management of circuit breakers with:
    - Auto-creation of breakers for new providers
    - Global health status
    - Bulk reset functionality
    """
    
    _instance: Optional["CircuitBreakerManager"] = None
    
    def __init__(self, default_config: Optional[CircuitBreakerConfig] = None):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._default_config = default_config or CircuitBreakerConfig()
        self._lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> "CircuitBreakerManager":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def get_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> CircuitBreaker:
        """Get or create a circuit breaker for a provider."""
        async with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(
                    name=name,
                    config=config or self._default_config,
                )
            return self._breakers[name]
    
    def get_breaker_sync(self, name: str) -> Optional[CircuitBreaker]:
        """Synchronously get a circuit breaker if it exists."""
        return self._breakers.get(name)
    
    async def is_available(self, name: str) -> bool:
        """Check if a provider's circuit is available."""
        breaker = await self.get_breaker(name)
        return await breaker.can_execute()
    
    async def record_success(self, name: str) -> None:
        """Record a successful request for a provider."""
        breaker = await self.get_breaker(name)
        await breaker.record_success()
    
    async def record_failure(self, name: str, error: Optional[str] = None) -> None:
        """Record a failed request for a provider."""
        breaker = await self.get_breaker(name)
        await breaker.record_failure(error)
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers."""
        return {name: breaker.get_status() for name, breaker in self._breakers.items()}
    
    def get_available_providers(self) -> Set[str]:
        """Get set of providers with closed/half-open circuits."""
        return {
            name for name, breaker in self._breakers.items()
            if breaker.is_available
        }
    
    def get_unavailable_providers(self) -> Set[str]:
        """Get set of providers with open circuits."""
        return {
            name for name, breaker in self._breakers.items()
            if not breaker.is_available
        }
    
    async def reset_all(self) -> None:
        """Reset all circuit breakers to CLOSED state."""
        async with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()


@dataclass
class HealthCheckResult:
    """Result of a provider health check."""
    
    provider: str
    healthy: bool
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class ProviderHealthChecker:
    """Proactive health checker for providers.
    
    Performs periodic health checks to detect issues before they cause failures:
    - Lightweight ping/connectivity tests
    - Latency monitoring
    - Automatic circuit breaker updates
    """
    
    def __init__(
        self,
        circuit_manager: Optional[CircuitBreakerManager] = None,
        check_interval: float = 60.0,  # Seconds between checks
        timeout: float = 10.0,  # Timeout for health check
    ):
        self._circuit_manager = circuit_manager or CircuitBreakerManager.get_instance()
        self._check_interval = check_interval
        self._timeout = timeout
        self._health_status: Dict[str, HealthCheckResult] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    # Health check endpoints for known providers
    HEALTH_ENDPOINTS: Dict[str, str] = {
        "cerebras": "https://api.cerebras.ai/v1/models",
        "gemini": "https://generativelanguage.googleapis.com/v1beta/models",
        "gemini_flash": "https://generativelanguage.googleapis.com/v1beta/models",
        "claude_opus": "https://api.anthropic.com/v1/messages",
        "claude_sonnet": "https://api.anthropic.com/v1/messages",
        "codex": "https://api.openai.com/v1/models",
    }
    
    async def check_provider(self, provider: str) -> HealthCheckResult:
        """Perform a health check for a single provider."""
        import httpx
        
        endpoint = self.HEALTH_ENDPOINTS.get(provider)
        if not endpoint:
            return HealthCheckResult(
                provider=provider,
                healthy=True,  # Unknown providers assumed healthy
                error="No health endpoint configured",
            )
        
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                # Just check connectivity, don't need valid auth for health check
                response = await client.head(endpoint)
                latency_ms = (time.time() - start_time) * 1000
                
                # 401/403 means service is up but needs auth - that's healthy
                healthy = response.status_code < 500
                
                result = HealthCheckResult(
                    provider=provider,
                    healthy=healthy,
                    latency_ms=latency_ms,
                    error=None if healthy else f"HTTP {response.status_code}",
                )
        except httpx.TimeoutException:
            result = HealthCheckResult(
                provider=provider,
                healthy=False,
                error="Timeout",
            )
        except Exception as e:
            result = HealthCheckResult(
                provider=provider,
                healthy=False,
                error=str(e),
            )
        
        self._health_status[provider] = result
        
        # Update circuit breaker based on health check
        if result.healthy:
            await self._circuit_manager.record_success(provider)
        else:
            await self._circuit_manager.record_failure(provider, result.error)
        
        return result
    
    async def check_all_providers(self) -> Dict[str, HealthCheckResult]:
        """Check health of all known providers."""
        results = {}
        for provider in self.HEALTH_ENDPOINTS:
            results[provider] = await self.check_provider(provider)
        return results
    
    async def start_background_checks(self) -> None:
        """Start background health check loop."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._check_loop())
        logger.info("Started provider health check loop")
    
    async def stop_background_checks(self) -> None:
        """Stop background health check loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped provider health check loop")
    
    async def _check_loop(self) -> None:
        """Background loop for periodic health checks."""
        while self._running:
            try:
                await self.check_all_providers()
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
            
            await asyncio.sleep(self._check_interval)
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get summary of all provider health status."""
        healthy_count = sum(1 for r in self._health_status.values() if r.healthy)
        total_count = len(self._health_status)
        
        return {
            "healthy_providers": healthy_count,
            "total_providers": total_count,
            "health_percentage": (healthy_count / total_count * 100) if total_count else 100.0,
            "providers": {
                name: {
                    "healthy": result.healthy,
                    "latency_ms": result.latency_ms,
                    "error": result.error,
                    "last_check": result.timestamp,
                }
                for name, result in self._health_status.items()
            },
        }


# Convenience functions for global access
def get_circuit_manager() -> CircuitBreakerManager:
    """Get the global circuit breaker manager."""
    return CircuitBreakerManager.get_instance()


async def check_circuit(provider: str) -> bool:
    """Check if a provider's circuit is available."""
    return await get_circuit_manager().is_available(provider)


async def with_circuit_breaker(
    provider: str,
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Execute a function with circuit breaker protection.
    
    Args:
        provider: Name of the provider
        func: Async function to execute
        *args, **kwargs: Arguments for the function
    
    Returns:
        Result of the function
    
    Raises:
        CircuitOpenError: If circuit is open
        Original exception: If function fails
    """
    manager = get_circuit_manager()
    breaker = await manager.get_breaker(provider)
    
    if not await breaker.can_execute():
        raise CircuitOpenError(
            f"Circuit breaker {provider} is OPEN - service unavailable"
        )
    
    try:
        result = await func(*args, **kwargs)
        await breaker.record_success()
        return result
    except Exception as e:
        await breaker.record_failure(str(e))
        raise


class CircuitOpenError(Exception):
    """Raised when a circuit breaker is open and request is rejected."""
    pass
