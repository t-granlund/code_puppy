"""Rate Limit Header Parser - Proactive Rate Limiting via API Headers.

Implements GLM-Token-Saver best practices for proactive rate limiting:
- Parse x-ratelimit-* headers from API responses
- Track remaining capacity BEFORE hitting 429 errors
- Trigger fallback at configurable threshold (default: 20% remaining)
- Support for Cerebras, OpenAI, Anthropic header formats
- Logfire telemetry for rate limit events

This enables PROACTIVE rate limiting instead of REACTIVE (waiting for 429).
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple

logger = logging.getLogger(__name__)

# Import Logfire for telemetry (optional)
try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False
    logfire = None


def _emit_rate_limit_telemetry(
    event: str,
    provider: str,
    remaining_pct: Optional[float] = None,
    threshold_pct: Optional[float] = None,
    **kwargs,
) -> None:
    """Emit structured telemetry for rate limit events."""
    if LOGFIRE_AVAILABLE and logfire is not None:
        logfire.info(
            f"rate_limit.{event}",
            provider=provider,
            remaining_pct=remaining_pct,
            threshold_pct=threshold_pct,
            **kwargs,
        )
    else:
        # Fall back to standard logging
        logger.info(
            f"Rate limit {event}: provider={provider} "
            f"remaining={remaining_pct:.1%}" if remaining_pct else ""
        )


@dataclass
class RateLimitState:
    """Current rate limit state from API headers.
    
    Based on GLM-Token-Saver's CerebrasRateLimits pattern.
    """
    
    # Limits from API headers
    limit_requests_day: Optional[int] = None
    limit_requests_minute: Optional[int] = None
    limit_tokens_minute: Optional[int] = None
    limit_tokens_day: Optional[int] = None
    
    # Remaining capacity from API headers
    remaining_requests_day: Optional[int] = None
    remaining_requests_minute: Optional[int] = None
    remaining_tokens_minute: Optional[int] = None
    remaining_tokens_day: Optional[int] = None
    
    # Reset times (seconds until reset)
    reset_requests_day: Optional[int] = None
    reset_requests_minute: Optional[int] = None
    reset_tokens_minute: Optional[int] = None
    reset_tokens_day: Optional[int] = None
    
    # Tracking
    last_updated: float = field(default_factory=time.time)
    provider: str = "unknown"
    
    def update_from_headers(self, headers: Mapping[str, str]) -> bool:
        """Update rate limit info from response headers.
        
        Supports multiple header formats:
        - Cerebras: x-ratelimit-remaining-tokens-minute, x-ratelimit-limit-requests-day, etc.
        - OpenAI: x-ratelimit-remaining-tokens, x-ratelimit-limit-tokens
        - Anthropic: anthropic-ratelimit-tokens-remaining, anthropic-ratelimit-requests-remaining
        
        Returns True if any headers were parsed.
        """
        updated = False
        
        # Normalize header access (case-insensitive)
        h = {k.lower(): v for k, v in headers.items()}
        
        # === CEREBRAS FORMAT (most specific) ===
        # x-ratelimit-limit-requests-day, x-ratelimit-remaining-tokens-minute, etc.
        cerebras_mappings = [
            ('x-ratelimit-limit-requests-day', 'limit_requests_day'),
            ('x-ratelimit-limit-requests-minute', 'limit_requests_minute'),
            ('x-ratelimit-limit-tokens-minute', 'limit_tokens_minute'),
            ('x-ratelimit-limit-tokens-day', 'limit_tokens_day'),
            ('x-ratelimit-remaining-requests-day', 'remaining_requests_day'),
            ('x-ratelimit-remaining-requests-minute', 'remaining_requests_minute'),
            ('x-ratelimit-remaining-tokens-minute', 'remaining_tokens_minute'),
            ('x-ratelimit-remaining-tokens-day', 'remaining_tokens_day'),
            ('x-ratelimit-reset-requests-day', 'reset_requests_day'),
            ('x-ratelimit-reset-requests-minute', 'reset_requests_minute'),
            ('x-ratelimit-reset-tokens-minute', 'reset_tokens_minute'),
            ('x-ratelimit-reset-tokens-day', 'reset_tokens_day'),
        ]
        
        for header_key, attr_name in cerebras_mappings:
            if header_key in h:
                try:
                    setattr(self, attr_name, int(h[header_key]))
                    updated = True
                except (ValueError, TypeError):
                    pass
        
        # === OPENAI FORMAT ===
        # x-ratelimit-limit-tokens, x-ratelimit-remaining-tokens
        openai_mappings = [
            ('x-ratelimit-limit-tokens', 'limit_tokens_minute'),
            ('x-ratelimit-limit-requests', 'limit_requests_minute'),
            ('x-ratelimit-remaining-tokens', 'remaining_tokens_minute'),
            ('x-ratelimit-remaining-requests', 'remaining_requests_minute'),
            ('x-ratelimit-reset-tokens', 'reset_tokens_minute'),
            ('x-ratelimit-reset-requests', 'reset_requests_minute'),
        ]
        
        for header_key, attr_name in openai_mappings:
            if header_key in h and getattr(self, attr_name) is None:
                try:
                    value = h[header_key]
                    # OpenAI sometimes uses format like "1000ms" or "1s"
                    if value.endswith('ms'):
                        setattr(self, attr_name, int(float(value[:-2]) / 1000))
                    elif value.endswith('s'):
                        setattr(self, attr_name, int(float(value[:-1])))
                    else:
                        setattr(self, attr_name, int(value))
                    updated = True
                except (ValueError, TypeError):
                    pass
        
        # === ANTHROPIC FORMAT ===
        # anthropic-ratelimit-tokens-remaining, anthropic-ratelimit-requests-limit
        anthropic_mappings = [
            ('anthropic-ratelimit-tokens-limit', 'limit_tokens_minute'),
            ('anthropic-ratelimit-tokens-remaining', 'remaining_tokens_minute'),
            ('anthropic-ratelimit-tokens-reset', 'reset_tokens_minute'),
            ('anthropic-ratelimit-requests-limit', 'limit_requests_minute'),
            ('anthropic-ratelimit-requests-remaining', 'remaining_requests_minute'),
            ('anthropic-ratelimit-requests-reset', 'reset_requests_minute'),
        ]
        
        for header_key, attr_name in anthropic_mappings:
            if header_key in h and getattr(self, attr_name) is None:
                try:
                    setattr(self, attr_name, int(h[header_key]))
                    updated = True
                except (ValueError, TypeError):
                    pass
        
        if updated:
            self.last_updated = time.time()
            logger.debug(f"Updated rate limits from headers: {self.get_summary()}")
        
        return updated
    
    def is_near_limit(self, threshold_percent: float = 0.2) -> Tuple[bool, str]:
        """Check if we're approaching rate limits (PROACTIVE detection).
        
        GLM-Token-Saver best practice: Fallback at 20% remaining capacity,
        NOT after hitting 429 errors.
        
        Args:
            threshold_percent: Fallback when remaining drops below this
                             (0.2 = 20% remaining = 80% used)
        
        Returns:
            Tuple of (should_fallback, reason_string)
        """
        # Check tokens per minute (most critical for streaming)
        if (self.remaining_tokens_minute is not None and 
            self.limit_tokens_minute is not None and
            self.limit_tokens_minute > 0):
            remaining_pct = self.remaining_tokens_minute / self.limit_tokens_minute
            if remaining_pct <= threshold_percent:
                reason = (
                    f"⚠️ Token limit approaching: "
                    f"{self.remaining_tokens_minute:,}/{self.limit_tokens_minute:,} tokens/minute "
                    f"({remaining_pct*100:.1f}% remaining, threshold: {threshold_percent*100:.0f}%)"
                )
                # Emit telemetry for proactive rate limit warning
                _emit_rate_limit_telemetry(
                    "approaching_limit",
                    self.provider,
                    remaining_pct=remaining_pct,
                    threshold_pct=threshold_percent,
                    limit_type="tokens_minute",
                    remaining=self.remaining_tokens_minute,
                    limit=self.limit_tokens_minute,
                )
                return True, reason
        
        # Check requests per minute
        if (self.remaining_requests_minute is not None and
            self.limit_requests_minute is not None and
            self.limit_requests_minute > 0):
            remaining_pct = self.remaining_requests_minute / self.limit_requests_minute
            if remaining_pct <= threshold_percent:
                reason = (
                    f"⚠️ Request limit approaching: "
                    f"{self.remaining_requests_minute:,}/{self.limit_requests_minute:,} requests/minute "
                    f"({remaining_pct*100:.1f}% remaining)"
                )
                _emit_rate_limit_telemetry(
                    "approaching_limit",
                    self.provider,
                    remaining_pct=remaining_pct,
                    threshold_pct=threshold_percent,
                    limit_type="requests_minute",
                    remaining=self.remaining_requests_minute,
                    limit=self.limit_requests_minute,
                )
                return True, reason
        
        # Check daily limits (less critical but important)
        if (self.remaining_requests_day is not None and 
            self.limit_requests_day is not None and
            self.limit_requests_day > 0):
            remaining_pct = self.remaining_requests_day / self.limit_requests_day
            if remaining_pct <= threshold_percent:
                reason = (
                    f"⚠️ Daily request limit approaching: "
                    f"{self.remaining_requests_day:,}/{self.limit_requests_day:,} requests/day "
                    f"({remaining_pct*100:.1f}% remaining)"
                )
                _emit_rate_limit_telemetry(
                    "approaching_limit",
                    self.provider,
                    remaining_pct=remaining_pct,
                    threshold_pct=threshold_percent,
                    limit_type="requests_day",
                    remaining=self.remaining_requests_day,
                    limit=self.limit_requests_day,
                )
                return True, reason
        
        if (self.remaining_tokens_day is not None and
            self.limit_tokens_day is not None and
            self.limit_tokens_day > 0):
            remaining_pct = self.remaining_tokens_day / self.limit_tokens_day
            if remaining_pct <= threshold_percent:
                reason = (
                    f"⚠️ Daily token limit approaching: "
                    f"{self.remaining_tokens_day:,}/{self.limit_tokens_day:,} tokens/day "
                    f"({remaining_pct*100:.1f}% remaining)"
                )
                _emit_rate_limit_telemetry(
                    "approaching_limit",
                    self.provider,
                    remaining_pct=remaining_pct,
                    threshold_pct=threshold_percent,
                    limit_type="tokens_day",
                    remaining=self.remaining_tokens_day,
                    limit=self.limit_tokens_day,
                )
                return True, reason
        
        return False, "Rate limits are healthy ✅"
    
    def get_time_until_reset_minutes(self) -> Optional[int]:
        """Get seconds until minute token limit resets."""
        if self.reset_tokens_minute is not None:
            return max(0, self.reset_tokens_minute)
        return None
    
    def get_time_until_reset_day(self) -> Optional[int]:
        """Get seconds until daily limit resets."""
        if self.reset_requests_day is not None:
            return max(0, self.reset_requests_day)
        return None
    
    def is_stale(self, max_age_seconds: float = 120) -> bool:
        """Check if rate limit info is stale (old data may be inaccurate)."""
        return (time.time() - self.last_updated) > max_age_seconds
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of current rate limit status."""
        return {
            "provider": self.provider,
            "tokens_minute": {
                "remaining": self.remaining_tokens_minute,
                "limit": self.limit_tokens_minute,
                "reset_seconds": self.reset_tokens_minute,
            },
            "requests_minute": {
                "remaining": self.remaining_requests_minute,
                "limit": self.limit_requests_minute,
                "reset_seconds": self.reset_requests_minute,
            },
            "requests_day": {
                "remaining": self.remaining_requests_day,
                "limit": self.limit_requests_day,
                "reset_seconds": self.reset_requests_day,
            },
            "last_updated": self.last_updated,
            "is_stale": self.is_stale(),
        }
    
    def __str__(self) -> str:
        """Human-readable status string."""
        parts = [f"RateLimitState({self.provider})"]
        
        if self.remaining_tokens_minute is not None:
            parts.append(f"tokens/min: {self.remaining_tokens_minute:,}/{self.limit_tokens_minute or '?':,}")
        if self.remaining_requests_minute is not None:
            parts.append(f"reqs/min: {self.remaining_requests_minute:,}/{self.limit_requests_minute or '?':,}")
        if self.remaining_requests_day is not None:
            parts.append(f"reqs/day: {self.remaining_requests_day:,}/{self.limit_requests_day or '?':,}")
        
        return " | ".join(parts)


class RateLimitTracker:
    """Global tracker for rate limit states across providers.
    
    Singleton that maintains rate limit state for each provider,
    enabling proactive fallback decisions before hitting 429s.
    """
    
    _instance: Optional["RateLimitTracker"] = None
    
    def __new__(cls) -> "RateLimitTracker":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._states: Dict[str, RateLimitState] = {}
            cls._instance._fallback_threshold = 0.2  # 20% remaining = time to fallback
            cls._instance._cooldown_seconds = 60.0
            cls._instance._last_fallback_time: Dict[str, float] = {}
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> "RateLimitTracker":
        """Get the singleton instance."""
        return cls()
    
    def get_state(self, provider: str) -> RateLimitState:
        """Get rate limit state for a provider (creates if not exists)."""
        provider_key = self._normalize_provider(provider)
        if provider_key not in self._states:
            self._states[provider_key] = RateLimitState(provider=provider_key)
        return self._states[provider_key]
    
    def update_from_response(
        self, 
        provider: str, 
        headers: Mapping[str, str]
    ) -> bool:
        """Update rate limit state from response headers.
        
        Call this after every API response to track capacity.
        
        Returns True if headers contained rate limit info.
        """
        state = self.get_state(provider)
        return state.update_from_headers(headers)
    
    def should_fallback(self, provider: str) -> Tuple[bool, str]:
        """Check if we should proactively fallback from this provider.
        
        Returns (should_fallback, reason) tuple.
        """
        state = self.get_state(provider)
        
        # If state is stale, we can't make a proactive decision
        if state.is_stale():
            return False, "Rate limit info is stale, proceeding with request"
        
        # Check if in cooldown period
        provider_key = self._normalize_provider(provider)
        if provider_key in self._last_fallback_time:
            elapsed = time.time() - self._last_fallback_time[provider_key]
            if elapsed < self._cooldown_seconds:
                remaining = self._cooldown_seconds - elapsed
                return True, f"In cooldown period ({remaining:.0f}s remaining)"
        
        return state.is_near_limit(self._fallback_threshold)
    
    def record_fallback(self, provider: str) -> None:
        """Record that we triggered a fallback for this provider."""
        provider_key = self._normalize_provider(provider)
        self._last_fallback_time[provider_key] = time.time()
        logger.info(f"🔄 Recorded proactive fallback from {provider_key}")
        
        # Emit telemetry for fallback event
        state = self._states.get(provider_key)
        if state and logfire:
            logfire.info(
                "rate_limit_fallback_triggered",
                provider=provider_key,
                cooldown_seconds=self._cooldown_seconds,
                tokens_minute_remaining=state.tokens_remaining_minute,
                requests_minute_remaining=state.requests_remaining_minute,
            )
    
    def set_threshold(self, threshold: float) -> None:
        """Set the fallback threshold (0.0 to 1.0).
        
        Lower = more aggressive fallback (0.2 = fallback at 20% remaining).
        """
        self._fallback_threshold = max(0.0, min(1.0, threshold))
    
    def set_cooldown(self, seconds: float) -> None:
        """Set cooldown period after fallback."""
        self._cooldown_seconds = max(0.0, seconds)
    
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all tracked providers."""
        return {
            provider: state.get_summary()
            for provider, state in self._states.items()
        }
    
    def _normalize_provider(self, provider: str) -> str:
        """Normalize provider name for consistent tracking."""
        provider_lower = provider.lower()
        
        # Map to canonical names
        if "cerebras" in provider_lower or "glm" in provider_lower:
            return "cerebras"
        elif "opus" in provider_lower:
            return "anthropic-opus"
        elif "sonnet" in provider_lower:
            return "anthropic-sonnet"
        elif "haiku" in provider_lower:
            return "anthropic-haiku"
        elif "claude" in provider_lower:
            return "anthropic"
        elif "gemini" in provider_lower:
            return "gemini"
        elif "gpt" in provider_lower or "openai" in provider_lower:
            return "openai"
        elif "antigravity" in provider_lower:
            # Extract the underlying model
            if "opus" in provider_lower:
                return "antigravity-opus"
            elif "sonnet" in provider_lower:
                return "antigravity-sonnet"
            return "antigravity"
        elif "chatgpt" in provider_lower:
            return "chatgpt"
        
        return provider_lower


# Convenience function for quick access
def get_rate_limit_tracker() -> RateLimitTracker:
    """Get the global rate limit tracker singleton."""
    return RateLimitTracker.get_instance()


def parse_rate_limit_headers(headers: Mapping[str, str]) -> Dict[str, Any]:
    """Quick utility to parse rate limit headers without tracking.
    
    Returns dict with parsed values (useful for logging/telemetry).
    """
    state = RateLimitState()
    state.update_from_headers(headers)
    return state.get_summary()
