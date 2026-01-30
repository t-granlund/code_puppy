"""Core infrastructure for hybrid inference and token efficiency.

This module provides:
- TokenBudgetManager: Rate limiting and token bucket management
- ModelRouter: Intelligent task-to-model routing
- ContextCompressor: AST pruning and history truncation
- SmartContextLoader: Artifact caching to prevent duplicate reads
- PackGovernor: Concurrent agent execution management
- RateLimitFailover: Automatic failover on 429 errors
"""

from .token_budget import TokenBudgetManager, smart_retry
from .model_router import ModelRouter, TaskComplexity, ModelTier, TaskType
from .context_compressor import ContextCompressor
from .smart_context_loader import SmartContextLoader, ContextManager
from .pack_governor import (
    PackGovernor,
    AgentRole,
    GovernorConfig,
    acquire_agent_slot,
    release_agent_slot,
    get_governor_status,
)
from .rate_limit_failover import (
    RateLimitFailover,
    get_failover_manager,
    with_rate_limit_failover,
    WorkloadType,
)

__all__ = [
    "TokenBudgetManager",
    "smart_retry",
    "ModelRouter",
    "TaskComplexity",
    "ModelTier",
    "TaskType",
    "ContextCompressor",
    "SmartContextLoader",
    "ContextManager",
    "PackGovernor",
    "AgentRole",
    "GovernorConfig",
    "acquire_agent_slot",
    "release_agent_slot",
    "get_governor_status",
    "RateLimitFailover",
    "get_failover_manager",
    "with_rate_limit_failover",
    "WorkloadType",
]
