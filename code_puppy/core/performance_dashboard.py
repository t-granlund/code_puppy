"""Performance Dashboard - System Health & Analytics.

Provides a unified view of system health and performance:
1. Real-time metrics aggregation
2. Health indicators
3. Cost and efficiency analytics
4. Trend analysis
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from .circuit_breaker import CircuitBreakerManager, CircuitState
from .cost_budget import CostBudgetEnforcer
from .model_metrics import ModelMetricsTracker
from .response_cache import get_response_cache
from .smart_selection import SmartModelSelector, SelectionStrategy

logger = logging.getLogger(__name__)


@dataclass
class HealthIndicator:
    """A health indicator for a component."""
    
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    value: float  # 0-100 health percentage
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """Overall system health status."""
    
    overall_status: str  # "healthy", "degraded", "unhealthy"
    overall_score: float  # 0-100
    indicators: List[HealthIndicator] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
    @classmethod
    def from_indicators(cls, indicators: List[HealthIndicator]) -> "SystemHealth":
        """Create system health from a list of indicators."""
        if not indicators:
            return cls(
                overall_status="unknown",
                overall_score=0.0,
                indicators=[],
            )
        
        avg_score = sum(i.value for i in indicators) / len(indicators)
        
        # Determine status based on worst indicator
        if any(i.status == "unhealthy" for i in indicators):
            status = "unhealthy"
        elif any(i.status == "degraded" for i in indicators):
            status = "degraded"
        else:
            status = "healthy"
        
        return cls(
            overall_status=status,
            overall_score=avg_score,
            indicators=indicators,
        )


class PerformanceDashboard:
    """Centralized dashboard for system health and performance.
    
    Aggregates data from:
    - Model metrics tracker
    - Circuit breakers
    - Cost budget enforcer
    - Response cache
    
    Provides:
    - Real-time health status
    - Performance trends
    - Cost analytics
    - Efficiency recommendations
    """
    
    _instance: Optional["PerformanceDashboard"] = None
    
    def __init__(self):
        self._metrics = ModelMetricsTracker.get_instance()
        self._circuits = CircuitBreakerManager.get_instance()
        self._costs = CostBudgetEnforcer.get_instance()
        self._cache = get_response_cache()
        self._selector = SmartModelSelector()
        
        # Historical data for trends
        self._health_history: List[SystemHealth] = []
        self._metrics_history: List[Dict[str, Any]] = []
        self._max_history = 1440  # 24 hours at 1-minute intervals
    
    @classmethod
    def get_instance(cls) -> "PerformanceDashboard":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def get_system_health(self) -> SystemHealth:
        """Get current overall system health."""
        indicators = []
        
        # 1. Model availability health
        indicators.append(await self._check_model_availability())
        
        # 2. Error rate health
        indicators.append(self._check_error_rate())
        
        # 3. Latency health
        indicators.append(self._check_latency())
        
        # 4. Budget health
        indicators.append(self._check_budget_health())
        
        # 5. Cache health
        indicators.append(self._check_cache_health())
        
        health = SystemHealth.from_indicators(indicators)
        
        # Store in history
        self._health_history.append(health)
        if len(self._health_history) > self._max_history:
            self._health_history = self._health_history[-self._max_history // 2:]
        
        return health
    
    async def _check_model_availability(self) -> HealthIndicator:
        """Check model availability via circuit breakers."""
        all_status = self._circuits.get_all_status()
        
        if not all_status:
            return HealthIndicator(
                name="Model Availability",
                status="healthy",
                value=100.0,
                message="No models tracked yet",
            )
        
        open_circuits = [
            name for name, status in all_status.items()
            if status.get("state") == "open"
        ]
        
        available_pct = ((len(all_status) - len(open_circuits)) / len(all_status)) * 100
        
        if open_circuits:
            status = "degraded" if available_pct > 50 else "unhealthy"
            message = f"{len(open_circuits)} model(s) unavailable: {', '.join(open_circuits)}"
        else:
            status = "healthy"
            message = f"All {len(all_status)} models available"
        
        return HealthIndicator(
            name="Model Availability",
            status=status,
            value=available_pct,
            message=message,
            details={"open_circuits": open_circuits},
        )
    
    def _check_error_rate(self) -> HealthIndicator:
        """Check overall error rate."""
        summary = self._metrics.get_summary()
        
        total_requests = summary.get("total_requests", 0)
        if total_requests == 0:
            return HealthIndicator(
                name="Error Rate",
                status="healthy",
                value=100.0,
                message="No requests tracked yet",
            )
        
        # Parse success rate
        success_str = summary.get("overall_success_rate", "100%")
        success_rate = float(success_str.rstrip("%"))
        error_rate = 100 - success_rate
        
        if error_rate > 10:
            status = "unhealthy"
            message = f"High error rate: {error_rate:.1f}%"
        elif error_rate > 5:
            status = "degraded"
            message = f"Elevated error rate: {error_rate:.1f}%"
        else:
            status = "healthy"
            message = f"Error rate normal: {error_rate:.1f}%"
        
        return HealthIndicator(
            name="Error Rate",
            status=status,
            value=success_rate,
            message=message,
            details={"total_requests": total_requests},
        )
    
    def _check_latency(self) -> HealthIndicator:
        """Check overall latency health."""
        # Get last hour metrics
        recent = self._metrics.get_time_windowed_metrics(window_seconds=3600)
        
        if not recent.latencies_ms:
            return HealthIndicator(
                name="Latency",
                status="healthy",
                value=100.0,
                message="No recent requests",
            )
        
        p95 = recent.p95_latency_ms
        
        if p95 > 10000:  # > 10s
            status = "unhealthy"
            score = 20.0
            message = f"Very high P95 latency: {p95:.0f}ms"
        elif p95 > 5000:  # > 5s
            status = "degraded"
            score = 50.0
            message = f"High P95 latency: {p95:.0f}ms"
        elif p95 > 2000:  # > 2s
            status = "degraded"
            score = 70.0
            message = f"Moderate P95 latency: {p95:.0f}ms"
        else:
            status = "healthy"
            score = min(100, 100 - (p95 / 50))  # 0ms = 100, 2000ms = 60
            message = f"P95 latency healthy: {p95:.0f}ms"
        
        return HealthIndicator(
            name="Latency",
            status=status,
            value=score,
            message=message,
            details={
                "p50_ms": recent.p50_latency_ms,
                "p95_ms": p95,
                "p99_ms": recent.p99_latency_ms,
            },
        )
    
    def _check_budget_health(self) -> HealthIndicator:
        """Check budget usage health."""
        status_data = self._costs.get_status()
        global_data = status_data.get("global", {})
        
        daily_limit = Decimal(global_data.get("daily_limit", "50"))
        cost_today = Decimal(global_data.get("cost_today", "0"))
        
        if daily_limit == 0:
            usage_pct = 0
        else:
            usage_pct = float(cost_today / daily_limit * 100)
        
        if usage_pct >= 95:
            status = "unhealthy"
            message = f"Budget nearly exhausted: {usage_pct:.1f}% used"
        elif usage_pct >= 80:
            status = "degraded"
            message = f"Budget usage high: {usage_pct:.1f}% used"
        else:
            status = "healthy"
            message = f"Budget usage normal: {usage_pct:.1f}% used"
        
        remaining_score = max(0, 100 - usage_pct)
        
        return HealthIndicator(
            name="Budget",
            status=status,
            value=remaining_score,
            message=message,
            details={
                "cost_today_usd": str(cost_today),
                "daily_limit_usd": str(daily_limit),
                "usage_percent": usage_pct,
            },
        )
    
    def _check_cache_health(self) -> HealthIndicator:
        """Check response cache health."""
        stats = self._cache.get_stats()
        
        hit_rate_str = stats.get("hit_rate", "0%")
        hit_rate = float(hit_rate_str.rstrip("%"))
        
        entries = stats.get("entries", 0)
        max_entries = stats.get("max_entries", 1000)
        fill_pct = (entries / max_entries * 100) if max_entries else 0
        
        # Cache health is based on hit rate
        if hit_rate >= 30:
            status = "healthy"
            message = f"Good cache hit rate: {hit_rate:.1f}%"
        elif hit_rate >= 10:
            status = "healthy"
            message = f"Moderate cache hit rate: {hit_rate:.1f}%"
        else:
            status = "healthy"  # Low hit rate isn't unhealthy, just not optimal
            message = f"Low cache hit rate: {hit_rate:.1f}%"
        
        # Warn if cache is too full
        if fill_pct > 90:
            status = "degraded"
            message = f"Cache nearly full ({fill_pct:.0f}%), hit rate: {hit_rate:.1f}%"
        
        return HealthIndicator(
            name="Cache",
            status=status,
            value=min(100, hit_rate + 50),  # Hit rate + base score
            message=message,
            details={
                "hit_rate": hit_rate,
                "entries": entries,
                "max_entries": max_entries,
                "tokens_saved": stats.get("tokens_saved", 0),
            },
        )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of system performance."""
        metrics_summary = self._metrics.get_summary()
        cache_stats = self._cache.get_stats()
        cost_status = self._costs.get_status()
        circuit_status = self._circuits.get_all_status()
        
        # Calculate requests per minute
        recent = self._metrics.get_time_windowed_metrics(window_seconds=60)
        requests_per_minute = recent.total_requests
        
        return {
            "timestamp": time.time(),
            "requests": {
                "total": metrics_summary.get("total_requests", 0),
                "per_minute": requests_per_minute,
                "success_rate": metrics_summary.get("overall_success_rate", "100%"),
            },
            "tokens": {
                "total": metrics_summary.get("total_tokens", 0),
                "cached_saved": cache_stats.get("tokens_saved", 0),
            },
            "cost": {
                "today_usd": cost_status["global"]["cost_today"],
                "all_time_usd": cost_status["global"]["cost_all_time"],
            },
            "latency": {
                "p50_ms": recent.p50_latency_ms,
                "p95_ms": recent.p95_latency_ms,
            },
            "cache": {
                "hit_rate": cache_stats.get("hit_rate", "0%"),
                "entries": cache_stats.get("entries", 0),
            },
            "models": {
                "tracked": metrics_summary.get("models_tracked", 0),
                "available": len(self._circuits.get_available_providers()),
                "unavailable": len(self._circuits.get_unavailable_providers()),
            },
        }
    
    def get_cost_analytics(self) -> Dict[str, Any]:
        """Get detailed cost analytics."""
        cost_status = self._costs.get_status()
        efficiency_ranking = self._metrics.get_efficiency_ranking()
        
        # Calculate cost by provider
        provider_costs = {}
        for name, data in cost_status.get("providers", {}).items():
            provider_costs[name] = {
                "today_usd": data.get("cost_today", "0"),
                "usage_percent": data.get("daily_usage_percent", "0%"),
            }
        
        return {
            "global": cost_status.get("global", {}),
            "by_provider": provider_costs,
            "efficiency_ranking": [
                {"model": model, **data}
                for model, data in efficiency_ranking[:5]
            ],
            "recommendations": self._generate_cost_recommendations(),
        }
    
    def _generate_cost_recommendations(self) -> List[str]:
        """Generate cost optimization recommendations."""
        recommendations = []
        
        # Check for expensive models being overused
        efficiency = self._metrics.get_efficiency_ranking()
        if efficiency:
            least_efficient = efficiency[-1]
            model, data = least_efficient
            if data.get("total_requests", 0) > 100:
                recommendations.append(
                    f"Consider reducing usage of {model} - lowest token efficiency"
                )
        
        # Check cache hit rate
        cache_stats = self._cache.get_stats()
        hit_rate_str = cache_stats.get("hit_rate", "0%")
        hit_rate = float(hit_rate_str.rstrip("%"))
        if hit_rate < 20:
            recommendations.append(
                "Low cache hit rate - consider caching more responses"
            )
        
        # Check budget usage
        cost_status = self._costs.get_status()
        for provider, data in cost_status.get("providers", {}).items():
            usage_str = data.get("daily_usage_percent", "0%")
            usage = float(usage_str.rstrip("%"))
            if usage > 80:
                recommendations.append(
                    f"Provider {provider} nearing daily limit ({usage:.0f}%)"
                )
        
        if not recommendations:
            recommendations.append("No immediate cost optimization needed")
        
        return recommendations
    
    def get_model_comparison(self) -> Dict[str, Any]:
        """Compare all tracked models."""
        return {
            "by_efficiency": self._selector.get_model_rankings(
                SelectionStrategy.COST_OPTIMIZED
            ),
            "by_speed": self._selector.get_model_rankings(
                SelectionStrategy.SPEED_OPTIMIZED
            ),
            "by_reliability": self._selector.get_model_rankings(
                SelectionStrategy.RELIABILITY_OPTIMIZED
            ),
        }
    
    def get_trend_analysis(
        self,
        window_minutes: int = 60,
    ) -> Dict[str, Any]:
        """Analyze trends over time."""
        if not self._health_history:
            return {"message": "Not enough data for trend analysis"}
        
        cutoff = time.time() - (window_minutes * 60)
        recent_health = [
            h for h in self._health_history
            if h.timestamp >= cutoff
        ]
        
        if len(recent_health) < 2:
            return {"message": "Not enough data points for trend analysis"}
        
        # Calculate health trend
        first_half = recent_health[:len(recent_health) // 2]
        second_half = recent_health[len(recent_health) // 2:]
        
        avg_first = sum(h.overall_score for h in first_half) / len(first_half)
        avg_second = sum(h.overall_score for h in second_half) / len(second_half)
        
        if avg_second > avg_first + 5:
            trend = "improving"
        elif avg_second < avg_first - 5:
            trend = "degrading"
        else:
            trend = "stable"
        
        return {
            "window_minutes": window_minutes,
            "data_points": len(recent_health),
            "health_trend": trend,
            "first_half_avg": avg_first,
            "second_half_avg": avg_second,
            "current_score": recent_health[-1].overall_score if recent_health else 0,
        }
    
    def get_full_dashboard(self) -> Dict[str, Any]:
        """Get complete dashboard data."""
        # Note: This is synchronous for display purposes
        # For async health check, call get_system_health() separately
        
        return {
            "performance": self.get_performance_summary(),
            "costs": self.get_cost_analytics(),
            "models": self.get_model_comparison(),
            "trends": self.get_trend_analysis(),
            "recent_errors": self._metrics.get_recent_errors(),
        }


# Convenience functions
def get_dashboard() -> PerformanceDashboard:
    """Get the global performance dashboard."""
    return PerformanceDashboard.get_instance()


async def get_health_status() -> SystemHealth:
    """Get current system health status."""
    dashboard = get_dashboard()
    return await dashboard.get_system_health()


def get_performance_metrics() -> Dict[str, Any]:
    """Get current performance metrics."""
    dashboard = get_dashboard()
    return dashboard.get_performance_summary()


def print_dashboard_summary() -> None:
    """Print a text summary of the dashboard."""
    dashboard = get_dashboard()
    data = dashboard.get_full_dashboard()
    
    print("\n" + "=" * 60)
    print("CODE PUPPY PERFORMANCE DASHBOARD")
    print("=" * 60)
    
    perf = data["performance"]
    print(f"\n📊 Requests: {perf['requests']['total']} total, "
          f"{perf['requests']['per_minute']}/min")
    print(f"✅ Success Rate: {perf['requests']['success_rate']}")
    print(f"⏱️  Latency: P50={perf['latency']['p50_ms']:.0f}ms, "
          f"P95={perf['latency']['p95_ms']:.0f}ms")
    print(f"💰 Cost Today: ${perf['cost']['today_usd']}")
    print(f"🎯 Cache: {perf['cache']['hit_rate']} hit rate, "
          f"{perf['cache']['entries']} entries")
    print(f"🤖 Models: {perf['models']['available']} available, "
          f"{perf['models']['unavailable']} unavailable")
    
    trends = data["trends"]
    if "health_trend" in trends:
        print(f"\n📈 Trend: {trends['health_trend'].upper()}")
    
    print("\n" + "=" * 60)
