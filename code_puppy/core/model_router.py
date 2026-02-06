"""Model Router - BART Reasoning Layer.

Routes tasks to the optimal model based on:
- Task type and complexity
- Provider availability and budget
- Model capabilities and cost

Tier Hierarchy:
- Tier 5 (Sprinter): Cerebras GLM 4.7 - High-volume, fast generation
- Tier 4 (Librarian): Gemini 3 Flash/Pro - Context, search, summarization
- Tier 3/2 (Builders): Codex 5.2 / Sonnet 4.5 - Complex logic
- Tier 1 (Architect): Claude Opus 4.5 - Planning, security, QA
"""

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .token_budget import TokenBudgetManager

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """Model tiers from most expensive/capable to cheapest/fastest."""
    
    ARCHITECT = 1  # Claude Opus 4.5 - Planning, security, QA
    BUILDER_HIGH = 2  # Codex 5.2 - Complex logic
    BUILDER_MID = 3  # Sonnet 4.5 - Refactoring, design
    LIBRARIAN = 4  # Gemini 3 - Context, search
    SPRINTER = 5  # Cerebras GLM - High-volume code


class TaskType(Enum):
    """Types of tasks for routing decisions."""
    
    # Tier 1 tasks (Architect)
    PLANNING = "planning"
    SECURITY_AUDIT = "security_audit"
    CONFLICT_RESOLUTION = "conflict_resolution"
    FINAL_QA = "final_qa"
    
    # Tier 2/3 tasks (Builders)
    COMPLEX_REFACTORING = "complex_refactoring"
    CLASS_DESIGN = "class_design"
    ALGORITHM_IMPLEMENTATION = "algorithm_implementation"
    API_DESIGN = "api_design"
    
    # Tier 4 tasks (Librarian)
    CONTEXT_SEARCH = "context_search"
    SUMMARIZATION = "summarization"
    LOG_ANALYSIS = "log_analysis"
    DOCUMENTATION = "documentation"
    
    # Tier 5 tasks (Sprinter)
    CODE_GENERATION = "code_generation"
    SYNTAX_FIXING = "syntax_fixing"
    LINTING = "linting"
    UNIT_TESTS = "unit_tests"
    BOILERPLATE = "boilerplate"
    
    UNKNOWN = "unknown"


class TaskComplexity(Enum):
    """Complexity levels for fine-grained routing."""
    
    LOW = "low"  # Simple, repetitive tasks
    MEDIUM = "medium"  # Standard development tasks
    HIGH = "high"  # Complex logic, careful consideration
    CRITICAL = "critical"  # Security-sensitive, architectural


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    
    name: str  # e.g., "cerebras-glm-4.7"
    provider: str  # e.g., "cerebras"
    tier: ModelTier
    max_context: int  # Max input tokens
    max_output: int  # Max output tokens
    cost_per_1k_input: float  # Cost in USD
    cost_per_1k_output: float
    supports_context_caching: bool = False
    context_cache_threshold: int = 30_000  # Min tokens for caching


@dataclass
class RoutingDecision:
    """Result of routing decision."""
    
    model: str
    provider: str
    tier: ModelTier
    task_type: TaskType
    complexity: TaskComplexity
    estimated_tokens: int
    reason: str
    fallback_model: Optional[str] = None


class ModelRouter:
    """Routes tasks to the optimal model based on task characteristics.
    
    Uses a tiered approach:
    1. Detect task type from prompt/context
    2. Assess complexity
    3. Check budget availability
    4. Route to appropriate tier with fallback
    
    Model Capabilities Reference (researched from official docs):
    - Claude Opus 4.5: 200K context, 64K output, effort parameter, best reasoning
    - Claude Sonnet 4.5: 200K context, 64K output, agentic coding leader
    - Gemini 3 Pro: 1M context, 64K output, thinking levels
    - Gemini 3 Flash: 1M context, 8K output, fast, cheap
    - GPT-5.2: 400K context, 32K output, reasoning, long context
    - GPT-5.2-Codex: 400K context, 32K output, agentic coding optimized
    - DeepSeek R1-0528: 131K context, 131K output, reasoning model
    - Kimi K2.5: 256K context, 1T MoE, agent swarms, thinking
    - Kimi K2-Thinking: 256K context, 1T MoE, reasoning
    - Qwen3-235B-Thinking: 262K context, 16K output, math leader
    - MiniMax M2.1: 1M context, 1M output, multilang coding
    - GLM-4.7: 200K context, 358B MoE, agentic coding, tool use
    """
    
    # Default model configurations - use EXACT keys from models.json
    DEFAULT_MODELS: Dict[str, ModelConfig] = {
        # =====================================================================
        # Tier 5: Sprinter - High volume, fast generation
        # =====================================================================
        "Cerebras-GLM-4.7": ModelConfig(
            name="Cerebras-GLM-4.7",
            provider="cerebras",
            tier=ModelTier.SPRINTER,
            max_context=131_072,
            max_output=40_000,
            cost_per_1k_input=0.0,  # Free tier
            cost_per_1k_output=0.0,
        ),
        "synthetic-GLM-4.7": ModelConfig(
            name="synthetic-GLM-4.7",
            provider="synthetic",
            tier=ModelTier.SPRINTER,
            max_context=200_000,
            max_output=16_000,
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0,
        ),
        "synthetic-hf-zai-org-GLM-4.7": ModelConfig(
            name="synthetic-hf-zai-org-GLM-4.7",
            provider="synthetic",
            tier=ModelTier.SPRINTER,
            max_context=200_000,
            max_output=16_000,
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0,
        ),
        
        # =====================================================================
        # Tier 4: Librarian - Context, search, docs
        # =====================================================================
        "antigravity-gemini-3-flash": ModelConfig(
            name="antigravity-gemini-3-flash",
            provider="gemini_flash",
            tier=ModelTier.LIBRARIAN,
            max_context=1_000_000,
            max_output=8_000,
            cost_per_1k_input=0.0001,
            cost_per_1k_output=0.0004,
            supports_context_caching=True,
            context_cache_threshold=30_000,
        ),
        "antigravity-gemini-3-pro-low": ModelConfig(
            name="antigravity-gemini-3-pro-low",
            provider="gemini",
            tier=ModelTier.LIBRARIAN,
            max_context=1_000_000,
            max_output=64_000,
            cost_per_1k_input=0.00025,
            cost_per_1k_output=0.001,
            supports_context_caching=True,
            context_cache_threshold=30_000,
        ),
        "openrouter-arcee-ai-trinity-large-preview-free": ModelConfig(
            name="openrouter-arcee-ai-trinity-large-preview-free",
            provider="openrouter",
            tier=ModelTier.LIBRARIAN,
            max_context=128_000,
            max_output=8_000,
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0,
        ),
        "openrouter-stepfun-step-3.5-flash-free": ModelConfig(
            name="openrouter-stepfun-step-3.5-flash-free",
            provider="openrouter",
            tier=ModelTier.LIBRARIAN,
            max_context=128_000,
            max_output=8_000,
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0,
        ),
        "claude-code-claude-haiku-4-5-20251001": ModelConfig(
            name="claude-code-claude-haiku-4-5-20251001",
            provider="claude_haiku",
            tier=ModelTier.LIBRARIAN,
            max_context=200_000,
            max_output=16_000,
            cost_per_1k_input=0.001,
            cost_per_1k_output=0.005,
        ),
        
        # =====================================================================
        # Tier 3: Builder Mid - Standard development
        # =====================================================================
        "synthetic-MiniMax-M2.1": ModelConfig(
            name="synthetic-MiniMax-M2.1",
            provider="minimax",
            tier=ModelTier.BUILDER_MID,
            max_context=1_000_000,
            max_output=1_000_000,
            cost_per_1k_input=0.0003,
            cost_per_1k_output=0.0012,
        ),
        "synthetic-hf-MiniMaxAI-MiniMax-M2.1": ModelConfig(
            name="synthetic-hf-MiniMaxAI-MiniMax-M2.1",
            provider="minimax",
            tier=ModelTier.BUILDER_MID,
            max_context=1_000_000,
            max_output=1_000_000,
            cost_per_1k_input=0.0003,
            cost_per_1k_output=0.0012,
        ),
        "antigravity-gemini-3-pro-high": ModelConfig(
            name="antigravity-gemini-3-pro-high",
            provider="gemini",
            tier=ModelTier.BUILDER_MID,
            max_context=1_000_000,
            max_output=64_000,
            cost_per_1k_input=0.004,
            cost_per_1k_output=0.004,
        ),
        "claude-code-claude-sonnet-4-5-20250929": ModelConfig(
            name="claude-code-claude-sonnet-4-5-20250929",
            provider="claude_sonnet",
            tier=ModelTier.BUILDER_MID,
            max_context=200_000,
            max_output=64_000,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
        ),
        "antigravity-claude-sonnet-4-5": ModelConfig(
            name="antigravity-claude-sonnet-4-5",
            provider="claude_sonnet",
            tier=ModelTier.BUILDER_MID,
            max_context=200_000,
            max_output=64_000,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
        ),
        
        # =====================================================================
        # Tier 2: Builder High - Complex coding, reasoning
        # =====================================================================
        "chatgpt-gpt-5.2-codex": ModelConfig(
            name="chatgpt-gpt-5.2-codex",
            provider="codex",
            tier=ModelTier.BUILDER_HIGH,
            max_context=400_000,
            max_output=32_000,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
        ),
        "chatgpt-gpt-5.2": ModelConfig(
            name="chatgpt-gpt-5.2",
            provider="gpt",
            tier=ModelTier.BUILDER_HIGH,
            max_context=400_000,
            max_output=32_000,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
        ),
        "synthetic-hf-deepseek-ai-DeepSeek-R1-0528": ModelConfig(
            name="synthetic-hf-deepseek-ai-DeepSeek-R1-0528",
            provider="deepseek",
            tier=ModelTier.BUILDER_HIGH,
            max_context=131_072,
            max_output=131_072,
            cost_per_1k_input=0.00055,
            cost_per_1k_output=0.00219,
        ),
        "synthetic-Kimi-K2-Thinking": ModelConfig(
            name="synthetic-Kimi-K2-Thinking",
            provider="kimi",
            tier=ModelTier.BUILDER_HIGH,
            max_context=256_000,
            max_output=32_000,
            cost_per_1k_input=0.001,
            cost_per_1k_output=0.003,
        ),
        "antigravity-claude-sonnet-4-5-thinking-high": ModelConfig(
            name="antigravity-claude-sonnet-4-5-thinking-high",
            provider="claude_sonnet",
            tier=ModelTier.BUILDER_HIGH,
            max_context=200_000,
            max_output=64_000,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
        ),
        "antigravity-claude-sonnet-4-5-thinking-medium": ModelConfig(
            name="antigravity-claude-sonnet-4-5-thinking-medium",
            provider="claude_sonnet",
            tier=ModelTier.BUILDER_MID,
            max_context=200_000,
            max_output=64_000,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
        ),
        "antigravity-claude-sonnet-4-5-thinking-low": ModelConfig(
            name="antigravity-claude-sonnet-4-5-thinking-low",
            provider="claude_sonnet",
            tier=ModelTier.BUILDER_MID,
            max_context=200_000,
            max_output=64_000,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
        ),
        
        # =====================================================================
        # Tier 1: Architect - Planning, reasoning, orchestration
        # =====================================================================
        "claude-code-claude-opus-4-5-20251101": ModelConfig(
            name="claude-code-claude-opus-4-5-20251101",
            provider="claude_opus",
            tier=ModelTier.ARCHITECT,
            max_context=200_000,
            max_output=64_000,
            cost_per_1k_input=0.005,
            cost_per_1k_output=0.025,
        ),
        "antigravity-claude-opus-4-5-thinking-high": ModelConfig(
            name="antigravity-claude-opus-4-5-thinking-high",
            provider="claude_opus",
            tier=ModelTier.ARCHITECT,
            max_context=200_000,
            max_output=64_000,
            cost_per_1k_input=0.005,
            cost_per_1k_output=0.025,
        ),
        "antigravity-claude-opus-4-5-thinking-medium": ModelConfig(
            name="antigravity-claude-opus-4-5-thinking-medium",
            provider="claude_opus",
            tier=ModelTier.ARCHITECT,
            max_context=200_000,
            max_output=64_000,
            cost_per_1k_input=0.005,
            cost_per_1k_output=0.025,
        ),
        "antigravity-claude-opus-4-5-thinking-low": ModelConfig(
            name="antigravity-claude-opus-4-5-thinking-low",
            provider="claude_opus",
            tier=ModelTier.ARCHITECT,
            max_context=200_000,
            max_output=64_000,
            cost_per_1k_input=0.005,
            cost_per_1k_output=0.025,
        ),
        "synthetic-Kimi-K2.5-Thinking": ModelConfig(
            name="synthetic-Kimi-K2.5-Thinking",
            provider="kimi",
            tier=ModelTier.ARCHITECT,
            max_context=256_000,
            max_output=32_000,
            cost_per_1k_input=0.001,
            cost_per_1k_output=0.003,
        ),
        "synthetic-hf-Qwen-Qwen3-235B-A22B-Thinking-2507": ModelConfig(
            name="synthetic-hf-Qwen-Qwen3-235B-A22B-Thinking-2507",
            provider="qwen",
            tier=ModelTier.ARCHITECT,
            max_context=262_144,
            max_output=16_384,
            cost_per_1k_input=0.00086,
            cost_per_1k_output=0.00344,
        ),
    }
    
    # Task type to tier mapping
    TASK_TIER_MAP: Dict[TaskType, ModelTier] = {
        # Tier 1: Architect
        TaskType.PLANNING: ModelTier.ARCHITECT,
        TaskType.SECURITY_AUDIT: ModelTier.ARCHITECT,
        TaskType.CONFLICT_RESOLUTION: ModelTier.ARCHITECT,
        TaskType.FINAL_QA: ModelTier.ARCHITECT,
        
        # Tier 2: Builder High
        TaskType.COMPLEX_REFACTORING: ModelTier.BUILDER_HIGH,
        TaskType.ALGORITHM_IMPLEMENTATION: ModelTier.BUILDER_HIGH,
        
        # Tier 3: Builder Mid
        TaskType.CLASS_DESIGN: ModelTier.BUILDER_MID,
        TaskType.API_DESIGN: ModelTier.BUILDER_MID,
        
        # Tier 4: Librarian
        TaskType.CONTEXT_SEARCH: ModelTier.LIBRARIAN,
        TaskType.SUMMARIZATION: ModelTier.LIBRARIAN,
        TaskType.LOG_ANALYSIS: ModelTier.LIBRARIAN,
        TaskType.DOCUMENTATION: ModelTier.LIBRARIAN,
        
        # Tier 5: Sprinter
        TaskType.CODE_GENERATION: ModelTier.SPRINTER,
        TaskType.SYNTAX_FIXING: ModelTier.SPRINTER,
        TaskType.LINTING: ModelTier.SPRINTER,
        TaskType.UNIT_TESTS: ModelTier.SPRINTER,
        TaskType.BOILERPLATE: ModelTier.SPRINTER,
        
        TaskType.UNKNOWN: ModelTier.BUILDER_MID,  # Safe default
    }
    
    # Patterns for task detection
    TASK_PATTERNS: Dict[TaskType, List[str]] = {
        # Tier 1
        TaskType.PLANNING: [
            r"\bplan\b", r"\barchitecture\b", r"\bdesign\s+system\b",
            r"\bhigh[\s-]?level\b", r"\bstrategy\b", r"\broadmap\b",
        ],
        TaskType.SECURITY_AUDIT: [
            r"\bsecurity\b", r"\baudit\b", r"\bvulnerab", r"\bcve\b",
            r"\binjection\b", r"\bxss\b", r"\bauth\w*\s+flaw",
        ],
        TaskType.CONFLICT_RESOLUTION: [
            r"\bconflict\b", r"\bmerge\b", r"\bresolve\b", r"\bdispute\b",
        ],
        TaskType.FINAL_QA: [
            r"\bfinal\s+review\b", r"\bqa\b", r"\bquality\s+assurance\b",
            r"\brelease\s+check\b", r"\bpre[\s-]?merge\b",
        ],
        
        # Tier 2/3
        TaskType.COMPLEX_REFACTORING: [
            r"\brefactor\b.*\b(complex|major|significant)\b",
            r"\b(complex|major)\b.*\brefactor\b",
            r"\brewrite\b", r"\bredesign\b",
        ],
        TaskType.CLASS_DESIGN: [
            r"\bclass\b.*\bdesign\b", r"\binterface\b", r"\babstract\b",
            r"\binheritance\b", r"\bpolymorphism\b",
        ],
        TaskType.ALGORITHM_IMPLEMENTATION: [
            r"\balgorithm\b", r"\boptimize\b", r"\btime\s+complexity\b",
            r"\bspace\s+complexity\b", r"\bdata\s+structure\b",
        ],
        TaskType.API_DESIGN: [
            r"\bapi\b.*\bdesign\b", r"\bendpoint\b", r"\brest\b",
            r"\bgraphql\b", r"\bschema\b",
        ],
        
        # Tier 4
        TaskType.CONTEXT_SEARCH: [
            r"\bsearch\b", r"\bfind\b", r"\bgrep\b", r"\blocate\b",
            r"\bwhere\s+is\b", r"\blook\s+for\b",
        ],
        TaskType.SUMMARIZATION: [
            r"\bsummar", r"\bdigest\b", r"\boverview\b", r"\btl;?dr\b",
            r"\bbrief\b", r"\bcondense\b",
        ],
        TaskType.LOG_ANALYSIS: [
            r"\blog\b", r"\btrace\b", r"\bdebug\b", r"\berror\s+message\b",
            r"\bstack\s*trace\b",
        ],
        TaskType.DOCUMENTATION: [
            r"\bdoc\b", r"\bcomment\b", r"\breadme\b", r"\bexplain\b",
            r"\bdocstring\b",
        ],
        
        # Tier 5
        TaskType.CODE_GENERATION: [
            r"\bwrite\b", r"\bcreate\b", r"\bimplement\b", r"\bbuild\b",
            r"\bgenerate\b", r"\badd\b.*\bfunction\b",
        ],
        TaskType.SYNTAX_FIXING: [
            r"\bfix\b.*\bsyntax\b", r"\bsyntax\s+error\b", r"\bparse\s+error\b",
            r"\btypo\b", r"\bmissing\b.*\b(bracket|paren|semicolon)\b",
        ],
        TaskType.LINTING: [
            r"\blint\b", r"\bformat\b", r"\bstyle\b", r"\bprettier\b",
            r"\bblack\b", r"\bflake8\b", r"\beslint\b",
        ],
        TaskType.UNIT_TESTS: [
            r"\btest\b", r"\bunittest\b", r"\bpytest\b", r"\bspec\b",
            r"\bassertion\b", r"\bmock\b",
        ],
        TaskType.BOILERPLATE: [
            r"\bboilerplate\b", r"\bscaffold\b", r"\btemplate\b",
            r"\bstarter\b", r"\bskeleton\b",
        ],
    }

    # Model type to tier mapping (for auto-detection from ModelFactory configs)
    MODEL_TYPE_TIERS: Dict[str, ModelTier] = {
        # Claude Code OAuth models (Architect/Builder tier)
        "claude_code": ModelTier.ARCHITECT,
        "claude_opus": ModelTier.ARCHITECT,
        "claude_sonnet": ModelTier.BUILDER_MID,
        "claude_haiku": ModelTier.LIBRARIAN,
        "anthropic": ModelTier.BUILDER_MID,
        # Antigravity OAuth (provider-level mappings)
        "antigravity": ModelTier.LIBRARIAN,
        "antigravity_gemini": ModelTier.LIBRARIAN,
        "antigravity_claude": ModelTier.BUILDER_MID,
        # Standard Gemini
        "gemini": ModelTier.LIBRARIAN,
        "gemini_flash": ModelTier.LIBRARIAN,
        # ChatGPT Teams (Builder tier)
        "openai": ModelTier.BUILDER_HIGH,
        "codex": ModelTier.BUILDER_HIGH,
        # Cerebras (Sprinter - free)
        "cerebras": ModelTier.SPRINTER,
        # Custom endpoints
        "custom_openai": ModelTier.BUILDER_MID,
        "custom_anthropic": ModelTier.BUILDER_MID,
    }
    
    def __init__(self, extra_models_path: Optional[Path] = None, load_from_factory: bool = True):
        """Initialize router with models from ModelFactory or custom config.
        
        Args:
            extra_models_path: Path to extra_models.json for custom configs
            load_from_factory: If True, load available models from ModelFactory
        """
        self._models: Dict[str, ModelConfig] = {}
        self._budget_mgr = TokenBudgetManager()
        
        if load_from_factory:
            self._load_from_model_factory()
        else:
            # Use hardcoded defaults only if factory loading disabled
            self._models = dict(self.DEFAULT_MODELS)
        
        if extra_models_path:
            self._load_extra_models(extra_models_path)
        
        logger.info(f"ModelRouter initialized with {len(self._models)} models")
    
    def _load_from_model_factory(self) -> None:
        """Load available models from ModelFactory config.
        
        This ensures we only route to models that are actually
        configured and authenticated (OAuth, API keys, etc.)
        """
        try:
            from code_puppy.model_factory import ModelFactory
            
            configs = ModelFactory.load_config()
            
            for name, config in configs.items():
                if not isinstance(config, dict):
                    continue
                
                model_type = config.get("type", "unknown")
                tier = self._detect_tier_from_config(name, config)
                
                self._models[name] = ModelConfig(
                    name=config.get("name", name),
                    provider=model_type,
                    tier=tier,
                    max_context=config.get("context_length", 100_000),
                    max_output=config.get("max_output", 4_000),
                    cost_per_1k_input=config.get("cost_per_1k_input", 0.0),
                    cost_per_1k_output=config.get("cost_per_1k_output", 0.0),
                    supports_context_caching=config.get("supports_context_caching", False),
                    context_cache_threshold=config.get("context_cache_threshold", 30_000),
                )
            
            logger.info(f"Loaded {len(self._models)} models from ModelFactory")
            
        except Exception as e:
            logger.warning(f"Failed to load from ModelFactory, using defaults: {e}")
            self._models = dict(self.DEFAULT_MODELS)
    
    def _detect_tier_from_config(self, name: str, config: Dict[str, Any]) -> ModelTier:
        """Detect appropriate tier from model configuration.
        
        Uses model type, name patterns, and explicit tier setting.
        """
        # Check for explicit tier setting
        if "tier" in config:
            tier_val = config["tier"]
            try:
                # Handle numeric tier values (1-5 matching ModelTier enum values)
                if isinstance(tier_val, int):
                    return ModelTier(tier_val)
                # Handle string tier names (e.g., "ARCHITECT", "BUILDER_HIGH")
                return ModelTier[str(tier_val).upper()]
            except (KeyError, ValueError):
                pass
        
        model_type = config.get("type", "")
        model_name = config.get("name", name).lower()
        
        # Check type-based tier
        if model_type in self.MODEL_TYPE_TIERS:
            base_tier = self.MODEL_TYPE_TIERS[model_type]
            
            # Refine based on model name patterns
            if "opus" in model_name:
                return ModelTier.ARCHITECT
            elif "sonnet" in model_name:
                return ModelTier.BUILDER_MID
            elif "haiku" in model_name:
                return ModelTier.LIBRARIAN
            elif "flash" in model_name:
                return ModelTier.LIBRARIAN
            elif "codex" in model_name:
                return ModelTier.BUILDER_HIGH
            elif "cerebras" in model_name or "glm" in model_name:
                return ModelTier.SPRINTER
            
            return base_tier
        
        # Default to Builder Mid for unknown types
        return ModelTier.BUILDER_MID
    
    def get_available_models(self) -> List[str]:
        """Get list of all available model names."""
        return list(self._models.keys())
    
    def get_models_by_tier(self, tier: ModelTier) -> List[ModelConfig]:
        """Get all models for a specific tier."""
        return [m for m in self._models.values() if m.tier == tier]

    def _parse_tier_value(self, tier_val: Any, default: ModelTier = ModelTier.BUILDER_MID) -> ModelTier:
        """Parse tier value from config (int or string) to ModelTier enum.
        
        Args:
            tier_val: Tier value from config (int like 1-5 or string like "ARCHITECT")
            default: Default tier if parsing fails
            
        Returns:
            ModelTier enum value
        """
        if tier_val is None:
            return default
        try:
            # Handle numeric tier values (1-5 matching ModelTier enum values)
            if isinstance(tier_val, int):
                return ModelTier(tier_val)
            # Handle string tier names (e.g., "ARCHITECT", "BUILDER_HIGH")
            return ModelTier[str(tier_val).upper()]
        except (KeyError, ValueError):
            return default

    def _load_extra_models(self, path: Path) -> None:
        """Load additional model configurations from JSON file."""
        try:
            with open(path) as f:
                extra = json.load(f)
            
            for name, config in extra.get("models", {}).items():
                self._models[name] = ModelConfig(
                    name=name,
                    provider=config.get("provider", name),
                    tier=self._parse_tier_value(config.get("tier")),
                    max_context=config.get("max_context", 100_000),
                    max_output=config.get("max_output", 4_000),
                    cost_per_1k_input=config.get("cost_per_1k_input", 0.001),
                    cost_per_1k_output=config.get("cost_per_1k_output", 0.003),
                    supports_context_caching=config.get("supports_context_caching", False),
                    context_cache_threshold=config.get("context_cache_threshold", 30_000),
                )
            
            logger.info(f"Loaded {len(extra.get('models', {}))} extra models from {path}")
        except Exception as e:
            logger.warning(f"Failed to load extra models from {path}: {e}")
    
    def detect_task_type(self, prompt: str, context: Optional[str] = None) -> TaskType:
        """Detect task type from prompt and optional context.
        
        Args:
            prompt: The user's prompt/request
            context: Optional additional context
            
        Returns:
            Detected TaskType
        """
        text = (prompt + " " + (context or "")).lower()
        
        for task_type, patterns in self.TASK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return task_type
        
        return TaskType.UNKNOWN
    
    def assess_complexity(
        self,
        prompt: str,
        context: Optional[str] = None,
        file_count: int = 0,
    ) -> TaskComplexity:
        """Assess task complexity based on various signals.
        
        Args:
            prompt: The user's prompt/request
            context: Optional additional context
            file_count: Number of files involved
            
        Returns:
            Assessed TaskComplexity
        """
        text = (prompt + " " + (context or "")).lower()
        score = 0
        
        # Length signals
        if len(prompt) > 500:
            score += 1
        if len(prompt) > 1000:
            score += 1
        
        # Multi-file operations
        if file_count > 3:
            score += 1
        if file_count > 10:
            score += 2
        
        # Complexity keywords
        complex_keywords = [
            r"\bcomplex\b", r"\btricky\b", r"\bcareful\b", r"\bsensitive\b",
            r"\bcritical\b", r"\bsecurity\b", r"\bperformance\b", r"\bscalable\b",
        ]
        for kw in complex_keywords:
            if re.search(kw, text):
                score += 1
        
        # Simple keywords (negative score)
        simple_keywords = [
            r"\bsimple\b", r"\bquick\b", r"\beasy\b", r"\bbasic\b",
            r"\bjust\b", r"\bonly\b",
        ]
        for kw in simple_keywords:
            if re.search(kw, text):
                score -= 1
        
        # Map score to complexity
        if score <= 0:
            return TaskComplexity.LOW
        elif score <= 2:
            return TaskComplexity.MEDIUM
        elif score <= 4:
            return TaskComplexity.HIGH
        else:
            return TaskComplexity.CRITICAL
    
    def _get_tier_models(self, tier: ModelTier) -> List[ModelConfig]:
        """Get all models at a specific tier."""
        return [m for m in self._models.values() if m.tier == tier]
    
    def _get_fallback_tier(self, tier: ModelTier) -> Optional[ModelTier]:
        """Get fallback tier when primary is unavailable."""
        fallbacks = {
            ModelTier.SPRINTER: ModelTier.LIBRARIAN,  # Cerebras → Gemini Flash
            ModelTier.LIBRARIAN: ModelTier.BUILDER_MID,  # Gemini → Sonnet
            ModelTier.BUILDER_MID: ModelTier.BUILDER_HIGH,  # Sonnet → Codex
            ModelTier.BUILDER_HIGH: ModelTier.ARCHITECT,  # Codex → Opus
            ModelTier.ARCHITECT: None,  # No fallback for top tier
        }
        return fallbacks.get(tier)
    
    def route(
        self,
        prompt: str,
        context: Optional[str] = None,
        file_count: int = 0,
        estimated_tokens: int = 10_000,
        force_tier: Optional[ModelTier] = None,
    ) -> RoutingDecision:
        """Route a task to the optimal model.
        
        Args:
            prompt: The user's prompt/request
            context: Optional additional context
            file_count: Number of files involved
            estimated_tokens: Estimated total tokens
            force_tier: Force routing to specific tier (override auto-detection)
            
        Returns:
            RoutingDecision with model selection and reasoning
        """
        # Detect task and complexity
        task_type = self.detect_task_type(prompt, context)
        complexity = self.assess_complexity(prompt, context, file_count)
        
        # Determine target tier
        if force_tier:
            target_tier = force_tier
        else:
            target_tier = self.TASK_TIER_MAP.get(task_type, ModelTier.BUILDER_MID)
            
            # Upgrade tier for high complexity
            if complexity == TaskComplexity.CRITICAL:
                target_tier = ModelTier.ARCHITECT
            elif complexity == TaskComplexity.HIGH and target_tier.value > ModelTier.BUILDER_HIGH.value:
                target_tier = ModelTier.BUILDER_HIGH
        
        # Find available model at target tier
        tier_models = self._get_tier_models(target_tier)
        selected_model: Optional[ModelConfig] = None
        fallback_model: Optional[str] = None
        
        for model in tier_models:
            budget_check = self._budget_mgr.check_budget(model.provider, estimated_tokens)
            if budget_check.can_proceed:
                selected_model = model
                break
            elif budget_check.failover_to:
                # Note failover for later
                fallback_model = budget_check.failover_to
        
        # Try fallback tier if no model available
        if not selected_model:
            fallback_tier = self._get_fallback_tier(target_tier)
            while fallback_tier:
                fallback_models = self._get_tier_models(fallback_tier)
                for model in fallback_models:
                    budget_check = self._budget_mgr.check_budget(model.provider, estimated_tokens)
                    if budget_check.can_proceed:
                        selected_model = model
                        break
                if selected_model:
                    break
                fallback_tier = self._get_fallback_tier(fallback_tier)
        
        # Last resort: use first available model
        if not selected_model:
            for model in self._models.values():
                budget_check = self._budget_mgr.check_budget(model.provider, estimated_tokens)
                if budget_check.can_proceed:
                    selected_model = model
                    break
        
        # Still nothing? Use user's configured model or any available
        if not selected_model:
            from code_puppy.config import get_global_model_name
            global_model = get_global_model_name()
            selected_model = self._models.get(
                global_model, list(self._models.values())[0] if self._models else None
            )
            if selected_model:
                logger.warning(f"All providers over budget, using {selected_model.name} anyway")
        
        # Build decision
        reason_parts = [
            f"Task: {task_type.value}",
            f"Complexity: {complexity.value}",
            f"Target tier: {target_tier.name}",
        ]
        if selected_model.tier != target_tier:
            reason_parts.append(f"Downgraded to {selected_model.tier.name} due to budget")
        
        return RoutingDecision(
            model=selected_model.name,
            provider=selected_model.provider,
            tier=selected_model.tier,
            task_type=task_type,
            complexity=complexity,
            estimated_tokens=estimated_tokens,
            reason=" | ".join(reason_parts),
            fallback_model=fallback_model,
        )
    
    def get_model_for_tier(self, tier: ModelTier) -> Optional[ModelConfig]:
        """Get the primary model for a specific tier."""
        tier_models = self._get_tier_models(tier)
        return tier_models[0] if tier_models else None

    # =========================================================================
    # RATE LIMIT FAILOVER - PURPOSE-DRIVEN
    # =========================================================================
    #
    # ARCHITECT (Orchestrator, Pack Leader, Governor, Planning):
    #   Claude Code Opus → Antigravity Opus → Gemini Pro → Codex 5.2
    #
    # BUILDER (Complex logic, design, refactoring):
    #   Claude Code Sonnet → Antigravity Sonnet → Gemini Pro → Codex 5.2
    #
    # SPRINTER (Main code work, high volume):
    #   Cerebras GLM 4.7 → Claude Haiku → Gemini Flash
    #
    # LIBRARIAN (Search, docs, less intensive):
    #   Haiku → GPT 5.2 → Gemini Flash
    # =========================================================================

    def get_failover_for_model(
        self, 
        model_name: str,
        task_type: Optional[TaskType] = None,
    ) -> Optional[str]:
        """Get failover model when the primary hits rate limits.
        
        Uses PURPOSE-DRIVEN failover logic:
        1. If task_type provided, use workload-appropriate chain
        2. Otherwise, use tier-aware fallback
        
        Args:
            model_name: Model that hit rate limit
            task_type: Optional task type for smarter failover
            
        Returns:
            Alternative model name, or None if no failover available
        """
        # Try workload-aware failover first
        try:
            from .rate_limit_failover import get_failover_manager, WorkloadType
            
            failover_mgr = get_failover_manager()
            
            # Map TaskType to WorkloadType for smarter failover
            workload = None
            if task_type:
                if task_type in (TaskType.PLANNING, TaskType.CONFLICT_RESOLUTION, TaskType.FINAL_QA):
                    workload = WorkloadType.ORCHESTRATOR
                elif task_type in (TaskType.SECURITY_AUDIT, TaskType.COMPLEX_REFACTORING, 
                                   TaskType.CLASS_DESIGN, TaskType.API_DESIGN):
                    workload = WorkloadType.REASONING
                elif task_type in (TaskType.CODE_GENERATION, TaskType.SYNTAX_FIXING,
                                   TaskType.UNIT_TESTS, TaskType.BOILERPLATE):
                    workload = WorkloadType.CODING
                else:
                    workload = WorkloadType.LIBRARIAN
            
            failover = failover_mgr.get_workload_failover(model_name, workload)
            if failover:
                logger.info(f"Workload failover: {model_name} → {failover}")
                return failover
                
        except ImportError:
            pass
        
        # Fall back to tier-aware logic
        rate_limited = self._models.get(model_name)
        if not rate_limited:
            return None
        
        # 1. Try same tier, different provider
        same_tier = self._get_tier_models(rate_limited.tier)
        for model in same_tier:
            if model.name != model_name:
                budget_check = self._budget_mgr.check_budget(model.provider, 10_000)
                if budget_check.can_proceed:
                    logger.info(f"Failover: {model_name} → {model.name} (same tier)")
                    return model.name
        
        # 2. Try one tier down
        fallback_tier = self._get_fallback_tier(rate_limited.tier)
        if fallback_tier:
            fallback_models = self._get_tier_models(fallback_tier)
            for model in fallback_models:
                budget_check = self._budget_mgr.check_budget(model.provider, 10_000)
                if budget_check.can_proceed:
                    logger.info(f"Failover: {model_name} → {model.name} (tier down)")
                    return model.name
        
        # 3. Try any available model
        for model in self._models.values():
            if model.name != model_name:
                budget_check = self._budget_mgr.check_budget(model.provider, 10_000)
                if budget_check.can_proceed:
                    logger.info(f"Failover: {model_name} → {model.name} (emergency)")
                    return model.name
        
        logger.warning(f"No failover available for {model_name}")
        return None

    def record_rate_limit(self, model_name: str, task_type: Optional[TaskType] = None) -> Optional[str]:
        """Record that a model hit rate limit and return failover.
        
        This integrates with TokenBudgetManager's 429 tracking.
        
        Args:
            model_name: Model that hit rate limit
            task_type: Optional task type for smarter failover
            
        Returns:
            Suggested failover model, or None
        """
        model = self._models.get(model_name)
        if model:
            wait_time, budget_failover = self._budget_mgr.record_429(model.provider)
            if budget_failover:
                # Map provider back to model name
                for m in self._models.values():
                    if m.provider == budget_failover:
                        return m.name
        
        # Fall back to workload-aware failover
        return self.get_failover_for_model(model_name, task_type)

    # =========================================================================
    # PROMPT ADAPTATION
    # =========================================================================

    # Personality text patterns to strip for Sprinter models
    # DIALECT OPTIMIZATION: Aggressively remove token-wasting preamble
    PERSONALITY_PATTERNS = [
        r"You are [a-zA-Z\s]+\. ",  # "You are a helpful assistant."
        r"You are a [^.]+\.",  # "You are a friendly coder."
        r"As an? [^,]+, ",  # "As a helpful assistant, "
        r"\bfriendly\b",
        r"\bhelpful\b",
        r"\bpolite\b",
        r"\bpersonality\b",
        r"Please feel free to[^.]+\.",
        r"Don't hesitate to[^.]+\.",
        r"You're here to help[^.]+\.",
        r"I'm here to help[^.]+\.",
        r"Feel free to ask[^.]+\.",
        r"Let me know if[^.]+\.",
        r"Happy to help[^.]+\.",
        r"I'd be happy to[^.]+\.",
    ]

    # Suffixes for different tiers
    # DIALECT OPTIMIZATION: Each tier gets appropriate instruction mode
    TIER_SUFFIXES = {
        # Sprinter (Cerebras): Maximum token efficiency, zero explanation overhead
        ModelTier.SPRINTER: "\n\n[STRICT MODE]: OUTPUT CODE ONLY. NO MARKDOWN. NO EXPLANATION. NO COMMENTS UNLESS EXPLICITLY REQUIRED. RESPOND WITH RAW CODE.",
        # Architect (Claude Opus): Full reasoning and architectural context preserved
        ModelTier.ARCHITECT: "",
        # Librarian (Gemini): Concise summaries, no verbose explanations
        ModelTier.LIBRARIAN: "\n\n[CONCISE MODE]: Summarize efficiently. No redundant context.",
    }

    def adapt_prompt(self, prompt: str, tier: ModelTier) -> str:
        """Adapt system prompt based on target model tier.

        For Sprinter (Cerebras):
        - Strip personality text to reduce tokens
        - Append strict output mode directive

        For Architect (Claude Opus):
        - Keep full architectural reasoning

        For Librarian (Gemini):
        - Add concise mode directive

        Args:
            prompt: Original system prompt
            tier: Target model tier

        Returns:
            Adapted prompt for the target tier
        """
        if tier == ModelTier.SPRINTER:
            # Strip personality text for maximum token efficiency
            adapted = prompt
            for pattern in self.PERSONALITY_PATTERNS:
                adapted = re.sub(pattern, "", adapted, flags=re.IGNORECASE)
            
            # Remove excessive whitespace
            adapted = re.sub(r"\n{3,}", "\n\n", adapted)
            adapted = re.sub(r" {2,}", " ", adapted)
            
            # Add strict output suffix
            adapted = adapted.strip() + self.TIER_SUFFIXES[tier]
            return adapted

        elif tier == ModelTier.ARCHITECT:
            # Architect gets full context - no modifications
            return prompt

        elif tier == ModelTier.LIBRARIAN:
            # Librarian gets concise mode
            return prompt.strip() + self.TIER_SUFFIXES.get(tier, "")

        # Default: return as-is
        return prompt

    def estimate_prompt_savings(self, original: str, tier: ModelTier) -> int:
        """Estimate token savings from prompt adaptation.

        Args:
            original: Original prompt
            tier: Target tier

        Returns:
            Estimated tokens saved
        """
        adapted = self.adapt_prompt(original, tier)
        original_tokens = len(original) // 4
        adapted_tokens = len(adapted) // 4
        return max(0, original_tokens - adapted_tokens)
