"""Unified Failover Configuration - Single Source of Truth.

This module consolidates all failover chain definitions to eliminate redundancy.
Previously, failover chains were defined in both:
- code_puppy/core/token_budget.py (FAILOVER_CHAIN dict)
- code_puppy/core/rate_limit_failover.py (WORKLOAD_CHAINS dict)

Now they are defined here and imported by both modules.

Implements GLM-Token-Saver best practices:
- Workload-aware routing (Orchestrator, Reasoning, Coding, Librarian)
- Proactive failover based on rate limit headers
- Tier-respecting fallback (same tier → lower tier)
"""

from enum import IntEnum
from typing import Dict, List, Optional


class WorkloadType(IntEnum):
    """Types of workloads for smart failover routing.
    
    Each workload type has its own failover chain optimized for:
    - ORCHESTRATOR: Pack leader, governor, planning - needs Opus/Sonnet
    - REASONING: Complex logic, security audit - needs Opus/Sonnet  
    - CODING: Main code generation - Cerebras preferred (speed)
    - LIBRARIAN: Search, docs, context - Gemini/Haiku (cost)
    """
    
    ORCHESTRATOR = 1  # Pack leader, governor, planning
    REASONING = 2     # Complex logic, security audit
    CODING = 3        # Main code generation
    LIBRARIAN = 4     # Search, docs, context


class FailoverPriority(IntEnum):
    """Priority order for failover (lower = prefer first)."""
    SAME_TIER = 1      # Same tier, different provider
    ONE_TIER_DOWN = 2  # One tier below
    TWO_TIERS_DOWN = 3 # Two tiers below
    EMERGENCY = 4      # Any working model


# =============================================================================
# MODEL TIER MAPPINGS (Read-only reference data)
# =============================================================================
# Tier 1: Architect (big reasoning, planning, orchestrator)
# Tier 2: Builder High (strong coding, complex logic)
# Tier 3: Builder Mid (capable all-rounder)
# Tier 4: Librarian (search, docs, less intensive code)
# Tier 5: Sprinter (main code work, ultra-fast)

TIER_MAPPINGS: Dict[str, int] = {
    # Tier 1: Architect
    "opus": 1,
    "o3": 1,
    "o1": 1,
    "opus-4-5-thinking": 1,
    
    # Tier 2: Builder High
    "codex": 2,
    "gpt-5": 2,
    "sonnet-4-5-thinking-high": 2,
    
    # Tier 3: Builder Mid
    "sonnet": 3,
    "gpt-4": 3,
    "sonnet-4-5-thinking-medium": 3,
    "sonnet-4-5-thinking-low": 3,
    
    # Tier 4: Librarian
    "gemini": 4,
    "haiku": 4,
    "flash": 4,
    "gemini-3-pro": 4,
    "gemini-3-flash": 4,
    
    # Tier 5: Sprinter
    "cerebras": 5,
    "glm": 5,
}


# =============================================================================
# WORKLOAD-SPECIFIC FAILOVER CHAINS
# =============================================================================
# These define ordered lists of models for each workload type.
# First model is primary, subsequent are fallbacks.

WORKLOAD_CHAINS: Dict[WorkloadType, List[str]] = {
    # Pack leader, governor, planning - needs reasoning power
    WorkloadType.ORCHESTRATOR: [
        "claude-code-claude-opus-4-5-20251101",
        "antigravity-claude-opus-4-5-thinking-high",
        "antigravity-claude-opus-4-5-thinking-medium",
        "antigravity-claude-opus-4-5-thinking-low",
        "claude-code-claude-sonnet-4-5-20250929",
        "antigravity-claude-sonnet-4-5-thinking-high",
        "antigravity-claude-sonnet-4-5-thinking-medium",
        "Cerebras-GLM-4.7",
    ],
    
    # Complex logic, security audit, design
    WorkloadType.REASONING: [
        "claude-code-claude-sonnet-4-5-20250929",
        "antigravity-claude-sonnet-4-5-thinking-high",
        "antigravity-claude-sonnet-4-5-thinking-medium",
        "antigravity-claude-sonnet-4-5-thinking-low",
        "antigravity-claude-sonnet-4-5",
        "Cerebras-GLM-4.7",
    ],
    
    # Main code generation (high volume, fast)
    WorkloadType.CODING: [
        "Cerebras-GLM-4.7",
        "claude-code-claude-haiku-4-5-20251001",
        "antigravity-gemini-3-flash",
    ],
    
    # Search, docs, context (less intensive)
    WorkloadType.LIBRARIAN: [
        "claude-code-claude-haiku-4-5-20251001",
        "antigravity-gemini-3-flash",
        "Cerebras-GLM-4.7",
    ],
}


# =============================================================================
# UNIFIED AGENT WORKLOAD REGISTRY
# =============================================================================
# Maps agent names to their appropriate workload type for automatic model selection.

AGENT_WORKLOAD_REGISTRY: Dict[str, WorkloadType] = {
    # ═══════════════════════════════════════════════════════════════════
    # ORCHESTRATORS (Claude Opus → Antigravity Opus → Gemini Pro → Codex)
    # ═══════════════════════════════════════════════════════════════════
    "pack-leader": WorkloadType.ORCHESTRATOR,
    "helios": WorkloadType.ORCHESTRATOR,
    "epistemic-architect": WorkloadType.ORCHESTRATOR,
    "planning": WorkloadType.ORCHESTRATOR,
    "agent-creator": WorkloadType.ORCHESTRATOR,
    
    # ═══════════════════════════════════════════════════════════════════
    # REASONING (Claude Sonnet → Antigravity Sonnet → Gemini Pro → Codex)
    # ═══════════════════════════════════════════════════════════════════
    "shepherd": WorkloadType.REASONING,
    "watchdog": WorkloadType.REASONING,
    "code-reviewer": WorkloadType.REASONING,
    "python-reviewer": WorkloadType.REASONING,
    "c-reviewer": WorkloadType.REASONING,
    "cpp-reviewer": WorkloadType.REASONING,
    "golang-reviewer": WorkloadType.REASONING,
    "javascript-reviewer": WorkloadType.REASONING,
    "typescript-reviewer": WorkloadType.REASONING,
    "prompt-reviewer": WorkloadType.REASONING,
    "qa-expert": WorkloadType.REASONING,
    "security-auditor": WorkloadType.REASONING,
    
    # ═══════════════════════════════════════════════════════════════════
    # CODING (Cerebras GLM 4.7 → Claude Haiku → Gemini Flash)
    # ═══════════════════════════════════════════════════════════════════
    "husky": WorkloadType.CODING,
    "terrier": WorkloadType.CODING,
    "retriever": WorkloadType.CODING,
    "code-puppy": WorkloadType.CODING,
    "python-programmer": WorkloadType.CODING,
    "qa-kitten": WorkloadType.CODING,
    "c-programmer": WorkloadType.CODING,
    "cpp-programmer": WorkloadType.CODING,
    "golang-programmer": WorkloadType.CODING,
    "javascript-programmer": WorkloadType.CODING,
    "typescript-programmer": WorkloadType.CODING,
    "ui-programmer": WorkloadType.CODING,
    "test-generator": WorkloadType.CODING,
    "commit-message-generator": WorkloadType.CODING,
    "rag-agent": WorkloadType.CODING,
    
    # ═══════════════════════════════════════════════════════════════════
    # LIBRARIAN (Haiku → Gemini Flash → Cerebras)
    # ═══════════════════════════════════════════════════════════════════
    "bloodhound": WorkloadType.LIBRARIAN,
    "lab-rat": WorkloadType.LIBRARIAN,
    "file-summarizer": WorkloadType.LIBRARIAN,
    "doc-writer": WorkloadType.LIBRARIAN,
}


# =============================================================================
# LINEAR FAILOVER CHAIN (for simple A → B lookups)
# =============================================================================
# This provides direct model-to-model fallback for backward compatibility.
# Used when a specific model hits rate limits.

FAILOVER_CHAIN: Dict[str, str] = {
    # =====================================================================
    # ARCHITECT TIER - Big reasoning, planning, orchestrator roles
    # =====================================================================
    "claude_opus": "antigravity-claude-opus-4-5-thinking-high",
    "claude-code-claude-opus-4-5-20251101": "antigravity-claude-opus-4-5-thinking-high",
    "antigravity-claude-opus-4-5-thinking-high": "antigravity-claude-opus-4-5-thinking-medium",
    "antigravity-claude-opus-4-5-thinking-medium": "antigravity-claude-opus-4-5-thinking-low",
    "antigravity-claude-opus-4-5-thinking-low": "antigravity-claude-sonnet-4-5-thinking-high",
    
    # =====================================================================
    # BUILDER TIER - Complex logic, design, refactoring
    # =====================================================================
    "claude_sonnet": "antigravity-claude-sonnet-4-5",
    "claude-code-claude-sonnet-4-5-20250929": "antigravity-claude-sonnet-4-5",
    "antigravity-claude-sonnet-4-5": "antigravity-claude-sonnet-4-5-thinking-high",
    "antigravity-claude-sonnet-4-5-thinking-high": "antigravity-claude-sonnet-4-5-thinking-medium",
    "antigravity-claude-sonnet-4-5-thinking-medium": "antigravity-claude-sonnet-4-5-thinking-low",
    "antigravity-claude-sonnet-4-5-thinking-low": "Cerebras-GLM-4.7",
    
    # =====================================================================
    # SPRINTER TIER - Main code work (high volume, fast generation)
    # =====================================================================
    "cerebras": "claude-code-claude-haiku-4-5-20251001",
    "cerebras-glm-4.7": "claude-code-claude-haiku-4-5-20251001",
    "Cerebras-GLM-4.7": "claude-code-claude-haiku-4-5-20251001",
    "claude-haiku": "antigravity-gemini-3-flash",
    "claude_haiku": "antigravity-gemini-3-flash",
    "claude-code-claude-haiku-4-5-20251001": "antigravity-gemini-3-flash",
    
    # =====================================================================
    # LIBRARIAN TIER - Search, docs, context, less intensive code
    # =====================================================================
    "antigravity-gemini-3-pro-high": "antigravity-gemini-3-pro-low",
    "antigravity-gemini-3-pro-low": "antigravity-gemini-3-flash",
    "antigravity-gemini-3-flash": "Cerebras-GLM-4.7",
    
    # ChatGPT models are OAuth-only and added at runtime
}


# =============================================================================
# TOKEN BUDGET CONSTANTS (Single Source of Truth)
# =============================================================================
# These constants are used across the codebase for consistent token budgeting.
# Import from here instead of hardcoding values like 50_000.

# Cerebras GLM context limits
CEREBRAS_TARGET_INPUT_TOKENS: int = 50_000  # Conservative target for rate limits
CEREBRAS_MAX_CONTEXT_TOKENS: int = 131_072  # 131K context window
CEREBRAS_MAX_OUTPUT_TOKENS: int = 40_000  # Max output on Cerebras

# Summary/compaction thresholds
FORCE_SUMMARY_THRESHOLD: int = CEREBRAS_TARGET_INPUT_TOKENS  # When to force summarization

# Antigravity OAuth limits (shared quota across all antigravity-* models)
ANTIGRAVITY_MAX_INPUT_TOKENS: int = 100_000
ANTIGRAVITY_COMPACTION_THRESHOLD: float = 0.50  # 50% usage triggers compaction


# =============================================================================
# PROVIDER RATE LIMITS
# =============================================================================
# Consolidated from token_budget.py - static limits per provider.

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


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_failover_for_model(model: str) -> Optional[str]:
    """Get the next model in the failover chain.
    
    Args:
        model: Current model name (case-sensitive)
        
    Returns:
        Next model to try, or None if no failover defined.
    """
    return FAILOVER_CHAIN.get(model)


def get_chain_for_workload(workload: WorkloadType) -> List[str]:
    """Get the full failover chain for a workload type.
    
    Args:
        workload: The workload type (ORCHESTRATOR, REASONING, CODING, LIBRARIAN)
        
    Returns:
        Ordered list of models to try.
    """
    return WORKLOAD_CHAINS.get(workload, WORKLOAD_CHAINS[WorkloadType.CODING])


def get_workload_for_agent(agent_name: str) -> WorkloadType:
    """Get the workload type for a given agent.
    
    Args:
        agent_name: Name of the agent (e.g., "pack-leader", "code-puppy")
        
    Returns:
        WorkloadType for the agent, defaults to CODING.
    """
    return AGENT_WORKLOAD_REGISTRY.get(agent_name.lower(), WorkloadType.CODING)


def get_tier_for_model(model: str) -> int:
    """Get the tier number for a model (1=Architect, 5=Sprinter).
    
    Args:
        model: Model name or partial name
        
    Returns:
        Tier number (1-5), or 3 as default.
    """
    model_lower = model.lower()
    for key, tier in TIER_MAPPINGS.items():
        if key in model_lower:
            return tier
    return 3  # Default to Builder Mid


def get_provider_limits(provider: str) -> Dict[str, int]:
    """Get rate limits for a provider.
    
    Args:
        provider: Provider name (e.g., "cerebras", "claude_opus")
        
    Returns:
        Dict with tokens_per_minute, tokens_per_day, reset_window_seconds.
    """
    # Normalize provider name
    provider_lower = provider.lower().replace("-", "_")
    
    if provider_lower in PROVIDER_LIMITS:
        return PROVIDER_LIMITS[provider_lower]
    
    # Pattern matching
    if "cerebras" in provider_lower or "glm" in provider_lower:
        return PROVIDER_LIMITS["cerebras"]
    elif "opus" in provider_lower:
        return PROVIDER_LIMITS["claude_opus"]
    elif "sonnet" in provider_lower:
        return PROVIDER_LIMITS["claude_sonnet"]
    elif "haiku" in provider_lower or "flash" in provider_lower:
        return PROVIDER_LIMITS["gemini_flash"]
    elif "gemini" in provider_lower:
        return PROVIDER_LIMITS["gemini"]
    elif "gpt" in provider_lower or "codex" in provider_lower:
        return PROVIDER_LIMITS["codex"]
    
    # Default to conservative limits
    return PROVIDER_LIMITS["gemini"]
