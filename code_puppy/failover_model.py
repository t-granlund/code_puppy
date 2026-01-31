"""Failover Model - Wrapper that automatically fails over on rate limits.

This module provides a FailoverModel that wraps a primary model and automatically
switches to failover models when rate limit (429) errors occur.

Works with the AGENT_WORKLOAD_REGISTRY to select appropriate failover models
based on the agent's workload type (ORCHESTRATOR, REASONING, CODING, LIBRARIAN).
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, List

from pydantic_ai.models import (
    Model,
    ModelMessage,
    ModelRequestParameters,
    ModelResponse,
    ModelSettings,
    StreamedResponse,
)

logger = logging.getLogger(__name__)

# Rate limit backoff configuration
# These prevent rapid cascade failures across providers
BACKOFF_BASE_SECONDS = 2.0  # Initial backoff delay
BACKOFF_MULTIPLIER = 1.5    # Exponential multiplier
BACKOFF_MAX_SECONDS = 30.0  # Cap on backoff delay
COOLDOWN_SECONDS = 60.0     # How long a model stays in cooldown after 429


def _is_rate_limit_error(exc: Exception) -> bool:
    """Check if an exception is a rate limit error (429).
    
    Handles various exception types from different providers:
    - anthropic.RateLimitError
    - openai.RateLimitError  
    - httpx-based 429 responses
    - Generic API errors with 429 status
    """
    exc_type = type(exc).__name__
    exc_str = str(exc).lower()
    
    # Check by exception type name
    if "ratelimit" in exc_type.lower():
        return True
    
    # Check by message content
    if "429" in exc_str or "rate limit" in exc_str or "too many requests" in exc_str:
        return True
    
    # Check for status_code attribute
    if hasattr(exc, "status_code") and exc.status_code == 429:
        return True
    
    # Check for response with 429 status
    if hasattr(exc, "response") and hasattr(exc.response, "status_code"):
        if exc.response.status_code == 429:
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
        
        Returns:
            Next available model, or None if all models have failed/cooling down.
        """
        now = time.time()
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
        Also notifies RateLimitFailover to track the failure.
        """
        model_name = model.model_name
        now = time.time()
        
        # Set cooldown - this model won't be tried until cooldown expires
        self._model_cooldowns[model_name] = now + COOLDOWN_SECONDS
        
        # Track consecutive 429s for backoff calculation
        self._consecutive_429s += 1
        self._last_failover_time = now
        
        # Notify the global failover manager
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
    
    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        """Make a request with automatic failover on rate limits.
        
        Tries the current model first. If it fails with a rate limit error,
        marks it as failed and tries the next model in the failover chain.
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
                logger.debug(f"🎯 Trying {model.model_name} ({self.workload} workload)")
                response = await model.request(
                    messages, model_settings, model_request_parameters
                )
                
                # Success - log if this was a failover
                if attempts > 0:
                    logger.info(
                        f"✅ Failover succeeded: {model.model_name} "
                        f"(attempt {attempts + 1}/{self._max_failovers + 1})"
                    )
                
                return response
                
            except Exception as e:
                last_error = e
                
                if _is_rate_limit_error(e):
                    self._mark_model_failed(model)
                    
                    # Calculate backoff delay to prevent rapid cascade failures
                    backoff_delay = self._calculate_backoff_delay()
                    
                    # Get next model for log message
                    next_model = self._get_next_model()
                    if next_model:
                        logger.info(
                            f"🔄 Rate limit on {model.model_name} → "
                            f"Backing off {backoff_delay:.1f}s → "
                            f"Failing over to {next_model.model_name}"
                        )
                        # Apply backoff delay before trying next model
                        await asyncio.sleep(backoff_delay)
                    else:
                        logger.warning(
                            f"⚠️  Rate limit on {model.model_name}, "
                            f"no more failover models available (all in cooldown)"
                        )
                    
                    attempts += 1
                    continue
                
                # Non-rate-limit error - propagate immediately
                raise
        
        # Max failovers exceeded
        if last_error:
            raise last_error
        raise RuntimeError(f"Max failover attempts ({self._max_failovers}) exceeded")
    
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> StreamedResponse:
        """Make a streaming request with automatic failover on rate limits.
        
        Same failover logic as request(), but for streaming responses.
        """
        attempts = 0
        last_error: Exception | None = None
        
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
                logger.debug(f"🎯 Trying stream {model.model_name} ({self.workload} workload)")
                response = await model.request_stream(
                    messages, model_settings, model_request_parameters
                )
                
                if attempts > 0:
                    logger.info(
                        f"✅ Stream failover succeeded: {model.model_name} "
                        f"(attempt {attempts + 1}/{self._max_failovers + 1})"
                    )
                
                return response
                
            except Exception as e:
                last_error = e
                
                if _is_rate_limit_error(e):
                    self._mark_model_failed(model)
                    
                    next_model = self._get_next_model()
                    if next_model:
                        logger.info(
                            f"🔄 Stream rate limit on {model.model_name} → "
                            f"Failing over to {next_model.model_name}"
                        )
                    else:
                        logger.warning(
                            f"⚠️  Stream rate limit on {model.model_name}, "
                            f"no more failover models available"
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
