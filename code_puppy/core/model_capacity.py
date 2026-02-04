"""Model Capacity and Rate Budget Management.

Intelligent model routing that ensures work NEVER stops due to rate limits:
- Tracks per-model capacity (context windows, rate limits, usage budgets)
- Proactively switches models BEFORE hitting limits
- Learns from Logfire telemetry to optimize routing
- Round-robins across models based on available capacity

Key Design Principles:
1. Each model has its own limits (tokens/min, requests/min, tokens/day, etc.)
2. Switch at 80% capacity (20% remaining) to avoid disruption
3. Prefer same-tier fallbacks to maintain quality
4. Track reset windows to know when capacity refreshes
5. Emit telemetry for self-learning optimization
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# Import Logfire for telemetry (optional)
try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False
    logfire = None


class CapacityStatus(IntEnum):
    """Current capacity status for a model."""
    AVAILABLE = 1      # Plenty of capacity, prefer this model
    APPROACHING = 2    # 50-80% capacity used, can still use but consider alternatives  
    LOW = 3            # 80-95% capacity, should switch soon
    EXHAUSTED = 4      # 95%+ or hit 429, must switch
    COOLDOWN = 5       # In cooldown after rate limit, wait for reset


@dataclass
class ModelLimits:
    """Static limits for a model (from config/docs).
    
    All values are optional - models may not report all limits.
    """
    # Context and output limits
    context_window: int = 128_000          # Max input tokens
    max_output: int = 8_000                # Max output tokens
    optimal_prompt_size: int = 50_000      # Recommended prompt size for best perf
    
    # Rate limits per minute
    tokens_per_minute: int = 100_000       # TPM limit
    requests_per_minute: int = 50          # RPM limit
    
    # Rate limits per day
    tokens_per_day: int = 2_000_000        # Daily token limit  
    requests_per_day: int = 10_000         # Daily request limit
    
    # Rolling window limits (e.g., Synthetic.new's 5-hour window)
    rolling_window_hours: Optional[int] = None
    tokens_per_window: Optional[int] = None
    requests_per_window: Optional[int] = None
    
    # Reset timing
    minute_reset_seconds: int = 60         # When minute limits reset
    day_reset_seconds: int = 86_400        # When daily limits reset
    
    # Provider info
    provider: str = "unknown"
    tier: int = 3                          # 1=Architect, 2=BuilderHigh, 3=BuilderMid, 4=Librarian, 5=Sprinter
    plan: str = "free"                     # free, pro, teams, max, etc.
    cost_per_month: float = 0.0


@dataclass
class ModelUsage:
    """Real-time usage tracking for a model.
    
    Updated from API response headers and local counting.
    """
    # Current usage (minute window)
    tokens_used_minute: int = 0
    requests_used_minute: int = 0
    minute_window_start: float = field(default_factory=time.time)
    
    # Current usage (day window)
    tokens_used_day: int = 0
    requests_used_day: int = 0
    day_window_start: float = field(default_factory=lambda: time.time() - (time.time() % 86400))
    
    # Rolling window usage (for providers like Synthetic.new)
    tokens_used_window: int = 0
    requests_used_window: int = 0
    window_start: float = field(default_factory=time.time)
    
    # API-reported remaining (from headers)
    remaining_tokens_minute: Optional[int] = None
    remaining_requests_minute: Optional[int] = None
    remaining_tokens_day: Optional[int] = None
    remaining_requests_day: Optional[int] = None
    
    # Cooldown tracking
    last_429_time: Optional[float] = None
    cooldown_until: Optional[float] = None
    consecutive_429s: int = 0
    
    # Last update
    last_updated: float = field(default_factory=time.time)
    
    def reset_minute_window(self) -> None:
        """Reset minute counters when window expires."""
        self.tokens_used_minute = 0
        self.requests_used_minute = 0
        self.minute_window_start = time.time()
    
    def reset_day_window(self) -> None:
        """Reset daily counters when window expires."""
        self.tokens_used_day = 0
        self.requests_used_day = 0
        self.day_window_start = time.time()
    
    def reset_rolling_window(self) -> None:
        """Reset rolling window counters (e.g., Synthetic.new's 5-hour window)."""
        self.tokens_used_window = 0
        self.requests_used_window = 0
        self.window_start = time.time()
    
    def record_request(
        self, 
        input_tokens: int, 
        output_tokens: int,
        rolling_window_hours: Optional[int] = None
    ) -> None:
        """Record a completed request's token usage.
        
        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
            rolling_window_hours: Rolling window size in hours (e.g., 5 for Synthetic.new)
        """
        total_tokens = input_tokens + output_tokens
        
        # Check if windows need reset
        now = time.time()
        if now - self.minute_window_start >= 60:
            self.reset_minute_window()
        if now - self.day_window_start >= 86_400:
            self.reset_day_window()
        
        # Rolling window reset (e.g., Synthetic.new uses 5-hour windows)
        if rolling_window_hours is not None:
            window_seconds = rolling_window_hours * 3600
            if now - self.window_start >= window_seconds:
                self.reset_rolling_window()
        
        # Update counters
        self.tokens_used_minute += total_tokens
        self.requests_used_minute += 1
        self.tokens_used_day += total_tokens
        self.requests_used_day += 1
        self.tokens_used_window += total_tokens
        self.requests_used_window += 1
        self.last_updated = now
    
    def record_rate_limit(self, cooldown_seconds: float = 60.0) -> None:
        """Record that we hit a 429 error."""
        now = time.time()
        self.last_429_time = now
        self.consecutive_429s += 1
        
        # Exponential backoff: 60s, 120s, 240s, max 600s
        backoff = min(cooldown_seconds * (2 ** (self.consecutive_429s - 1)), 600)
        self.cooldown_until = now + backoff
        
        logger.warning(
            f"Rate limit hit - cooldown for {backoff:.0f}s "
            f"(consecutive 429s: {self.consecutive_429s})"
        )
    
    def clear_cooldown(self) -> None:
        """Clear cooldown after successful request."""
        if self.consecutive_429s > 0:
            self.consecutive_429s = 0
            self.cooldown_until = None
            logger.info("Rate limit cooldown cleared after successful request")
    
    def is_in_cooldown(self) -> bool:
        """Check if model is in cooldown period."""
        if self.cooldown_until is None:
            return False
        return time.time() < self.cooldown_until
    
    def seconds_until_cooldown_end(self) -> float:
        """Get seconds remaining in cooldown."""
        if self.cooldown_until is None:
            return 0.0
        return max(0.0, self.cooldown_until - time.time())


@dataclass
class ModelCapacity:
    """Complete capacity state for a model.
    
    Combines static limits with real-time usage to determine availability.
    """
    model_name: str
    limits: ModelLimits
    usage: ModelUsage = field(default_factory=ModelUsage)
    workloads: List[str] = field(default_factory=list)  # ["coding", "reasoning", etc.]
    enabled: bool = True
    
    # Thresholds for capacity decisions
    warning_threshold: float = 0.5     # 50% used = APPROACHING
    switch_threshold: float = 0.8      # 80% used = LOW, should switch
    exhausted_threshold: float = 0.95  # 95% used = EXHAUSTED
    
    def get_status(self) -> CapacityStatus:
        """Determine current capacity status.
        
        Checks all limit types and returns the worst status.
        """
        if not self.enabled:
            return CapacityStatus.EXHAUSTED
        
        if self.usage.is_in_cooldown():
            return CapacityStatus.COOLDOWN
        
        # Calculate usage percentages for all limit types
        usage_pcts = []
        
        # Minute limits (most critical for real-time operations)
        if self.limits.tokens_per_minute > 0:
            if self.usage.remaining_tokens_minute is not None:
                # Use API-reported remaining (more accurate)
                remaining_pct = self.usage.remaining_tokens_minute / self.limits.tokens_per_minute
                usage_pcts.append(1 - remaining_pct)
            else:
                # Use local tracking
                usage_pcts.append(self.usage.tokens_used_minute / self.limits.tokens_per_minute)
        
        if self.limits.requests_per_minute > 0:
            if self.usage.remaining_requests_minute is not None:
                remaining_pct = self.usage.remaining_requests_minute / self.limits.requests_per_minute
                usage_pcts.append(1 - remaining_pct)
            else:
                usage_pcts.append(self.usage.requests_used_minute / self.limits.requests_per_minute)
        
        # Daily limits
        if self.limits.tokens_per_day > 0:
            if self.usage.remaining_tokens_day is not None:
                remaining_pct = self.usage.remaining_tokens_day / self.limits.tokens_per_day
                usage_pcts.append(1 - remaining_pct)
            else:
                usage_pcts.append(self.usage.tokens_used_day / self.limits.tokens_per_day)
        
        if self.limits.requests_per_day > 0:
            if self.usage.remaining_requests_day is not None:
                remaining_pct = self.usage.remaining_requests_day / self.limits.requests_per_day
                usage_pcts.append(1 - remaining_pct)
            else:
                usage_pcts.append(self.usage.requests_used_day / self.limits.requests_per_day)
        
        # Rolling window limits (e.g., Synthetic.new's 5-hour window)
        if self.limits.tokens_per_window and self.limits.tokens_per_window > 0:
            usage_pcts.append(self.usage.tokens_used_window / self.limits.tokens_per_window)
        
        if self.limits.requests_per_window and self.limits.requests_per_window > 0:
            usage_pcts.append(self.usage.requests_used_window / self.limits.requests_per_window)
        
        # Get highest usage percentage
        if not usage_pcts:
            return CapacityStatus.AVAILABLE
        
        max_usage = max(usage_pcts)
        
        if max_usage >= self.exhausted_threshold:
            return CapacityStatus.EXHAUSTED
        elif max_usage >= self.switch_threshold:
            return CapacityStatus.LOW
        elif max_usage >= self.warning_threshold:
            return CapacityStatus.APPROACHING
        else:
            return CapacityStatus.AVAILABLE
    
    def get_available_tokens(self) -> int:
        """Get estimated available tokens before hitting limits."""
        available = []
        
        # Minute limit
        if self.limits.tokens_per_minute > 0:
            if self.usage.remaining_tokens_minute is not None:
                available.append(self.usage.remaining_tokens_minute)
            else:
                available.append(self.limits.tokens_per_minute - self.usage.tokens_used_minute)
        
        # Daily limit
        if self.limits.tokens_per_day > 0:
            if self.usage.remaining_tokens_day is not None:
                available.append(self.usage.remaining_tokens_day)
            else:
                available.append(self.limits.tokens_per_day - self.usage.tokens_used_day)
        
        if available:
            return max(0, min(available))
        return self.limits.context_window  # If no limits tracked, use context window
    
    def can_handle_prompt(self, estimated_tokens: int) -> bool:
        """Check if model can handle a prompt of given size."""
        # Check context window
        if estimated_tokens > self.limits.context_window:
            return False
        
        # Check rate limits
        available = self.get_available_tokens()
        return estimated_tokens <= available
    
    def seconds_until_capacity_refresh(self) -> float:
        """Get seconds until some capacity refreshes."""
        now = time.time()
        
        # Check minute window
        minute_refresh = 60 - (now - self.usage.minute_window_start)
        if minute_refresh > 0:
            return minute_refresh
        
        return 0.0
    
    def update_from_headers(self, headers: Mapping[str, str]) -> bool:
        """Update usage from API response headers."""
        updated = False
        h = {k.lower(): v for k, v in headers.items()}
        
        # Parse standard rate limit headers
        header_mappings = [
            ('x-ratelimit-remaining-tokens', 'remaining_tokens_minute'),
            ('x-ratelimit-remaining-requests', 'remaining_requests_minute'),
            ('x-ratelimit-remaining-tokens-minute', 'remaining_tokens_minute'),
            ('x-ratelimit-remaining-requests-minute', 'remaining_requests_minute'),
            ('x-ratelimit-remaining-tokens-day', 'remaining_tokens_day'),
            ('x-ratelimit-remaining-requests-day', 'remaining_requests_day'),
            ('anthropic-ratelimit-tokens-remaining', 'remaining_tokens_minute'),
            ('anthropic-ratelimit-requests-remaining', 'remaining_requests_minute'),
        ]
        
        for header_key, attr_name in header_mappings:
            if header_key in h:
                try:
                    value = h[header_key]
                    # Handle time formats like "1000ms" or "1s"
                    if isinstance(value, str):
                        if value.endswith('ms'):
                            value = int(float(value[:-2]) / 1000)
                        elif value.endswith('s'):
                            value = int(float(value[:-1]))
                        else:
                            value = int(value)
                    setattr(self.usage, attr_name, value)
                    updated = True
                except (ValueError, TypeError):
                    pass
        
        if updated:
            self.usage.last_updated = time.time()
            self.usage.clear_cooldown()  # Successful response = clear cooldown
        
        return updated
    
    def to_telemetry(self) -> Dict[str, Any]:
        """Get telemetry data for Logfire."""
        status = self.get_status()
        return {
            "model_name": self.model_name,
            "provider": self.limits.provider,
            "tier": self.limits.tier,
            "status": status.name,
            "status_value": int(status),
            "tokens_used_minute": self.usage.tokens_used_minute,
            "tokens_limit_minute": self.limits.tokens_per_minute,
            "requests_used_minute": self.usage.requests_used_minute,
            "requests_limit_minute": self.limits.requests_per_minute,
            "tokens_used_day": self.usage.tokens_used_day,
            "tokens_limit_day": self.limits.tokens_per_day,
            "tokens_used_window": self.usage.tokens_used_window,
            "tokens_limit_window": self.limits.tokens_per_window,
            "available_tokens": self.get_available_tokens(),
            "in_cooldown": self.usage.is_in_cooldown(),
            "consecutive_429s": self.usage.consecutive_429s,
        }


# Import terminal-visible messaging (optional)
try:
    from code_puppy.messaging.bus import emit_info, emit_warning
    MESSAGING_AVAILABLE = True
except ImportError:
    MESSAGING_AVAILABLE = False
    def emit_info(msg, **kwargs): pass
    def emit_warning(msg, **kwargs): pass


def _emit_capacity_telemetry(
    event: str,
    model_name: str,
    **kwargs
) -> None:
    """Emit capacity telemetry to Logfire and terminal."""
    if LOGFIRE_AVAILABLE and logfire is not None:
        logfire.info(
            f"model_capacity.{event}",
            model_name=model_name,
            **kwargs,
        )
    else:
        logger.debug(f"Capacity {event}: {model_name} - {kwargs}")


def _emit_capacity_warning(
    model_name: str,
    limit_type: str,
    used: int,
    limit: int,
    provider: str = "",
) -> None:
    """Emit terminal-visible capacity warning and log to Logfire."""
    pct = (used / limit * 100) if limit > 0 else 0
    
    # Format based on limit type
    if "window" in limit_type:
        window_desc = "5-hour" if "synthetic" in provider.lower() else "rolling"
        msg = f"⚠️ {model_name}: {window_desc} window {pct:.0f}% used ({used:,}/{limit:,} {limit_type.replace('_', ' ')})"
    elif "day" in limit_type:
        msg = f"⚠️ {model_name}: Daily limit {pct:.0f}% used ({used:,}/{limit:,} {limit_type.replace('_', ' ')})"
    elif "minute" in limit_type:
        msg = f"⚠️ {model_name}: Minute limit {pct:.0f}% used ({used:,}/{limit:,} {limit_type.replace('_', ' ')})"
    else:
        msg = f"⚠️ {model_name}: {limit_type} {pct:.0f}% used ({used:,}/{limit:,})"
    
    if MESSAGING_AVAILABLE:
        emit_warning(msg)
    else:
        logger.warning(msg)
    
    # Log to Logfire for observability
    try:
        import logfire
        logfire.warn(
            "Capacity warning: {model} at {pct}% ({limit_type})",
            model=model_name,
            pct=round(pct, 1),
            limit_type=limit_type,
            used=used,
            limit=limit,
            provider=provider,
        )
    except Exception:
        pass  # Don't let logging break capacity tracking


class CapacityRegistry:
    """Global registry of model capacities.
    
    Singleton that tracks capacity across all configured models.
    Enables intelligent routing decisions.
    """
    
    _instance: Optional["CapacityRegistry"] = None
    
    def __new__(cls) -> "CapacityRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._models: Dict[str, ModelCapacity] = {}
            cls._instance._initialized = False
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> "CapacityRegistry":
        """Get the singleton instance."""
        return cls()
    
    def initialize_from_config(self) -> None:
        """Load model configurations and initialize capacity tracking."""
        if self._initialized:
            return
        
        try:
            from code_puppy.core.failover_config import PROVIDER_LIMITS, get_tier_for_model
            from code_puppy.model_factory import ModelFactory
            
            models_config = ModelFactory.load_config()
            
            for model_name, config in models_config.items():
                if not isinstance(config, dict):
                    continue
                
                # Skip metadata entries
                if model_name.startswith("_"):
                    continue
                
                # Get limits from PROVIDER_LIMITS
                model_type = config.get("type", "unknown")
                provider_key = self._get_provider_key(model_name, model_type)
                provider_limits = PROVIDER_LIMITS.get(provider_key, {})
                
                # Build ModelLimits
                limits = ModelLimits(
                    context_window=config.get("context_length", 128_000),
                    max_output=config.get("max_output", 8_000),
                    optimal_prompt_size=config.get("optimal_prompt_size", 
                                                   config.get("context_length", 128_000) // 2),
                    tokens_per_minute=provider_limits.get("tokens_per_minute", 100_000),
                    requests_per_minute=provider_limits.get("requests_per_minute", 50),
                    tokens_per_day=provider_limits.get("tokens_per_day", 2_000_000),
                    requests_per_day=provider_limits.get("requests_per_day", 10_000),
                    rolling_window_hours=provider_limits.get("rolling_window_hours"),
                    provider=model_type,
                    tier=config.get("tier", get_tier_for_model(model_name)),
                    plan=provider_limits.get("plan", "unknown"),
                    cost_per_month=provider_limits.get("cost_per_month", 0.0),
                )
                
                # Build ModelCapacity
                self._models[model_name] = ModelCapacity(
                    model_name=model_name,
                    limits=limits,
                    workloads=config.get("workload", []),
                    enabled=True,
                )
            
            self._initialized = True
            logger.info(f"Initialized capacity tracking for {len(self._models)} models")
            
        except Exception as e:
            logger.warning(f"Failed to initialize capacity registry: {e}")
            self._initialized = False
    
    def _get_provider_key(self, model_name: str, model_type: str) -> str:
        """Map model to provider limits key."""
        model_lower = model_name.lower()
        type_lower = model_type.lower()
        
        # Check model name patterns
        if "cerebras" in model_lower:
            return "cerebras"
        elif "synthetic" in model_lower or type_lower == "custom_openai":
            return "synthetic_glm"
        elif "antigravity" in model_lower or type_lower == "antigravity":
            return "antigravity"
        elif "claude-code" in model_lower or type_lower == "claude_code":
            return "claude_code"
        elif "chatgpt" in model_lower or type_lower == "chatgpt":
            return "chatgpt_teams"
        elif "openrouter" in model_lower or type_lower == "openrouter":
            return "openrouter_free"
        elif "gemini" in model_lower or type_lower == "gemini":
            if "flash" in model_lower:
                return "gemini_flash"
            return "gemini"
        elif "opus" in model_lower:
            return "claude_opus"
        elif "sonnet" in model_lower:
            return "claude_sonnet"
        elif "haiku" in model_lower:
            return "gemini_flash"  # Similar limits
        elif "codex" in model_lower or "gpt-5" in model_lower:
            return "codex"
        
        return "gemini"  # Conservative default
    
    def get_capacity(self, model_name: str) -> Optional[ModelCapacity]:
        """Get capacity for a specific model."""
        if not self._initialized:
            self.initialize_from_config()
        return self._models.get(model_name)
    
    def get_all_capacities(self) -> Dict[str, ModelCapacity]:
        """Get all model capacities."""
        if not self._initialized:
            self.initialize_from_config()
        return self._models.copy()
    
    def get_available_for_workload(
        self, 
        workload: str, 
        estimated_tokens: int = 10_000,
        filter_by_credentials: bool = True,
    ) -> List[ModelCapacity]:
        """Get models available for a workload, sorted by capacity.
        
        Returns models that:
        1. Have valid credentials (API key or OAuth token)
        2. Support the workload type
        3. Have capacity for the estimated token count
        4. Are not in cooldown
        
        Sorted by: tier (same tier first), then available capacity.
        
        Args:
            workload: Workload type (coding, reasoning, orchestrator, librarian)
            estimated_tokens: Estimated token count for the request
            filter_by_credentials: If True, exclude models without valid credentials
        """
        if not self._initialized:
            self.initialize_from_config()
        
        # Get credential checker if filtering enabled
        cred_checker = None
        if filter_by_credentials:
            try:
                from code_puppy.core.credential_availability import get_credential_checker
                cred_checker = get_credential_checker()
            except ImportError:
                pass
        
        available = []
        workload_lower = workload.lower()
        
        for capacity in self._models.values():
            # Check credentials FIRST - most important filter
            if cred_checker and not cred_checker.has_credentials(capacity.model_name):
                continue
            
            # Check workload match
            if workload_lower not in [w.lower() for w in capacity.workloads]:
                # Also check tier-based workload inference
                if not self._workload_matches_tier(workload_lower, capacity.limits.tier):
                    continue
            
            # Check capacity
            status = capacity.get_status()
            if status in (CapacityStatus.EXHAUSTED, CapacityStatus.COOLDOWN):
                continue
            
            # Check can handle prompt
            if not capacity.can_handle_prompt(estimated_tokens):
                continue
            
            available.append(capacity)
        
        # Sort by: status (AVAILABLE first), tier, then available tokens
        available.sort(key=lambda c: (
            c.get_status(),
            c.limits.tier,
            -c.get_available_tokens()
        ))
        
        return available
    
    def _workload_matches_tier(self, workload: str, tier: int) -> bool:
        """Check if workload matches tier (fallback matching)."""
        tier_workloads = {
            1: ["orchestrator", "architect", "planning"],
            2: ["reasoning", "builder_high", "refactoring"],
            3: ["coding", "builder", "builder_mid"],
            4: ["librarian", "search", "docs"],
            5: ["sprinter", "coding", "fast"],
        }
        return workload.lower() in tier_workloads.get(tier, [])
    
    def record_request(
        self, 
        model_name: str, 
        input_tokens: int, 
        output_tokens: int,
        headers: Optional[Mapping[str, str]] = None
    ) -> None:
        """Record a completed request."""
        capacity = self.get_capacity(model_name)
        if capacity:
            # Pass rolling window hours for proper window reset tracking
            rolling_window_hours = capacity.limits.rolling_window_hours
            capacity.usage.record_request(
                input_tokens, 
                output_tokens, 
                rolling_window_hours=rolling_window_hours
            )
            if headers:
                capacity.update_from_headers(headers)
            
            # Check status and emit warnings if approaching limits
            status = capacity.get_status()
            if status in (CapacityStatus.LOW, CapacityStatus.APPROACHING):
                # Emit terminal-visible warnings for approaching limits
                provider = capacity.limits.provider
                
                # Check rolling window (e.g., synthetic.new's 5-hour window)
                if capacity.limits.tokens_per_window and capacity.limits.tokens_per_window > 0:
                    pct = capacity.usage.tokens_used_window / capacity.limits.tokens_per_window
                    if pct >= 0.8:  # 80%+ used
                        _emit_capacity_warning(
                            model_name,
                            "tokens_per_window",
                            capacity.usage.tokens_used_window,
                            capacity.limits.tokens_per_window,
                            provider,
                        )
                
                # Check daily limit
                if capacity.limits.tokens_per_day > 0:
                    pct = capacity.usage.tokens_used_day / capacity.limits.tokens_per_day
                    if pct >= 0.8:
                        _emit_capacity_warning(
                            model_name,
                            "tokens_per_day",
                            capacity.usage.tokens_used_day,
                            capacity.limits.tokens_per_day,
                            provider,
                        )
                
                # Check minute RPM limit
                if capacity.limits.requests_per_minute > 0:
                    pct = capacity.usage.requests_used_minute / capacity.limits.requests_per_minute
                    if pct >= 0.8:
                        _emit_capacity_warning(
                            model_name,
                            "requests_per_minute",
                            capacity.usage.requests_used_minute,
                            capacity.limits.requests_per_minute,
                            provider,
                        )
            
            # Emit telemetry
            _emit_capacity_telemetry(
                "request_completed",
                model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                status=status.name,
                available_tokens=capacity.get_available_tokens(),
                tokens_used_window=capacity.usage.tokens_used_window,
                rolling_window_hours=rolling_window_hours,
            )
    
    def record_rate_limit(self, model_name: str) -> None:
        """Record a 429 rate limit error."""
        capacity = self.get_capacity(model_name)
        if capacity:
            capacity.usage.record_rate_limit()
            
            # Emit telemetry
            _emit_capacity_telemetry(
                "rate_limit_hit",
                model_name,
                consecutive_429s=capacity.usage.consecutive_429s,
                cooldown_seconds=capacity.usage.seconds_until_cooldown_end(),
            )
    
    def get_best_model_for_request(
        self, 
        workload: str,
        estimated_tokens: int = 10_000,
        current_model: Optional[str] = None
    ) -> Optional[str]:
        """Get the best model for a request.
        
        This is the main routing decision point:
        1. If current model has capacity, use it
        2. Otherwise, find best alternative for workload
        
        Returns model name or None if no models available.
        """
        available = self.get_available_for_workload(workload, estimated_tokens)
        
        if not available:
            logger.warning(f"No models available for workload '{workload}' with {estimated_tokens} tokens")
            return None
        
        # If current model is still good, prefer it (avoid unnecessary switches)
        if current_model:
            for cap in available:
                if cap.model_name == current_model:
                    status = cap.get_status()
                    if status in (CapacityStatus.AVAILABLE, CapacityStatus.APPROACHING):
                        return current_model
        
        # Return best available
        return available[0].model_name
    
    def should_switch_model(self, model_name: str) -> Tuple[bool, str]:
        """Check if we should proactively switch from this model.
        
        Returns (should_switch, reason).
        """
        capacity = self.get_capacity(model_name)
        if not capacity:
            return False, "Model not tracked"
        
        status = capacity.get_status()
        
        if status == CapacityStatus.COOLDOWN:
            return True, f"In cooldown for {capacity.usage.seconds_until_cooldown_end():.0f}s"
        
        if status == CapacityStatus.EXHAUSTED:
            return True, "Capacity exhausted"
        
        if status == CapacityStatus.LOW:
            available = capacity.get_available_tokens()
            return True, f"Low capacity: ~{available:,} tokens remaining"
        
        return False, f"Capacity healthy ({status.name})"
    
    def get_status_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all model capacities for monitoring."""
        if not self._initialized:
            self.initialize_from_config()
        
        summary = {}
        for name, capacity in self._models.items():
            status = capacity.get_status()
            summary[name] = {
                "status": status.name,
                "tier": capacity.limits.tier,
                "provider": capacity.limits.provider,
                "available_tokens": capacity.get_available_tokens(),
                "tokens_used_minute": capacity.usage.tokens_used_minute,
                "requests_used_minute": capacity.usage.requests_used_minute,
                "in_cooldown": capacity.usage.is_in_cooldown(),
            }
        
        return summary


# Convenience functions
def get_capacity_registry() -> CapacityRegistry:
    """Get the global capacity registry singleton."""
    return CapacityRegistry.get_instance()


def get_best_model(workload: str, estimated_tokens: int = 10_000) -> Optional[str]:
    """Quick helper to get best model for a workload."""
    return get_capacity_registry().get_best_model_for_request(workload, estimated_tokens)


def record_model_usage(
    model_name: str, 
    input_tokens: int, 
    output_tokens: int,
    headers: Optional[Mapping[str, str]] = None
) -> None:
    """Quick helper to record model usage."""
    get_capacity_registry().record_request(model_name, input_tokens, output_tokens, headers)


def record_model_rate_limit(model_name: str) -> None:
    """Quick helper to record a rate limit."""
    get_capacity_registry().record_rate_limit(model_name)
