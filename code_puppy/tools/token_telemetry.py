"""Token Accounting and Session Telemetry for Code Puppy.

AUDIT-1.1 Part G compliance:
- Usage ledger at .codepuppy/usage.jsonl
- Burn rate alerts when approaching limits
- Daily budget mode with automatic fallback
- Per-provider tracking

This module provides comprehensive token usage tracking, enabling:
1. Session-level token accounting
2. Daily budget enforcement
3. Burn rate monitoring and alerts
4. Historical usage analysis
"""

import json
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import fcntl

from code_puppy.config import get_value


# ============================================================================
# Configuration Constants
# ============================================================================

# Cerebras Code Pro limits (free tier)
CEREBRAS_DAILY_LIMIT = 24_000_000  # 24M tokens/day
CEREBRAS_TPM_LIMIT = 1_000_000     # 1M tokens/minute
CEREBRAS_RPM_LIMIT = 50            # 50 requests/minute

# Default thresholds for alerts
DEFAULT_BURN_RATE_WARN = 0.70      # Warn at 70% of daily budget
DEFAULT_BURN_RATE_CRITICAL = 0.90  # Critical at 90% of daily budget
DEFAULT_FALLBACK_AT = 0.95         # Fallback to review-only at 95%

# Telemetry file location
DEFAULT_USAGE_DIR = ".codepuppy"
USAGE_FILE = "usage.jsonl"
DAILY_SUMMARY_FILE = "daily_usage.json"


class AlertLevel(Enum):
    """Alert severity levels."""
    NONE = "none"
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    FALLBACK = "fallback"


class BudgetMode(Enum):
    """Budget enforcement modes."""
    NORMAL = "normal"           # Full capabilities
    CONSERVATIVE = "conservative"  # Reduced output, more compaction
    REVIEW_ONLY = "review_only"   # No code generation, only review
    BLOCKED = "blocked"           # Quota exhausted


@dataclass
class UsageEntry:
    """A single token usage entry."""
    timestamp: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    request_type: str = "chat"  # chat, completion, embedding
    session_id: str = ""
    latency_ms: int = 0
    was_cached: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ts": self.timestamp,
            "provider": self.provider,
            "model": self.model,
            "in": self.input_tokens,
            "out": self.output_tokens,
            "total": self.total_tokens,
            "type": self.request_type,
            "session": self.session_id,
            "latency": self.latency_ms,
            "cached": self.was_cached,
            "error": self.error,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UsageEntry":
        """Create from dictionary."""
        return cls(
            timestamp=data.get("ts", ""),
            provider=data.get("provider", ""),
            model=data.get("model", ""),
            input_tokens=data.get("in", 0),
            output_tokens=data.get("out", 0),
            total_tokens=data.get("total", 0),
            request_type=data.get("type", "chat"),
            session_id=data.get("session", ""),
            latency_ms=data.get("latency", 0),
            was_cached=data.get("cached", False),
            error=data.get("error"),
        )


@dataclass
class DailySummary:
    """Daily usage summary."""
    date: str
    provider: str
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    request_count: int = 0
    error_count: int = 0
    cached_count: int = 0
    avg_latency_ms: int = 0
    peak_tokens_per_minute: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "provider": self.provider,
            "total": self.total_tokens,
            "in": self.input_tokens,
            "out": self.output_tokens,
            "requests": self.request_count,
            "errors": self.error_count,
            "cached": self.cached_count,
            "avg_latency": self.avg_latency_ms,
            "peak_tpm": self.peak_tokens_per_minute,
        }


@dataclass
class BurnRateInfo:
    """Current burn rate information."""
    provider: str
    tokens_today: int
    daily_limit: int
    usage_percent: float
    tokens_per_minute: float
    estimated_exhaustion_minutes: float
    alert_level: AlertLevel
    budget_mode: BudgetMode
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "tokens_today": self.tokens_today,
            "daily_limit": self.daily_limit,
            "usage_percent": self.usage_percent,
            "tpm": self.tokens_per_minute,
            "minutes_remaining": self.estimated_exhaustion_minutes,
            "alert": self.alert_level.value,
            "mode": self.budget_mode.value,
            "message": self.message,
        }


# ============================================================================
# Token Ledger
# ============================================================================

class TokenLedger:
    """Persistent token usage ledger.
    
    Writes usage entries to .codepuppy/usage.jsonl for durability.
    Maintains in-memory aggregates for fast access.
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize the ledger.
        
        Args:
            base_dir: Base directory for telemetry files.
                      Defaults to current directory.
        """
        self._base_dir = base_dir or os.getcwd()
        self._usage_dir = os.path.join(self._base_dir, DEFAULT_USAGE_DIR)
        self._usage_file = os.path.join(self._usage_dir, USAGE_FILE)
        self._daily_file = os.path.join(self._usage_dir, DAILY_SUMMARY_FILE)
        
        # In-memory state
        self._lock = threading.Lock()
        self._session_tokens: Dict[str, int] = {}  # provider -> tokens
        self._session_start = datetime.now()
        self._minute_buckets: Dict[str, List[Tuple[float, int]]] = {}  # provider -> [(timestamp, tokens)]
        
        # Ensure directory exists
        self._ensure_dir()
        
        # Load today's summary
        self._daily_summaries: Dict[str, DailySummary] = {}
        self._load_daily_summary()
    
    def _ensure_dir(self):
        """Ensure the usage directory exists."""
        os.makedirs(self._usage_dir, exist_ok=True)
    
    def _load_daily_summary(self):
        """Load today's summary from disk."""
        today = date.today().isoformat()
        try:
            if os.path.exists(self._daily_file):
                with open(self._daily_file, 'r') as f:
                    data = json.load(f)
                for provider, summary_data in data.items():
                    if summary_data.get("date") == today:
                        self._daily_summaries[provider] = DailySummary(
                            date=summary_data.get("date", today),
                            provider=provider,
                            total_tokens=summary_data.get("total", 0),
                            input_tokens=summary_data.get("in", 0),
                            output_tokens=summary_data.get("out", 0),
                            request_count=summary_data.get("requests", 0),
                            error_count=summary_data.get("errors", 0),
                            cached_count=summary_data.get("cached", 0),
                            avg_latency_ms=summary_data.get("avg_latency", 0),
                            peak_tokens_per_minute=summary_data.get("peak_tpm", 0),
                        )
        except (json.JSONDecodeError, IOError):
            pass
    
    def _save_daily_summary(self):
        """Save daily summary to disk."""
        try:
            data = {p: s.to_dict() for p, s in self._daily_summaries.items()}
            with open(self._daily_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError:
            pass
    
    def record_usage(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int = 0,
        request_type: str = "chat",
        session_id: str = "",
        was_cached: bool = False,
        error: Optional[str] = None,
    ) -> UsageEntry:
        """Record a usage entry.
        
        Args:
            provider: Provider name (e.g., "cerebras").
            model: Model name.
            input_tokens: Input token count.
            output_tokens: Output token count.
            latency_ms: Request latency in milliseconds.
            request_type: Type of request.
            session_id: Optional session identifier.
            was_cached: Whether response was cached.
            error: Error message if request failed.
            
        Returns:
            The recorded UsageEntry.
        """
        now = datetime.now()
        total = input_tokens + output_tokens
        
        entry = UsageEntry(
            timestamp=now.isoformat(),
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total,
            request_type=request_type,
            session_id=session_id,
            latency_ms=latency_ms,
            was_cached=was_cached,
            error=error,
        )
        
        with self._lock:
            # Update session totals
            self._session_tokens[provider] = self._session_tokens.get(provider, 0) + total
            
            # Update minute buckets (for TPM calculation)
            bucket_key = provider
            if bucket_key not in self._minute_buckets:
                self._minute_buckets[bucket_key] = []
            self._minute_buckets[bucket_key].append((now.timestamp(), total))
            
            # Clean old buckets (keep last 5 minutes)
            cutoff = now.timestamp() - 300
            self._minute_buckets[bucket_key] = [
                (ts, t) for ts, t in self._minute_buckets[bucket_key]
                if ts > cutoff
            ]
            
            # Update daily summary
            today = date.today().isoformat()
            if provider not in self._daily_summaries or self._daily_summaries[provider].date != today:
                self._daily_summaries[provider] = DailySummary(date=today, provider=provider)
            
            summary = self._daily_summaries[provider]
            summary.total_tokens += total
            summary.input_tokens += input_tokens
            summary.output_tokens += output_tokens
            summary.request_count += 1
            if error:
                summary.error_count += 1
            if was_cached:
                summary.cached_count += 1
            
            # Update peak TPM
            current_tpm = self._calculate_tpm(provider)
            if current_tpm > summary.peak_tokens_per_minute:
                summary.peak_tokens_per_minute = int(current_tpm)
            
            # Persist entry to ledger
            self._append_to_ledger(entry)
            
            # Save daily summary periodically (every 10 requests)
            if summary.request_count % 10 == 0:
                self._save_daily_summary()
        
        return entry
    
    def _append_to_ledger(self, entry: UsageEntry):
        """Append entry to JSONL ledger file with file locking."""
        try:
            with open(self._usage_file, 'a') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    f.write(json.dumps(entry.to_dict()) + "\n")
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except IOError:
            pass  # Best effort
    
    def _calculate_tpm(self, provider: str) -> float:
        """Calculate tokens per minute for a provider."""
        now = time.time()
        cutoff = now - 60  # Last minute
        
        buckets = self._minute_buckets.get(provider, [])
        recent = [t for ts, t in buckets if ts > cutoff]
        return sum(recent)
    
    def get_burn_rate(self, provider: str = "cerebras") -> BurnRateInfo:
        """Get current burn rate information for a provider.
        
        Args:
            provider: Provider to check.
            
        Returns:
            BurnRateInfo with current status.
        """
        provider_lower = provider.lower()
        
        # Get limits for provider
        if provider_lower == "cerebras":
            daily_limit = CEREBRAS_DAILY_LIMIT
        else:
            daily_limit = int(get_value(f"{provider_lower}_daily_limit") or 100_000_000)
        
        # Get thresholds
        warn_threshold = float(get_value("burn_rate_warn") or DEFAULT_BURN_RATE_WARN)
        critical_threshold = float(get_value("burn_rate_critical") or DEFAULT_BURN_RATE_CRITICAL)
        fallback_threshold = float(get_value("burn_rate_fallback") or DEFAULT_FALLBACK_AT)
        
        with self._lock:
            summary = self._daily_summaries.get(provider_lower)
            tokens_today = summary.total_tokens if summary else 0
            tpm = self._calculate_tpm(provider_lower)
        
        usage_percent = tokens_today / daily_limit if daily_limit > 0 else 1.0
        
        # Calculate estimated exhaustion
        if tpm > 0:
            remaining = daily_limit - tokens_today
            minutes_remaining = remaining / tpm
        else:
            minutes_remaining = float('inf')
        
        # Determine alert level and mode
        if usage_percent >= fallback_threshold:
            alert_level = AlertLevel.FALLBACK
            budget_mode = BudgetMode.REVIEW_ONLY
            message = f"🚫 Daily budget {usage_percent:.0%} exhausted. Review-only mode active."
        elif usage_percent >= critical_threshold:
            alert_level = AlertLevel.CRITICAL
            budget_mode = BudgetMode.CONSERVATIVE
            message = f"🔴 CRITICAL: {usage_percent:.0%} of daily budget used. Reduce usage immediately."
        elif usage_percent >= warn_threshold:
            alert_level = AlertLevel.WARNING
            budget_mode = BudgetMode.CONSERVATIVE
            message = f"⚠️ {usage_percent:.0%} of daily budget used. Consider compacting."
        else:
            alert_level = AlertLevel.NONE
            budget_mode = BudgetMode.NORMAL
            message = f"✓ {usage_percent:.0%} of daily budget used."
        
        return BurnRateInfo(
            provider=provider_lower,
            tokens_today=tokens_today,
            daily_limit=daily_limit,
            usage_percent=usage_percent,
            tokens_per_minute=tpm,
            estimated_exhaustion_minutes=minutes_remaining,
            alert_level=alert_level,
            budget_mode=budget_mode,
            message=message,
        )
    
    def get_session_usage(self) -> Dict[str, int]:
        """Get token usage for current session by provider."""
        with self._lock:
            return dict(self._session_tokens)
    
    def get_daily_summary(self, provider: str) -> Optional[DailySummary]:
        """Get daily summary for a provider."""
        with self._lock:
            return self._daily_summaries.get(provider.lower())
    
    def reset_session(self):
        """Reset session-level tracking."""
        with self._lock:
            self._session_tokens = {}
            self._session_start = datetime.now()
            self._minute_buckets = {}
    
    def read_history(
        self,
        provider: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[UsageEntry]:
        """Read historical usage entries from ledger.
        
        Args:
            provider: Filter by provider.
            since: Only entries after this time.
            limit: Maximum entries to return.
            
        Returns:
            List of UsageEntry objects.
        """
        entries = []
        try:
            with open(self._usage_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        entry = UsageEntry.from_dict(data)
                        
                        # Apply filters
                        if provider and entry.provider.lower() != provider.lower():
                            continue
                        if since:
                            entry_time = datetime.fromisoformat(entry.timestamp)
                            if entry_time < since:
                                continue
                        
                        entries.append(entry)
                        
                        if len(entries) >= limit:
                            break
                    except (json.JSONDecodeError, KeyError):
                        continue
        except IOError:
            pass
        
        return entries


# ============================================================================
# Global Ledger Instance
# ============================================================================

_global_ledger: Optional[TokenLedger] = None
_ledger_lock = threading.Lock()


def get_ledger(base_dir: Optional[str] = None) -> TokenLedger:
    """Get or create the global token ledger.
    
    Args:
        base_dir: Base directory for ledger files.
        
    Returns:
        TokenLedger instance.
    """
    global _global_ledger
    with _ledger_lock:
        if _global_ledger is None:
            _global_ledger = TokenLedger(base_dir)
        return _global_ledger


def record_usage(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    **kwargs,
) -> UsageEntry:
    """Convenience function to record usage to global ledger.
    
    Args:
        provider: Provider name.
        model: Model name.
        input_tokens: Input token count.
        output_tokens: Output token count.
        **kwargs: Additional arguments for UsageEntry.
        
    Returns:
        The recorded UsageEntry.
    """
    return get_ledger().record_usage(
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        **kwargs,
    )


def check_burn_rate(provider: str = "cerebras") -> BurnRateInfo:
    """Convenience function to check burn rate.
    
    Args:
        provider: Provider to check.
        
    Returns:
        BurnRateInfo with current status.
    """
    return get_ledger().get_burn_rate(provider)


def should_fallback_to_review_only(provider: str = "cerebras") -> bool:
    """Check if we should enter review-only mode.
    
    Args:
        provider: Provider to check.
        
    Returns:
        True if review-only mode should be active.
    """
    info = check_burn_rate(provider)
    return info.budget_mode == BudgetMode.REVIEW_ONLY


def format_burn_rate_alert(info: BurnRateInfo) -> str:
    """Format burn rate info as an alert message.
    
    Args:
        info: BurnRateInfo to format.
        
    Returns:
        Formatted alert string.
    """
    lines = [info.message]
    
    if info.alert_level != AlertLevel.NONE:
        lines.append(f"  Today: {info.tokens_today:,} / {info.daily_limit:,} tokens")
        lines.append(f"  Rate: {info.tokens_per_minute:,.0f} tokens/min")
        
        if info.estimated_exhaustion_minutes < float('inf'):
            if info.estimated_exhaustion_minutes < 60:
                lines.append(f"  ⏰ Quota exhausts in ~{info.estimated_exhaustion_minutes:.0f} minutes")
            else:
                hours = info.estimated_exhaustion_minutes / 60
                lines.append(f"  ⏰ Quota exhausts in ~{hours:.1f} hours")
    
    return "\n".join(lines)
