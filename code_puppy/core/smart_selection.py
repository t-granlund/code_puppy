"""Smart Model Selection & Priority Queue - Intelligent Routing.

Implements intelligent model selection and request prioritization:
1. Multi-factor model selection (cost, speed, reliability, capability)
2. Priority queue for request ordering
3. Dynamic load balancing
"""

import asyncio
import heapq
import logging
import time
from dataclasses import dataclass, field
from decimal import Decimal
from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from .model_metrics import ModelMetricsTracker, AggregatedMetrics
from .circuit_breaker import CircuitBreakerManager
from .cost_budget import CostBudgetEnforcer

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RequestPriority(IntEnum):
    """Priority levels for requests."""
    
    CRITICAL = 1  # Must process immediately (security, errors)
    HIGH = 2  # User-facing, time-sensitive
    NORMAL = 3  # Standard requests
    LOW = 4  # Background tasks, batch processing
    BULK = 5  # Lowest priority, can be delayed


class SelectionStrategy(IntEnum):
    """Strategies for model selection."""
    
    COST_OPTIMIZED = 1  # Minimize cost
    SPEED_OPTIMIZED = 2  # Minimize latency
    RELIABILITY_OPTIMIZED = 3  # Maximize success rate
    BALANCED = 4  # Balance all factors
    CAPABILITY_FIRST = 5  # Choose most capable regardless of cost


@dataclass
class ModelScore:
    """Scoring result for a model."""
    
    model: str
    provider: str
    total_score: float
    cost_score: float
    speed_score: float
    reliability_score: float
    capability_score: float
    available: bool
    reason: str = ""


@dataclass
class QueuedRequest:
    """A request in the priority queue."""
    
    id: str
    priority: RequestPriority
    created_at: float
    payload: Any
    callback: Optional[Callable] = None
    timeout: float = 60.0  # Max wait time in seconds
    model_preference: Optional[str] = None
    
    def __lt__(self, other: "QueuedRequest") -> bool:
        """Compare by priority, then by creation time."""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.created_at < other.created_at
    
    @property
    def is_expired(self) -> bool:
        """Check if request has exceeded timeout."""
        return time.time() - self.created_at > self.timeout


class SmartModelSelector:
    """Selects the optimal model based on multiple factors.
    
    Factors considered:
    - Cost efficiency
    - Response speed
    - Reliability (success rate)
    - Task capability requirements
    - Current availability (circuit breaker state)
    - Budget constraints
    """
    
    # Model capability tiers (1 = highest capability)
    CAPABILITY_TIERS: Dict[str, int] = {
        "claude-opus-4.5": 1,
        "chatgpt-codex-5.2": 2,
        "claude-sonnet-4.5": 3,
        "gemini-3-pro": 4,
        "gemini-3-flash": 5,
        "cerebras-glm-4.7": 5,
    }
    
    # Model to provider mapping
    MODEL_PROVIDERS: Dict[str, str] = {
        "claude-opus-4.5": "claude_opus",
        "claude-sonnet-4.5": "claude_sonnet",
        "chatgpt-codex-5.2": "codex",
        "gemini-3-pro": "gemini",
        "gemini-3-flash": "gemini_flash",
        "cerebras-glm-4.7": "cerebras",
    }
    
    # Weight factors for balanced scoring
    BALANCED_WEIGHTS: Dict[str, float] = {
        "cost": 0.3,
        "speed": 0.3,
        "reliability": 0.25,
        "capability": 0.15,
    }
    
    def __init__(
        self,
        metrics_tracker: Optional[ModelMetricsTracker] = None,
        circuit_manager: Optional[CircuitBreakerManager] = None,
        cost_enforcer: Optional[CostBudgetEnforcer] = None,
    ):
        self._metrics = metrics_tracker or ModelMetricsTracker.get_instance()
        self._circuits = circuit_manager or CircuitBreakerManager.get_instance()
        self._costs = cost_enforcer or CostBudgetEnforcer.get_instance()
    
    async def select_model(
        self,
        available_models: List[str],
        strategy: SelectionStrategy = SelectionStrategy.BALANCED,
        min_capability_tier: int = 5,  # 1-5, lower = more capable required
        estimated_tokens: int = 1000,
    ) -> Optional[ModelScore]:
        """Select the best model based on strategy.
        
        Args:
            available_models: List of model names to consider
            strategy: Selection strategy to use
            min_capability_tier: Minimum capability tier required (1=best)
            estimated_tokens: Estimated token usage for cost calculation
        
        Returns:
            Best model's score, or None if no suitable model found
        """
        scores = await self._score_models(
            available_models,
            min_capability_tier,
            estimated_tokens,
        )
        
        if not scores:
            return None
        
        # Filter to available models only
        available_scores = [s for s in scores if s.available]
        if not available_scores:
            logger.warning("No available models found, using unavailable ones")
            available_scores = scores
        
        # Apply strategy-specific weighting
        if strategy == SelectionStrategy.COST_OPTIMIZED:
            available_scores.sort(key=lambda s: -s.cost_score)
        elif strategy == SelectionStrategy.SPEED_OPTIMIZED:
            available_scores.sort(key=lambda s: -s.speed_score)
        elif strategy == SelectionStrategy.RELIABILITY_OPTIMIZED:
            available_scores.sort(key=lambda s: -s.reliability_score)
        elif strategy == SelectionStrategy.CAPABILITY_FIRST:
            available_scores.sort(key=lambda s: -s.capability_score)
        else:  # BALANCED
            available_scores.sort(key=lambda s: -s.total_score)
        
        return available_scores[0]
    
    async def _score_models(
        self,
        models: List[str],
        min_capability_tier: int,
        estimated_tokens: int,
    ) -> List[ModelScore]:
        """Score all candidate models."""
        scores = []
        
        for model in models:
            provider = self.MODEL_PROVIDERS.get(model, model)
            capability_tier = self.CAPABILITY_TIERS.get(model, 5)
            
            # Check capability requirement
            if capability_tier > min_capability_tier:
                continue
            
            # Check circuit breaker
            circuit = self._circuits.get_breaker_sync(provider)
            available = circuit.is_available if circuit else True
            
            # Check budget
            if not self._costs.can_proceed(provider):
                available = False
            
            # Get metrics
            metrics = self._metrics.get_model_metrics(model)
            
            # Calculate component scores (0-100 scale)
            cost_score = self._calculate_cost_score(model, metrics)
            speed_score = self._calculate_speed_score(metrics)
            reliability_score = self._calculate_reliability_score(metrics)
            capability_score = self._calculate_capability_score(capability_tier)
            
            # Calculate weighted total
            total_score = (
                cost_score * self.BALANCED_WEIGHTS["cost"]
                + speed_score * self.BALANCED_WEIGHTS["speed"]
                + reliability_score * self.BALANCED_WEIGHTS["reliability"]
                + capability_score * self.BALANCED_WEIGHTS["capability"]
            )
            
            scores.append(ModelScore(
                model=model,
                provider=provider,
                total_score=total_score,
                cost_score=cost_score,
                speed_score=speed_score,
                reliability_score=reliability_score,
                capability_score=capability_score,
                available=available,
                reason=self._get_score_reason(
                    cost_score, speed_score, reliability_score, capability_score, available
                ),
            ))
        
        return scores
    
    def _calculate_cost_score(
        self,
        model: str,
        metrics: Optional[AggregatedMetrics],
    ) -> float:
        """Calculate cost efficiency score (higher = cheaper)."""
        # Cerebras is free, gets perfect score
        if "cerebras" in model.lower():
            return 100.0
        
        if not metrics or metrics.total_cost_usd == 0:
            return 50.0  # Unknown, neutral score
        
        # Calculate tokens per dollar
        total_tokens = metrics.total_input_tokens + metrics.total_output_tokens
        if total_tokens == 0:
            return 50.0
        
        tokens_per_dollar = float(Decimal(str(total_tokens)) / metrics.total_cost_usd)
        
        # Score: 100 for >1M tokens/$, 0 for <10k tokens/$
        score = min(100, max(0, (tokens_per_dollar - 10000) / 10000))
        return score
    
    def _calculate_speed_score(
        self,
        metrics: Optional[AggregatedMetrics],
    ) -> float:
        """Calculate speed score (higher = faster)."""
        if not metrics or not metrics.latencies_ms:
            return 50.0  # Unknown, neutral score
        
        p50 = metrics.p50_latency_ms
        
        # Score: 100 for <100ms, 0 for >10000ms
        if p50 <= 100:
            return 100.0
        elif p50 >= 10000:
            return 0.0
        else:
            return 100 - (p50 - 100) / 99
    
    def _calculate_reliability_score(
        self,
        metrics: Optional[AggregatedMetrics],
    ) -> float:
        """Calculate reliability score (higher = more reliable)."""
        if not metrics or metrics.total_requests == 0:
            return 80.0  # Unknown, assume decent reliability
        
        return metrics.success_rate  # Already 0-100 scale
    
    def _calculate_capability_score(self, tier: int) -> float:
        """Calculate capability score from tier (higher = more capable)."""
        # Tier 1 = 100, Tier 5 = 20
        return 100 - (tier - 1) * 20
    
    def _get_score_reason(
        self,
        cost: float,
        speed: float,
        reliability: float,
        capability: float,
        available: bool,
    ) -> str:
        """Generate a human-readable reason for the score."""
        if not available:
            return "Model unavailable (circuit open or budget exceeded)"
        
        best = max(cost, speed, reliability, capability)
        if best == cost:
            return f"Best cost efficiency (score: {cost:.0f})"
        elif best == speed:
            return f"Best speed (score: {speed:.0f})"
        elif best == reliability:
            return f"Best reliability (score: {reliability:.0f})"
        else:
            return f"Best capability (score: {capability:.0f})"
    
    def get_model_rankings(
        self,
        strategy: SelectionStrategy = SelectionStrategy.BALANCED,
    ) -> List[Dict[str, Any]]:
        """Get all models ranked by the specified strategy."""
        rankings = []
        
        for model in self.CAPABILITY_TIERS.keys():
            provider = self.MODEL_PROVIDERS.get(model, model)
            metrics = self._metrics.get_model_metrics(model)
            
            rankings.append({
                "model": model,
                "provider": provider,
                "cost_score": self._calculate_cost_score(model, metrics),
                "speed_score": self._calculate_speed_score(metrics),
                "reliability_score": self._calculate_reliability_score(metrics),
                "capability_tier": self.CAPABILITY_TIERS.get(model, 5),
            })
        
        # Sort by strategy
        if strategy == SelectionStrategy.COST_OPTIMIZED:
            rankings.sort(key=lambda r: r["cost_score"], reverse=True)
        elif strategy == SelectionStrategy.SPEED_OPTIMIZED:
            rankings.sort(key=lambda r: r["speed_score"], reverse=True)
        elif strategy == SelectionStrategy.RELIABILITY_OPTIMIZED:
            rankings.sort(key=lambda r: r["reliability_score"], reverse=True)
        elif strategy == SelectionStrategy.CAPABILITY_FIRST:
            rankings.sort(key=lambda r: r["capability_tier"])
        
        return rankings


class RequestPriorityQueue:
    """Priority queue for managing request ordering.
    
    Features:
    - Multiple priority levels
    - Timeout handling for stale requests
    - Fair scheduling within priority levels
    - Concurrent request limiting
    """
    
    def __init__(
        self,
        max_concurrent: int = 10,
        max_queue_size: int = 1000,
    ):
        self._queue: List[QueuedRequest] = []
        self._max_concurrent = max_concurrent
        self._max_queue_size = max_queue_size
        self._active_requests = 0
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Event()
        self._request_counter = 0
    
    async def enqueue(
        self,
        payload: Any,
        priority: RequestPriority = RequestPriority.NORMAL,
        timeout: float = 60.0,
        model_preference: Optional[str] = None,
        callback: Optional[Callable] = None,
    ) -> str:
        """Add a request to the queue.
        
        Returns:
            Request ID
        """
        async with self._lock:
            if len(self._queue) >= self._max_queue_size:
                # Remove lowest priority expired requests
                self._cleanup_expired()
                
                if len(self._queue) >= self._max_queue_size:
                    raise QueueFullError("Request queue is full")
            
            self._request_counter += 1
            request_id = f"req-{self._request_counter}-{int(time.time())}"
            
            request = QueuedRequest(
                id=request_id,
                priority=priority,
                created_at=time.time(),
                payload=payload,
                callback=callback,
                timeout=timeout,
                model_preference=model_preference,
            )
            
            heapq.heappush(self._queue, request)
            self._not_empty.set()
            
            logger.debug(
                f"Enqueued request {request_id} with priority {priority.name}"
            )
            
            return request_id
    
    async def dequeue(self) -> Optional[QueuedRequest]:
        """Get the next request from the queue.
        
        Blocks until a request is available and concurrency allows.
        """
        while True:
            async with self._lock:
                # Check if we can process more
                if self._active_requests >= self._max_concurrent:
                    # Wait for a slot
                    pass
                elif self._queue:
                    # Get next request
                    request = heapq.heappop(self._queue)
                    
                    # Skip expired requests
                    if request.is_expired:
                        logger.warning(
                            f"Dropping expired request {request.id}"
                        )
                        continue
                    
                    self._active_requests += 1
                    
                    if not self._queue:
                        self._not_empty.clear()
                    
                    return request
            
            # Wait for queue changes
            await asyncio.sleep(0.1)
    
    async def complete(self, request_id: str) -> None:
        """Mark a request as completed."""
        async with self._lock:
            self._active_requests = max(0, self._active_requests - 1)
            logger.debug(f"Completed request {request_id}")
    
    def _cleanup_expired(self) -> int:
        """Remove expired requests from the queue."""
        original_len = len(self._queue)
        self._queue = [r for r in self._queue if not r.is_expired]
        heapq.heapify(self._queue)
        removed = original_len - len(self._queue)
        if removed:
            logger.info(f"Cleaned up {removed} expired requests")
        return removed
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get current queue statistics."""
        priority_counts = {p.name: 0 for p in RequestPriority}
        for request in self._queue:
            priority_counts[request.priority.name] += 1
        
        return {
            "queued": len(self._queue),
            "active": self._active_requests,
            "max_concurrent": self._max_concurrent,
            "max_queue_size": self._max_queue_size,
            "by_priority": priority_counts,
            "oldest_age_seconds": (
                time.time() - self._queue[0].created_at
                if self._queue else 0
            ),
        }
    
    async def cancel(self, request_id: str) -> bool:
        """Cancel a queued request."""
        async with self._lock:
            for i, request in enumerate(self._queue):
                if request.id == request_id:
                    self._queue.pop(i)
                    heapq.heapify(self._queue)
                    logger.info(f"Cancelled request {request_id}")
                    return True
            return False


class DynamicLoadBalancer:
    """Distributes load across models based on real-time performance.
    
    Features:
    - Weighted round-robin based on model scores
    - Automatic rebalancing on performance changes
    - Circuit breaker integration
    """
    
    def __init__(
        self,
        selector: Optional[SmartModelSelector] = None,
        rebalance_interval: float = 60.0,
    ):
        self._selector = selector or SmartModelSelector()
        self._rebalance_interval = rebalance_interval
        self._last_rebalance = 0.0
        self._weights: Dict[str, float] = {}
        self._counters: Dict[str, int] = {}
        self._lock = asyncio.Lock()
    
    async def get_next_model(
        self,
        available_models: List[str],
        strategy: SelectionStrategy = SelectionStrategy.BALANCED,
    ) -> Optional[str]:
        """Get the next model to use based on load balancing.
        
        Uses weighted selection based on model scores.
        """
        async with self._lock:
            # Rebalance if needed
            if time.time() - self._last_rebalance > self._rebalance_interval:
                await self._rebalance(available_models, strategy)
            
            # Filter to available models with positive weights
            candidates = [
                m for m in available_models
                if self._weights.get(m, 0) > 0
            ]
            
            if not candidates:
                # Fall back to selector
                result = await self._selector.select_model(
                    available_models, strategy
                )
                return result.model if result else None
            
            # Weighted selection
            total_weight = sum(self._weights.get(m, 0) for m in candidates)
            if total_weight == 0:
                return candidates[0]
            
            # Choose based on weights and current usage
            best_model = None
            best_ratio = float('inf')
            
            for model in candidates:
                weight = self._weights.get(model, 1)
                count = self._counters.get(model, 0)
                # Lower ratio = more underused relative to weight
                ratio = count / weight if weight > 0 else float('inf')
                
                if ratio < best_ratio:
                    best_ratio = ratio
                    best_model = model
            
            if best_model:
                self._counters[best_model] = self._counters.get(best_model, 0) + 1
            
            return best_model
    
    async def _rebalance(
        self,
        models: List[str],
        strategy: SelectionStrategy,
    ) -> None:
        """Recalculate weights for all models."""
        self._weights.clear()
        
        for model in models:
            score = await self._selector.select_model(
                [model], strategy
            )
            if score:
                # Weight is proportional to total score
                self._weights[model] = max(0.1, score.total_score / 100)
        
        self._last_rebalance = time.time()
        logger.debug(f"Rebalanced weights: {self._weights}")
    
    def reset_counters(self) -> None:
        """Reset usage counters for a new balancing period."""
        self._counters.clear()


class QueueFullError(Exception):
    """Raised when the request queue is full."""
    pass


# Convenience functions
def get_model_selector() -> SmartModelSelector:
    """Get a smart model selector instance."""
    return SmartModelSelector()


async def select_best_model(
    models: List[str],
    strategy: SelectionStrategy = SelectionStrategy.BALANCED,
    min_capability: int = 5,
) -> Optional[str]:
    """Select the best model from a list.
    
    Args:
        models: List of model names
        strategy: Selection strategy
        min_capability: Minimum capability tier (1-5, 1=highest)
    
    Returns:
        Best model name or None
    """
    selector = get_model_selector()
    result = await selector.select_model(models, strategy, min_capability)
    return result.model if result else None
