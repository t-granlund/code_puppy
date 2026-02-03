"""Core infrastructure for hybrid inference and token efficiency.

This module provides:
- TokenBudgetManager: Rate limiting and token bucket management
- ModelRouter: Intelligent task-to-model routing
- ContextCompressor: AST pruning and history truncation
- SmartContextLoader: Artifact caching to prevent duplicate reads
- PackGovernor: Concurrent agent execution management
- RateLimitFailover: Automatic failover on 429 errors
- AgentOrchestrator: Workload-aware agent coordination
- CircuitBreaker: Protection against cascading failures
- ResponseCache: Intelligent response caching with TTL
- PromptCompressor: Prompt optimization to reduce tokens
- CostBudgetEnforcer: Cost limits and alerting
- ModelMetricsTracker: Performance analytics
- SmartModelSelector: Multi-factor model selection
- RequestPriorityQueue: Request prioritization
- PerformanceDashboard: System health monitoring
- ConnectionPoolManager: HTTP connection management
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
from .agent_orchestration import (
    AgentOrchestrator,
    get_orchestrator,
    get_model_for_agent,
    get_failover_chain_for_agent,
    get_workload_for_agent,
    create_failover_model_for_agent,
    ORCHESTRATION_HIERARCHY,
)

# New robustness and performance modules
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerManager,
    CircuitState,
    CircuitOpenError,
    ProviderHealthChecker,
    get_circuit_manager,
    check_circuit,
    with_circuit_breaker,
)
from .response_cache import (
    ResponseCache,
    PromptCompressor,
    CacheEntry,
    CompressionResult,
    get_response_cache,
    get_prompt_compressor,
    cached_completion,
)
from .cost_budget import (
    CostBudgetEnforcer,
    CostAlert,
    AlertSeverity,
    AlertType,
    get_cost_enforcer,
    check_and_record_cost,
)
from .model_metrics import (
    ModelMetricsTracker,
    AggregatedMetrics,
    RequestMetric,
    MetricsContext,
    get_metrics_tracker,
    track_request,
)
from .credential_availability import (
    CredentialChecker,
    get_credential_checker,
    has_valid_credentials,
    get_available_models_with_credentials,
    filter_workload_chain,
    get_credential_status,
    invalidate_credential_cache,
)
from .smart_selection import (
    SmartModelSelector,
    RequestPriorityQueue,
    DynamicLoadBalancer,
    RequestPriority,
    SelectionStrategy,
    ModelScore,
    QueueFullError,
    get_model_selector,
    select_best_model,
)
from .performance_dashboard import (
    PerformanceDashboard,
    SystemHealth,
    HealthIndicator,
    get_dashboard,
    get_health_status,
    get_performance_metrics,
    print_dashboard_summary,
)
from .connection_pool import (
    ConnectionPool,
    ConnectionPoolManager,
    StreamingResponse,
    StreamingClient,
    PoolConfig,
    get_pool_manager,
    get_provider_pool,
    streaming_completion,
    cleanup_connections,
)

# BART System - Belief-Augmented Reasoning & Tasking (Plan → Execute → Verify)
from .epistemic_orchestrator import (
    EpistemicOrchestrator,
    EpistemicStateArtifact,
    ContextCurator,
    RalphLoopVerifier,
    MinimumViableContext,
    VerificationReport,
    VerificationResult,
    OrchestratorPhase,
    # Epistemic models
    Assumption,
    Hypothesis,
    Constraint,
    Gap,
    Goal,
    Epic,
    Phase,
    Milestone,
    Checkpoint,
    ConfidenceLevel,
    GapSeverity,
    PhaseStatus,
)

# Husky Execution Layer - Cerebras GLM 4.7 Optimization
from .husky_execution import (
    HuskyExecutionLayer,
    CerebrasGLMSettings,
    GLMPromptOptimizer,
    TaskDecomposer,
    ExecutionRequest,
    ExecutionResult,
    ReasoningMode,
    ThinkingMemory,
)

__all__ = [
    # Token budget management
    "TokenBudgetManager",
    "smart_retry",
    # Model routing
    "ModelRouter",
    "TaskComplexity",
    "ModelTier",
    "TaskType",
    # Context management
    "ContextCompressor",
    "SmartContextLoader",
    "ContextManager",
    # Pack governance
    "PackGovernor",
    "AgentRole",
    "GovernorConfig",
    "acquire_agent_slot",
    "release_agent_slot",
    "get_governor_status",
    # Rate limit failover
    "RateLimitFailover",
    "get_failover_manager",
    "with_rate_limit_failover",
    "WorkloadType",
    # Agent orchestration
    "AgentOrchestrator",
    "get_orchestrator",
    "get_model_for_agent",
    "get_failover_chain_for_agent",
    "get_workload_for_agent",
    "create_failover_model_for_agent",
    "ORCHESTRATION_HIERARCHY",
    # Circuit breaker
    "CircuitBreaker",
    "CircuitBreakerManager",
    "CircuitState",
    "CircuitOpenError",
    "ProviderHealthChecker",
    "get_circuit_manager",
    "check_circuit",
    "with_circuit_breaker",
    # Response caching
    "ResponseCache",
    "PromptCompressor",
    "CacheEntry",
    "CompressionResult",
    "get_response_cache",
    "get_prompt_compressor",
    "cached_completion",
    # Cost budget
    "CostBudgetEnforcer",
    "CostAlert",
    "AlertSeverity",
    "AlertType",
    "get_cost_enforcer",
    "check_and_record_cost",
    # Model metrics
    "ModelMetricsTracker",
    "AggregatedMetrics",
    "RequestMetric",
    "MetricsContext",
    "get_metrics_tracker",
    "track_request",
    # Smart selection
    "SmartModelSelector",
    "RequestPriorityQueue",
    "DynamicLoadBalancer",
    "RequestPriority",
    "SelectionStrategy",
    "ModelScore",
    "QueueFullError",
    "get_model_selector",
    "select_best_model",
    # Performance dashboard
    "PerformanceDashboard",
    "SystemHealth",
    "HealthIndicator",
    "get_dashboard",
    "get_health_status",
    "get_performance_metrics",
    "print_dashboard_summary",
    # Connection pooling
    "ConnectionPool",
    "ConnectionPoolManager",
    "StreamingResponse",
    "StreamingClient",
    "PoolConfig",
    "get_pool_manager",
    "get_provider_pool",
    "streaming_completion",
    "cleanup_connections",
    # BART Orchestration System
    "EpistemicOrchestrator",
    "EpistemicStateArtifact",
    "ContextCurator",
    "RalphLoopVerifier",
    "MinimumViableContext",
    "VerificationReport",
    "VerificationResult",
    "OrchestratorPhase",
    "Assumption",
    "Hypothesis",
    "Constraint",
    "Gap",
    "Goal",
    "Epic",
    "Phase",
    "Milestone",
    "Checkpoint",
    "ConfidenceLevel",
    "GapSeverity",
    "PhaseStatus",
    # Husky Execution Layer
    "HuskyExecutionLayer",
    "CerebrasGLMSettings",
    "GLMPromptOptimizer",
    "TaskDecomposer",
    "ExecutionRequest",
    "ExecutionResult",
    "ReasoningMode",
    "ThinkingMemory",
]
