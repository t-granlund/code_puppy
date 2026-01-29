"""Cerebras-specific token optimization strategies.

Implements aggressive token management for Cerebras Code Pro:
- Auto-compaction at 50% context usage (vs default 85%)
- Sliding window with max 6 exchanges
- Smart max_tokens based on task type
- Provider-specific output limits

Based on analysis showing 98:1 input:output ratio with avg 28.5K tokens/request.
Target: Reduce to <15K tokens/request for 50%+ savings.
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


# Cerebras-specific limits (more aggressive than default)
CEREBRAS_LIMITS = {
    "compaction_threshold": 0.50,  # Trigger compaction at 50% (vs 85% default)
    "hard_limit_threshold": 0.70,  # Hard block at 70% (vs 95% default)
    "max_input_tokens": 50_000,  # Cerebras Pro limit
    "target_input_tokens": 25_000,  # Target to stay under
    "max_exchanges": 6,  # Keep only last 6 user-assistant pairs
    "max_output_by_task": {
        TaskType.TOOL_CALL: 500,
        TaskType.CODE_GENERATION: 4000,
        TaskType.EXPLANATION: 2000,
        TaskType.FILE_READ: 200,
        TaskType.PLANNING: 3000,
        TaskType.REVIEW: 2000,
        TaskType.UNKNOWN: 2000,
    },
    "default_max_output": 2000,
}


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
    provider: str = "cerebras",
) -> int:
    """Get optimal max_tokens based on detected task type.
    
    This prevents over-allocation which counts against TPM limits
    even if the actual response is shorter.
    """
    if provider.lower() != "cerebras":
        # Default for non-Cerebras providers
        return 4000
    
    task_type = detect_task_type(messages)
    max_output = CEREBRAS_LIMITS["max_output_by_task"].get(
        task_type, 
        CEREBRAS_LIMITS["default_max_output"]
    )
    
    return max_output


def check_cerebras_budget(
    current_input_tokens: int,
    messages: List[Any] = None,
) -> TokenBudgetCheck:
    """Check if current context is within Cerebras budget.
    
    Returns actionable recommendations for token management.
    """
    max_tokens = CEREBRAS_LIMITS["max_input_tokens"]
    target_tokens = CEREBRAS_LIMITS["target_input_tokens"]
    compaction_threshold = CEREBRAS_LIMITS["compaction_threshold"]
    hard_limit = CEREBRAS_LIMITS["hard_limit_threshold"]
    
    usage_percent = current_input_tokens / max_tokens if max_tokens > 0 else 1.0
    
    # Estimate output tokens based on task
    estimated_output = get_optimal_max_tokens(messages or [], "cerebras")
    
    should_compact = usage_percent >= compaction_threshold
    should_block = usage_percent >= hard_limit
    
    if should_block:
        action = (
            f"🚫 HARD LIMIT: Context at {usage_percent:.0%} ({current_input_tokens:,} tokens). "
            f"Must compact or truncate before proceeding. Run `/truncate 4` now."
        )
    elif should_compact:
        action = (
            f"⚠️ COMPACT NEEDED: Context at {usage_percent:.0%} ({current_input_tokens:,} tokens). "
            f"Auto-compacting to stay under {target_tokens:,} target."
        )
    elif current_input_tokens > target_tokens:
        action = (
            f"📊 Context at {usage_percent:.0%} ({current_input_tokens:,} tokens). "
            f"Consider `/truncate 6` to improve response quality."
        )
    else:
        action = f"✅ Context healthy: {current_input_tokens:,} tokens ({usage_percent:.0%})"
    
    return TokenBudgetCheck(
        current_tokens=current_input_tokens,
        max_tokens=max_tokens,
        usage_percent=usage_percent,
        should_compact=should_compact,
        should_block=should_block,
        recommended_action=action,
        estimated_output_tokens=estimated_output,
    )


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


def apply_sliding_window(
    messages: List[Any],
    config: SlidingWindowConfig = None,
    estimate_tokens_fn=None,
) -> Tuple[List[Any], CompactionResult]:
    """Apply sliding window to keep only recent exchanges.
    
    Keeps the last N exchange pairs while preserving:
    - System messages (if configured)
    - Tool call/result chains (never orphan tool results)
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
    
    # CRITICAL: Check for orphaned tool results at the start of kept messages
    # Tool results must have a preceding assistant message with tool_calls
    if kept_exchanges:
        first_exchange = kept_exchanges[0]
        # Check if first message after user request is a tool result
        cleaned_first_exchange = []
        drop_tool_results = True  # Drop leading tool results until we see assistant with tool_calls
        
        for msg in first_exchange:
            kind = getattr(msg, 'kind', '')
            
            if kind == 'request':
                cleaned_first_exchange.append(msg)
                continue
            
            # Check if this is a tool result (kind varies by implementation)
            is_tool_result = (
                kind == 'tool-result' or 
                kind == 'tool' or
                (hasattr(msg, 'role') and getattr(msg, 'role', '') == 'tool')
            )
            
            # Check if this is an assistant message with tool_calls
            has_tool_calls = False
            if hasattr(msg, 'parts'):
                for part in msg.parts:
                    if hasattr(part, 'tool_name') or hasattr(part, 'tool_calls'):
                        has_tool_calls = True
                        break
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                has_tool_calls = True
            
            if is_tool_result and drop_tool_results:
                # Skip orphaned tool result
                continue
            elif has_tool_calls or kind == 'response':
                drop_tool_results = False  # Now we've seen an assistant, tool results are OK
                cleaned_first_exchange.append(msg)
            else:
                cleaned_first_exchange.append(msg)
        
        kept_exchanges[0] = cleaned_first_exchange
    
    # Rebuild message list
    compacted = []
    
    if config.preserve_system:
        compacted.extend(system_messages)
    
    for exchange in kept_exchanges:
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


# Export key items
__all__ = [
    "TaskType",
    "CEREBRAS_LIMITS",
    "CompactionResult",
    "TokenBudgetCheck",
    "SlidingWindowConfig",
    "detect_task_type",
    "get_optimal_max_tokens",
    "check_cerebras_budget",
    "apply_sliding_window",
    "should_auto_compact",
    "get_cerebras_model_settings_override",
    "cerebras_pre_request_hook",
]
