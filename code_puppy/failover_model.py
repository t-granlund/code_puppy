"""Failover Model - Wrapper that automatically fails over on rate limits.

This module provides a FailoverModel that wraps a primary model and automatically
switches to failover models when rate limit (429) errors occur.

Works with the AGENT_WORKLOAD_REGISTRY to select appropriate failover models
based on the agent's workload type (ORCHESTRATOR, REASONING, CODING, LIBRARIAN).

Enhanced with IntelligentModelRouter integration for:
- Proactive switching BEFORE hitting limits (80% capacity threshold)
- Capacity tracking from API response headers
- Round-robin among models with available capacity
- Logfire telemetry for self-learning optimization
"""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, List, Mapping, Optional

from pydantic_ai.models import (
    Model,
    ModelMessage,
    ModelRequestParameters,
    ModelResponse,
    ModelSettings,
    StreamedResponse,
)
from pydantic_ai import RunContext

# Import intelligent routing (optional - graceful fallback if not available)
try:
    from code_puppy.core.model_capacity import (
        get_capacity_registry,
        CapacityStatus,
    )
    from code_puppy.core.intelligent_router import get_router
    INTELLIGENT_ROUTING_AVAILABLE = True
except ImportError:
    INTELLIGENT_ROUTING_AVAILABLE = False
    def get_capacity_registry():
        return None
    def get_router():
        return None

# Import centralized observability logging
try:
    from code_puppy.core.observability import (
        log_failover_triggered,
        log_failover_success,
        log_rate_limit,
    )
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False

logger = logging.getLogger(__name__)

# Import messaging for terminal-visible output
try:
    from code_puppy.messaging import emit_info, emit_warning
    MESSAGING_AVAILABLE = True
except ImportError:
    MESSAGING_AVAILABLE = False
    def emit_info(msg, **kwargs): logger.info(msg)
    def emit_warning(msg, **kwargs): logger.warning(msg)

# Rate limit backoff configuration
# These prevent rapid cascade failures across providers
BACKOFF_BASE_SECONDS = 2.0  # Initial backoff delay
BACKOFF_MULTIPLIER = 1.5    # Exponential multiplier
BACKOFF_MAX_SECONDS = 30.0  # Cap on backoff delay
COOLDOWN_SECONDS = 60.0     # How long a model stays in cooldown after 429


def _is_failover_error(exc: Exception) -> bool:
    """Check if an exception should trigger failover to next model.
    
    Triggers failover on:
    - 429 Rate Limit errors
    - 422 Unprocessable Entity (message format incompatibility)
    - 400 Bad Request (model doesn't support feature)
    - 500/502/503 Server errors (model unavailable or misconfigured)
    - 401/403 Authentication errors (invalid token/model access)
    - UnexpectedModelBehavior (output validation failures, malformed tool calls)
    - ToolRetryError (tool call validation errors)
    - RemoteProtocolError (connection closed mid-stream, incomplete chunked read)
    - ConnectionError (generic connection failures)
    - Timeout errors
    
    Handles various exception types from different providers:
    - anthropic.RateLimitError, InternalServerError, AuthenticationError
    - openai.RateLimitError, APIError, UnprocessableEntityError
    - pydantic_ai.exceptions.UnexpectedModelBehavior (output validation)
    - pydantic_ai.exceptions.ToolRetryError (tool call validation)
    - httpx.RemoteProtocolError (connection closed mid-stream)
    - httpcore.RemoteProtocolError (peer closed connection)
    - httpx-based status code responses
    - Generic API errors with status codes
    """
    exc_type = type(exc).__name__
    exc_str = str(exc).lower()
    
    # Check by exception type name (includes pydantic-ai validation errors)
    if any(err in exc_type.lower() for err in [
        "ratelimit", "internalserver", "authentication", "apierror",
        "unprocessableentity", "badrequest",
        "unexpectedmodelbehavior",  # pydantic-ai output validation failure
        "toolretryerror",           # pydantic-ai tool call validation failure
        "remoteprotocolerror",      # httpx/httpcore connection closed mid-stream
        "connectionerror",          # Generic connection failures
        "timeout",                  # Request timeouts
    ]):
        return True
    
    # Check by message content
    failover_indicators = [
        "429", "rate limit", "too many requests",
        "422", "unprocessable", "wrong_api_format",  # Model format incompatibility
        "400", "bad request", "invalid_request",      # Model doesn't support feature
        "500", "502", "503", "internal server error", "service unavailable",
        "401", "403", "authentication", "unauthorized", "forbidden",
        "exceeded maximum retries",                   # pydantic-ai output validation
        "output validation",                          # pydantic-ai output validation
        "incomplete chunked read",                    # httpx connection closed mid-stream
        "peer closed connection",                     # httpcore connection dropped
        "connection reset",                           # TCP connection reset
        "connection refused",                         # Server not accepting connections
    ]
    if any(indicator in exc_str for indicator in failover_indicators):
        return True
    
    # Check for status_code attribute (expanded list)
    if hasattr(exc, "status_code"):
        if exc.status_code in (400, 401, 403, 422, 429, 500, 502, 503):
            return True
    
    # Check for response with failover status codes
    if hasattr(exc, "response") and hasattr(exc.response, "status_code"):
        if exc.response.status_code in (400, 401, 403, 422, 429, 500, 502, 503):
            return True
    
    return False


@dataclass(init=False)
class FailoverModel(Model):
    """A model that automatically fails over to alternate models on rate limits.
    
    When the primary model hits a 429 rate limit error, this wrapper:
    1. Marks the model as rate-limited in RateLimitFailover
    2. Gets the next workload-appropriate failover model
    3. Retries the request with the failover model
    
    This provides seamless rate limit handling at the pydantic-ai model level,
    so agents don't need to handle failover logic themselves.
    
    Usage:
        from code_puppy.failover_model import FailoverModel
        
        primary_model = AnthropicModel("claude-opus-4.5", ...)
        failover_chain = [
            AnthropicModel("antigravity-claude-opus-4-5-thinking-high", ...),
            GeminiModel("gemini-3-pro", ...),
        ]
        
        model = FailoverModel(primary_model, *failover_chain, workload="orchestrator")
    """
    
    primary_model: Model
    failover_models: List[Model]
    workload: str
    _current_model: Model = field(repr=False)
    _failed_models: set = field(default_factory=set, repr=False)
    _max_failovers: int = field(default=3, repr=False)
    # Rate limit backoff tracking
    _last_failover_time: float = field(default=0.0, repr=False)
    _consecutive_429s: int = field(default=0, repr=False)
    _model_cooldowns: dict = field(default_factory=dict, repr=False)  # model_name -> cooldown_until
    
    def __init__(
        self,
        primary_model: Model,
        *failover_models: Model,
        workload: str = "coding",
        max_failovers: int = 3,
        settings: ModelSettings | None = None,
    ):
        """Initialize a failover model.
        
        Args:
            primary_model: The primary model to use.
            failover_models: Backup models to try if primary hits rate limits.
            workload: Workload type for logging ("orchestrator", "reasoning", "coding", "librarian").
            max_failovers: Maximum number of failover attempts per request.
            settings: Model settings defaults.
        """
        super().__init__(settings=settings)
        self.primary_model = primary_model
        self.failover_models = list(failover_models)
        self.workload = workload
        self._current_model = primary_model
        self._failed_models = set()
        self._max_failovers = max_failovers
        # Rate limit backoff tracking
        self._last_failover_time = 0.0
        self._consecutive_429s = 0
        self._model_cooldowns = {}
    
    @property
    def model_name(self) -> str:
        """Return the current active model name."""
        return self._current_model.model_name
    
    @property
    def system(self) -> str:
        """System prompt from the current model."""
        return self._current_model.system
    
    @property
    def base_url(self) -> str | None:
        """Base URL from the current model."""
        return getattr(self._current_model, "base_url", None)
    
    def _get_all_models(self) -> List[Model]:
        """Get all models in order (primary first, then failovers)."""
        return [self.primary_model] + self.failover_models
    
    def _get_next_model(self) -> Model | None:
        """Get the next available model that hasn't failed and isn't in cooldown.
        
        Enhanced with intelligent routing:
        1. First check proactive capacity limits
        2. Then check cooldowns and failures
        3. Use IntelligentModelRouter if available for smarter selection
        
        Returns:
            Next available model, or None if all models have failed/cooling down.
        """
        now = time.time()
        
        # Try intelligent routing first (proactive capacity checking)
        if INTELLIGENT_ROUTING_AVAILABLE:
            registry = get_capacity_registry()
            if registry:
                for model in self._get_all_models():
                    model_name = model.model_name
                    
                    # Skip permanently failed or cooling down
                    if model_name in self._failed_models:
                        continue
                    cooldown_until = self._model_cooldowns.get(model_name, 0.0)
                    if now < cooldown_until:
                        continue
                    
                    # Check capacity proactively
                    capacity = registry.get_capacity(model_name)
                    if capacity:
                        status = capacity.get_status()
                        if status == CapacityStatus.EXHAUSTED:
                            logger.debug(f"⚠️ {model_name} capacity exhausted, skipping")
                            continue
                        if status == CapacityStatus.COOLDOWN:
                            logger.debug(f"⏳ {model_name} in capacity cooldown, skipping")
                            continue
                        # LOW capacity: log warning but can still use
                        if status == CapacityStatus.LOW:
                            logger.debug(
                                f"⚡ {model_name} low capacity ({capacity.get_available_tokens():,} tokens), using cautiously"
                            )
                    
                    return model
        
        # Fallback to traditional checking
        for model in self._get_all_models():
            model_name = model.model_name
            # Skip permanently failed models
            if model_name in self._failed_models:
                continue
            # Skip models still in cooldown
            cooldown_until = self._model_cooldowns.get(model_name, 0.0)
            if now < cooldown_until:
                remaining = cooldown_until - now
                logger.debug(f"⏳ {model_name} still cooling down ({remaining:.1f}s remaining)")
                continue
            return model
        return None
    
    def _calculate_backoff_delay(self) -> float:
        """Calculate exponential backoff delay based on consecutive 429s.
        
        Uses exponential backoff to prevent rapid cascade failures:
        - 1st failover: 2s delay
        - 2nd failover: 3s delay  
        - 3rd failover: 4.5s delay
        - etc., capped at 30s max
        
        Returns:
            Delay in seconds before trying next model.
        """
        delay = BACKOFF_BASE_SECONDS * (BACKOFF_MULTIPLIER ** self._consecutive_429s)
        return min(delay, BACKOFF_MAX_SECONDS)
    
    def _mark_model_failed(self, model: Model) -> None:
        """Mark a model as failed (rate limited) with cooldown.
        
        Sets a cooldown period during which this model won't be tried.
        Also notifies RateLimitFailover and CapacityRegistry to track the failure.
        Logs the failure to Logfire for observability.
        """
        model_name = model.model_name
        now = time.time()
        
        # Set cooldown - this model won't be tried until cooldown expires
        self._model_cooldowns[model_name] = now + COOLDOWN_SECONDS
        
        # Track consecutive 429s for backoff calculation
        self._consecutive_429s += 1
        self._last_failover_time = now
        
        # Log to Logfire for observability
        if OBSERVABILITY_AVAILABLE:
            try:
                log_rate_limit(
                    model=model_name,
                    workload=self.workload,
                    cooldown_seconds=COOLDOWN_SECONDS,
                    consecutive_429s=self._consecutive_429s,
                )
            except Exception:
                pass  # Don't let logging break failover
        else:
            try:
                import logfire
                logfire.warn(
                    "Model rate limited: {model} ({workload} workload) - cooldown {cooldown}s",
                    model=model_name,
                    workload=self.workload,
                    cooldown=COOLDOWN_SECONDS,
                    consecutive_429s=self._consecutive_429s,
                )
            except Exception:
                pass  # Don't let logging break failover
        
        # Notify the capacity registry (intelligent routing)
        if INTELLIGENT_ROUTING_AVAILABLE:
            try:
                registry = get_capacity_registry()
                if registry:
                    registry.record_rate_limit(model_name)
            except Exception as e:
                logger.debug(f"Failed to record rate limit in CapacityRegistry: {e}")
        
        # Notify the global failover manager (legacy)
        try:
            from code_puppy.core.rate_limit_failover import RateLimitFailover
            failover = RateLimitFailover()
            failover.mark_rate_limited(model_name, COOLDOWN_SECONDS)
        except Exception as e:
            logger.debug(f"Failed to mark model in RateLimitFailover: {e}")
        
        logger.info(
            f"🔴 Rate limited: {model_name} ({self.workload} workload) "
            f"- cooldown {COOLDOWN_SECONDS}s, consecutive 429s: {self._consecutive_429s}"
        )
    
    def _record_success(
        self, 
        model: Model, 
        response: ModelResponse,
        headers: Optional[Mapping[str, str]] = None
    ) -> None:
        """Record a successful request for capacity tracking.
        
        Updates the capacity registry with usage data from the response.
        """
        if not INTELLIGENT_ROUTING_AVAILABLE:
            return
        
        try:
            registry = get_capacity_registry()
            if registry and hasattr(response, "usage") and response.usage:
                registry.record_request(
                    model.model_name,
                    response.usage.input_tokens or 0,
                    response.usage.output_tokens or 0,
                    headers,
                )
                # Clear consecutive 429s on success
                self._consecutive_429s = 0
        except Exception as e:
            logger.debug(f"Failed to record success in CapacityRegistry: {e}")
    
    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        """Make a request with automatic failover on rate limits.
        
        Tries the current model first. If it fails with a rate limit error,
        marks it as failed and tries the next model in the failover chain.
        
        Enhanced with proactive capacity tracking - will check capacity
        before attempting request and update capacity after success.
        """
        attempts = 0
        last_error: Exception | None = None
        
        while attempts < self._max_failovers + 1:
            model = self._get_next_model()
            if model is None:
                # All models exhausted
                if last_error:
                    raise last_error
                raise RuntimeError(
                    f"All models exhausted for {self.workload} workload: "
                    f"{list(self._failed_models)}"
                )
            
            self._current_model = model
            
            try:
                # Log current model being tried (visible in terminal)
                if attempts == 0:
                    logger.debug(f"🎯 Trying {model.model_name} ({self.workload} workload)")
                else:
                    emit_info(
                        f"🎯 Trying {model.model_name} ({self.workload} workload)",
                        message_group="model_failover"
                    )
                
                response = await model.request(
                    messages, model_settings, model_request_parameters
                )
                
                # Record success for capacity tracking
                self._record_success(model, response)
                
                # Success - log if this was a failover (visible in terminal)
                if attempts > 0:
                    emit_info(
                        f"✅ Failover succeeded: {model.model_name} "
                        f"(attempt {attempts + 1}/{self._max_failovers + 1})",
                        message_group="model_failover"
                    )
                    # Log to Logfire for observability
                    if OBSERVABILITY_AVAILABLE:
                        try:
                            log_failover_success(
                                model=model.model_name,
                                workload=self.workload,
                                attempt=attempts + 1,
                                max_attempts=self._max_failovers + 1,
                            )
                        except Exception:
                            pass
                    else:
                        try:
                            import logfire
                            logfire.info(
                                "Failover succeeded: {model} ({workload} workload) - attempt {attempt}",
                                model=model.model_name,
                                workload=self.workload,
                                attempt=attempts + 1,
                                max_attempts=self._max_failovers + 1,
                            )
                        except Exception:
                            pass
                
                return response
                
            except Exception as e:
                last_error = e
                
                if _is_failover_error(e):
                    self._mark_model_failed(model)
                    
                    # Calculate backoff delay to prevent rapid cascade failures
                    backoff_delay = self._calculate_backoff_delay()
                    
                    # Get next model for log message
                    next_model = self._get_next_model()
                    if next_model:
                        # Determine error type for better logging
                        err_str = str(e)
                        if "429" in err_str or "rate limit" in err_str.lower():
                            error_type = "Rate limit"
                        elif "422" in err_str or "wrong_api_format" in err_str.lower():
                            error_type = "Format error"
                        elif "500" in err_str or "502" in err_str or "503" in err_str:
                            error_type = "Server error"
                        elif "400" in err_str or "bad request" in err_str.lower():
                            error_type = "Bad request"
                        else:
                            error_type = "Auth error"
                        
                        # Visible in terminal
                        emit_warning(
                            f"🔄 {error_type} on {model.model_name} → "
                            f"Backing off {backoff_delay:.1f}s → "
                            f"Failing over to {next_model.model_name}",
                            message_group="model_failover"
                        )
                        # Log to Logfire for observability
                        if OBSERVABILITY_AVAILABLE:
                            try:
                                log_failover_triggered(
                                    from_model=model.model_name,
                                    to_model=next_model.model_name,
                                    workload=self.workload,
                                    error_type=error_type,
                                    attempt=attempts + 1,
                                    backoff_delay=backoff_delay,
                                )
                            except Exception:
                                pass
                        else:
                            try:
                                import logfire
                                logfire.warn(
                                    "Failover triggered: {from_model} → {to_model} ({error_type})",
                                    from_model=model.model_name,
                                    to_model=next_model.model_name,
                                    error_type=error_type,
                                    workload=self.workload,
                                    backoff_delay=backoff_delay,
                                    attempt=attempts + 1,
                                )
                            except Exception:
                                pass
                        # Apply backoff delay before trying next model
                        await asyncio.sleep(backoff_delay)
                    else:
                        emit_warning(
                            f"⚠️  Error on {model.model_name}, "
                            f"no more failover models available (all in cooldown)",
                            message_group="model_failover"
                        )
                    
                    attempts += 1
                    continue
                
                # Non-rate-limit error - propagate immediately
                raise
        
        # Max failovers exceeded
        if last_error:
            raise last_error
        raise RuntimeError(f"Max failover attempts ({self._max_failovers}) exceeded")
    
    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
        run_context: RunContext[Any] | None = None,
    ) -> AsyncIterator[StreamedResponse]:
        """Make a streaming request with automatic failover on rate limits.
        
        Same failover logic as request(), but for streaming responses.
        This is an async context manager that yields the StreamedResponse.
        
        Note: Failover happens BEFORE yielding (during stream setup).
        Once we yield a response, we cannot failover mid-stream because
        the caller is already consuming it. If an error occurs after yield
        (during consumption), it propagates to the caller.
        """
        attempts = 0
        last_error: Exception | None = None
        yielded = False  # Track if we've yielded to caller
        
        while attempts < self._max_failovers + 1:
            model = self._get_next_model()
            if model is None:
                if last_error:
                    raise last_error
                raise RuntimeError(
                    f"All models exhausted for {self.workload} workload: "
                    f"{list(self._failed_models)}"
                )
            
            self._current_model = model
            
            try:
                # Log current model being tried (visible in terminal on failover)
                if attempts == 0:
                    logger.debug(f"🎯 Trying stream {model.model_name} ({self.workload} workload)")
                else:
                    emit_info(
                        f"🎯 Trying stream {model.model_name} ({self.workload} workload)",
                        message_group="model_failover"
                    )
                
                # Use async with on the inner model's request_stream
                async with model.request_stream(
                    messages, model_settings, model_request_parameters, run_context
                ) as response:
                    if attempts > 0:
                        emit_info(
                            f"✅ Stream failover succeeded: {model.model_name} "
                            f"(attempt {attempts + 1}/{self._max_failovers + 1})",
                            message_group="model_failover"
                        )
                    
                    # Yield the response - caller will iterate over it
                    # Once yielded, we're committed to this model - no mid-stream failover
                    yielded = True
                    yield response
                    # If we reach here, caller finished consuming the stream successfully
                    return
                
            except Exception as e:
                # CRITICAL: If we've already yielded to caller, any exception must propagate
                # immediately to satisfy asynccontextmanager protocol. Do NOT retry.
                if yielded:
                    raise
                
                last_error = e
                
                if _is_failover_error(e):
                    self._mark_model_failed(model)
                    
                    next_model = self._get_next_model()
                    if next_model:
                        # Determine error type for better logging
                        err_str = str(e)
                        if "429" in err_str or "rate limit" in err_str.lower():
                            error_type = "Rate limit"
                        elif "incomplete chunked" in err_str.lower() or "peer closed" in err_str.lower():
                            error_type = "Connection dropped"
                        elif "422" in err_str or "wrong_api_format" in err_str.lower():
                            error_type = "Format error"
                        elif "500" in err_str or "502" in err_str or "503" in err_str:
                            error_type = "Server error"
                        elif "400" in err_str or "bad request" in err_str.lower():
                            error_type = "Bad request"
                        else:
                            error_type = "Error"
                        
                        emit_warning(
                            f"🔄 Stream {error_type} on {model.model_name} → "
                            f"Failing over to {next_model.model_name}",
                            message_group="model_failover"
                        )
                    else:
                        emit_warning(
                            f"⚠️  Stream error on {model.model_name}, "
                            f"no more failover models available",
                            message_group="model_failover"
                        )
                    
                    attempts += 1
                    continue
                
                raise
        
        if last_error:
            raise last_error
        raise RuntimeError(f"Max stream failover attempts ({self._max_failovers}) exceeded")
    
    def reset_failures(self) -> None:
        """Reset all failure tracking.
        
        Call this to clear the failed models set and start fresh.
        Useful between requests or after a cooldown period.
        """
        self._failed_models.clear()
        self._current_model = self.primary_model
        logger.debug(f"Reset failover state for {self.workload} workload")


def create_failover_model_for_agent(
    agent_name: str,
    primary_model: Model,
    model_factory_func: callable = None,
) -> FailoverModel | Model:
    """Create a FailoverModel configured for a specific agent's workload.
    
    Uses AGENT_WORKLOAD_REGISTRY to determine the agent's workload type,
    then creates appropriate failover models from the WORKLOAD_CHAINS.
    
    Args:
        agent_name: Name of the agent (e.g., "bloodhound", "husky").
        primary_model: The primary model for the agent.
        model_factory_func: Optional function to create Model instances from names.
            Signature: (model_name: str) -> Model
            If not provided, only the primary model is used (no failover chain).
    
    Returns:
        FailoverModel if failover chain is available, otherwise the primary model.
    """
    try:
        from code_puppy.core.rate_limit_failover import RateLimitFailover, WorkloadType
        
        failover = RateLimitFailover()
        failover.load_from_model_factory()
        
        workload = failover.get_workload_for_agent(agent_name)
        chain = RateLimitFailover.WORKLOAD_CHAINS.get(workload, [])
        
        if not chain or not model_factory_func:
            # No failover chain or no way to create models
            logger.debug(f"No failover chain for {agent_name}, using primary only")
            return primary_model
        
        # Filter out the primary model from the chain
        primary_name = primary_model.model_name
        failover_names = [m for m in chain if m != primary_name][:3]  # Max 3 failovers
        
        if not failover_names:
            return primary_model
        
        # Create failover model instances
        failover_models = []
        for model_name in failover_names:
            try:
                model = model_factory_func(model_name)
                if model:
                    failover_models.append(model)
            except Exception as e:
                logger.debug(f"Could not create failover model {model_name}: {e}")
        
        if not failover_models:
            return primary_model
        
        workload_name = workload.name if hasattr(workload, "name") else str(workload)
        logger.info(
            f"🛡️ Created failover chain for {agent_name} ({workload_name}): "
            f"{primary_name} → {' → '.join(m.model_name for m in failover_models)}"
        )
        
        return FailoverModel(
            primary_model,
            *failover_models,
            workload=workload_name.lower(),
            max_failovers=len(failover_models),
        )
        
    except Exception as e:
        logger.debug(f"Could not create failover model for {agent_name}: {e}")
        return primary_model
