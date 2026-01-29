"""Tests for Token Telemetry module.

AUDIT-1.1 Part G test coverage.
"""

import json
import os
import tempfile
import pytest
from datetime import datetime, date
from unittest.mock import patch, MagicMock

from code_puppy.tools.token_telemetry import (
    # Constants
    CEREBRAS_DAILY_LIMIT,
    CEREBRAS_TPM_LIMIT,
    CEREBRAS_RPM_LIMIT,
    DEFAULT_BURN_RATE_WARN,
    DEFAULT_BURN_RATE_CRITICAL,
    DEFAULT_FALLBACK_AT,
    # Enums
    AlertLevel,
    BudgetMode,
    # Data classes
    UsageEntry,
    DailySummary,
    BurnRateInfo,
    # Classes
    TokenLedger,
    # Functions
    get_ledger,
    record_usage,
    check_burn_rate,
    should_fallback_to_review_only,
    format_burn_rate_alert,
)


class TestUsageEntry:
    """Test UsageEntry data class."""
    
    def test_create_entry(self):
        """Create usage entry."""
        entry = UsageEntry(
            timestamp="2024-01-01T10:00:00",
            provider="cerebras",
            model="qwen-3-32b",
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
        )
        assert entry.total_tokens == 1500
        assert entry.provider == "cerebras"
    
    def test_entry_to_dict(self):
        """Entry serializes to dict."""
        entry = UsageEntry(
            timestamp="2024-01-01T10:00:00",
            provider="cerebras",
            model="qwen-3-32b",
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
            latency_ms=250,
        )
        data = entry.to_dict()
        
        assert data["provider"] == "cerebras"
        assert data["in"] == 1000
        assert data["out"] == 500
        assert data["total"] == 1500
        assert data["latency"] == 250
    
    def test_entry_from_dict(self):
        """Entry deserializes from dict."""
        data = {
            "ts": "2024-01-01T10:00:00",
            "provider": "anthropic",
            "model": "claude-3",
            "in": 2000,
            "out": 1000,
            "total": 3000,
        }
        entry = UsageEntry.from_dict(data)
        
        assert entry.provider == "anthropic"
        assert entry.input_tokens == 2000
        assert entry.total_tokens == 3000


class TestDailySummary:
    """Test DailySummary data class."""
    
    def test_create_summary(self):
        """Create daily summary."""
        summary = DailySummary(
            date="2024-01-01",
            provider="cerebras",
            total_tokens=50000,
            request_count=20,
        )
        assert summary.total_tokens == 50000
        assert summary.request_count == 20
    
    def test_summary_to_dict(self):
        """Summary serializes correctly."""
        summary = DailySummary(
            date="2024-01-01",
            provider="cerebras",
            total_tokens=100000,
            input_tokens=70000,
            output_tokens=30000,
            request_count=50,
        )
        data = summary.to_dict()
        
        assert data["date"] == "2024-01-01"
        assert data["total"] == 100000
        assert data["in"] == 70000
        assert data["requests"] == 50


class TestBurnRateInfo:
    """Test BurnRateInfo data class."""
    
    def test_create_burn_rate(self):
        """Create burn rate info."""
        info = BurnRateInfo(
            provider="cerebras",
            tokens_today=1000000,
            daily_limit=24000000,
            usage_percent=0.0417,
            tokens_per_minute=5000,
            estimated_exhaustion_minutes=4600,
            alert_level=AlertLevel.NONE,
            budget_mode=BudgetMode.NORMAL,
            message="All good",
        )
        assert info.usage_percent < 0.05
        assert info.budget_mode == BudgetMode.NORMAL
    
    def test_burn_rate_to_dict(self):
        """Burn rate serializes correctly."""
        info = BurnRateInfo(
            provider="cerebras",
            tokens_today=20000000,
            daily_limit=24000000,
            usage_percent=0.833,
            tokens_per_minute=10000,
            estimated_exhaustion_minutes=400,
            alert_level=AlertLevel.WARNING,
            budget_mode=BudgetMode.CONSERVATIVE,
            message="Warning",
        )
        data = info.to_dict()
        
        assert data["provider"] == "cerebras"
        assert data["alert"] == "warning"
        assert data["mode"] == "conservative"


class TestTokenLedger:
    """Test TokenLedger class."""
    
    @pytest.fixture
    def temp_ledger(self):
        """Create a temporary ledger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = TokenLedger(base_dir=tmpdir)
            yield ledger
    
    def test_record_usage(self, temp_ledger):
        """Record usage entry."""
        entry = temp_ledger.record_usage(
            provider="cerebras",
            model="qwen-3-32b",
            input_tokens=5000,
            output_tokens=2000,
        )
        
        assert entry.total_tokens == 7000
        assert entry.provider == "cerebras"
    
    def test_session_tracking(self, temp_ledger):
        """Session tokens are tracked."""
        temp_ledger.record_usage(
            provider="cerebras",
            model="model1",
            input_tokens=1000,
            output_tokens=500,
        )
        temp_ledger.record_usage(
            provider="cerebras",
            model="model1",
            input_tokens=2000,
            output_tokens=1000,
        )
        
        session = temp_ledger.get_session_usage()
        assert session["cerebras"] == 4500  # 1500 + 3000
    
    def test_daily_summary_accumulation(self, temp_ledger):
        """Daily summary accumulates."""
        for i in range(5):
            temp_ledger.record_usage(
                provider="cerebras",
                model="model1",
                input_tokens=1000,
                output_tokens=500,
            )
        
        summary = temp_ledger.get_daily_summary("cerebras")
        assert summary is not None
        assert summary.request_count == 5
        assert summary.total_tokens == 7500  # 5 * 1500
    
    def test_burn_rate_calculation(self, temp_ledger):
        """Burn rate is calculated correctly."""
        # Record some usage
        temp_ledger.record_usage(
            provider="cerebras",
            model="model1",
            input_tokens=100000,
            output_tokens=50000,
        )
        
        info = temp_ledger.get_burn_rate("cerebras")
        
        assert info.tokens_today == 150000
        assert info.daily_limit == CEREBRAS_DAILY_LIMIT
        assert info.usage_percent > 0
    
    def test_reset_session(self, temp_ledger):
        """Session can be reset."""
        temp_ledger.record_usage(
            provider="cerebras",
            model="model1",
            input_tokens=1000,
            output_tokens=500,
        )
        
        temp_ledger.reset_session()
        session = temp_ledger.get_session_usage()
        
        assert session.get("cerebras", 0) == 0
    
    def test_ledger_persistence(self):
        """Ledger persists to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and record
            ledger1 = TokenLedger(base_dir=tmpdir)
            ledger1.record_usage(
                provider="cerebras",
                model="model1",
                input_tokens=1000,
                output_tokens=500,
            )
            
            # Check file exists
            usage_file = os.path.join(tmpdir, ".codepuppy", "usage.jsonl")
            assert os.path.exists(usage_file)
            
            # Read back
            with open(usage_file, 'r') as f:
                line = f.readline()
                data = json.loads(line)
                assert data["provider"] == "cerebras"


class TestAlertLevels:
    """Test alert level detection."""
    
    def test_alert_none(self):
        """No alert under threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = TokenLedger(base_dir=tmpdir)
            # Record small usage (well under threshold)
            ledger.record_usage(
                provider="cerebras",
                model="model1",
                input_tokens=100000,  # Small fraction of 24M
                output_tokens=50000,
            )
            
            info = ledger.get_burn_rate("cerebras")
            assert info.alert_level == AlertLevel.NONE
            assert info.budget_mode == BudgetMode.NORMAL
    
    def test_alert_warning(self):
        """Warning at 70% threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = TokenLedger(base_dir=tmpdir)
            # Record 75% of daily limit
            tokens = int(CEREBRAS_DAILY_LIMIT * 0.75)
            ledger.record_usage(
                provider="cerebras",
                model="model1",
                input_tokens=tokens,
                output_tokens=0,
            )
            
            info = ledger.get_burn_rate("cerebras")
            assert info.alert_level in (AlertLevel.WARNING, AlertLevel.CRITICAL)
            assert info.budget_mode == BudgetMode.CONSERVATIVE
    
    def test_alert_critical(self):
        """Critical at 90% threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = TokenLedger(base_dir=tmpdir)
            # Record 92% of daily limit
            tokens = int(CEREBRAS_DAILY_LIMIT * 0.92)
            ledger.record_usage(
                provider="cerebras",
                model="model1",
                input_tokens=tokens,
                output_tokens=0,
            )
            
            info = ledger.get_burn_rate("cerebras")
            assert info.alert_level == AlertLevel.CRITICAL
    
    def test_alert_fallback(self):
        """Fallback at 95% threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = TokenLedger(base_dir=tmpdir)
            # Record 96% of daily limit
            tokens = int(CEREBRAS_DAILY_LIMIT * 0.96)
            ledger.record_usage(
                provider="cerebras",
                model="model1",
                input_tokens=tokens,
                output_tokens=0,
            )
            
            info = ledger.get_burn_rate("cerebras")
            assert info.alert_level == AlertLevel.FALLBACK
            assert info.budget_mode == BudgetMode.REVIEW_ONLY


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_should_fallback_to_review_only(self):
        """Test fallback mode check."""
        with patch("code_puppy.tools.token_telemetry.get_ledger") as mock_ledger:
            mock_info = BurnRateInfo(
                provider="cerebras",
                tokens_today=23000000,
                daily_limit=24000000,
                usage_percent=0.96,
                tokens_per_minute=1000,
                estimated_exhaustion_minutes=1000,
                alert_level=AlertLevel.FALLBACK,
                budget_mode=BudgetMode.REVIEW_ONLY,
                message="Fallback",
            )
            mock_ledger.return_value.get_burn_rate.return_value = mock_info
            
            assert should_fallback_to_review_only("cerebras")
    
    def test_format_burn_rate_alert(self):
        """Test alert formatting."""
        info = BurnRateInfo(
            provider="cerebras",
            tokens_today=18000000,
            daily_limit=24000000,
            usage_percent=0.75,
            tokens_per_minute=5000,
            estimated_exhaustion_minutes=1200,
            alert_level=AlertLevel.WARNING,
            budget_mode=BudgetMode.CONSERVATIVE,
            message="⚠️ 75% of daily budget used.",
        )
        
        formatted = format_burn_rate_alert(info)
        
        assert "75%" in formatted
        assert "18,000,000" in formatted
        assert "tokens/min" in formatted.lower()


class TestBudgetMode:
    """Test budget mode enum."""
    
    def test_all_modes(self):
        """All budget modes are defined."""
        assert BudgetMode.NORMAL.value == "normal"
        assert BudgetMode.CONSERVATIVE.value == "conservative"
        assert BudgetMode.REVIEW_ONLY.value == "review_only"
        assert BudgetMode.BLOCKED.value == "blocked"


class TestAlertLevel:
    """Test alert level enum."""
    
    def test_all_levels(self):
        """All alert levels are defined."""
        assert AlertLevel.NONE.value == "none"
        assert AlertLevel.INFO.value == "info"
        assert AlertLevel.WARNING.value == "warning"
        assert AlertLevel.CRITICAL.value == "critical"
        assert AlertLevel.FALLBACK.value == "fallback"
