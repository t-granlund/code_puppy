"""Cerebras Token Optimizer - DEPRECATED, use token_slimmer instead.

This module is maintained for backward compatibility only.
All functionality has been moved to token_slimmer.py which provides
universal, provider-aware token optimization.

Usage migration:
    # Old (Cerebras-only):
    from code_puppy.tools.cerebras_optimizer import check_cerebras_budget
    
    # New (Universal):
    from code_puppy.tools.token_slimmer import check_token_budget
    result = check_token_budget(tokens, provider="cerebras")  # or any provider
"""

# Re-export everything from token_slimmer for backward compatibility
from code_puppy.tools.token_slimmer import (
    # Core types
    TaskType,
    CompactionResult,
    TokenBudgetCheck,
    SlidingWindowConfig,
    
    # Provider configuration
    PROVIDER_LIMITS,
    get_provider_limits,
    
    # Universal functions
    detect_task_type,
    get_optimal_max_tokens,
    check_token_budget,
    apply_sliding_window,
    should_auto_compact,
    count_exchanges,
    
    # Backward compatibility aliases
    CEREBRAS_LIMITS,
    check_cerebras_budget,
    get_cerebras_model_settings_override,
    cerebras_pre_request_hook,
)

__all__ = [
    "TaskType",
    "CEREBRAS_LIMITS",
    "PROVIDER_LIMITS",
    "CompactionResult",
    "TokenBudgetCheck",
    "SlidingWindowConfig",
    "detect_task_type",
    "get_optimal_max_tokens",
    "check_cerebras_budget",
    "check_token_budget",
    "get_provider_limits",
    "apply_sliding_window",
    "should_auto_compact",
    "count_exchanges",
    "get_cerebras_model_settings_override",
    "cerebras_pre_request_hook",
]
