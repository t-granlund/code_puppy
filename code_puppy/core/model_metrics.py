"""Model Performance Tracking - Analytics & Metrics.

Tracks model performance metrics for optimization:
1. Latency tracking (p50, p95, p99)
2. Success/failure rates
3. Token usage patterns
4. Cost efficiency metrics
"""

import asyncio
import logging
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class RequestMetric:
    """Metrics for a single request."""
    
    model: str
    provider: str
    timestamp: float = field(default_factory=time.time)
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: Decimal = Decimal("0.0")
    success: bool = True
    error: Optional[str] = None
    task_type: Optional[str] = None
    cached: bool = False


@dataclass
class AggregatedMetrics:
    """Aggregated metrics for a model/provider."""
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cached_requests: int = 0
    
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: Decimal = field(default_factory=lambda: Decimal("0.0"))
    
    latencies_ms: List[float] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.cached_requests / self.total_requests) * 100
    
    @property
    def avg_latency_ms(self) -> float:
        """Average latency in milliseconds."""
        if not self.latencies_ms:
            return 0.0
        return statistics.mean(self.latencies_ms)
    
    @property
    def p50_latency_ms(self) -> float:
        """50th percentile latency."""
        if not self.latencies_ms:
            return 0.0
        return statistics.median(self.latencies_ms)
    
    @property
    def p95_latency_ms(self) -> float:
        """95th percentile latency."""
        if len(self.latencies_ms) < 2:
            return self.avg_latency_ms
        sorted_latencies = sorted(self.latencies_ms)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    @property
    def p99_latency_ms(self) -> float:
        """99th percentile latency."""
        if len(self.latencies_ms) < 2:
            return self.avg_latency_ms
        sorted_latencies = sorted(self.latencies_ms)
        idx = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    @property
    def avg_tokens_per_request(self) -> float:
        """Average tokens per request."""
        if self.total_requests == 0:
            return 0.0
        return (self.total_input_tokens + self.total_output_tokens) / self.total_requests
    
    @property
    def cost_per_1k_tokens(self) -> Decimal:
        """Cost per 1000 tokens."""
        total_tokens = self.total_input_tokens + self.total_output_tokens
        if total_tokens == 0:
            return Decimal("0.0")
        return (self.total_cost_usd / Decimal(str(total_tokens))) * 1000
    
    @property
    def tokens_per_second(self) -> float:
        """Average throughput in tokens per second."""
        if not self.latencies_ms or self.total_requests == 0:
            return 0.0
        avg_latency_s = self.avg_latency_ms / 1000
        if avg_latency_s == 0:
            return 0.0
        return self.avg_tokens_per_request / avg_latency_s


class ModelMetricsTracker:
    """Tracks performance metrics for all models.
    
    Provides:
    - Per-model and per-provider aggregations
    - Time-windowed metrics (last hour, day)
    - Efficiency rankings
    """
    
    _instance: Optional["ModelMetricsTracker"] = None
    
    def __init__(self, max_metrics_per_model: int = 10000):
        self._metrics: Dict[str, List[RequestMetric]] = defaultdict(list)
        self._max_per_model = max_metrics_per_model
        self._aggregated: Dict[str, AggregatedMetrics] = {}
        self._lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> "ModelMetricsTracker":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def record_request(
        self,
        model: str,
        provider: str,
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
        cost_usd: Decimal = Decimal("0.0"),
        success: bool = True,
        error: Optional[str] = None,
        task_type: Optional[str] = None,
        cached: bool = False,
    ) -> None:
        """Record metrics for a request."""
        metric = RequestMetric(
            model=model,
            provider=provider,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            success=success,
            error=error,
            task_type=task_type,
            cached=cached,
        )
        
        async with self._lock:
            self._metrics[model].append(metric)
            
            # Prune old metrics
            if len(self._metrics[model]) > self._max_per_model:
                self._metrics[model] = self._metrics[model][-self._max_per_model // 2:]
            
            # Update aggregated metrics
            self._update_aggregated(model, metric)
    
    def _update_aggregated(self, model: str, metric: RequestMetric) -> None:
        """Update aggregated metrics for a model."""
        if model not in self._aggregated:
            self._aggregated[model] = AggregatedMetrics()
        
        agg = self._aggregated[model]
        agg.total_requests += 1
        
        if metric.success:
            agg.successful_requests += 1
        else:
            agg.failed_requests += 1
        
        if metric.cached:
            agg.cached_requests += 1
        
        agg.total_input_tokens += metric.input_tokens
        agg.total_output_tokens += metric.output_tokens
        agg.total_cost_usd += metric.cost_usd
        agg.latencies_ms.append(metric.latency_ms)
        
        # Keep latencies bounded
        if len(agg.latencies_ms) > 1000:
            agg.latencies_ms = agg.latencies_ms[-500:]
    
    def get_model_metrics(self, model: str) -> Optional[AggregatedMetrics]:
        """Get aggregated metrics for a specific model."""
        return self._aggregated.get(model)
    
    def get_provider_metrics(self, provider: str) -> AggregatedMetrics:
        """Get aggregated metrics for a provider (across all models)."""
        combined = AggregatedMetrics()
        
        for model, metrics in self._metrics.items():
            for metric in metrics:
                if metric.provider == provider:
                    combined.total_requests += 1
                    if metric.success:
                        combined.successful_requests += 1
                    else:
                        combined.failed_requests += 1
                    if metric.cached:
                        combined.cached_requests += 1
                    combined.total_input_tokens += metric.input_tokens
                    combined.total_output_tokens += metric.output_tokens
                    combined.total_cost_usd += metric.cost_usd
                    combined.latencies_ms.append(metric.latency_ms)
        
        return combined
    
    def get_time_windowed_metrics(
        self,
        model: Optional[str] = None,
        window_seconds: float = 3600.0,  # Last hour by default
    ) -> AggregatedMetrics:
        """Get metrics within a time window."""
        cutoff = time.time() - window_seconds
        windowed = AggregatedMetrics()
        
        models_to_check = [model] if model else list(self._metrics.keys())
        
        for m in models_to_check:
            if m not in self._metrics:
                continue
            
            for metric in self._metrics[m]:
                if metric.timestamp >= cutoff:
                    windowed.total_requests += 1
                    if metric.success:
                        windowed.successful_requests += 1
                    else:
                        windowed.failed_requests += 1
                    if metric.cached:
                        windowed.cached_requests += 1
                    windowed.total_input_tokens += metric.input_tokens
                    windowed.total_output_tokens += metric.output_tokens
                    windowed.total_cost_usd += metric.cost_usd
                    windowed.latencies_ms.append(metric.latency_ms)
        
        return windowed
    
    def get_efficiency_ranking(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Rank models by efficiency (tokens per dollar).
        
        Returns list of (model_name, metrics_dict) sorted by efficiency.
        """
        rankings = []
        
        for model, agg in self._aggregated.items():
            if agg.total_requests == 0:
                continue
            
            total_tokens = agg.total_input_tokens + agg.total_output_tokens
            
            # Calculate tokens per dollar (higher is better)
            if agg.total_cost_usd > 0:
                tokens_per_dollar = float(Decimal(str(total_tokens)) / agg.total_cost_usd)
            else:
                tokens_per_dollar = float('inf')  # Free models are most efficient
            
            rankings.append((model, {
                "tokens_per_dollar": tokens_per_dollar,
                "avg_latency_ms": agg.avg_latency_ms,
                "success_rate": agg.success_rate,
                "total_requests": agg.total_requests,
                "total_cost_usd": str(agg.total_cost_usd),
            }))
        
        # Sort by tokens per dollar (descending)
        rankings.sort(key=lambda x: x[1]["tokens_per_dollar"], reverse=True)
        return rankings
    
    def get_speed_ranking(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Rank models by speed (tokens per second).
        
        Returns list of (model_name, metrics_dict) sorted by speed.
        """
        rankings = []
        
        for model, agg in self._aggregated.items():
            if agg.total_requests == 0:
                continue
            
            rankings.append((model, {
                "tokens_per_second": agg.tokens_per_second,
                "p50_latency_ms": agg.p50_latency_ms,
                "p95_latency_ms": agg.p95_latency_ms,
                "success_rate": agg.success_rate,
                "total_requests": agg.total_requests,
            }))
        
        # Sort by tokens per second (descending)
        rankings.sort(key=lambda x: x[1]["tokens_per_second"], reverse=True)
        return rankings
    
    def get_reliability_ranking(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Rank models by reliability (success rate).
        
        Returns list of (model_name, metrics_dict) sorted by reliability.
        """
        rankings = []
        
        for model, agg in self._aggregated.items():
            if agg.total_requests == 0:
                continue
            
            rankings.append((model, {
                "success_rate": agg.success_rate,
                "total_requests": agg.total_requests,
                "failed_requests": agg.failed_requests,
                "p99_latency_ms": agg.p99_latency_ms,
            }))
        
        # Sort by success rate (descending)
        rankings.sort(key=lambda x: x[1]["success_rate"], reverse=True)
        return rankings
    
    def get_summary(self) -> Dict[str, Any]:
        """Get overall summary of all tracked metrics."""
        total_requests = sum(agg.total_requests for agg in self._aggregated.values())
        total_cost = sum(agg.total_cost_usd for agg in self._aggregated.values())
        total_tokens = sum(
            agg.total_input_tokens + agg.total_output_tokens
            for agg in self._aggregated.values()
        )
        
        # Calculate overall success rate
        total_success = sum(agg.successful_requests for agg in self._aggregated.values())
        overall_success_rate = (total_success / total_requests * 100) if total_requests else 100.0
        
        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost_usd": str(total_cost),
            "overall_success_rate": f"{overall_success_rate:.1f}%",
            "models_tracked": len(self._aggregated),
            "efficiency_leader": self.get_efficiency_ranking()[0][0] if self._aggregated else None,
            "speed_leader": self.get_speed_ranking()[0][0] if self._aggregated else None,
            "per_model": {
                model: {
                    "requests": agg.total_requests,
                    "success_rate": f"{agg.success_rate:.1f}%",
                    "avg_latency_ms": f"{agg.avg_latency_ms:.0f}",
                    "tokens_per_second": f"{agg.tokens_per_second:.0f}",
                    "total_cost_usd": str(agg.total_cost_usd),
                }
                for model, agg in self._aggregated.items()
            },
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent error messages across all models."""
        errors = []
        
        for model, metrics in self._metrics.items():
            for metric in reversed(metrics):
                if not metric.success and metric.error:
                    errors.append({
                        "model": model,
                        "provider": metric.provider,
                        "error": metric.error,
                        "timestamp": metric.timestamp,
                    })
                    if len(errors) >= limit:
                        break
            if len(errors) >= limit:
                break
        
        return errors[:limit]


# Context manager for tracking request metrics
class MetricsContext:
    """Context manager for automatically tracking request metrics."""
    
    def __init__(
        self,
        model: str,
        provider: str,
        task_type: Optional[str] = None,
    ):
        self.model = model
        self.provider = provider
        self.task_type = task_type
        self.start_time = 0.0
        self.input_tokens = 0
        self.output_tokens = 0
        self.cost_usd = Decimal("0.0")
        self.cached = False
        self.error: Optional[str] = None
    
    async def __aenter__(self) -> "MetricsContext":
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        latency_ms = (time.time() - self.start_time) * 1000
        success = exc_type is None
        
        if exc_val:
            self.error = str(exc_val)
        
        tracker = ModelMetricsTracker.get_instance()
        await tracker.record_request(
            model=self.model,
            provider=self.provider,
            latency_ms=latency_ms,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            cost_usd=self.cost_usd,
            success=success,
            error=self.error,
            task_type=self.task_type,
            cached=self.cached,
        )


# Convenience functions
def get_metrics_tracker() -> ModelMetricsTracker:
    """Get the global metrics tracker."""
    return ModelMetricsTracker.get_instance()


def track_request(
    model: str,
    provider: str,
    task_type: Optional[str] = None,
) -> MetricsContext:
    """Create a metrics tracking context.
    
    Usage:
        async with track_request("cerebras-glm", "cerebras") as ctx:
            response = await model.generate(...)
            ctx.input_tokens = response.input_tokens
            ctx.output_tokens = response.output_tokens
    """
    return MetricsContext(model, provider, task_type)
