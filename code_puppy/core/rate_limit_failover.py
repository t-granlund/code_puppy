"""Rate Limit Failover - Automatic failover when models hit rate limits.

Provides intelligent model switching when 429 errors occur:
1. Dynamic failover chains built from OAuth-configured models
2. Tier-aware failover (prefer same tier, then downgrade gracefully)
3. Proper failover injection into API calls

DO NOT modify OAuth credentials - only reads from existing configurations.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import IntEnum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class FailoverPriority(IntEnum):
    """Priority order for failover (lower = prefer first)."""

    SAME_TIER = 1  # Same tier, different provider
    ONE_TIER_DOWN = 2  # One tier below
    TWO_TIERS_DOWN = 3  # Two tiers below
    EMERGENCY = 4  # Any working model


@dataclass
class FailoverTarget:
    """A model that can be used as failover target."""

    model_name: str
    provider: str
    tier: int  # 1=Architect, 2=BuilderHigh, 3=BuilderMid, 4=Librarian, 5=Sprinter
    priority: FailoverPriority
    rate_limited: bool = False
    last_429_time: float = 0.0


@dataclass
class FailoverResult:
    """Result of a failover attempt."""

    success: bool
    original_model: str
    failover_model: Optional[str] = None
    attempts: int = 0
    error: Optional[str] = None


class WorkloadType(IntEnum):
    """Types of workloads for smart failover routing."""
    
    ORCHESTRATOR = 1  # Pack leader, governor, planning - needs Opus/Sonnet
    REASONING = 2     # Complex logic, security audit - needs Opus/Sonnet
    CODING = 3        # Main code generation - Cerebras preferred
    LIBRARIAN = 4     # Search, docs, context - Gemini/Haiku


class RateLimitFailover:
    """Manages automatic failover when models hit rate limits.

    PURPOSE-DRIVEN FAILOVER STRUCTURE:
    
    ARCHITECT TIER (Orchestrator, Pack Leader, Governor, Planning):
      Claude Code Opus → Antigravity Opus → Gemini Pro → Codex 5.2
    
    BUILDER TIER (Complex logic, design, refactoring):
      Claude Code Sonnet → Antigravity Sonnet → Gemini Pro → Codex 5.2
    
    SPRINTER TIER (Main code work, high volume generation):
      Cerebras GLM 4.7 → Claude Haiku → Gemini Flash
    
    LIBRARIAN TIER (Search, docs, context, less intensive):
      Haiku → GPT 5.2 → Gemini Flash

    Reads from existing OAuth configurations to build failover chains.
    Never modifies authentication credentials.
    """

    _instance: Optional["RateLimitFailover"] = None

    # Tier mapping for known model types
    # This is read-only reference data, not modifying any config
    TIER_MAPPINGS: Dict[str, int] = {
        # Tier 1: Architect (big reasoning, planning, orchestrator)
        "opus": 1,
        "o3": 1,
        "o1": 1,
        "opus-4-5-thinking": 1,  # Antigravity Opus thinking
        # Tier 2: Builder High (strong coding, complex logic)
        "codex": 2,
        "gpt-5": 2,
        "sonnet-4-5-thinking-high": 2,  # Sonnet high thinking = Builder
        # Tier 3: Builder Mid (capable all-rounder)
        "sonnet": 3,
        "gpt-4": 3,
        "sonnet-4-5-thinking-medium": 3,
        "sonnet-4-5-thinking-low": 3,
        # Tier 4: Librarian (search, docs, less intensive code)
        "gemini": 4,
        "haiku": 4,
        "flash": 4,
        "gemini-3-pro": 4,
        "gemini-3-flash": 4,
        # Tier 5: Sprinter (main code work, ultra-fast)
        "cerebras": 5,
        "glm": 5,
    }

    # PURPOSE-DRIVEN FAILOVER CHAINS
    # These chains respect the intended use of each model
    WORKLOAD_CHAINS: Dict[WorkloadType, List[str]] = {
        # Pack leader, governor, planning - needs reasoning power
        WorkloadType.ORCHESTRATOR: [
            "claude-opus-4.5",  # Claude Code OAuth
            "antigravity-claude-opus-4-5-thinking-high",
            "antigravity-claude-opus-4-5-thinking-medium",
            "antigravity-claude-opus-4-5-thinking-low",
            "claude-sonnet-4.5",  # Downgrade to Sonnet if Opus exhausted
            "antigravity-claude-sonnet-4-5-thinking-high",
            "gemini-3-pro",  # Last resort for reasoning
            "chatgpt-codex-5.2",
        ],
        # Complex logic, security audit, design
        WorkloadType.REASONING: [
            "claude-sonnet-4.5",
            "antigravity-claude-sonnet-4-5",
            "antigravity-claude-sonnet-4-5-thinking-high",
            "antigravity-claude-sonnet-4-5-thinking-medium",
            "gemini-3-pro",
            "chatgpt-codex-5.2",
            "gemini-3-flash",
        ],
        # Main code generation - speed matters
        WorkloadType.CODING: [
            "cerebras-glm-4.7",  # Primary: ultra-fast
            "claude-haiku",  # Fast fallback
            "gemini-3-flash",  # Reliable fallback
            "antigravity-gemini-3-flash",
        ],
        # Search, docs, context - efficiency matters
        WorkloadType.LIBRARIAN: [
            "claude-haiku",  # Fast and cheap
            "gpt-5.2",
            "gemini-3-flash",
            "antigravity-gemini-3-flash",
            "cerebras-glm-4.7",  # Can do search too
        ],
    }

    # UNIFIED AGENT WORKLOAD REGISTRY
    # Maps every agent to its appropriate workload type for automatic model selection
    AGENT_WORKLOAD_REGISTRY: Dict[str, "WorkloadType"] = {
        # ═══════════════════════════════════════════════════════════════════
        # ORCHESTRATORS (Claude Opus → Antigravity Opus → Gemini Pro → Codex)
        # These agents coordinate other agents and need strong reasoning
        # ═══════════════════════════════════════════════════════════════════
        "pack-leader": WorkloadType.ORCHESTRATOR,
        "helios": WorkloadType.ORCHESTRATOR,  # Universal Constructor
        "epistemic-architect": WorkloadType.ORCHESTRATOR,  # EAR/Ralph loops
        "planning": WorkloadType.ORCHESTRATOR,
        "agent-creator": WorkloadType.ORCHESTRATOR,  # Creates new agents
        
        # ═══════════════════════════════════════════════════════════════════
        # REASONING (Claude Sonnet → Antigravity Sonnet → Gemini Pro → Codex)
        # Complex analysis, code review, security audit, QA strategy
        # ═══════════════════════════════════════════════════════════════════
        # Pack reviewer agents
        "shepherd": WorkloadType.REASONING,  # Code review guardian
        "watchdog": WorkloadType.REASONING,  # Monitoring/guarding
        
        # Language-specific reviewers
        "code-reviewer": WorkloadType.REASONING,
        "python-reviewer": WorkloadType.REASONING,
        "c-reviewer": WorkloadType.REASONING,
        "cpp-reviewer": WorkloadType.REASONING,
        "golang-reviewer": WorkloadType.REASONING,
        "javascript-reviewer": WorkloadType.REASONING,
        "typescript-reviewer": WorkloadType.REASONING,
        "prompt-reviewer": WorkloadType.REASONING,
        
        # QA/Security (need deep analysis)
        "qa-expert": WorkloadType.REASONING,
        "security-auditor": WorkloadType.REASONING,
        
        # ═══════════════════════════════════════════════════════════════════
        # CODING (Cerebras GLM 4.7 → Claude Haiku → Gemini Flash)
        # Main code generation - speed matters for high-volume work
        # ═══════════════════════════════════════════════════════════════════
        # Pack coding agents
        "husky": WorkloadType.CODING,  # Heavy lifting, task execution
        "terrier": WorkloadType.CODING,  # Worktree management (git commands)
        "retriever": WorkloadType.CODING,  # Code/file retrieval with modification
        
        # Main coding agents
        "code-puppy": WorkloadType.CODING,  # Main agent
        "python-programmer": WorkloadType.CODING,
        "qa-kitten": WorkloadType.CODING,  # Lightweight QA (runs tests)
        "terminal-qa": WorkloadType.CODING,  # Terminal-based QA
        
        # ═══════════════════════════════════════════════════════════════════
        # LIBRARIAN (Haiku → GPT 5.2 → Gemini Flash)
        # Search, docs, context gathering - efficiency over power
        # ═══════════════════════════════════════════════════════════════════
        "bloodhound": WorkloadType.LIBRARIAN,  # Issue tracking with bd
        "json-agent": WorkloadType.LIBRARIAN,  # JSON parsing/generation
    }

    def __new__(cls) -> "RateLimitFailover":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._available_models: Dict[str, FailoverTarget] = {}
        self._failover_chains: Dict[str, List[str]] = {}
        self._rate_limited: Set[str] = set()
        self._lock = asyncio.Lock()
        self._initialized = True
        self._loaded = False

    def _detect_tier(self, model_name: str) -> int:
        """Detect tier from model name patterns."""
        model_lower = model_name.lower()
        for pattern, tier in self.TIER_MAPPINGS.items():
            if pattern in model_lower:
                return tier
        return 4  # Default to Librarian tier if unknown

    def _detect_provider(self, model_name: str, config: Dict[str, Any]) -> str:
        """Detect provider from model config."""
        # Check explicit provider field
        if "provider" in config:
            return config["provider"]

        # Infer from model name
        model_lower = model_name.lower()
        
        # Antigravity OAuth models (prefix detection)
        if "antigravity" in model_lower:
            if "gemini" in model_lower:
                return "antigravity_gemini"
            elif "claude" in model_lower or "opus" in model_lower or "sonnet" in model_lower:
                return "antigravity_claude"
            return "antigravity"
        
        if "cerebras" in model_lower or "glm" in model_lower:
            return "cerebras"
        elif "gemini" in model_lower:
            return "gemini"
        elif "claude" in model_lower or "opus" in model_lower or "sonnet" in model_lower:
            return "anthropic"
        elif "gpt" in model_lower or "codex" in model_lower:
            return "openai"

        return "unknown"

    def load_from_model_factory(self) -> None:
        """Load available models from ModelFactory (reads OAuth-configured models).

        This only READS from existing configurations, never modifies them.
        """
        if self._loaded:
            return

        try:
            from ..model_factory import ModelFactory

            # Load all configured models (includes OAuth sources)
            models = ModelFactory.load_config()

            for model_name, config in models.items():
                if not isinstance(config, dict):
                    continue

                tier = self._detect_tier(model_name)
                provider = self._detect_provider(model_name, config)

                self._available_models[model_name] = FailoverTarget(
                    model_name=model_name,
                    provider=provider,
                    tier=tier,
                    priority=FailoverPriority.SAME_TIER,
                )

            # Build failover chains after loading
            self._build_failover_chains()
            self._loaded = True

            logger.info(
                f"RateLimitFailover loaded {len(self._available_models)} models from OAuth config"
            )

        except Exception as e:
            logger.warning(f"Failed to load models from ModelFactory: {e}")
            # Fall back to static defaults
            self._load_fallback_models()
            self._loaded = True

    def _load_fallback_models(self) -> None:
        """Load fallback models if ModelFactory fails."""
        fallbacks = [
            # Standard models
            ("gemini-3-flash", "gemini", 4),
            ("gemini-3-pro", "gemini", 4),
            ("claude-sonnet-4.5", "anthropic", 3),
            ("cerebras-glm-4.7", "cerebras", 5),
            # Antigravity OAuth models
            ("antigravity-gemini-3-flash", "antigravity_gemini", 4),
            ("antigravity-gemini-3-pro-low", "antigravity_gemini", 4),
            ("antigravity-gemini-3-pro-high", "antigravity_gemini", 4),
            ("antigravity-claude-sonnet-4-5", "antigravity_claude", 3),
            ("antigravity-claude-sonnet-4-5-thinking-low", "antigravity_claude", 3),
            ("antigravity-claude-sonnet-4-5-thinking-medium", "antigravity_claude", 3),
            ("antigravity-claude-sonnet-4-5-thinking-high", "antigravity_claude", 2),
            ("antigravity-claude-opus-4-5-thinking-low", "antigravity_claude", 1),
            ("antigravity-claude-opus-4-5-thinking-medium", "antigravity_claude", 1),
            ("antigravity-claude-opus-4-5-thinking-high", "antigravity_claude", 1),
        ]
        for name, provider, tier in fallbacks:
            self._available_models[name] = FailoverTarget(
                model_name=name,
                provider=provider,
                tier=tier,
                priority=FailoverPriority.SAME_TIER,
            )
        self._build_failover_chains()

    def _build_failover_chains(self) -> None:
        """Build failover chains for each model based on tiers."""
        for model_name, target in self._available_models.items():
            chain: List[str] = []

            # Group other models by how many tiers away
            same_tier: List[str] = []
            one_down: List[str] = []
            two_down: List[str] = []
            emergency: List[str] = []

            for other_name, other_target in self._available_models.items():
                if other_name == model_name:
                    continue

                tier_diff = other_target.tier - target.tier

                if tier_diff == 0:
                    same_tier.append(other_name)
                elif tier_diff == 1:
                    one_down.append(other_name)
                elif tier_diff == 2:
                    two_down.append(other_name)
                else:
                    emergency.append(other_name)

            # Build chain: same tier first, then graceful degradation
            chain.extend(same_tier)
            chain.extend(one_down)
            chain.extend(two_down)
            chain.extend(emergency)

            self._failover_chains[model_name] = chain

        logger.debug(f"Built failover chains for {len(self._failover_chains)} models")

    def get_failover_chain(self, model_name: str) -> List[str]:
        """Get ordered list of failover models for a given model."""
        self.load_from_model_factory()

        if model_name in self._failover_chains:
            # Filter out currently rate-limited models
            return [
                m
                for m in self._failover_chains[model_name]
                if m not in self._rate_limited
            ]

        # Unknown model - return any available non-rate-limited models
        return [m for m in self._available_models.keys() if m not in self._rate_limited]

    def get_next_failover(self, model_name: str) -> Optional[str]:
        """Get the next available failover model."""
        chain = self.get_failover_chain(model_name)
        return chain[0] if chain else None

    def get_workload_failover(
        self, 
        model_name: str, 
        workload: Optional[WorkloadType] = None
    ) -> Optional[str]:
        """Get workload-appropriate failover model.
        
        Uses purpose-driven chains based on workload type:
        - ORCHESTRATOR: Pack leader, governor, planning → needs Opus/Sonnet
        - REASONING: Complex logic, security → needs Sonnet/Pro
        - CODING: Main code generation → Cerebras/Haiku/Flash
        - LIBRARIAN: Search, docs → Haiku/Flash
        
        Args:
            model_name: Model that needs failover
            workload: Type of workload (auto-detected if None)
            
        Returns:
            Workload-appropriate failover model
        """
        self.load_from_model_factory()
        
        # Auto-detect workload from model if not specified
        if workload is None:
            workload = self._detect_workload(model_name)
        
        # Get the workload-specific chain
        chain = self.WORKLOAD_CHAINS.get(workload, [])
        
        # Find the current model's position in chain (if present)
        try:
            current_idx = chain.index(model_name)
            # Return next model in chain
            remaining = chain[current_idx + 1:]
        except ValueError:
            # Model not in chain, use full chain
            remaining = chain
        
        # Filter out rate-limited models
        for model in remaining:
            if model not in self._rate_limited:
                return model
        
        # Chain exhausted, fall back to generic failover
        return self.get_next_failover(model_name)

    def _detect_workload(self, model_name: str) -> WorkloadType:
        """Detect workload type from model name."""
        model_lower = model_name.lower()
        
        # Opus models → Orchestrator/Reasoning
        if "opus" in model_lower:
            return WorkloadType.ORCHESTRATOR
        
        # Sonnet models → Reasoning/Complex logic
        if "sonnet" in model_lower:
            return WorkloadType.REASONING
        
        # Cerebras → Coding (main code work)
        if "cerebras" in model_lower or "glm" in model_lower:
            return WorkloadType.CODING
        
        # Haiku, Gemini → Librarian
        if "haiku" in model_lower or "gemini" in model_lower or "flash" in model_lower:
            return WorkloadType.LIBRARIAN
        
        # Codex → could be coding or reasoning
        if "codex" in model_lower:
            return WorkloadType.REASONING
        
        # Default to Librarian (safest)
        return WorkloadType.LIBRARIAN

    def get_workload_for_agent(self, agent_name: str) -> WorkloadType:
        """Get the workload type for a specific agent.
        
        Uses AGENT_WORKLOAD_REGISTRY to map agents to their appropriate workload,
        which determines which model failover chain to use.
        
        Args:
            agent_name: Name of the agent (e.g., "pack-leader", "husky")
            
        Returns:
            WorkloadType for the agent (defaults to CODING if unknown)
        """
        # Normalize agent name (handle variations)
        normalized = agent_name.lower().strip()
        
        # Direct lookup
        if normalized in self.AGENT_WORKLOAD_REGISTRY:
            return self.AGENT_WORKLOAD_REGISTRY[normalized]
        
        # Try with dashes converted to underscores and vice versa
        underscore_name = normalized.replace("-", "_")
        dash_name = normalized.replace("_", "-")
        
        if underscore_name in self.AGENT_WORKLOAD_REGISTRY:
            return self.AGENT_WORKLOAD_REGISTRY[underscore_name]
        if dash_name in self.AGENT_WORKLOAD_REGISTRY:
            return self.AGENT_WORKLOAD_REGISTRY[dash_name]
        
        # Pattern-based inference for unknown agents
        if "reviewer" in normalized or "auditor" in normalized:
            return WorkloadType.REASONING
        if "leader" in normalized or "orchestrat" in normalized or "planning" in normalized:
            return WorkloadType.ORCHESTRATOR
        if "search" in normalized or "librarian" in normalized or "doc" in normalized:
            return WorkloadType.LIBRARIAN
        
        # Default to CODING for unknown agents
        logger.debug(f"Agent '{agent_name}' not in registry, defaulting to CODING workload")
        return WorkloadType.CODING

    def get_failover_chain_for_agent(self, agent_name: str) -> List[str]:
        """Get the appropriate failover chain for a specific agent.
        
        This is the main entry point for agent-aware model selection:
        1. Looks up agent's workload type from AGENT_WORKLOAD_REGISTRY
        2. Returns the appropriate WORKLOAD_CHAINS for that type
        
        Args:
            agent_name: Name of the agent requesting models
            
        Returns:
            List of model names in failover priority order
        """
        workload = self.get_workload_for_agent(agent_name)
        return self.WORKLOAD_CHAINS.get(workload, self.WORKLOAD_CHAINS[WorkloadType.CODING])

    def get_primary_model_for_agent(self, agent_name: str) -> str:
        """Get the primary (first choice) model for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Primary model name for this agent's workload
        """
        chain = self.get_failover_chain_for_agent(agent_name)
        
        # Filter out rate-limited models
        for model in chain:
            if model not in self._rate_limited:
                return model
        
        # All rate-limited, return first anyway (will trigger failover)
        return chain[0] if chain else "gemini-3-flash"

    def record_rate_limit(self, model_name: str, duration_seconds: float = 60.0) -> str:
        """Record that a model hit rate limit, return suggested failover.

        Args:
            model_name: Model that hit rate limit
            duration_seconds: How long to consider it rate-limited

        Returns:
            Suggested failover model name, or empty string if none available
        """
        import time

        self._rate_limited.add(model_name)

        if model_name in self._available_models:
            self._available_models[model_name].rate_limited = True
            self._available_models[model_name].last_429_time = time.time()

        failover = self.get_next_failover(model_name)
        if failover:
            logger.info(f"Model {model_name} rate-limited, suggesting failover to {failover}")
        else:
            logger.warning(f"Model {model_name} rate-limited, no failover available!")

        # Schedule automatic clear after duration
        asyncio.get_event_loop().call_later(
            duration_seconds, lambda: self._clear_rate_limit(model_name)
        )

        return failover or ""

    def _clear_rate_limit(self, model_name: str) -> None:
        """Clear rate limit flag for a model."""
        self._rate_limited.discard(model_name)
        if model_name in self._available_models:
            self._available_models[model_name].rate_limited = False
        logger.debug(f"Cleared rate limit for {model_name}")

    def is_rate_limited(self, model_name: str) -> bool:
        """Check if a model is currently rate-limited."""
        return model_name in self._rate_limited

    def get_available_models(self, exclude_rate_limited: bool = True) -> List[str]:
        """Get list of available models."""
        self.load_from_model_factory()
        if exclude_rate_limited:
            return [m for m in self._available_models.keys() if m not in self._rate_limited]
        return list(self._available_models.keys())


# Global singleton accessor
def get_failover_manager() -> RateLimitFailover:
    """Get the global RateLimitFailover instance."""
    return RateLimitFailover()


def with_rate_limit_failover(
    model_param: str = "model",
    max_failovers: int = 3,
) -> Callable[[F], F]:
    """Decorator that automatically handles rate limit failovers.

    Wraps an async function and automatically retries with failover models
    when rate limits (429) are encountered.

    Args:
        model_param: Name of the parameter that specifies the model
        max_failovers: Maximum number of failover attempts

    Usage:
        @with_rate_limit_failover(model_param="model_name")
        async def call_model(prompt: str, model_name: str = "cerebras") -> str:
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            failover_mgr = get_failover_manager()
            current_model = kwargs.get(model_param, "")
            attempts = 0
            last_error = None

            while attempts <= max_failovers:
                try:
                    result = await func(*args, **kwargs)
                    return result

                except Exception as e:
                    error_str = str(e).lower()
                    last_error = e

                    # Check if this is a rate limit error
                    if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
                        attempts += 1
                        logger.info(
                            f"Rate limit on {current_model} (attempt {attempts}/{max_failovers + 1})"
                        )

                        # Get failover
                        failover = failover_mgr.record_rate_limit(current_model, 60.0)

                        if not failover or attempts > max_failovers:
                            logger.error(f"No more failovers available after {attempts} attempts")
                            raise

                        # Update model parameter for retry
                        logger.info(f"Failing over from {current_model} to {failover}")
                        kwargs[model_param] = failover
                        current_model = failover

                        # Brief pause before retry
                        await asyncio.sleep(0.5)
                        continue
                    else:
                        # Not a rate limit error - don't retry
                        raise

            # Should not reach here, but safety
            if last_error:
                raise last_error
            raise RuntimeError("Exhausted failover attempts")

        return wrapper  # type: ignore

    return decorator


# Integration with TokenBudgetManager
def enhanced_failover_chain() -> Dict[str, str]:
    """Get enhanced failover chain that includes OAuth-configured models.

    This can be used to update TokenBudgetManager.FAILOVER_CHAIN dynamically.
    """
    failover_mgr = get_failover_manager()
    chain = {}

    for model_name in failover_mgr.get_available_models(exclude_rate_limited=False):
        failover = failover_mgr.get_next_failover(model_name)
        if failover:
            chain[model_name] = failover

    return chain
