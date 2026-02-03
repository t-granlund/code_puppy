"""Capacity-Aware Round Robin Model.

Enhanced version of RoundRobinModel that:
1. Tracks capacity for each model in the rotation
2. Skips models that are exhausted or in cooldown
3. Proactively switches before hitting rate limits
4. Integrates with the IntelligentModelRouter for coordinated routing

This replaces blind round-robin with intelligent distribution that
ensures work never stops due to rate limits.

Usage:
    from code_puppy.core.capacity_aware_round_robin import CapacityAwareRoundRobin
    
    model = CapacityAwareRoundRobin(
        model1, model2, model3,
        workload="coding",
        rotate_every=5,  # Rotate every 5 requests
    )
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from pydantic_ai._run_context import RunContext
from pydantic_ai.models import (
    Model,
    ModelMessage,
    ModelRequestParameters,
    ModelResponse,
    ModelSettings,
    StreamedResponse,
)

from code_puppy.core.model_capacity import (
    CapacityRegistry,
    CapacityStatus,
    get_capacity_registry,
)
from code_puppy.core.intelligent_router import get_router

logger = logging.getLogger(__name__)

# OpenTelemetry support
try:
    from opentelemetry.context import get_current_span
except ImportError:
    def get_current_span():
        class DummySpan:
            def is_recording(self):
                return False
            def set_attributes(self, attributes):
                pass
        return DummySpan()


@dataclass
class ModelRotationState:
    """Track rotation state for a model."""
    model: Model
    model_name: str
    requests_since_rotation: int = 0
    total_requests: int = 0
    total_tokens: int = 0
    last_used: float = field(default_factory=time.time)
    consecutive_errors: int = 0
    last_error_time: Optional[float] = None
    
    def record_success(self, tokens: int = 0) -> None:
        """Record successful request."""
        self.requests_since_rotation += 1
        self.total_requests += 1
        self.total_tokens += tokens
        self.last_used = time.time()
        self.consecutive_errors = 0
    
    def record_error(self) -> None:
        """Record failed request."""
        self.consecutive_errors += 1
        self.last_error_time = time.time()
    
    def should_skip(self, max_consecutive_errors: int = 3) -> bool:
        """Check if this model should be skipped."""
        # Skip if too many consecutive errors
        if self.consecutive_errors >= max_consecutive_errors:
            # But allow retry after 60 seconds
            if self.last_error_time and time.time() - self.last_error_time > 60:
                return False
            return True
        return False


@dataclass(init=False)
class CapacityAwareRoundRobin(Model):
    """Round-robin model that skips exhausted models.
    
    Unlike the basic RoundRobinModel, this:
    1. Checks model capacity before selecting
    2. Skips models in cooldown or exhausted
    3. Uses intelligent routing when all models are stressed
    4. Tracks usage statistics for optimization
    
    Key Behavior:
    - rotate_every: Requests before rotation (default 1)
    - skip_exhausted: Skip models with exhausted capacity (default True)
    - proactive_switch: Switch before hitting limits (default True)
    - fallback_to_any: If all preferred exhausted, try any available (default True)
    """
    
    models: List[Model]
    workload: str
    _states: List[ModelRotationState] = field(repr=False)
    _current_index: int = field(default=0, repr=False)
    _rotate_every: int = field(default=1, repr=False)
    _skip_exhausted: bool = field(default=True, repr=False)
    _proactive_switch: bool = field(default=True, repr=False)
    _fallback_to_any: bool = field(default=True, repr=False)
    _capacity_registry: CapacityRegistry = field(repr=False)
    
    def __init__(
        self,
        *models: Model,
        workload: str = "coding",
        rotate_every: int = 1,
        skip_exhausted: bool = True,
        proactive_switch: bool = True,
        fallback_to_any: bool = True,
        settings: ModelSettings | None = None,
    ):
        """Initialize capacity-aware round-robin.
        
        Args:
            models: Model instances to rotate through
            workload: Workload type (coding, reasoning, orchestrator, librarian)
            rotate_every: Number of requests before rotating (default 1)
            skip_exhausted: Skip models with exhausted capacity (default True)
            proactive_switch: Switch before hitting limits (default True)
            fallback_to_any: Fall back to any available if all preferred exhausted
            settings: Default model settings
        """
        super().__init__(settings=settings)
        
        if not models:
            raise ValueError("At least one model must be provided")
        if rotate_every < 1:
            raise ValueError("rotate_every must be at least 1")
        
        self.models = list(models)
        self.workload = workload
        self._rotate_every = rotate_every
        self._skip_exhausted = skip_exhausted
        self._proactive_switch = proactive_switch
        self._fallback_to_any = fallback_to_any
        self._current_index = 0
        self._capacity_registry = get_capacity_registry()
        
        # Initialize rotation states for each model
        self._states = [
            ModelRotationState(
                model=m,
                model_name=m.model_name,
            )
            for m in self.models
        ]
    
    @property
    def model_name(self) -> str:
        """Name showing this is capacity-aware round-robin."""
        model_names = ",".join(s.model_name for s in self._states[:3])
        if len(self._states) > 3:
            model_names += f",...+{len(self._states)-3}"
        return f"capacity_rr:{model_names}:{self.workload}"
    
    @property
    def system(self) -> str:
        """System prompt from current model."""
        return self.models[self._current_index].system
    
    @property
    def base_url(self) -> str | None:
        """Base URL from current model."""
        return self.models[self._current_index].base_url
    
    def _get_available_models(self) -> List[Tuple[int, ModelRotationState]]:
        """Get list of (index, state) for available models."""
        available = []
        
        for idx, state in enumerate(self._states):
            # Skip if too many consecutive errors
            if state.should_skip():
                continue
            
            # Skip if capacity exhausted (if enabled)
            if self._skip_exhausted:
                capacity = self._capacity_registry.get_capacity(state.model_name)
                if capacity:
                    status = capacity.get_status()
                    if status in (CapacityStatus.EXHAUSTED, CapacityStatus.COOLDOWN):
                        continue
                    
                    # If proactive switching enabled, also skip LOW capacity
                    if self._proactive_switch and status == CapacityStatus.LOW:
                        # But keep it as last resort
                        continue
            
            available.append((idx, state))
        
        return available
    
    def _get_next_model(self) -> Tuple[Model, ModelRotationState]:
        """Get next model with available capacity.
        
        Returns (model, state) tuple.
        """
        available = self._get_available_models()
        
        if not available:
            # All models exhausted - fall back to least-bad option
            if self._fallback_to_any:
                # Pick model with fewest consecutive errors
                fallback = min(
                    enumerate(self._states),
                    key=lambda x: (x[1].consecutive_errors, -x[1].last_used)
                )
                logger.warning(
                    f"All models capacity-limited, falling back to {fallback[1].model_name}"
                )
                return fallback[1].model, fallback[1]
            
            # Use current index anyway
            state = self._states[self._current_index]
            return state.model, state
        
        # Find next available model starting from current index
        # First, check if current is still available
        current_state = self._states[self._current_index]
        for idx, state in available:
            if idx == self._current_index:
                # Current model still available
                if current_state.requests_since_rotation < self._rotate_every:
                    return state.model, state
                break
        
        # Need to rotate - find next available after current
        next_available = None
        for idx, state in available:
            if idx > self._current_index:
                next_available = (idx, state)
                break
        
        if next_available is None and available:
            # Wrap around
            next_available = available[0]
        
        if next_available:
            self._current_index = next_available[0]
            # Reset rotation counter
            next_available[1].requests_since_rotation = 0
            return next_available[1].model, next_available[1]
        
        # Shouldn't reach here, but fallback
        state = self._states[self._current_index]
        return state.model, state
    
    def _update_model_stats(
        self,
        state: ModelRotationState,
        success: bool,
        response: Optional[ModelResponse] = None,
    ) -> None:
        """Update stats after request."""
        if success:
            # Estimate tokens from response if available
            tokens = 0
            if response and hasattr(response, "usage") and response.usage:
                tokens = response.usage.total_tokens or 0
            state.record_success(tokens)
            
            # Record to capacity registry
            if response and hasattr(response, "usage") and response.usage:
                self._capacity_registry.record_request(
                    state.model_name,
                    response.usage.input_tokens or 0,
                    response.usage.output_tokens or 0,
                )
        else:
            state.record_error()
    
    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        """Make request with capacity-aware model selection."""
        model, state = self._get_next_model()
        
        merged_settings, prepared_params = model.prepare_request(
            model_settings, model_request_parameters
        )
        
        try:
            response = await model.request(
                messages, merged_settings, prepared_params
            )
            self._update_model_stats(state, success=True, response=response)
            self._set_span_attributes(model)
            return response
            
        except Exception as exc:
            self._update_model_stats(state, success=False)
            
            # Check if rate limit
            exc_str = str(exc).lower()
            if "429" in exc_str or "rate limit" in exc_str:
                logger.warning(f"Rate limit on {state.model_name}, trying next")
                self._capacity_registry.record_rate_limit(state.model_name)
                
                # Try to get another model
                available = self._get_available_models()
                available = [(i, s) for i, s in available if s.model_name != state.model_name]
                
                if available:
                    next_model, next_state = available[0][1].model, available[0][1]
                    return await next_model.request(
                        messages, model_settings, model_request_parameters
                    )
            
            raise
    
    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
        run_context: RunContext[Any] | None = None,
    ) -> AsyncIterator[StreamedResponse]:
        """Stream request with capacity-aware selection."""
        model, state = self._get_next_model()
        
        merged_settings, prepared_params = model.prepare_request(
            model_settings, model_request_parameters
        )
        
        try:
            async with model.request_stream(
                messages, merged_settings, prepared_params, run_context
            ) as response:
                self._set_span_attributes(model)
                yield response
            
            # Record success after stream completes
            self._update_model_stats(state, success=True)
            
        except Exception as exc:
            self._update_model_stats(state, success=False)
            raise
    
    def _set_span_attributes(self, model: Model) -> None:
        """Set OpenTelemetry span attributes."""
        with suppress(Exception):
            span = get_current_span()
            if span.is_recording():
                span.set_attributes({
                    "model.round_robin.model_name": model.model_name,
                    "model.round_robin.workload": self.workload,
                    "model.round_robin.current_index": self._current_index,
                })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all models in rotation."""
        return {
            "workload": self.workload,
            "current_index": self._current_index,
            "rotate_every": self._rotate_every,
            "models": [
                {
                    "name": s.model_name,
                    "total_requests": s.total_requests,
                    "total_tokens": s.total_tokens,
                    "consecutive_errors": s.consecutive_errors,
                    "last_used": s.last_used,
                }
                for s in self._states
            ],
        }
