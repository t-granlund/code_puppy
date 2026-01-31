"""Token Budget Manager - The Governor.

Implements token bucket algorithm to prevent 429 Too Many Requests errors.
Provides smart retry with exponential backoff and jitter, plus failover logic.

Rate Limits (Hard Constraints):
- Cerebras: 300,000 tokens/minute, 24M tokens/day
- Gemini: ~2M tokens/day (~100k/minute effective)
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from decimal import Decimal
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

# Import genai-prices for cost tracking
try:
    from genai_prices import Usage, calc_price
    GENAI_PRICES_AVAILABLE = True
except ImportError:
    GENAI_PRICES_AVAILABLE = False

logger = logging.getLogger(__name__)

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class ProviderBudget:
    """Token budget state for a single provider."""
    
    tokens_per_minute: int
    tokens_per_day: int
    reset_window_seconds: int = 60
    daily_reset_hour: int = 0  # Hour when daily limit resets (UTC)
    
    # Runtime state
    tokens_used_this_minute: int = 0
    tokens_used_today: int = 0
    last_minute_reset: float = field(default_factory=time.time)
    last_daily_reset: float = field(default_factory=time.time)
    consecutive_429s: int = 0
    
    # Cost tracking (genai-prices integration)
    total_cost_usd: Decimal = field(default_factory=lambda: Decimal("0.0"))
    cost_this_minute: Decimal = field(default_factory=lambda: Decimal("0.0"))
    cost_today: Decimal = field(default_factory=lambda: Decimal("0.0"))
    
    def reset_minute_if_needed(self) -> None:
        """Reset minute counter if window has passed."""
        now = time.time()
        if now - self.last_minute_reset >= self.reset_window_seconds:
            self.tokens_used_this_minute = 0
            self.last_minute_reset = now
            self.consecutive_429s = 0  # Reset 429 counter on successful window
    
    def reset_daily_if_needed(self) -> None:
        """Reset daily counter if day has passed."""
        now = time.time()
        if now - self.last_daily_reset >= 86400:  # 24 hours
            self.tokens_used_today = 0
            self.last_daily_reset = now
    
    @property
    def remaining_minute(self) -> int:
        """Tokens remaining in current minute window."""
        self.reset_minute_if_needed()
        return max(0, self.tokens_per_minute - self.tokens_used_this_minute)
    
    @property
    def remaining_daily(self) -> int:
        """Tokens remaining today."""
        self.reset_daily_if_needed()
        return max(0, self.tokens_per_day - self.tokens_used_today)
    
    @property
    def seconds_until_reset(self) -> float:
        """Seconds until minute window resets."""
        elapsed = time.time() - self.last_minute_reset
        return max(0, self.reset_window_seconds - elapsed)
    
    @property
    def usage_percent_minute(self) -> float:
        """Percentage of minute budget used."""
        self.reset_minute_if_needed()
        return self.tokens_used_this_minute / self.tokens_per_minute
    
    @property
    def usage_percent_daily(self) -> float:
        """Percentage of daily budget used."""
        self.reset_daily_if_needed()
        return self.tokens_used_today / self.tokens_per_day


@dataclass
class BudgetCheckResult:
    """Result of budget check."""
    
    provider: str
    can_proceed: bool
    estimated_tokens: int
    remaining_minute: int
    remaining_daily: int
    wait_seconds: float = 0.0
    failover_to: Optional[str] = None
    reason: str = ""
    estimated_cost_usd: Optional[Decimal] = None
    total_cost_usd: Optional[Decimal] = None


class TokenBudgetManager:
    """Manages token budgets across providers to prevent rate limiting.
    
    Implements token bucket algorithm with:
    - Per-minute rate limiting
    - Daily budget tracking
    - Smart failover to cheaper providers
    - Exponential backoff with jitter on 429s
    """
    
    # Provider configurations (Tier 5 → Tier 1)
    PROVIDER_LIMITS: Dict[str, Dict[str, int]] = {
        # Tier 5: The Sprinter
        "cerebras": {
            "tokens_per_minute": 300_000,
            "tokens_per_day": 24_000_000,
            "reset_window_seconds": 60,
        },
        # Tier 4: The Librarian
        "gemini": {
            "tokens_per_minute": 100_000,
            "tokens_per_day": 2_000_000,
            "reset_window_seconds": 60,
        },
        "gemini_flash": {
            "tokens_per_minute": 150_000,
            "tokens_per_day": 2_000_000,
            "reset_window_seconds": 60,
        },
        # Tier 2/3: The Builders
        "codex": {
            "tokens_per_minute": 200_000,
            "tokens_per_day": 10_000_000,
            "reset_window_seconds": 60,
        },
        "claude_sonnet": {
            "tokens_per_minute": 100_000,
            "tokens_per_day": 5_000_000,
            "reset_window_seconds": 60,
        },
        # Tier 1: The Architect
        "claude_opus": {
            "tokens_per_minute": 50_000,
            "tokens_per_day": 1_000_000,
            "reset_window_seconds": 60,
        },
    }
    
    # Static failover chain: when provider X hits limits, try Y
    # PURPOSE-DRIVEN FAILOVER STRUCTURE:
    #
    # ARCHITECT TIER (Big reasoning, planning, orchestrator, pack-leader, governor):
    #   Claude Code Opus → Antigravity Opus → Gemini Pro → Codex 5.2
    #
    # BUILDER TIER (Complex logic, design, refactoring):
    #   Claude Code Sonnet → Antigravity Sonnet → Gemini Pro → Codex 5.2
    #
    # SPRINTER TIER (Main code work, high volume generation):
    #   Cerebras GLM 4.7 → Claude Haiku → Gemini Flash
    #
    # LIBRARIAN TIER (Search, docs, context, less intensive):
    #   Claude Haiku → GPT 5.2 → Gemini Flash
    #   Gemini Pro → Gemini Flash
    #   Codex 5.2 → Gemini Flash
    #
    FAILOVER_CHAIN: Dict[str, str] = {
        # =====================================================================
        # ARCHITECT TIER - Big reasoning, planning, orchestrator roles
        # Claude Code Opus → Antigravity Opus thinking → Antigravity Sonnet thinking → ChatGPT 5.2
        # =====================================================================
        "claude_opus": "antigravity-claude-opus-4-5-thinking-high",
        "claude-code-claude-opus-4-5-20251101": "antigravity-claude-opus-4-5-thinking-high",
        "antigravity-claude-opus-4-5-thinking-high": "antigravity-claude-opus-4-5-thinking-medium",
        "antigravity-claude-opus-4-5-thinking-medium": "antigravity-claude-opus-4-5-thinking-low",
        "antigravity-claude-opus-4-5-thinking-low": "antigravity-claude-sonnet-4-5-thinking-high",
        
        # =====================================================================
        # BUILDER TIER - Complex logic, design, refactoring
        # Claude Code Sonnet → Antigravity Sonnet → ChatGPT 5.2
        # =====================================================================
        "claude_sonnet": "antigravity-claude-sonnet-4-5",
        "claude-code-claude-sonnet-4-5-20250929": "antigravity-claude-sonnet-4-5",
        "antigravity-claude-sonnet-4-5": "antigravity-claude-sonnet-4-5-thinking-high",
        "antigravity-claude-sonnet-4-5-thinking-high": "antigravity-claude-sonnet-4-5-thinking-medium",
        "antigravity-claude-sonnet-4-5-thinking-medium": "antigravity-claude-sonnet-4-5-thinking-low",
        # After Sonnet thinking chain exhausts, fallback to Cerebras → Haiku → Gemini
        "antigravity-claude-sonnet-4-5-thinking-low": "Cerebras-GLM-4.7",
        
        # =====================================================================
        # SPRINTER TIER - Main code work (high volume, fast generation)
        # Cerebras GLM 4.7 → Claude Haiku → Antigravity Gemini Flash → ChatGPT 5.2
        # =====================================================================
        "cerebras": "claude-code-claude-haiku-4-5-20251001",
        "cerebras-glm-4.7": "claude-code-claude-haiku-4-5-20251001",
        "Cerebras-GLM-4.7": "claude-code-claude-haiku-4-5-20251001",
        "claude-haiku": "antigravity-gemini-3-flash",
        "claude_haiku": "antigravity-gemini-3-flash",
        "claude-code-claude-haiku-4-5-20251001": "antigravity-gemini-3-flash",
        
        # =====================================================================
        # LIBRARIAN TIER - Search, docs, context, less intensive code
        # Antigravity Gemini → Cerebras (always available)
        # =====================================================================
        "antigravity-gemini-3-pro-high": "antigravity-gemini-3-pro-low",
        "antigravity-gemini-3-pro-low": "antigravity-gemini-3-flash",
        # Gemini flash loops to Cerebras (always available)
        "antigravity-gemini-3-flash": "Cerebras-GLM-4.7",
        
        # NOTE: ChatGPT models are OAuth-only and dynamically added when user
        # runs /chatgpt-auth. The failover chain entries for chatgpt models are
        # added at runtime by the chatgpt_oauth plugin.
        
        # Cross-tier emergency fallbacks (when primary chain exhausted)
        # Architect → Builder → Librarian
        # These kick in after tier-specific chains are exhausted
    }
    
    _instance: Optional["TokenBudgetManager"] = None
    
    def __new__(cls) -> "TokenBudgetManager":
        """Singleton pattern to ensure single budget state."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> "TokenBudgetManager":
        """Get the singleton instance of TokenBudgetManager.
        
        This is an alias for the __new__ singleton pattern for compatibility.
        """
        return cls()
    
    def __init__(self):
        if self._initialized:
            return
        
        self._budgets: Dict[str, ProviderBudget] = {}
        self._lock = asyncio.Lock()
        self._initialized = True
        
        # Initialize budgets for all providers
        for provider, limits in self.PROVIDER_LIMITS.items():
            self._budgets[provider] = ProviderBudget(**limits)
    
    def _normalize_provider(self, provider: str) -> str:
        """Normalize provider name to canonical form."""
        provider = provider.lower().strip()
        
        # Map model names to providers
        mappings = {
            # Cerebras models
            "cerebras-glm-4.7": "cerebras",  # lowercase variant
            "Cerebras-GLM-4.7": "cerebras",  # Exact models.json key
            "glm-4.7": "cerebras",
            # Claude Code models (with dates)
            "claude-code-claude-opus-4-5-20251101": "claude_opus",
            "claude-code-claude-sonnet-4-5-20250929": "claude_sonnet",
            "claude-code-claude-haiku-4-5-20251001": "gemini_flash",
            # Antigravity models
            "antigravity-claude-sonnet-4-5": "claude_sonnet",
            "antigravity-claude-sonnet-4-5-thinking-low": "claude_sonnet",
            "antigravity-claude-sonnet-4-5-thinking-medium": "claude_sonnet",
            "antigravity-claude-sonnet-4-5-thinking-high": "claude_sonnet",
            "antigravity-gemini-3-pro-low": "gemini",
            "antigravity-gemini-3-pro-high": "gemini",
            "antigravity-gemini-3-flash": "gemini_flash",
            # Gemini models - both bare and antigravity-prefixed
            "gemini-3": "gemini",
            "Gemini-3": "gemini",  # Exact models.json key
            "gemini-3-flash": "gemini_flash",
            "antigravity-gemini-3-flash": "gemini_flash",  # Exact models.json key
            "gemini-3-pro": "gemini",
            "gemini-flash": "gemini_flash",
            # Provider aliases
            "custom_openai": "codex",
            "openai": "codex",
            # GPT/Codex models
            "gpt-5.1": "codex",
            "gpt-5.1-codex-api": "codex",
            "chatgpt-gpt-5.2": "codex",
            "chatgpt-gpt-5.2-codex": "codex",
            "chatgpt-codex-5.2": "codex",
            "codex-5.2": "codex",
            # Claude Code OAuth models (full names with date suffix)
            "claude-code-claude-opus-4-5-20251101": "claude_opus",
            "claude-code-claude-sonnet-4-5-20250929": "claude_sonnet",
            "claude-code-claude-haiku-4-5-20251001": "gemini_flash",  # Haiku shares limits with flash
            # Legacy Claude names (kept for compatibility)
            "claude-4-5-opus": "claude_opus",
            "claude-4-5-sonnet": "claude_sonnet",
            "claude-4-5-haiku": "gemini_flash",
            "claude-sonnet-4.5": "claude_sonnet",
            "sonnet-4.5": "claude_sonnet",
            "claude-opus-4.5": "claude_opus",
            "opus-4.5": "claude_opus",
            # Legacy Antigravity names
            "antigravity-claude-opus-4-5-thinking-low": "claude_opus",
            "antigravity-claude-opus-4-5-thinking-medium": "claude_opus",
            "antigravity-claude-opus-4-5-thinking-high": "claude_opus",
        }
        
        # Check direct mapping first
        if provider in mappings:
            return mappings[provider]
        
        # Fallback: detect from prefix patterns
        if "antigravity" in provider:
            if "gemini" in provider and "flash" in provider:
                return "gemini_flash"
            elif "gemini" in provider:
                return "gemini"
            elif "opus" in provider:
                return "claude_opus"
            elif "sonnet" in provider or "claude" in provider:
                return "claude_sonnet"
        
        return provider
    
    def check_budget(
        self,
        provider: str,
        estimated_tokens: int,
        allow_failover: bool = True,
    ) -> BudgetCheckResult:
        """Check if we have budget for the estimated tokens.
        
        Args:
            provider: Provider name or model name
            estimated_tokens: Estimated total tokens (input + output)
            allow_failover: Whether to suggest failover on budget exceeded
            
        Returns:
            BudgetCheckResult with proceed decision and any wait/failover needed
        """
        provider = self._normalize_provider(provider)
        
        if provider not in self._budgets:
            # Unknown provider - allow but log warning
            logger.warning(f"Unknown provider '{provider}', allowing request")
            return BudgetCheckResult(
                provider=provider,
                can_proceed=True,
                estimated_tokens=estimated_tokens,
                remaining_minute=estimated_tokens,
                remaining_daily=estimated_tokens,
                reason="Unknown provider - no limits applied",
            )
        
        budget = self._budgets[provider]
        budget.reset_minute_if_needed()
        budget.reset_daily_if_needed()
        
        # Check daily limit first (hard stop)
        if estimated_tokens > budget.remaining_daily:
            if allow_failover and provider in self.FAILOVER_CHAIN:
                failover = self.FAILOVER_CHAIN[provider]
                return BudgetCheckResult(
                    provider=provider,
                    can_proceed=False,
                    estimated_tokens=estimated_tokens,
                    remaining_minute=budget.remaining_minute,
                    remaining_daily=budget.remaining_daily,
                    failover_to=failover,
                    reason=f"Daily limit exhausted, failover to {failover}",
                )
            return BudgetCheckResult(
                provider=provider,
                can_proceed=False,
                estimated_tokens=estimated_tokens,
                remaining_minute=budget.remaining_minute,
                remaining_daily=budget.remaining_daily,
                reason="Daily limit exhausted, no failover available",
            )
        
        # Check minute limit
        if estimated_tokens > budget.remaining_minute:
            wait_time = budget.seconds_until_reset
            
            # If wait is short (<10s), suggest waiting
            if wait_time < 10:
                return BudgetCheckResult(
                    provider=provider,
                    can_proceed=False,
                    estimated_tokens=estimated_tokens,
                    remaining_minute=budget.remaining_minute,
                    remaining_daily=budget.remaining_daily,
                    wait_seconds=wait_time,
                    reason=f"Rate limit reached, wait {wait_time:.1f}s",
                )
            
            # Longer wait - suggest failover
            if allow_failover and provider in self.FAILOVER_CHAIN:
                failover = self.FAILOVER_CHAIN[provider]
                return BudgetCheckResult(
                    provider=provider,
                    can_proceed=False,
                    estimated_tokens=estimated_tokens,
                    remaining_minute=budget.remaining_minute,
                    remaining_daily=budget.remaining_daily,
                    wait_seconds=wait_time,
                    failover_to=failover,
                    reason=f"Rate limit reached ({wait_time:.1f}s wait), failover to {failover}",
                )
            
            return BudgetCheckResult(
                provider=provider,
                can_proceed=False,
                estimated_tokens=estimated_tokens,
                remaining_minute=budget.remaining_minute,
                remaining_daily=budget.remaining_daily,
                wait_seconds=wait_time,
                reason=f"Rate limit reached, wait {wait_time:.1f}s",
            )
        
        # All good - can proceed
        # Estimate cost if possible (assume 50/50 split for estimation)
        estimated_cost = None
        if GENAI_PRICES_AVAILABLE:
            try:
                provider_id_map = {
                    "cerebras": "cerebras",
                    "gemini": "google",
                    "gemini_flash": "google",
                    "codex": "openai",
                    "claude_sonnet": "anthropic",
                    "claude_opus": "anthropic",
                    "claude_haiku": "anthropic",
                }
                if provider in provider_id_map:
                    # Rough estimate: assume 50/50 input/output split
                    est_input = estimated_tokens // 2
                    est_output = estimated_tokens - est_input
                    usage = Usage(input_tokens=est_input, output_tokens=est_output)
                    # Use a generic model for provider if we don't have specific model
                    model_map = {
                        "cerebras": "cerebras-glm-4.7",
                        "gemini": "gemini-3-pro",
                        "gemini_flash": "gemini-3-flash",
                        "codex": "gpt-5.2",
                        "claude_sonnet": "claude-sonnet-4.5",
                        "claude_opus": "claude-opus-4.5",
                        "claude_haiku": "claude-haiku",
                    }
                    model_ref = model_map.get(provider, provider)
                    price_calc = calc_price(usage, model_ref, provider_id=provider_id_map[provider])
                    estimated_cost = price_calc.total_price
            except Exception:
                pass
        
        return BudgetCheckResult(
            provider=provider,
            can_proceed=True,
            estimated_tokens=estimated_tokens,
            remaining_minute=budget.remaining_minute,
            remaining_daily=budget.remaining_daily,
            reason="Within budget",
            estimated_cost_usd=estimated_cost,
            total_cost_usd=budget.total_cost_usd if hasattr(budget, 'total_cost_usd') else None,
        )
    
    def record_usage(
        self, 
        provider: str, 
        tokens_used: int,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        model_ref: Optional[str] = None,
    ) -> Optional[Decimal]:
        """Record actual token usage after a request completes.
        
        Args:
            provider: Provider that was used
            tokens_used: Actual tokens consumed
            input_tokens: Input tokens (for cost calculation)
            output_tokens: Output tokens (for cost calculation)
            model_ref: Model reference (e.g., 'gpt-5', 'claude-opus-4.5')
            
        Returns:
            Cost in USD if genai-prices is available, None otherwise
        """
        provider = self._normalize_provider(provider)
        
        if provider not in self._budgets:
            return None
        
        budget = self._budgets[provider]
        budget.tokens_used_this_minute += tokens_used
        budget.tokens_used_today += tokens_used
        
        # Calculate cost if genai-prices is available and we have token breakdown
        cost_usd = None
        if GENAI_PRICES_AVAILABLE and input_tokens is not None and output_tokens is not None and model_ref:
            try:
                # Map provider to genai-prices provider_id
                provider_id_map = {
                    "cerebras": "cerebras",
                    "gemini": "google",
                    "gemini_flash": "google",
                    "codex": "openai",
                    "claude_sonnet": "anthropic",
                    "claude_opus": "anthropic",
                    "claude_haiku": "anthropic",
                }
                
                provider_id = provider_id_map.get(provider)
                if provider_id:
                    usage = Usage(input_tokens=input_tokens, output_tokens=output_tokens)
                    price_calc = calc_price(usage, model_ref, provider_id=provider_id)
                    cost_usd = price_calc.total_price
                    
                    # Track costs
                    budget.total_cost_usd += cost_usd
                    budget.cost_this_minute += cost_usd
                    budget.cost_today += cost_usd
                    
                    logger.debug(
                        f"Cost for {provider}/{model_ref}: ${cost_usd:.6f} "
                        f"(in={input_tokens}, out={output_tokens})"
                    )
            except Exception as e:
                logger.debug(f"Could not calculate cost for {provider}/{model_ref}: {e}")
        
        logger.debug(
            f"Recorded {tokens_used} tokens for {provider}. "
            f"Minute: {budget.tokens_used_this_minute}/{budget.tokens_per_minute}, "
            f"Daily: {budget.tokens_used_today}/{budget.tokens_per_day}"
            + (f", Cost: ${cost_usd:.6f}" if cost_usd else "")
        )
        
        return cost_usd
    
    def record_429(self, provider: str) -> Tuple[float, Optional[str]]:
        """Record a 429 error and return backoff time + failover suggestion.
        
        Args:
            provider: Provider that returned 429
            
        Returns:
            (wait_seconds, failover_provider) tuple
        """
        provider = self._normalize_provider(provider)
        
        if provider not in self._budgets:
            return (1.0, None)
        
        budget = self._budgets[provider]
        budget.consecutive_429s += 1
        
        # Exponential backoff with jitter: base * 2^(n-1) + random jitter
        base_wait = 2.0
        max_wait = 60.0
        wait = min(max_wait, base_wait * (2 ** (budget.consecutive_429s - 1)))
        jitter = random.uniform(0, wait * 0.5)
        total_wait = wait + jitter
        
        # After 3 consecutive 429s, suggest failover
        failover = None
        if budget.consecutive_429s >= 3 and provider in self.FAILOVER_CHAIN:
            failover = self.FAILOVER_CHAIN[provider]
            logger.warning(
                f"{provider} hit {budget.consecutive_429s} consecutive 429s, "
                f"suggesting failover to {failover}"
            )
        
        logger.info(f"{provider} 429 #{budget.consecutive_429s}, waiting {total_wait:.2f}s")
        
        return (total_wait, failover)
    
    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """Get current status of all provider budgets.
        
        Returns:
            Dict with budget status for each provider
        """
        status = {}
        for provider, budget in self._budgets.items():
            budget.reset_minute_if_needed()
            budget.reset_daily_if_needed()
            provider_status = {
                "remaining_minute": budget.remaining_minute,
                "remaining_daily": budget.remaining_daily,
                "usage_percent_minute": f"{budget.usage_percent_minute:.1%}",
                "usage_percent_daily": f"{budget.usage_percent_daily:.1%}",
                "seconds_until_reset": budget.seconds_until_reset,
                "consecutive_429s": budget.consecutive_429s,
            }
            # Add cost tracking if available
            if hasattr(budget, 'total_cost_usd'):
                provider_status["total_cost_usd"] = f"${budget.total_cost_usd:.6f}"
                provider_status["cost_today"] = f"${budget.cost_today:.6f}"
            status[provider] = provider_status
        return status
    
    def reset_provider(self, provider: str) -> None:
        """Manually reset a provider's budget (for testing or admin)."""
        provider = self._normalize_provider(provider)
        if provider in self._budgets:
            limits = self.PROVIDER_LIMITS[provider]
            self._budgets[provider] = ProviderBudget(**limits)

    def get_failover(self, provider: str) -> Optional[str]:
        """Get failover provider for a given provider.
        
        Uses static FAILOVER_CHAIN, can be enhanced by RateLimitFailover.
        """
        provider = self._normalize_provider(provider)
        return self.FAILOVER_CHAIN.get(provider)


def smart_retry(
    provider: str,
    max_retries: int = 5,
    max_wait: float = 60.0,
    allow_failover: bool = True,
    model_param: str = "model",
) -> Callable[[F], F]:
    """Decorator for smart retry with exponential backoff and failover.
    
    Enhanced to actually inject failover model into kwargs when 429 occurs.
    
    Usage:
        @smart_retry("cerebras", max_retries=5, model_param="model_name")
        async def call_cerebras(prompt: str, model_name: str = "cerebras") -> str:
            ...
    
    Args:
        provider: Provider name for budget tracking
        max_retries: Maximum retry attempts
        max_wait: Maximum wait time per retry
        allow_failover: Whether to failover on repeated 429s
        model_param: Kwarg name for model injection on failover
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            budget_mgr = TokenBudgetManager()
            last_exception = None
            current_provider = provider
            
            for attempt in range(max_retries):
                try:
                    result = await func(*args, **kwargs)
                    return result
                    
                except Exception as e:
                    last_exception = e
                    error_str = str(e).lower()
                    
                    # Check for rate limit error
                    if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
                        wait_time, failover = budget_mgr.record_429(current_provider)
                        
                        if failover and allow_failover:
                            logger.info(f"Failing over from {current_provider} to {failover}")
                            current_provider = failover
                            # INJECT failover model into kwargs for retry
                            if model_param in kwargs or model_param == "model":
                                kwargs[model_param] = failover
                                logger.debug(f"Injected {model_param}={failover} for retry")
                        
                        if attempt < max_retries - 1:
                            capped_wait = min(wait_time, max_wait)
                            logger.info(f"Retry {attempt + 1}/{max_retries} after {capped_wait:.2f}s")
                            await asyncio.sleep(capped_wait)
                            continue
                    else:
                        # Non-rate-limit error - don't retry
                        raise
            
            # Exhausted retries
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Exhausted {max_retries} retries for {provider}")
        
        return wrapper  # type: ignore
    return decorator
