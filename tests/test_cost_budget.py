"""Tests for Cost Budget Enforcer module."""

import asyncio
import pytest
from decimal import Decimal

from code_puppy.core.cost_budget import (
    CostBudgetEnforcer,
    CostAlert,
    AlertSeverity,
    AlertType,
    ProviderCostBudget,
    GlobalCostBudget,
    get_cost_enforcer,
    check_and_record_cost,
)


class TestProviderCostBudget:
    """Tests for ProviderCostBudget class."""
    
    def test_initial_values(self):
        """Budget starts with zero costs."""
        budget = ProviderCostBudget(provider="test")
        
        assert budget.cost_today == Decimal("0.0")
        assert budget.cost_this_month == Decimal("0.0")
    
    def test_daily_usage_percent(self):
        """Daily usage percentage is calculated correctly."""
        budget = ProviderCostBudget(
            provider="test",
            daily_limit_usd=Decimal("10.00"),
        )
        budget.cost_today = Decimal("5.00")
        
        assert budget.daily_usage_percent == 50.0
    
    def test_monthly_usage_percent(self):
        """Monthly usage percentage is calculated correctly."""
        budget = ProviderCostBudget(
            provider="test",
            monthly_limit_usd=Decimal("100.00"),
        )
        budget.cost_this_month = Decimal("25.00")
        
        assert budget.monthly_usage_percent == 25.0
    
    def test_zero_limit_returns_zero_percent(self):
        """Zero limit returns zero usage percent."""
        budget = ProviderCostBudget(
            provider="test",
            daily_limit_usd=Decimal("0"),
        )
        budget.cost_today = Decimal("10.00")
        
        assert budget.daily_usage_percent == 0.0


class TestCostBudgetEnforcer:
    """Tests for CostBudgetEnforcer class."""
    
    def test_singleton_instance(self):
        """Get instance returns same object."""
        # Reset singleton for test
        CostBudgetEnforcer._instance = None
        
        instance1 = CostBudgetEnforcer.get_instance()
        instance2 = CostBudgetEnforcer.get_instance()
        
        assert instance1 is instance2
    
    def test_configure_provider(self):
        """Provider configuration is stored."""
        enforcer = CostBudgetEnforcer()
        enforcer.configure_provider(
            provider="test-provider",
            daily_limit=Decimal("50.00"),
            monthly_limit=Decimal("500.00"),
        )
        
        budget = enforcer._get_or_create_provider_budget("test-provider")
        assert budget.daily_limit_usd == Decimal("50.00")
        assert budget.monthly_limit_usd == Decimal("500.00")
    
    @pytest.mark.asyncio
    async def test_record_cost_updates_totals(self):
        """Recording cost updates all totals."""
        enforcer = CostBudgetEnforcer()
        enforcer.configure_provider("test", Decimal("100"), Decimal("1000"))
        
        await enforcer.record_cost("test", Decimal("5.00"))
        
        budget = enforcer._get_or_create_provider_budget("test")
        assert budget.cost_today == Decimal("5.00")
        assert budget.cost_this_month == Decimal("5.00")
        assert enforcer._global_budget.cost_today == Decimal("5.00")
    
    @pytest.mark.asyncio
    async def test_record_cost_returns_alerts(self):
        """Recording cost returns triggered alerts."""
        enforcer = CostBudgetEnforcer()
        enforcer.configure_provider("test", Decimal("10"), Decimal("100"))
        
        # Record cost that exceeds 50% threshold
        alerts = await enforcer.record_cost("test", Decimal("6.00"))
        
        # Should have at least one alert
        assert len(alerts) >= 1
        assert any(a.severity == AlertSeverity.INFO for a in alerts)
    
    def test_can_proceed_within_budget(self):
        """Can proceed when within budget."""
        enforcer = CostBudgetEnforcer(
            global_daily_limit=Decimal("100.00"),
        )
        enforcer.configure_provider("test", Decimal("50"), Decimal("500"))
        
        assert enforcer.can_proceed("test", Decimal("10.00"))
    
    def test_cannot_proceed_over_budget(self):
        """Cannot proceed when over budget."""
        enforcer = CostBudgetEnforcer()
        enforcer.configure_provider("test", Decimal("10"), Decimal("100"))
        
        # Manually set cost near limit
        budget = enforcer._get_or_create_provider_budget("test")
        budget.cost_today = Decimal("9.50")
        
        assert not enforcer.can_proceed("test", Decimal("1.00"))
    
    def test_get_throttle_factor(self):
        """Throttle factor reflects usage."""
        enforcer = CostBudgetEnforcer()
        enforcer.configure_provider("test", Decimal("100"), Decimal("1000"))
        
        # No usage = no throttle
        budget = enforcer._get_or_create_provider_budget("test")
        budget.cost_today = Decimal("0")
        assert enforcer.get_throttle_factor("test") == 1.0
        
        # 50% usage
        budget.cost_today = Decimal("50")
        assert enforcer.get_throttle_factor("test") == 0.8
        
        # 80% usage
        budget.cost_today = Decimal("80")
        assert enforcer.get_throttle_factor("test") == 0.5
        
        # 95% usage
        budget.cost_today = Decimal("95")
        assert enforcer.get_throttle_factor("test") == 0.1
        
        # 100% usage
        budget.cost_today = Decimal("100")
        assert enforcer.get_throttle_factor("test") == 0.0
    
    def test_add_alert_callback(self):
        """Alert callbacks are called."""
        enforcer = CostBudgetEnforcer()
        
        received_alerts = []
        
        def callback(alert):
            received_alerts.append(alert)
        
        enforcer.add_alert_callback(callback)
        
        # Create a test alert
        test_alert = CostAlert(
            alert_type=AlertType.BUDGET_THRESHOLD,
            severity=AlertSeverity.WARNING,
            provider="test",
            message="Test alert",
            current_cost=Decimal("10"),
            budget_limit=Decimal("100"),
            usage_percent=10.0,
        )
        
        enforcer._send_alert(test_alert)
        
        assert len(received_alerts) == 1
        assert received_alerts[0].message == "Test alert"
    
    def test_get_status(self):
        """Status contains expected fields."""
        enforcer = CostBudgetEnforcer()
        enforcer.configure_provider("test", Decimal("10"), Decimal("100"))
        
        status = enforcer.get_status()
        
        assert "global" in status
        assert "providers" in status
        assert "recent_alerts" in status
        assert "daily_limit" in status["global"]


class TestCostAlert:
    """Tests for CostAlert class."""
    
    def test_alert_str_format(self):
        """Alert string format is correct."""
        alert = CostAlert(
            alert_type=AlertType.BUDGET_THRESHOLD,
            severity=AlertSeverity.WARNING,
            provider="test",
            message="Budget at 80%",
            current_cost=Decimal("80"),
            budget_limit=Decimal("100"),
            usage_percent=80.0,
        )
        
        assert "[WARNING]" in str(alert)
        assert "Budget at 80%" in str(alert)


class TestCheckAndRecordCost:
    """Tests for check_and_record_cost helper."""
    
    @pytest.mark.asyncio
    async def test_allows_within_budget(self):
        """Returns True when within budget."""
        # Reset singleton
        CostBudgetEnforcer._instance = None
        enforcer = CostBudgetEnforcer.get_instance()
        enforcer.configure_provider("test", Decimal("100"), Decimal("1000"))
        
        can_proceed, alerts = await check_and_record_cost(
            provider="test",
            cost_usd=Decimal("1.00"),
        )
        
        assert can_proceed is True
    
    @pytest.mark.asyncio
    async def test_blocks_over_budget(self):
        """Returns False when over budget."""
        CostBudgetEnforcer._instance = None
        enforcer = CostBudgetEnforcer.get_instance()
        enforcer.configure_provider("test", Decimal("10"), Decimal("100"))
        
        # Set close to limit
        budget = enforcer._get_or_create_provider_budget("test")
        budget.cost_today = Decimal("9.50")
        
        can_proceed, alerts = await check_and_record_cost(
            provider="test",
            cost_usd=Decimal("1.00"),
        )
        
        assert can_proceed is False
        assert any(a.alert_type == AlertType.LIMIT_REACHED for a in alerts)
