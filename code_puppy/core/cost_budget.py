"""Cost Budget Enforcer & Alerts - Financial Controls.

Implements cost budgeting and alerting:
1. Daily and monthly cost limits per provider and global
2. Cost anomaly detection
3. Alert callbacks when thresholds are exceeded
4. Automatic throttling when limits approached
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Severity levels for cost alerts."""
    
    INFO = "info"  # Informational (50% of budget used)
    WARNING = "warning"  # Warning (80% of budget used)
    CRITICAL = "critical"  # Critical (95% of budget used)
    LIMIT_REACHED = "limit_reached"  # At or over limit


class AlertType(Enum):
    """Types of cost alerts."""
    
    BUDGET_THRESHOLD = "budget_threshold"  # Approaching budget limit
    ANOMALY_DETECTED = "anomaly_detected"  # Unusual spending pattern
    LIMIT_REACHED = "limit_reached"  # Budget exhausted
    RATE_SPIKE = "rate_spike"  # Sudden increase in spending rate


@dataclass
class CostAlert:
    """A cost alert notification."""
    
    alert_type: AlertType
    severity: AlertSeverity
    provider: Optional[str]  # None for global alerts
    message: str
    current_cost: Decimal
    budget_limit: Decimal
    usage_percent: float
    timestamp: float = field(default_factory=time.time)
    
    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.message}"


@dataclass 
class ProviderCostBudget:
    """Cost budget configuration for a single provider."""
    
    provider: str
    daily_limit_usd: Decimal = Decimal("10.00")
    monthly_limit_usd: Decimal = Decimal("100.00")
    
    # Runtime tracking
    cost_today: Decimal = field(default_factory=lambda: Decimal("0.0"))
    cost_this_month: Decimal = field(default_factory=lambda: Decimal("0.0"))
    cost_this_hour: Decimal = field(default_factory=lambda: Decimal("0.0"))
    
    # Timestamps for reset
    last_daily_reset: float = field(default_factory=time.time)
    last_monthly_reset: float = field(default_factory=time.time)
    last_hourly_reset: float = field(default_factory=time.time)
    
    # Alert state
    alerts_sent: Set[str] = field(default_factory=set)  # Alert keys already sent
    
    def check_resets(self) -> None:
        """Check and perform time-based resets."""
        now = time.time()
        
        # Hourly reset
        if now - self.last_hourly_reset >= 3600:
            self.cost_this_hour = Decimal("0.0")
            self.last_hourly_reset = now
        
        # Daily reset
        if now - self.last_daily_reset >= 86400:
            self.cost_today = Decimal("0.0")
            self.last_daily_reset = now
            self.alerts_sent.clear()  # Reset daily alerts
        
        # Monthly reset (approximate 30 days)
        if now - self.last_monthly_reset >= 86400 * 30:
            self.cost_this_month = Decimal("0.0")
            self.last_monthly_reset = now
    
    @property
    def daily_usage_percent(self) -> float:
        """Percentage of daily budget used."""
        if self.daily_limit_usd == 0:
            return 0.0
        return float(self.cost_today / self.daily_limit_usd * 100)
    
    @property
    def monthly_usage_percent(self) -> float:
        """Percentage of monthly budget used."""
        if self.monthly_limit_usd == 0:
            return 0.0
        return float(self.cost_this_month / self.monthly_limit_usd * 100)


@dataclass
class GlobalCostBudget:
    """Global cost budget across all providers."""
    
    daily_limit_usd: Decimal = Decimal("50.00")
    monthly_limit_usd: Decimal = Decimal("500.00")
    
    # Runtime tracking
    cost_today: Decimal = field(default_factory=lambda: Decimal("0.0"))
    cost_this_month: Decimal = field(default_factory=lambda: Decimal("0.0"))
    cost_all_time: Decimal = field(default_factory=lambda: Decimal("0.0"))
    
    # Timestamps
    last_daily_reset: float = field(default_factory=time.time)
    last_monthly_reset: float = field(default_factory=time.time)
    
    alerts_sent: Set[str] = field(default_factory=set)


AlertCallback = Callable[[CostAlert], None]


class CostBudgetEnforcer:
    """Enforces cost budgets and sends alerts.
    
    Features:
    - Per-provider and global budget limits
    - Automatic throttling when limits approached
    - Configurable alert callbacks
    - Anomaly detection for unusual spending
    """
    
    # Default provider limits
    DEFAULT_PROVIDER_LIMITS: Dict[str, Dict[str, float]] = {
        "cerebras": {"daily": 0.0, "monthly": 0.0},  # Free tier
        "gemini": {"daily": 5.0, "monthly": 50.0},
        "gemini_flash": {"daily": 2.0, "monthly": 20.0},
        "claude_opus": {"daily": 20.0, "monthly": 200.0},
        "claude_sonnet": {"daily": 10.0, "monthly": 100.0},
        "codex": {"daily": 15.0, "monthly": 150.0},
    }
    
    # Alert thresholds (percentage of budget)
    ALERT_THRESHOLDS: Dict[AlertSeverity, float] = {
        AlertSeverity.INFO: 50.0,
        AlertSeverity.WARNING: 80.0,
        AlertSeverity.CRITICAL: 95.0,
        AlertSeverity.LIMIT_REACHED: 100.0,
    }
    
    _instance: Optional["CostBudgetEnforcer"] = None
    
    def __init__(
        self,
        global_daily_limit: Decimal = Decimal("50.00"),
        global_monthly_limit: Decimal = Decimal("500.00"),
    ):
        self._global_budget = GlobalCostBudget(
            daily_limit_usd=global_daily_limit,
            monthly_limit_usd=global_monthly_limit,
        )
        self._provider_budgets: Dict[str, ProviderCostBudget] = {}
        self._alert_callbacks: List[AlertCallback] = []
        self._alert_history: List[CostAlert] = []
        self._hourly_costs: List[Tuple[float, Decimal]] = []  # For anomaly detection
        self._lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> "CostBudgetEnforcer":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def configure_provider(
        self,
        provider: str,
        daily_limit: Decimal,
        monthly_limit: Decimal,
    ) -> None:
        """Configure budget limits for a provider."""
        if provider not in self._provider_budgets:
            self._provider_budgets[provider] = ProviderCostBudget(provider=provider)
        
        budget = self._provider_budgets[provider]
        budget.daily_limit_usd = daily_limit
        budget.monthly_limit_usd = monthly_limit
    
    def add_alert_callback(self, callback: AlertCallback) -> None:
        """Add a callback to receive cost alerts."""
        self._alert_callbacks.append(callback)
    
    def _get_or_create_provider_budget(self, provider: str) -> ProviderCostBudget:
        """Get or create a provider budget with defaults."""
        if provider not in self._provider_budgets:
            limits = self.DEFAULT_PROVIDER_LIMITS.get(
                provider,
                {"daily": 10.0, "monthly": 100.0}
            )
            self._provider_budgets[provider] = ProviderCostBudget(
                provider=provider,
                daily_limit_usd=Decimal(str(limits["daily"])),
                monthly_limit_usd=Decimal(str(limits["monthly"])),
            )
        return self._provider_budgets[provider]
    
    async def record_cost(
        self,
        provider: str,
        cost_usd: Decimal,
    ) -> List[CostAlert]:
        """Record a cost and check for alerts.
        
        Returns list of any alerts triggered.
        """
        async with self._lock:
            # Update provider budget
            budget = self._get_or_create_provider_budget(provider)
            budget.check_resets()
            budget.cost_today += cost_usd
            budget.cost_this_month += cost_usd
            budget.cost_this_hour += cost_usd
            
            # Update global budget
            self._check_global_resets()
            self._global_budget.cost_today += cost_usd
            self._global_budget.cost_this_month += cost_usd
            self._global_budget.cost_all_time += cost_usd
            
            # Track for anomaly detection
            self._hourly_costs.append((time.time(), cost_usd))
            self._cleanup_old_costs()
            
            # Check for alerts
            alerts = []
            
            # Provider alerts
            alerts.extend(self._check_provider_alerts(provider, budget))
            
            # Global alerts
            alerts.extend(self._check_global_alerts())
            
            # Anomaly alerts
            anomaly = self._check_for_anomaly(provider)
            if anomaly:
                alerts.append(anomaly)
            
            # Send alerts
            for alert in alerts:
                self._send_alert(alert)
            
            return alerts
    
    def _check_global_resets(self) -> None:
        """Check and perform global budget resets."""
        now = time.time()
        
        if now - self._global_budget.last_daily_reset >= 86400:
            self._global_budget.cost_today = Decimal("0.0")
            self._global_budget.last_daily_reset = now
            self._global_budget.alerts_sent.clear()
        
        if now - self._global_budget.last_monthly_reset >= 86400 * 30:
            self._global_budget.cost_this_month = Decimal("0.0")
            self._global_budget.last_monthly_reset = now
    
    def _check_provider_alerts(
        self,
        provider: str,
        budget: ProviderCostBudget,
    ) -> List[CostAlert]:
        """Check if provider budget triggers any alerts."""
        alerts = []
        
        # Skip if no limits (e.g., free tier)
        if budget.daily_limit_usd == 0 and budget.monthly_limit_usd == 0:
            return alerts
        
        # Check daily limit
        if budget.daily_limit_usd > 0:
            for severity, threshold in self.ALERT_THRESHOLDS.items():
                if budget.daily_usage_percent >= threshold:
                    alert_key = f"{provider}_daily_{severity.value}"
                    if alert_key not in budget.alerts_sent:
                        budget.alerts_sent.add(alert_key)
                        alerts.append(CostAlert(
                            alert_type=AlertType.BUDGET_THRESHOLD,
                            severity=severity,
                            provider=provider,
                            message=f"Provider {provider} daily budget at {budget.daily_usage_percent:.1f}%",
                            current_cost=budget.cost_today,
                            budget_limit=budget.daily_limit_usd,
                            usage_percent=budget.daily_usage_percent,
                        ))
        
        return alerts
    
    def _check_global_alerts(self) -> List[CostAlert]:
        """Check if global budget triggers any alerts."""
        alerts = []
        budget = self._global_budget
        
        # Check daily limit
        if budget.daily_limit_usd > 0:
            usage_pct = float(budget.cost_today / budget.daily_limit_usd * 100)
            for severity, threshold in self.ALERT_THRESHOLDS.items():
                if usage_pct >= threshold:
                    alert_key = f"global_daily_{severity.value}"
                    if alert_key not in budget.alerts_sent:
                        budget.alerts_sent.add(alert_key)
                        alerts.append(CostAlert(
                            alert_type=AlertType.BUDGET_THRESHOLD,
                            severity=severity,
                            provider=None,
                            message=f"Global daily budget at {usage_pct:.1f}%",
                            current_cost=budget.cost_today,
                            budget_limit=budget.daily_limit_usd,
                            usage_percent=usage_pct,
                        ))
        
        return alerts
    
    def _check_for_anomaly(self, provider: str) -> Optional[CostAlert]:
        """Detect unusual spending patterns."""
        if len(self._hourly_costs) < 10:
            return None
        
        # Calculate recent rate vs historical
        now = time.time()
        recent_costs = [c for t, c in self._hourly_costs if now - t < 300]  # Last 5 min
        historical_costs = [c for t, c in self._hourly_costs if now - t >= 300]
        
        if not recent_costs or not historical_costs:
            return None
        
        recent_rate = sum(recent_costs) / Decimal("5")  # Per minute
        historical_rate = sum(historical_costs) / Decimal(str(len(historical_costs)))
        
        # Alert if recent rate is 3x historical
        if historical_rate > 0 and recent_rate > historical_rate * 3:
            return CostAlert(
                alert_type=AlertType.RATE_SPIKE,
                severity=AlertSeverity.WARNING,
                provider=provider,
                message=f"Cost rate spike detected: {recent_rate:.4f}/min vs {historical_rate:.4f}/min historical",
                current_cost=sum(recent_costs),
                budget_limit=Decimal("0"),
                usage_percent=0,
            )
        
        return None
    
    def _cleanup_old_costs(self) -> None:
        """Remove cost records older than 1 hour."""
        now = time.time()
        self._hourly_costs = [
            (t, c) for t, c in self._hourly_costs
            if now - t < 3600
        ]
    
    def _send_alert(self, alert: CostAlert) -> None:
        """Send an alert to all registered callbacks."""
        self._alert_history.append(alert)
        
        # Keep only recent alerts
        if len(self._alert_history) > 1000:
            self._alert_history = self._alert_history[-500:]
        
        # Log the alert
        log_func = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.CRITICAL: logger.error,
            AlertSeverity.LIMIT_REACHED: logger.error,
        }.get(alert.severity, logger.info)
        log_func(str(alert))
        
        # Call callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    def can_proceed(
        self,
        provider: str,
        estimated_cost: Decimal = Decimal("0.01"),
    ) -> bool:
        """Check if a request can proceed within budget.
        
        Returns False if request would exceed limits.
        """
        budget = self._get_or_create_provider_budget(provider)
        budget.check_resets()
        
        # Check provider daily limit
        if budget.daily_limit_usd > 0:
            if budget.cost_today + estimated_cost > budget.daily_limit_usd:
                return False
        
        # Check global daily limit
        self._check_global_resets()
        if self._global_budget.daily_limit_usd > 0:
            if self._global_budget.cost_today + estimated_cost > self._global_budget.daily_limit_usd:
                return False
        
        return True
    
    def get_throttle_factor(self, provider: str) -> float:
        """Get a throttle factor based on budget usage.
        
        Returns:
            1.0 = no throttle
            0.5 = 50% throttle (delay requests)
            0.0 = full throttle (block requests)
        """
        budget = self._get_or_create_provider_budget(provider)
        budget.check_resets()
        
        usage = max(budget.daily_usage_percent, budget.monthly_usage_percent)
        
        if usage >= 100:
            return 0.0
        elif usage >= 95:
            return 0.1
        elif usage >= 80:
            return 0.5
        elif usage >= 50:
            return 0.8
        else:
            return 1.0
    
    def get_status(self) -> Dict[str, Any]:
        """Get current cost budget status."""
        return {
            "global": {
                "cost_today": str(self._global_budget.cost_today),
                "cost_this_month": str(self._global_budget.cost_this_month),
                "cost_all_time": str(self._global_budget.cost_all_time),
                "daily_limit": str(self._global_budget.daily_limit_usd),
                "monthly_limit": str(self._global_budget.monthly_limit_usd),
            },
            "providers": {
                name: {
                    "cost_today": str(budget.cost_today),
                    "cost_this_month": str(budget.cost_this_month),
                    "daily_usage_percent": f"{budget.daily_usage_percent:.1f}%",
                    "monthly_usage_percent": f"{budget.monthly_usage_percent:.1f}%",
                }
                for name, budget in self._provider_budgets.items()
            },
            "recent_alerts": [
                {
                    "type": alert.alert_type.value,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp,
                }
                for alert in self._alert_history[-10:]
            ],
        }


# Convenience functions
def get_cost_enforcer() -> CostBudgetEnforcer:
    """Get the global cost budget enforcer."""
    return CostBudgetEnforcer.get_instance()


async def check_and_record_cost(
    provider: str,
    cost_usd: Decimal,
) -> Tuple[bool, List[CostAlert]]:
    """Check if cost is within budget and record it.
    
    Returns:
        Tuple of (can_proceed, alerts)
    """
    enforcer = get_cost_enforcer()
    can_proceed = enforcer.can_proceed(provider, cost_usd)
    
    if can_proceed:
        alerts = await enforcer.record_cost(provider, cost_usd)
    else:
        alerts = [CostAlert(
            alert_type=AlertType.LIMIT_REACHED,
            severity=AlertSeverity.LIMIT_REACHED,
            provider=provider,
            message=f"Budget limit reached for {provider}",
            current_cost=cost_usd,
            budget_limit=Decimal("0"),
            usage_percent=100.0,
        )]
    
    return can_proceed, alerts
