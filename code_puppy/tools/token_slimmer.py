"""🏋️ The Token Slimmer - Universal Context Optimization Engine.

"Your context is looking a bit chunky. Let's get it runway ready!" 💪

Implements intelligent token management for ALL providers:
- Provider-aware compaction thresholds (aggressive for free tiers, relaxed for paid)
- Sliding window with configurable exchange limits
- Smart max_tokens allocation based on task type
- Quality-preserving output limits

Philosophy: Trim the fat, keep the muscle. Every token should earn its place.

Supports: Cerebras, OpenAI, Anthropic, OAuth (Antigravity, Claude Code, ChatGPT Teams), and more.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import re


class TaskType(Enum):
    """Task types for output token estimation."""
    TOOL_CALL = "tool_call"  # Short response, typically <500 tokens
    CODE_GENERATION = "code_generation"  # Medium, 1-4K tokens
    EXPLANATION = "explanation"  # Variable, 500-2K tokens
    FILE_READ = "file_read"  # Just requesting, output is tool result
    PLANNING = "planning"  # Medium-long, 1-3K tokens
    REVIEW = "review"  # Medium, 1-2K tokens
    UNKNOWN = "unknown"


# =============================================================================
# 🎛️ PROVIDER-SPECIFIC LIMITS (The Diet Plans)
# =============================================================================
# Philosophy:
#   - Free/Rate-Limited tiers (Cerebras): ULTRA AGGRESSIVE ("Boot Camp")
#   - Paid tiers with high limits: RELAXED ("Maintenance Mode")
#   - OAuth/Teams subscriptions: BALANCED ("Sensible Eating")

# Standard output limits by task type (shared across providers, scaled per provider)
_BASE_OUTPUT_LIMITS = {
    TaskType.TOOL_CALL: 300,
    TaskType.CODE_GENERATION: 4000,
    TaskType.EXPLANATION: 2000,
    TaskType.FILE_READ: 200,
    TaskType.PLANNING: 2500,
    TaskType.REVIEW: 2000,
    TaskType.UNKNOWN: 2000,
}

def _scale_output_limits(scale: float) -> Dict[TaskType, int]:
    """Scale output limits by a factor (e.g., 0.5 for aggressive, 1.0 for relaxed)."""
    return {k: int(v * scale) for k, v in _BASE_OUTPUT_LIMITS.items()}


# Provider-specific configurations
PROVIDER_LIMITS = {
    # 🏋️ BOOT CAMP: Cerebras Code Pro ($50/month) - aggressive but not free tier
    "cerebras": {
        "compaction_threshold": 0.30,  # Compact at 30% (was 20%)
        "hard_limit_threshold": 0.50,  # Block at 50% (was 40%)
        "max_input_tokens": 80_000,    # Increased from 50K
        "target_input_tokens": 15_000, # Increased from 8K
        "max_exchanges": 5,            # Increased from 3
        "max_output_by_task": _scale_output_limits(0.75),  # 75% of base
        "default_max_output": 1500,
        "diet_mode": "boot_camp",  # 🏋️
    },
    
    # 🚀 HIGH VOLUME: Synthetic.new Pro ($60/month) - Z.ai GLM 4.7
    "synthetic_glm": {
        "compaction_threshold": 0.60,
        "hard_limit_threshold": 0.85,
        "max_input_tokens": 180_000,   # High context
        "target_input_tokens": 60_000,
        "max_exchanges": 10,
        "max_output_by_task": _scale_output_limits(1.0),
        "default_max_output": 3000,
        "diet_mode": "relaxed",  # 🚀
    },
    
    # 🥗 BALANCED: Antigravity Pro ($20/month)
    "antigravity": {
        "compaction_threshold": 0.50,
        "hard_limit_threshold": 0.80,
        "max_input_tokens": 100_000,
        "target_input_tokens": 40_000,
        "max_exchanges": 8,
        "max_output_by_task": _scale_output_limits(1.0),
        "default_max_output": 2000,
        "diet_mode": "balanced",  # 🥗
    },
    
    # 🥗 BALANCED: Claude Max ($100/month) via OAuth
    "claude_code": {
        "compaction_threshold": 0.60,
        "hard_limit_threshold": 0.85,
        "max_input_tokens": 180_000,
        "target_input_tokens": 80_000,
        "max_exchanges": 10,
        "max_output_by_task": _scale_output_limits(1.0),
        "default_max_output": 2500,
        "diet_mode": "balanced",  # 🥗
    },
    
    # 🥗 BALANCED: ChatGPT Teams ($35/month) via OAuth  
    "chatgpt_teams": {
        "compaction_threshold": 0.55,
        "hard_limit_threshold": 0.85,
        "max_input_tokens": 120_000,
        "target_input_tokens": 50_000,
        "max_exchanges": 8,
        "max_output_by_task": _scale_output_limits(1.0),
        "default_max_output": 2500,
        "diet_mode": "balanced",  # 🥗
    },
    
    # 🎁 FREE: OpenRouter free tier models
    "openrouter_free": {
        "compaction_threshold": 0.25,  # Very aggressive
        "hard_limit_threshold": 0.40,
        "max_input_tokens": 40_000,
        "target_input_tokens": 10_000,
        "max_exchanges": 4,
        "max_output_by_task": _scale_output_limits(0.5),  # 50% of base
        "default_max_output": 800,
        "diet_mode": "boot_camp",  # 🏋️
    },
    
    # 🍽️ MAINTENANCE: Anthropic API (paid, high limits)
    "anthropic": {
        "compaction_threshold": 0.70,
        "hard_limit_threshold": 0.90,
        "max_input_tokens": 180_000,
        "target_input_tokens": 100_000,
        "max_exchanges": 12,
        "max_output_by_task": _scale_output_limits(1.0),
        "default_max_output": 3000,
        "diet_mode": "maintenance",  # 🍽️
    },
    
    # 🍽️ MAINTENANCE: OpenAI API (paid)
    "openai": {
        "compaction_threshold": 0.70,
        "hard_limit_threshold": 0.90,
        "max_input_tokens": 120_000,
        "target_input_tokens": 60_000,
        "max_exchanges": 10,
        "max_output_by_task": _scale_output_limits(1.0),
        "default_max_output": 3000,
        "diet_mode": "maintenance",  # 🍽️
    },
    
    # 🥗 DEFAULT: Safe middle ground for unknown providers
    "default": {
        "compaction_threshold": 0.50,
        "hard_limit_threshold": 0.80,
        "max_input_tokens": 30_000,
        "target_input_tokens": 15_000,
        "max_exchanges": 6,
        "max_output_by_task": _scale_output_limits(0.75),
        "default_max_output": 1500,
        "diet_mode": "balanced",  # 🥗
    },
}

# Backward compatibility alias
CEREBRAS_LIMITS = PROVIDER_LIMITS["cerebras"]


def get_provider_limits(provider: str) -> Dict[str, Any]:
    """Get limits for a specific provider (case-insensitive).
    
    Supports provider detection from model names like:
    - "cerebras/glm-4" -> cerebras
    - "anthropic/claude-3" -> anthropic
    - "antigravity-oauth" -> antigravity
    - "synthetic-Kimi-K2.5" -> synthetic_glm
    """
    provider_lower = provider.lower()
    
    # Direct match
    if provider_lower in PROVIDER_LIMITS:
        return PROVIDER_LIMITS[provider_lower]
    
    # Pattern matching for OAuth providers
    if "antigravity" in provider_lower:
        return PROVIDER_LIMITS["antigravity"]
    if "claude_code" in provider_lower or "claude-code" in provider_lower:
        return PROVIDER_LIMITS["claude_code"]
    if "chatgpt" in provider_lower or "teams" in provider_lower:
        return PROVIDER_LIMITS["chatgpt_teams"]
    
    # Pattern matching for API providers
    # Synthetic.new models (Z.ai GLM, Kimi, Qwen, etc.)
    if "synthetic" in provider_lower or "z.ai" in provider_lower:
        return PROVIDER_LIMITS["synthetic_glm"]
    if "cerebras" in provider_lower:
        return PROVIDER_LIMITS["cerebras"]
    if "openrouter" in provider_lower:
        return PROVIDER_LIMITS["openrouter_free"]
    if "anthropic" in provider_lower or "claude" in provider_lower:
        return PROVIDER_LIMITS["anthropic"]
    if "openai" in provider_lower or "gpt" in provider_lower:
        return PROVIDER_LIMITS["openai"]
    
    return PROVIDER_LIMITS["default"]


@dataclass
class CompactionResult:
    """Result of a compaction operation."""
    original_tokens: int
    compacted_tokens: int
    original_messages: int
    compacted_messages: int
    strategy_used: str
    savings_percent: float
    
    @property
    def tokens_saved(self) -> int:
        return self.original_tokens - self.compacted_tokens


@dataclass
class TokenBudgetCheck:
    """Result of checking token budget."""
    current_tokens: int
    max_tokens: int
    usage_percent: float
    should_compact: bool
    should_block: bool
    recommended_action: str
    estimated_output_tokens: int
    
    
@dataclass
class SlidingWindowConfig:
    """Configuration for sliding window context management."""
    max_exchanges: int = 6
    preserve_system: bool = True
    preserve_tool_results: bool = True  # Keep pending tool results
    summarize_old: bool = True  # Summarize rather than drop


def detect_task_type(messages: List[Any]) -> TaskType:
    """Detect the likely task type from recent messages.
    
    Analyzes the last user message to determine what kind of response
    is expected, allowing for smarter max_tokens allocation.
    """
    if not messages:
        return TaskType.UNKNOWN
    
    # Find the last user message
    last_user_content = ""
    for msg in reversed(messages):
        if hasattr(msg, 'parts'):
            for part in msg.parts:
                if hasattr(part, 'content') and isinstance(part.content, str):
                    last_user_content = part.content.lower()
                    break
        if last_user_content:
            break
    
    if not last_user_content:
        return TaskType.UNKNOWN
    
    # Pattern matching for task types
    tool_patterns = [
        r'\bread\b.*file', r'\blist\b.*files?', r'\bgrep\b', r'\bsearch\b',
        r'\brun\b.*command', r'\bexecute\b', r'\bcheck\b.*status',
        r'\bwhat\s+is\b.*in', r'\bshow\s+me\b',
    ]
    
    code_gen_patterns = [
        r'\bwrite\b.*code', r'\bcreate\b.*function', r'\bimplement\b',
        r'\bgenerate\b', r'\bbuild\b.*module', r'\badd\b.*feature',
        r'\bfix\b.*bug', r'\bedit\b.*file', r'\bmodify\b', r'\brefactor\b',
    ]
    
    explanation_patterns = [
        r'\bexplain\b', r'\bwhy\b', r'\bhow\s+does\b', r'\bwhat\s+is\b',
        r'\bdescribe\b', r'\btell\s+me\b.*about',
    ]
    
    planning_patterns = [
        r'\bplan\b', r'\bdesign\b', r'\barchitect', r'\bstrategy\b',
        r'\bhow\s+should\b', r'\bwhat\s+approach\b', r'\bpropose\b',
    ]
    
    review_patterns = [
        r'\breview\b', r'\baudit\b', r'\bcheck\b.*code', r'\banalyze\b',
        r'\bvalidate\b', r'\bverify\b',
    ]
    
    for pattern in tool_patterns:
        if re.search(pattern, last_user_content):
            return TaskType.TOOL_CALL
    
    for pattern in code_gen_patterns:
        if re.search(pattern, last_user_content):
            return TaskType.CODE_GENERATION
    
    for pattern in explanation_patterns:
        if re.search(pattern, last_user_content):
            return TaskType.EXPLANATION
    
    for pattern in planning_patterns:
        if re.search(pattern, last_user_content):
            return TaskType.PLANNING
    
    for pattern in review_patterns:
        if re.search(pattern, last_user_content):
            return TaskType.REVIEW
    
    return TaskType.UNKNOWN


def get_optimal_max_tokens(
    messages: List[Any],
    provider: str = "default",
) -> int:
    """Get optimal max_tokens based on detected task type and provider.
    
    This prevents over-allocation which counts against TPM limits
    even if the actual response is shorter.
    
    Each provider has calibrated output limits:
    - Cerebras (boot_camp): Aggressive limits for free tier
    - OAuth providers (balanced): Reasonable limits for subscriptions
    - Paid APIs (maintenance): Generous limits for paid usage
    """
    limits = get_provider_limits(provider)
    task_type = detect_task_type(messages)
    
    max_output = limits["max_output_by_task"].get(
        task_type, 
        limits["default_max_output"]
    )
    
    return max_output


def check_token_budget(
    current_input_tokens: int,
    provider: str = "default",
    messages: List[Any] = None,
) -> TokenBudgetCheck:
    """Check if current context is within budget for the given provider.
    
    Returns actionable recommendations for token management.
    Works with ALL providers, not just Cerebras!
    """
    limits = get_provider_limits(provider)
    diet_mode = limits.get("diet_mode", "balanced")
    
    max_tokens = limits["max_input_tokens"]
    target_tokens = limits["target_input_tokens"]
    compaction_threshold = limits["compaction_threshold"]
    hard_limit = limits["hard_limit_threshold"]
    
    usage_percent = current_input_tokens / max_tokens if max_tokens > 0 else 1.0
    
    # Estimate output tokens based on task
    estimated_output = get_optimal_max_tokens(messages or [], provider)
    
    should_compact = usage_percent >= compaction_threshold
    should_block = usage_percent >= hard_limit
    
    # Diet-themed messages based on provider tier
    if diet_mode == "boot_camp":
        emoji = "🏋️"
    elif diet_mode == "maintenance":
        emoji = "🍽️"
    else:
        emoji = "🥗"
    
    if should_block:
        action = (
            f"🚫 {emoji} HARD LIMIT: Context at {usage_percent:.0%} ({current_input_tokens:,} tokens). "
            f"Must compact or truncate before proceeding. Run `/truncate 4` now."
        )
    elif should_compact:
        action = (
            f"⚠️ {emoji} COMPACT NEEDED: Context at {usage_percent:.0%} ({current_input_tokens:,} tokens). "
            f"Auto-compacting to stay under {target_tokens:,} target."
        )
    elif current_input_tokens > target_tokens:
        action = (
            f"📊 {emoji} Context at {usage_percent:.0%} ({current_input_tokens:,} tokens). "
            f"Consider `/truncate 6` to improve response quality."
        )
    else:
        action = f"✅ {emoji} Context healthy: {current_input_tokens:,} tokens ({usage_percent:.0%})"
    
    return TokenBudgetCheck(
        current_tokens=current_input_tokens,
        max_tokens=max_tokens,
        usage_percent=usage_percent,
        should_compact=should_compact,
        should_block=should_block,
        recommended_action=action,
        estimated_output_tokens=estimated_output,
    )


# Backward compatibility alias
def check_cerebras_budget(
    current_input_tokens: int,
    messages: List[Any] = None,
) -> TokenBudgetCheck:
    """DEPRECATED: Use check_token_budget(tokens, provider='cerebras') instead.
    
    Kept for backward compatibility with existing code.
    """
    return check_token_budget(current_input_tokens, "cerebras", messages)


def count_exchanges(messages: List[Any]) -> int:
    """Count user-assistant exchange pairs in message history."""
    user_count = 0
    assistant_count = 0
    
    for msg in messages:
        kind = getattr(msg, 'kind', '')
        if kind == 'request':
            user_count += 1
        elif kind == 'response':
            assistant_count += 1
    
    return min(user_count, assistant_count)


def _extract_tool_call_ids(msg: Any) -> set:
    """Extract tool_call IDs from ToolCallPart in response messages.
    
    In pydantic-ai:
    - ModelResponse contains ToolCallPart (part_kind='tool-call')
    - These are the source of tool_call_ids that tool results reference
    """
    ids = set()
    # Only look in response messages (where ToolCallPart lives)
    kind = getattr(msg, 'kind', '')
    if kind != 'response':
        return ids
    
    if hasattr(msg, 'parts'):
        for part in msg.parts:
            part_kind = getattr(part, 'part_kind', '')
            # ToolCallPart has part_kind='tool-call'
            if part_kind == 'tool-call' and hasattr(part, 'tool_call_id'):
                tc_id = part.tool_call_id
                if tc_id:
                    ids.add(tc_id)
    return ids


def _get_tool_result_id(msg: Any) -> Optional[str]:
    """Get the tool_call_id that this ToolReturnPart responds to.
    
    In pydantic-ai:
    - ModelRequest can contain ToolReturnPart (part_kind='tool-return')
    - Each ToolReturnPart has tool_call_id referencing a ToolCallPart
    """
    if hasattr(msg, 'parts'):
        for part in msg.parts:
            part_kind = getattr(part, 'part_kind', '')
            # ToolReturnPart has part_kind='tool-return'
            if part_kind == 'tool-return' and hasattr(part, 'tool_call_id'):
                return part.tool_call_id
    return None


def _is_tool_result_message(msg: Any) -> bool:
    """Check if a message contains ToolReturnPart(s).
    
    In pydantic-ai:
    - ModelRequest (kind='request') can contain ToolReturnPart
    - ToolReturnPart has part_kind='tool-return'
    """
    if not hasattr(msg, 'parts'):
        return False
    
    for part in msg.parts:
        part_kind = getattr(part, 'part_kind', '')
        if part_kind == 'tool-return':
            return True
    return False


def apply_sliding_window(
    messages: List[Any],
    config: SlidingWindowConfig = None,
    estimate_tokens_fn=None,
) -> Tuple[List[Any], CompactionResult]:
    """Apply sliding window to keep only recent exchanges.
    
    Keeps the last N exchange pairs while preserving:
    - System messages (if configured)
    - Tool call/result chains (never orphan tool results)
    
    CRITICAL: Tool results MUST have their corresponding assistant message
    with tool_calls in the kept messages, or the API will reject with 422.
    """
    if config is None:
        config = SlidingWindowConfig(max_exchanges=CEREBRAS_LIMITS["max_exchanges"])
    
    if estimate_tokens_fn is None:
        # Simple fallback token estimation
        def estimate_tokens_fn(msg):
            content = ""
            if hasattr(msg, 'parts'):
                for part in msg.parts:
                    if hasattr(part, 'content'):
                        content += str(part.content)
            return len(content) // 4
    
    original_count = len(messages)
    original_tokens = sum(estimate_tokens_fn(m) for m in messages)
    
    if count_exchanges(messages) <= config.max_exchanges:
        # Already within limit
        return messages, CompactionResult(
            original_tokens=original_tokens,
            compacted_tokens=original_tokens,
            original_messages=original_count,
            compacted_messages=original_count,
            strategy_used="none_needed",
            savings_percent=0.0,
        )
    
    # Separate messages by type
    system_messages = []
    exchanges = []  # Each exchange is a list of messages starting with user request
    current_exchange = []
    
    for msg in messages:
        kind = getattr(msg, 'kind', '')
        
        if kind == 'system-prompt':
            system_messages.append(msg)
        elif kind == 'request':
            if current_exchange:
                exchanges.append(current_exchange)
            current_exchange = [msg]
        else:
            current_exchange.append(msg)
    
    # Don't forget the last exchange
    if current_exchange:
        exchanges.append(current_exchange)
    
    # Keep only the last N exchanges
    kept_exchanges = exchanges[-config.max_exchanges:]
    
    # CRITICAL FIX: Collect all tool_call IDs from kept messages FIRST
    # Then filter out any tool results that reference missing tool_calls
    valid_tool_call_ids = set()
    for exchange in kept_exchanges:
        for msg in exchange:
            valid_tool_call_ids.update(_extract_tool_call_ids(msg))
    
    # Now filter each exchange to remove orphaned tool results
    cleaned_exchanges = []
    for exchange in kept_exchanges:
        cleaned = []
        for msg in exchange:
            if _is_tool_result_message(msg):
                result_id = _get_tool_result_id(msg)
                if result_id and result_id not in valid_tool_call_ids:
                    # Orphaned tool result - skip it
                    continue
            cleaned.append(msg)
        cleaned_exchanges.append(cleaned)
    
    # Rebuild message list
    compacted = []
    
    if config.preserve_system:
        compacted.extend(system_messages)
    
    for exchange in cleaned_exchanges:
        compacted.extend(exchange)
    
    compacted_tokens = sum(estimate_tokens_fn(m) for m in compacted)
    savings = (
        (original_tokens - compacted_tokens) / original_tokens * 100
        if original_tokens > 0
        else 0.0
    )
    
    return compacted, CompactionResult(
        original_tokens=original_tokens,
        compacted_tokens=compacted_tokens,
        original_messages=original_count,
        compacted_messages=len(compacted),
        strategy_used=f"sliding_window_{config.max_exchanges}",
        savings_percent=savings,
    )


def should_auto_compact(
    messages: List[Any],
    provider: str,
    estimate_tokens_fn=None,
) -> Tuple[bool, str]:
    """Determine if auto-compaction should trigger.
    
    Returns:
        Tuple of (should_compact, reason)
    """
    if provider.lower() != "cerebras":
        return False, "Not Cerebras provider"
    
    if estimate_tokens_fn is None:
        def estimate_tokens_fn(msg):
            content = ""
            if hasattr(msg, 'parts'):
                for part in msg.parts:
                    if hasattr(part, 'content'):
                        content += str(part.content)
            return len(content) // 4
    
    current_tokens = sum(estimate_tokens_fn(m) for m in messages)
    exchange_count = count_exchanges(messages)
    
    # Check token threshold
    budget_check = check_cerebras_budget(current_tokens, messages)
    if budget_check.should_compact:
        return True, f"Token usage at {budget_check.usage_percent:.0%}"
    
    # Check exchange count
    max_exchanges = CEREBRAS_LIMITS["max_exchanges"]
    if exchange_count > max_exchanges:
        return True, f"Exchange count ({exchange_count}) exceeds max ({max_exchanges})"
    
    return False, "Within limits"


def get_cerebras_model_settings_override(
    messages: List[Any],
    base_max_tokens: int = None,
) -> Dict[str, Any]:
    """Get Cerebras-optimized model settings.
    
    Returns settings dict to merge with base model settings.
    """
    optimal_output = get_optimal_max_tokens(messages, "cerebras")
    
    overrides = {
        "max_tokens": min(optimal_output, base_max_tokens or 4000),
    }
    
    return overrides


# Convenience functions for quick integration

def cerebras_pre_request_hook(
    messages: List[Any],
    estimate_tokens_fn=None,
) -> Tuple[List[Any], Dict[str, Any], str]:
    """Pre-request hook for Cerebras optimization.
    
    Call this before sending a request to:
    1. Auto-compact if needed
    2. Get optimal max_tokens
    3. Get status message for user
    
    Returns:
        Tuple of (processed_messages, settings_override, status_message)
    """
    if estimate_tokens_fn is None:
        def estimate_tokens_fn(msg):
            content = ""
            if hasattr(msg, 'parts'):
                for part in msg.parts:
                    if hasattr(part, 'content'):
                        content += str(part.content)
            return len(content) // 4
    
    # Check if compaction needed
    should_compact, reason = should_auto_compact(
        messages, "cerebras", estimate_tokens_fn
    )
    
    status_parts = []
    processed_messages = messages
    
    if should_compact:
        processed_messages, result = apply_sliding_window(
            messages,
            estimate_tokens_fn=estimate_tokens_fn,
        )
        status_parts.append(
            f"🧹 Auto-compacted: {result.original_tokens:,} → {result.compacted_tokens:,} tokens "
            f"({result.savings_percent:.0f}% saved)"
        )
    
    # Get optimal settings
    settings_override = get_cerebras_model_settings_override(processed_messages)
    
    # Get budget status
    current_tokens = sum(estimate_tokens_fn(m) for m in processed_messages)
    budget = check_cerebras_budget(current_tokens, processed_messages)
    
    if not should_compact:
        status_parts.append(budget.recommended_action)
    
    status_parts.append(f"📤 max_tokens: {settings_override['max_tokens']}")
    
    return processed_messages, settings_override, " | ".join(status_parts)


# Export key items - Universal Token Slimmer API
__all__ = [
    # Core types
    "TaskType",
    "CompactionResult",
    "TokenBudgetCheck",
    "SlidingWindowConfig",
    
    # Provider configuration (universal)
    "PROVIDER_LIMITS",
    "get_provider_limits",
    
    # Universal functions
    "detect_task_type",
    "get_optimal_max_tokens",
    "check_token_budget",  # NEW: Provider-aware budget check
    "apply_sliding_window",
    "should_auto_compact",
    "count_exchanges",
    
    # Backward compatibility (Cerebras-specific aliases)
    "CEREBRAS_LIMITS",  # Alias for PROVIDER_LIMITS["cerebras"]
    "check_cerebras_budget",  # Alias for check_token_budget(..., "cerebras")
    "get_cerebras_model_settings_override",
    "cerebras_pre_request_hook",
]
