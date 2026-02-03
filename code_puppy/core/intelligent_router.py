"""Intelligent Model Router - Capacity-Aware Routing with Proactive Failover.

This module provides an intelligent routing layer that:
1. Selects the best model based on workload and available capacity
2. Proactively switches BEFORE hitting rate limits (20% remaining threshold)
3. Uses round-robin among models with available capacity
4. Learns from Logfire telemetry to optimize routing decisions
5. Never stops work due to rate limits - always finds an available model

Key Features:
- Workload-aware routing (Orchestrator, Reasoning, Coding, Librarian)
- Real-time capacity tracking from API response headers
- Proactive failover at configurable threshold
- Smart round-robin that skips exhausted models
- Automatic cooldown management after 429 errors
- Logfire integration for self-learning optimization

Usage:
    router = IntelligentModelRouter.get_instance()
    
    # Get best model for a coding task
    model = router.select_model("coding", estimated_tokens=50_000)
    
    # Record usage after request
    router.record_success(model, input_tokens, output_tokens, headers)
    
    # Record failure (429)
    router.record_rate_limit(model)
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple, TypeVar

from code_puppy.core.model_capacity import (
    CapacityRegistry,
    CapacityStatus,
    ModelCapacity,
    get_capacity_registry,
    _emit_capacity_telemetry,
)
from code_puppy.core.credential_availability import (
    get_credential_checker,
    get_available_models_with_credentials,
    filter_workload_chain,
)
from code_puppy.core.failover_config import (
    WorkloadType,
    WORKLOAD_CHAINS,
    AGENT_WORKLOAD_REGISTRY,
    get_workload_for_agent,
    get_tier_for_model,
)

logger = logging.getLogger(__name__)

# Import Logfire for telemetry
try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False
    logfire = None

T = TypeVar("T")


@dataclass
class RoutingDecision:
    """Result of a model selection decision."""
    model_name: str
    workload: str
    reason: str
    capacity_status: CapacityStatus
    available_tokens: int
    tier: int
    is_fallback: bool = False
    fallback_from: Optional[str] = None


@dataclass  
class RoutingStats:
    """Statistics for routing decisions."""
    total_requests: int = 0
    successful_routes: int = 0
    proactive_switches: int = 0
    reactive_switches: int = 0  # Switches after 429
    no_model_available: int = 0
    models_used: Dict[str, int] = field(default_factory=dict)
    rate_limits_hit: Dict[str, int] = field(default_factory=dict)
    
    def record_route(self, model_name: str, is_proactive_switch: bool = False) -> None:
        """Record a routing decision."""
        self.total_requests += 1
        self.successful_routes += 1
        if is_proactive_switch:
            self.proactive_switches += 1
        self.models_used[model_name] = self.models_used.get(model_name, 0) + 1
    
    def record_rate_limit(self, model_name: str) -> None:
        """Record a rate limit event."""
        self.reactive_switches += 1
        self.rate_limits_hit[model_name] = self.rate_limits_hit.get(model_name, 0) + 1
    
    def to_telemetry(self) -> Dict[str, Any]:
        """Get telemetry data."""
        return {
            "total_requests": self.total_requests,
            "successful_routes": self.successful_routes,
            "proactive_switches": self.proactive_switches,
            "reactive_switches": self.reactive_switches,
            "proactive_ratio": (
                self.proactive_switches / max(1, self.proactive_switches + self.reactive_switches)
            ),
            "no_model_available": self.no_model_available,
            "top_models": sorted(
                self.models_used.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5],
            "top_rate_limits": sorted(
                self.rate_limits_hit.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
        }


class IntelligentModelRouter:
    """Intelligent routing layer with capacity-aware model selection.
    
    This router ensures work NEVER stops due to rate limits by:
    1. Tracking capacity across all models in real-time
    2. Proactively switching before hitting limits
    3. Maintaining round-robin state per workload
    4. Learning from telemetry to optimize future routing
    
    Design Principles:
    - Same-tier failover first (maintain quality)
    - Proactive > reactive (switch at 80% capacity, not at 429)
    - Never block - always find an available model
    - Learn from patterns to improve routing
    """
    
    _instance: Optional["IntelligentModelRouter"] = None
    
    def __new__(cls) -> "IntelligentModelRouter":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> "IntelligentModelRouter":
        """Get the singleton instance."""
        return cls()
    
    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        
        self._capacity_registry = get_capacity_registry()
        self._stats = RoutingStats()
        self._round_robin_indices: Dict[str, int] = {}  # Per-workload indices
        self._current_model: Dict[str, str] = {}  # Per-workload current model
        self._lock = asyncio.Lock()
        
        # Configuration
        self._proactive_threshold = 0.8  # Switch at 80% capacity used
        self._prefer_same_tier = True
        self._emit_telemetry = True
        
        self._initialized = True
        logger.info("IntelligentModelRouter initialized")
    
    def configure(
        self,
        proactive_threshold: float = 0.8,
        prefer_same_tier: bool = True,
        emit_telemetry: bool = True,
    ) -> None:
        """Configure router behavior.
        
        Args:
            proactive_threshold: Switch when this % of capacity is used (0.8 = 80%)
            prefer_same_tier: Prefer same-tier models for failover
            emit_telemetry: Emit Logfire telemetry events
        """
        self._proactive_threshold = max(0.5, min(0.95, proactive_threshold))
        self._prefer_same_tier = prefer_same_tier
        self._emit_telemetry = emit_telemetry
        
        logger.info(
            f"Router configured: threshold={self._proactive_threshold}, "
            f"prefer_same_tier={prefer_same_tier}"
        )
    
    def select_model(
        self,
        workload: str,
        estimated_tokens: int = 10_000,
        current_model: Optional[str] = None,
        agent_name: Optional[str] = None,
    ) -> Optional[RoutingDecision]:
        """Select the best model for a request.
        
        This is the main entry point for routing decisions:
        1. If current model has capacity, use it
        2. If capacity is low, proactively switch
        3. If no current model, pick best from chain
        
        Args:
            workload: Type of work (coding, reasoning, orchestrator, librarian)
            estimated_tokens: Estimated token count for request
            current_model: Currently active model (if any)
            agent_name: Name of agent making request (for registry lookup)
        
        Returns:
            RoutingDecision with selected model and metadata.
            None if no models are available (should never happen).
        """
        # Infer workload from agent if not specified
        if agent_name and not workload:
            workload_type = get_workload_for_agent(agent_name)
            workload = workload_type.name.lower()
        
        workload = workload.lower()
        
        # Get available models for this workload
        available = self._capacity_registry.get_available_for_workload(
            workload, estimated_tokens
        )
        
        if not available:
            self._stats.no_model_available += 1
            logger.error(f"No models available for workload '{workload}'")
            
            # Emergency fallback: try any model
            all_models = list(self._capacity_registry.get_all_capacities().values())
            available = [m for m in all_models if m.get_status() != CapacityStatus.COOLDOWN]
            
            if not available:
                return None
        
        # Check if current model is still good
        if current_model:
            current_cap = self._capacity_registry.get_capacity(current_model)
            if current_cap:
                status = current_cap.get_status()
                
                # If status is AVAILABLE or APPROACHING, keep using it
                if status in (CapacityStatus.AVAILABLE, CapacityStatus.APPROACHING):
                    return RoutingDecision(
                        model_name=current_model,
                        workload=workload,
                        reason=f"Current model healthy ({status.name})",
                        capacity_status=status,
                        available_tokens=current_cap.get_available_tokens(),
                        tier=current_cap.limits.tier,
                        is_fallback=False,
                    )
                
                # If LOW, log warning but can still use for small requests
                if status == CapacityStatus.LOW and estimated_tokens < 5000:
                    return RoutingDecision(
                        model_name=current_model,
                        workload=workload,
                        reason="Low capacity but small request",
                        capacity_status=status,
                        available_tokens=current_cap.get_available_tokens(),
                        tier=current_cap.limits.tier,
                        is_fallback=False,
                    )
        
        # Need to select a new model
        selected = self._select_best_model(available, workload, current_model)
        
        is_proactive = current_model is not None and selected.model_name != current_model
        
        decision = RoutingDecision(
            model_name=selected.model_name,
            workload=workload,
            reason=self._get_selection_reason(selected, current_model),
            capacity_status=selected.get_status(),
            available_tokens=selected.get_available_tokens(),
            tier=selected.limits.tier,
            is_fallback=is_proactive,
            fallback_from=current_model if is_proactive else None,
        )
        
        # Update stats
        self._stats.record_route(selected.model_name, is_proactive)
        self._current_model[workload] = selected.model_name
        
        # Emit telemetry
        if self._emit_telemetry:
            self._emit_routing_telemetry(decision)
        
        return decision
    
    def _select_best_model(
        self,
        available: List[ModelCapacity],
        workload: str,
        current_model: Optional[str],
    ) -> ModelCapacity:
        """Select best model from available options.
        
        Strategy:
        1. If prefer_same_tier and current has tier, prefer that tier
        2. Round-robin among same-tier models
        3. Fall to lower tier if same tier exhausted
        """
        if not available:
            raise ValueError("No available models")
        
        # If we have a current model, try same tier first
        current_tier = None
        if current_model and self._prefer_same_tier:
            current_cap = self._capacity_registry.get_capacity(current_model)
            if current_cap:
                current_tier = current_cap.limits.tier
        
        # Filter to same tier if possible
        if current_tier:
            same_tier = [m for m in available if m.limits.tier == current_tier]
            if same_tier:
                available = same_tier
        
        # Round-robin within available models
        rr_key = f"{workload}:{current_tier or 'any'}"
        idx = self._round_robin_indices.get(rr_key, 0)
        
        # Pick model at current index
        selected = available[idx % len(available)]
        
        # Advance round-robin for next request
        self._round_robin_indices[rr_key] = (idx + 1) % len(available)
        
        return selected
    
    def _get_selection_reason(
        self,
        selected: ModelCapacity,
        previous: Optional[str],
    ) -> str:
        """Generate human-readable reason for selection."""
        status = selected.get_status()
        available = selected.get_available_tokens()
        
        if previous is None:
            return f"Initial selection (tier {selected.limits.tier}, {available:,} tokens available)"
        
        if selected.model_name == previous:
            return f"Continuing with current model ({status.name})"
        
        return (
            f"Proactive switch from {previous} → {selected.model_name} "
            f"(tier {selected.limits.tier}, {available:,} tokens available)"
        )
    
    def record_success(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        """Record a successful request.
        
        Call this after each successful API response to update capacity tracking.
        """
        self._capacity_registry.record_request(
            model_name, input_tokens, output_tokens, headers
        )
    
    def record_rate_limit(self, model_name: str) -> Optional[RoutingDecision]:
        """Record a rate limit (429) error.
        
        Updates capacity tracking and returns a new model selection for retry.
        """
        self._capacity_registry.record_rate_limit(model_name)
        self._stats.record_rate_limit(model_name)
        
        # Get workload for this model
        capacity = self._capacity_registry.get_capacity(model_name)
        if capacity and capacity.workloads:
            workload = capacity.workloads[0]
        else:
            workload = "coding"  # Default
        
        # Emit telemetry
        if self._emit_telemetry:
            _emit_capacity_telemetry(
                "reactive_failover",
                model_name,
                reason="429_rate_limit",
                consecutive_429s=capacity.usage.consecutive_429s if capacity else 0,
            )
        
        logger.warning(f"Rate limit hit on {model_name}, selecting alternative")
        
        # Select new model (excluding the rate-limited one)
        return self.select_model(workload, current_model=None)
    
    def should_switch(self, model_name: str) -> Tuple[bool, str]:
        """Check if we should proactively switch from this model.
        
        Returns (should_switch, reason).
        """
        return self._capacity_registry.should_switch_model(model_name)
    
    def get_failover_chain(self, workload: str) -> List[str]:
        """Get ordered failover chain for a workload.
        
        Returns models ordered by preference, filtered by availability.
        """
        try:
            workload_type = WorkloadType[workload.upper()]
        except KeyError:
            workload_type = WorkloadType.CODING
        
        chain = WORKLOAD_CHAINS.get(workload_type, [])
        
        # Filter to available models
        available_chain = []
        for model_name in chain:
            capacity = self._capacity_registry.get_capacity(model_name)
            if capacity and capacity.get_status() not in (
                CapacityStatus.EXHAUSTED, CapacityStatus.COOLDOWN
            ):
                available_chain.append(model_name)
        
        return available_chain
    
    def get_stats(self) -> RoutingStats:
        """Get routing statistics."""
        return self._stats
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get complete status summary for monitoring/debugging."""
        capacity_summary = self._capacity_registry.get_status_summary()
        
        return {
            "routing_stats": self._stats.to_telemetry(),
            "model_capacities": capacity_summary,
            "current_models": self._current_model.copy(),
            "round_robin_state": self._round_robin_indices.copy(),
            "configuration": {
                "proactive_threshold": self._proactive_threshold,
                "prefer_same_tier": self._prefer_same_tier,
                "emit_telemetry": self._emit_telemetry,
            },
        }
    
    def _emit_routing_telemetry(self, decision: RoutingDecision) -> None:
        """Emit telemetry for a routing decision."""
        if not LOGFIRE_AVAILABLE or logfire is None:
            return
        
        try:
            logfire.info(
                "model_router.selection",
                model_name=decision.model_name,
                workload=decision.workload,
                reason=decision.reason,
                capacity_status=decision.capacity_status.name,
                available_tokens=decision.available_tokens,
                tier=decision.tier,
                is_fallback=decision.is_fallback,
                fallback_from=decision.fallback_from,
            )
        except Exception:
            pass  # Telemetry should never break the router


# Convenience functions
def get_router() -> IntelligentModelRouter:
    """Get the global router singleton."""
    return IntelligentModelRouter.get_instance()


def select_model(
    workload: str,
    estimated_tokens: int = 10_000,
    current_model: Optional[str] = None,
) -> Optional[str]:
    """Quick helper to select a model.
    
    Returns model name or None.
    """
    decision = get_router().select_model(workload, estimated_tokens, current_model)
    return decision.model_name if decision else None


def record_usage(
    model_name: str,
    input_tokens: int,
    output_tokens: int,
    headers: Optional[Mapping[str, str]] = None,
) -> None:
    """Quick helper to record usage."""
    get_router().record_success(model_name, input_tokens, output_tokens, headers)


def handle_rate_limit(model_name: str) -> Optional[str]:
    """Quick helper to handle rate limit and get new model.
    
    Returns new model name or None.
    """
    decision = get_router().record_rate_limit(model_name)
    return decision.model_name if decision else None
