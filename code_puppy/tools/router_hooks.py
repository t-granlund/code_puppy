"""Router Hooks for Code Puppy Model Pool Management.

AUDIT-1.1 Part I compliance:
- Model pool config schema
- Task class routing hint interface
- No auto-routing yet (deferred)
- Provider capability declarations

This module provides:
1. Model pool configuration with per-provider settings
2. Task classification for routing hints
3. Capability declarations for models
4. Foundation for future auto-routing
"""

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from code_puppy.config import get_value


# ============================================================================
# Task Classification
# ============================================================================

class TaskClass(Enum):
    """Classification of task types for routing hints.
    
    These are hints that can be used to select appropriate models.
    Currently for manual selection; auto-routing is deferred.
    """
    # Code generation tasks
    CODE_GENERATION = "code_generation"
    CODE_REFACTOR = "code_refactor"
    CODE_REVIEW = "code_review"
    BUG_FIX = "bug_fix"
    
    # Analysis tasks
    CODE_ANALYSIS = "code_analysis"
    ARCHITECTURE_REVIEW = "architecture_review"
    SECURITY_AUDIT = "security_audit"
    
    # Documentation tasks
    DOCUMENTATION = "documentation"
    COMMENT_GENERATION = "comment_generation"
    README_GENERATION = "readme_generation"
    
    # Testing tasks
    TEST_GENERATION = "test_generation"
    TEST_REVIEW = "test_review"
    
    # Planning tasks
    TASK_PLANNING = "task_planning"
    BREAKDOWN = "breakdown"
    
    # Quick tasks (suitable for fast/cheap models)
    SIMPLE_QUERY = "simple_query"
    FORMAT_FIX = "format_fix"
    IMPORT_FIX = "import_fix"
    
    # Complex tasks (may need premium models)
    COMPLEX_REASONING = "complex_reasoning"
    MULTI_FILE_EDIT = "multi_file_edit"
    LARGE_REFACTOR = "large_refactor"


class ModelCapability(Enum):
    """Capabilities that models may have."""
    CODE_COMPLETION = "code_completion"
    CHAT = "chat"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    LONG_CONTEXT = "long_context"
    FAST_INFERENCE = "fast_inference"
    STRUCTURED_OUTPUT = "structured_output"
    STREAMING = "streaming"


# ============================================================================
# Model Pool Configuration
# ============================================================================

@dataclass
class ModelConfig:
    """Configuration for a single model."""
    name: str
    provider: str
    model_id: str
    
    # Limits
    max_input_tokens: int = 30000
    max_output_tokens: int = 4096
    requests_per_minute: int = 60
    tokens_per_minute: int = 100000
    
    # Capabilities
    capabilities: Set[ModelCapability] = field(default_factory=set)
    
    # Task suitability (higher = better)
    task_scores: Dict[TaskClass, float] = field(default_factory=dict)
    
    # Cost info (relative units, 0-100)
    input_cost_score: int = 50
    output_cost_score: int = 50
    
    # Operational
    enabled: bool = True
    priority: int = 50  # Higher = prefer this model
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "provider": self.provider,
            "model_id": self.model_id,
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
            "requests_per_minute": self.requests_per_minute,
            "tokens_per_minute": self.tokens_per_minute,
            "capabilities": [c.value for c in self.capabilities],
            "task_scores": {k.value: v for k, v in self.task_scores.items()},
            "input_cost_score": self.input_cost_score,
            "output_cost_score": self.output_cost_score,
            "enabled": self.enabled,
            "priority": self.priority,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelConfig":
        """Create from dictionary."""
        capabilities = set()
        for cap in data.get("capabilities", []):
            try:
                capabilities.add(ModelCapability(cap))
            except ValueError:
                pass
        
        task_scores = {}
        for task, score in data.get("task_scores", {}).items():
            try:
                task_scores[TaskClass(task)] = float(score)
            except (ValueError, TypeError):
                pass
        
        return cls(
            name=data.get("name", ""),
            provider=data.get("provider", ""),
            model_id=data.get("model_id", ""),
            max_input_tokens=data.get("max_input_tokens", 30000),
            max_output_tokens=data.get("max_output_tokens", 4096),
            requests_per_minute=data.get("requests_per_minute", 60),
            tokens_per_minute=data.get("tokens_per_minute", 100000),
            capabilities=capabilities,
            task_scores=task_scores,
            input_cost_score=data.get("input_cost_score", 50),
            output_cost_score=data.get("output_cost_score", 50),
            enabled=data.get("enabled", True),
            priority=data.get("priority", 50),
        )


@dataclass
class ModelPool:
    """Pool of available models with routing configuration."""
    models: List[ModelConfig] = field(default_factory=list)
    default_model: str = ""
    fallback_model: str = ""
    
    # Pool-level settings
    enable_auto_routing: bool = False  # Deferred feature
    enable_fallback: bool = True
    max_retries_before_fallback: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "models": [m.to_dict() for m in self.models],
            "default_model": self.default_model,
            "fallback_model": self.fallback_model,
            "enable_auto_routing": self.enable_auto_routing,
            "enable_fallback": self.enable_fallback,
            "max_retries_before_fallback": self.max_retries_before_fallback,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelPool":
        """Create from dictionary."""
        models = [ModelConfig.from_dict(m) for m in data.get("models", [])]
        return cls(
            models=models,
            default_model=data.get("default_model", ""),
            fallback_model=data.get("fallback_model", ""),
            enable_auto_routing=data.get("enable_auto_routing", False),
            enable_fallback=data.get("enable_fallback", True),
            max_retries_before_fallback=data.get("max_retries_before_fallback", 3),
        )
    
    def get_model(self, name: str) -> Optional[ModelConfig]:
        """Get a model by name."""
        for model in self.models:
            if model.name == name:
                return model
        return None
    
    def get_enabled_models(self) -> List[ModelConfig]:
        """Get all enabled models."""
        return [m for m in self.models if m.enabled]
    
    def get_models_for_capability(
        self, capability: ModelCapability
    ) -> List[ModelConfig]:
        """Get models with a specific capability."""
        return [
            m for m in self.models
            if m.enabled and capability in m.capabilities
        ]


# ============================================================================
# Default Model Pool
# ============================================================================

DEFAULT_MODEL_POOL = ModelPool(
    models=[
        ModelConfig(
            name="cerebras-code-pro",
            provider="cerebras",
            model_id="qwen-3-32b",
            max_input_tokens=50000,
            max_output_tokens=8192,
            requests_per_minute=50,
            tokens_per_minute=1000000,
            capabilities={
                ModelCapability.CODE_COMPLETION,
                ModelCapability.CHAT,
                ModelCapability.FAST_INFERENCE,
                ModelCapability.STREAMING,
            },
            task_scores={
                TaskClass.CODE_GENERATION: 0.9,
                TaskClass.BUG_FIX: 0.85,
                TaskClass.SIMPLE_QUERY: 0.95,
                TaskClass.FORMAT_FIX: 0.9,
                TaskClass.IMPORT_FIX: 0.9,
            },
            input_cost_score=10,  # Very cheap (free tier)
            output_cost_score=10,
            priority=80,
        ),
        ModelConfig(
            name="claude-sonnet",
            provider="anthropic",
            model_id="claude-sonnet-4-20250514",
            max_input_tokens=180000,
            max_output_tokens=8192,
            requests_per_minute=60,
            tokens_per_minute=100000,
            capabilities={
                ModelCapability.CODE_COMPLETION,
                ModelCapability.CHAT,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.LONG_CONTEXT,
                ModelCapability.STRUCTURED_OUTPUT,
                ModelCapability.STREAMING,
            },
            task_scores={
                TaskClass.COMPLEX_REASONING: 0.95,
                TaskClass.ARCHITECTURE_REVIEW: 0.9,
                TaskClass.SECURITY_AUDIT: 0.85,
                TaskClass.LARGE_REFACTOR: 0.9,
                TaskClass.MULTI_FILE_EDIT: 0.9,
            },
            input_cost_score=60,
            output_cost_score=70,
            priority=70,
        ),
        ModelConfig(
            name="gpt-4o",
            provider="openai",
            model_id="gpt-4o",
            max_input_tokens=120000,
            max_output_tokens=16384,
            requests_per_minute=60,
            tokens_per_minute=100000,
            capabilities={
                ModelCapability.CODE_COMPLETION,
                ModelCapability.CHAT,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.VISION,
                ModelCapability.LONG_CONTEXT,
                ModelCapability.STRUCTURED_OUTPUT,
                ModelCapability.STREAMING,
            },
            task_scores={
                TaskClass.CODE_GENERATION: 0.85,
                TaskClass.DOCUMENTATION: 0.9,
                TaskClass.TEST_GENERATION: 0.85,
            },
            input_cost_score=50,
            output_cost_score=60,
            priority=60,
        ),
    ],
    default_model="cerebras-code-pro",
    fallback_model="gpt-4o",
    enable_auto_routing=False,
    enable_fallback=True,
)


# ============================================================================
# Pool Management
# ============================================================================

_pool_cache: Optional[ModelPool] = None


def load_model_pool(config_path: Optional[str] = None) -> ModelPool:
    """Load model pool from configuration.
    
    Args:
        config_path: Path to pool config file.
                     Defaults to .codepuppy/model_pool.json
                     
    Returns:
        ModelPool configuration.
    """
    global _pool_cache
    
    if config_path is None:
        config_path = os.path.join(os.getcwd(), ".codepuppy", "model_pool.json")
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            _pool_cache = ModelPool.from_dict(data)
            return _pool_cache
        except (json.JSONDecodeError, IOError):
            pass
    
    # Return default pool
    _pool_cache = DEFAULT_MODEL_POOL
    return _pool_cache


def save_model_pool(pool: ModelPool, config_path: Optional[str] = None):
    """Save model pool configuration.
    
    Args:
        pool: ModelPool to save.
        config_path: Path to save to.
    """
    if config_path is None:
        config_path = os.path.join(os.getcwd(), ".codepuppy", "model_pool.json")
    
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(pool.to_dict(), f, indent=2)


def get_model_pool() -> ModelPool:
    """Get the current model pool.
    
    Returns:
        ModelPool configuration.
    """
    global _pool_cache
    if _pool_cache is None:
        return load_model_pool()
    return _pool_cache


# ============================================================================
# Routing Hints
# ============================================================================

@dataclass
class RoutingHint:
    """A hint for model selection based on task characteristics.
    
    This is a manual hint interface - actual routing decisions
    are made by the user or agent, not automatically.
    """
    task_class: TaskClass
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    requires_capabilities: Set[ModelCapability] = field(default_factory=set)
    prefer_fast: bool = False
    prefer_cheap: bool = False
    prefer_accurate: bool = False
    context: str = ""  # Additional context for decision
    
    def get_recommended_models(self, pool: Optional[ModelPool] = None) -> List[str]:
        """Get recommended models based on this hint.
        
        Note: This is a suggestion, not auto-routing.
        
        Args:
            pool: Model pool to search.
            
        Returns:
            List of model names, in preference order.
        """
        if pool is None:
            pool = get_model_pool()
        
        candidates = []
        
        for model in pool.get_enabled_models():
            # Check capability requirements
            if self.requires_capabilities:
                if not self.requires_capabilities.issubset(model.capabilities):
                    continue
            
            # Check token limits
            if self.estimated_input_tokens > model.max_input_tokens:
                continue
            if self.estimated_output_tokens > model.max_output_tokens:
                continue
            
            # Calculate score
            score = model.priority
            
            # Task-specific score
            if self.task_class in model.task_scores:
                score += model.task_scores[self.task_class] * 20
            
            # Preference adjustments
            if self.prefer_fast and ModelCapability.FAST_INFERENCE in model.capabilities:
                score += 10
            if self.prefer_cheap:
                score += (100 - model.input_cost_score) / 5
            if self.prefer_accurate:
                # Assume higher cost = higher accuracy (rough heuristic)
                score += model.input_cost_score / 10
            
            candidates.append((model.name, score))
        
        # Sort by score descending
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in candidates]


def create_routing_hint(
    task_class: TaskClass,
    input_tokens: int = 0,
    output_tokens: int = 0,
    capabilities: Optional[Set[ModelCapability]] = None,
    prefer_fast: bool = False,
    prefer_cheap: bool = False,
) -> RoutingHint:
    """Create a routing hint for model selection.
    
    Args:
        task_class: The type of task.
        input_tokens: Estimated input tokens.
        output_tokens: Estimated output tokens.
        capabilities: Required capabilities.
        prefer_fast: Prefer fast inference.
        prefer_cheap: Prefer low cost.
        
    Returns:
        RoutingHint with recommendations.
    """
    return RoutingHint(
        task_class=task_class,
        estimated_input_tokens=input_tokens,
        estimated_output_tokens=output_tokens,
        requires_capabilities=capabilities or set(),
        prefer_fast=prefer_fast,
        prefer_cheap=prefer_cheap,
    )


# ============================================================================
# Utility Functions
# ============================================================================

def get_model_for_task(task_class: TaskClass) -> str:
    """Get the best model for a task class (simple interface).
    
    This is a convenience function that returns a single recommendation.
    
    Args:
        task_class: The type of task.
        
    Returns:
        Model name.
    """
    hint = create_routing_hint(task_class)
    recommendations = hint.get_recommended_models()
    
    if recommendations:
        return recommendations[0]
    
    # Fall back to default
    pool = get_model_pool()
    return pool.default_model


def get_fast_model() -> str:
    """Get the fastest available model.
    
    Returns:
        Model name.
    """
    pool = get_model_pool()
    fast_models = pool.get_models_for_capability(ModelCapability.FAST_INFERENCE)
    
    if fast_models:
        # Sort by priority
        fast_models.sort(key=lambda m: m.priority, reverse=True)
        return fast_models[0].name
    
    return pool.default_model


def get_long_context_model() -> str:
    """Get a model suitable for long context.
    
    Returns:
        Model name.
    """
    pool = get_model_pool()
    long_models = pool.get_models_for_capability(ModelCapability.LONG_CONTEXT)
    
    if long_models:
        # Sort by max input tokens
        long_models.sort(key=lambda m: m.max_input_tokens, reverse=True)
        return long_models[0].name
    
    return pool.default_model


def format_pool_summary(pool: Optional[ModelPool] = None) -> str:
    """Format model pool as a human-readable summary.
    
    Args:
        pool: Model pool to summarize.
        
    Returns:
        Formatted string.
    """
    if pool is None:
        pool = get_model_pool()
    
    lines = ["# Model Pool Summary", ""]
    lines.append(f"Default: {pool.default_model}")
    lines.append(f"Fallback: {pool.fallback_model}")
    lines.append(f"Auto-routing: {'enabled' if pool.enable_auto_routing else 'disabled'}")
    lines.append("")
    lines.append("## Available Models")
    lines.append("")
    
    for model in pool.models:
        status = "✓" if model.enabled else "✗"
        lines.append(f"### {status} {model.name}")
        lines.append(f"  Provider: {model.provider}")
        lines.append(f"  Model ID: {model.model_id}")
        lines.append(f"  Limits: {model.max_input_tokens:,} in / {model.max_output_tokens:,} out")
        lines.append(f"  Rate: {model.requests_per_minute} RPM, {model.tokens_per_minute:,} TPM")
        lines.append(f"  Priority: {model.priority}")
        lines.append(f"  Cost: {model.input_cost_score}/100 input, {model.output_cost_score}/100 output")
        if model.capabilities:
            caps = ", ".join(c.value for c in model.capabilities)
            lines.append(f"  Capabilities: {caps}")
        lines.append("")
    
    return "\n".join(lines)
