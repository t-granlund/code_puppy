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
    # Tier 1: Architect - Complex planning, reasoning, orchestration
    "opus": 1,
    "o3": 1,
    "o1": 1,
    "opus-4-5-thinking": 1,
    "kimi-k2.5": 1,           # 1T MoE, 256K context, agent swarms
    "qwen3-235b-thinking": 1, # 235B MoE, 262K context, AIME leader
    
    # Tier 2: Builder High - Complex coding, refactoring
    "codex": 2,
    "gpt-5": 2,
    "gpt-5.2": 2,
    "gpt-5.2-codex": 2,       # Optimized for agentic coding
    "deepseek-r1": 2,         # 671B, 131K context, reasoning model
    "kimi-k2-thinking": 2,    # 1T MoE, thinking mode
    "sonnet-4-5-thinking-high": 2,
    
    # Tier 3: Builder Mid - Standard development
    "sonnet": 3,
    "gpt-4": 3,
    "minimax-m2": 3,          # 1M context, multilang coding
    "sonnet-4-5-thinking-medium": 3,
    "sonnet-4-5-thinking-low": 3,
    "gemini-3-pro": 3,        # 1M context, 64K output
    
    # Tier 4: Librarian - Context, search, docs
    "gemini": 4,
    "haiku": 4,
    "flash": 4,
    "gemini-3-flash": 4,      # 1M context, fast
    "openrouter": 4,          # Free tier models
    "stepfun": 4,
    "arcee": 4,
    
    # Tier 5: Sprinter - High-volume, fast generation
    "cerebras": 5,
    "glm": 5,
    "glm-4.7": 5,             # 358B MoE, 200K context, agentic coding
}


# =============================================================================
# WORKLOAD-SPECIFIC FAILOVER CHAINS
# =============================================================================
# These define ordered lists of models for each workload type.
# First model is primary, subsequent are fallbacks.
#
# STRATEGY:
# - ORCHESTRATOR: Start with Claude Opus (best reasoning) → Kimi K2.5 (agent swarms)
#                 → Qwen3 Thinking (math reasoning) → fall to Sonnet
# - REASONING: Claude Sonnet thinking → DeepSeek R1 (reasoning model)
#              → Kimi K2 Thinking → GPT-5.2-Codex
# - CODING: Cerebras GLM (fastest) → GPT-5.2-Codex (agentic) → MiniMax M2.1
#           → Gemini Flash (1M context backup)
# - LIBRARIAN: Haiku (cheap) → Gemini Flash (1M context) → OpenRouter free
#              → Cerebras as last resort

WORKLOAD_CHAINS: Dict[WorkloadType, List[str]] = {
    # Pack leader, governor, planning - needs maximum reasoning power
    WorkloadType.ORCHESTRATOR: [
        "antigravity-claude-opus-4-5-thinking-high",  # Tier 1: Most stable Opus
        "antigravity-claude-opus-4-5-thinking-medium",
        "claude-code-claude-opus-4-5-20251101",      # Tier 1: Best reasoning (may have 500 errors)
        "synthetic-Kimi-K2.5-Thinking",               # Tier 1: 1T MoE, agent swarms
        "synthetic-hf-Qwen-Qwen3-235B-A22B-Thinking-2507",  # Tier 1: Math leader
        "antigravity-claude-opus-4-5-thinking-low",
        "claude-code-claude-sonnet-4-5-20250929",    # Fall to Tier 2/3
        "antigravity-claude-sonnet-4-5-thinking-high",
        "chatgpt-gpt-5.2-codex",                     # Tier 2: Agentic coding
        "Cerebras-GLM-4.7",                          # Emergency fallback
    ],
    
    # Complex logic, security audit, design - needs deep reasoning
    WorkloadType.REASONING: [
        "claude-code-claude-sonnet-4-5-20250929",    # Tier 2/3: Agentic coding leader
        "antigravity-claude-sonnet-4-5-thinking-high",
        "synthetic-hf-deepseek-ai-DeepSeek-R1-0528", # Tier 2: 671B reasoning model
        "synthetic-Kimi-K2-Thinking",                 # Tier 2: 1T MoE thinking
        "antigravity-claude-sonnet-4-5-thinking-medium",
        "chatgpt-gpt-5.2-codex",                     # Tier 2: Strong reasoning
        "antigravity-claude-sonnet-4-5-thinking-low",
        "antigravity-claude-sonnet-4-5",
        "synthetic-MiniMax-M2.1",                     # Tier 3: 1M context coding
        "Cerebras-GLM-4.7",
    ],
    
    # Main code generation (high volume, fast) - needs speed + quality
    WorkloadType.CODING: [
        "Cerebras-GLM-4.7",                          # Tier 5: Fastest, agentic
        "synthetic-GLM-4.7",                          # Tier 5: Backup GLM via Synthetic
        "chatgpt-gpt-5.2-codex",                     # Tier 2: Agentic coding
        "synthetic-MiniMax-M2.1",                     # Tier 3: 1M context, multilang
        "synthetic-hf-MiniMaxAI-MiniMax-M2.1",       # Tier 3: Backup MiniMax
        "claude-code-claude-haiku-4-5-20251001",     # Tier 4: Fast, cheaper
        "antigravity-gemini-3-flash",                # Tier 4: 1M context, fast
        "antigravity-claude-sonnet-4-5",             # Tier 3: Quality fallback
        "synthetic-hf-zai-org-GLM-4.7",              # Tier 5: Synthetic GLM backup
    ],
    
    # Search, docs, context (less intensive) - needs context + cost efficiency
    WorkloadType.LIBRARIAN: [
        "claude-code-claude-haiku-4-5-20251001",     # Tier 4: Fast, cheap
        "antigravity-gemini-3-flash",                # Tier 4: 1M context
        "openrouter-arcee-ai-trinity-large-preview-free",  # Tier 4: Free
        "openrouter-stepfun-step-3.5-flash-free",    # Tier 4: Free
        "antigravity-gemini-3-pro-low",              # Tier 4: Gemini Pro backup
        "synthetic-hf-zai-org-GLM-4.7",              # Tier 5: Synthetic GLM
        "Cerebras-GLM-4.7",                          # Tier 5: Emergency
        "synthetic-GLM-4.7",                          # Tier 5: Backup GLM
        "antigravity-gemini-3-pro-high",             # Tier 4: High-compute Gemini
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
    "antigravity-claude-opus-4-5-thinking-high": "synthetic-Kimi-K2.5-Thinking",
    "synthetic-Kimi-K2.5-Thinking": "antigravity-claude-opus-4-5-thinking-medium",
    "antigravity-claude-opus-4-5-thinking-medium": "synthetic-hf-Qwen-Qwen3-235B-A22B-Thinking-2507",
    "synthetic-hf-Qwen-Qwen3-235B-A22B-Thinking-2507": "antigravity-claude-opus-4-5-thinking-low",
    "antigravity-claude-opus-4-5-thinking-low": "antigravity-claude-sonnet-4-5-thinking-high",
    "synthetic-hf-moonshotai-Kimi-K2.5": "antigravity-claude-opus-4-5-thinking-medium",
    
    # =====================================================================
    # BUILDER TIER - Complex logic, design, refactoring
    # =====================================================================
    "claude_sonnet": "antigravity-claude-sonnet-4-5",
    "claude-code-claude-sonnet-4-5-20250929": "antigravity-claude-sonnet-4-5",
    "antigravity-claude-sonnet-4-5": "synthetic-hf-deepseek-ai-DeepSeek-R1-0528",
    "synthetic-hf-deepseek-ai-DeepSeek-R1-0528": "synthetic-Kimi-K2-Thinking",
    "synthetic-Kimi-K2-Thinking": "antigravity-claude-sonnet-4-5-thinking-high",
    "antigravity-claude-sonnet-4-5-thinking-high": "chatgpt-gpt-5.2-codex",
    "chatgpt-gpt-5.2-codex": "antigravity-claude-sonnet-4-5-thinking-medium",
    "antigravity-claude-sonnet-4-5-thinking-medium": "chatgpt-gpt-5.2",
    "chatgpt-gpt-5.2": "antigravity-claude-sonnet-4-5-thinking-low",
    "antigravity-claude-sonnet-4-5-thinking-low": "synthetic-MiniMax-M2.1",
    "synthetic-MiniMax-M2.1": "Cerebras-GLM-4.7",
    
    # =====================================================================
    # SPRINTER TIER - Main code work (high volume, fast generation)
    # =====================================================================
    "cerebras": "synthetic-GLM-4.7",
    "cerebras-glm-4.7": "synthetic-GLM-4.7",
    "Cerebras-GLM-4.7": "synthetic-GLM-4.7",
    "synthetic-GLM-4.7": "claude-code-claude-haiku-4-5-20251001",
    "synthetic-hf-zai-org-GLM-4.7": "claude-code-claude-haiku-4-5-20251001",
    "claude-haiku": "antigravity-gemini-3-flash",
    "claude_haiku": "antigravity-gemini-3-flash",
    "claude-code-claude-haiku-4-5-20251001": "antigravity-gemini-3-flash",
    
    # =====================================================================
    # LIBRARIAN TIER - Search, docs, context, less intensive code
    # =====================================================================
    "antigravity-gemini-3-pro-high": "antigravity-gemini-3-pro-low",
    "antigravity-gemini-3-pro-low": "antigravity-gemini-3-flash",
    "antigravity-gemini-3-flash": "openrouter-arcee-ai-trinity-large-preview-free",
    "openrouter-arcee-ai-trinity-large-preview-free": "openrouter-stepfun-step-3.5-flash-free",
    "openrouter-stepfun-step-3.5-flash-free": "Cerebras-GLM-4.7",
    
    # =====================================================================
    # SYNTHETIC/HF MODELS - Backup chains
    # =====================================================================
    "synthetic-hf-MiniMaxAI-MiniMax-M2.1": "synthetic-MiniMax-M2.1",
    "synthetic-hf-moonshotai-Kimi-K2-Thinking": "synthetic-Kimi-K2-Thinking",
    
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
# Model specs researched from official docs and benchmarks.
# Updated 2026-02-02 based on actual plan limits and usage data.
#
# COMPREHENSIVE LIMIT TRACKING:
# - tokens_per_minute: TPM (most APIs)
# - requests_per_minute: RPM
# - tokens_per_day: Daily token limit
# - requests_per_day: Daily request limit  
# - rolling_window_hours: For providers with rolling windows (e.g., 5-hour)
# - tokens_per_window / requests_per_window: Limits for rolling windows
# - optimal_prompt_size: Recommended prompt size for best performance
# - context_length: Maximum input tokens
# - max_output: Maximum output tokens

PROVIDER_LIMITS: Dict[str, Dict[str, int]] = {
    # =========================================================================
    # Tier 5: The Sprinter - High volume, fast generation
    # =========================================================================
    # Cerebras Code Pro ($50/month)
    # Based on Cerebras API docs and observed usage patterns
    "cerebras": {
        "tokens_per_minute": 1_000_000,    # 1M TPM on Code Pro
        "tokens_per_day": 24_000_000,      # 24M daily limit
        "requests_per_minute": 50,          # RPM limit
        "requests_per_day": 10_000,         # ~10K requests/day estimated
        "reset_window_seconds": 60,
        "context_length": 131_072,
        "max_output": 40_000,
        "optimal_prompt_size": 50_000,      # Conservative for rate limits
        "plan": "code_pro",
        "cost_per_month": 50,
    },
    # Synthetic.new Pro ($60/month) - Z.ai GLM 4.7
    # Based on usage data: peaks of 50+ requests/min, 500K-800K tokens/min
    # Uses 5-hour rolling windows for rate limiting
    "synthetic_glm": {
        "tokens_per_minute": 800_000,       # Observed peak ~800K/min
        "tokens_per_day": 50_000_000,       # Pro tier - high daily limit
        "requests_per_minute": 60,           # Observed 50-57 rpm peaks
        "requests_per_day": 50_000,          # ~50K requests/day estimated
        "reset_window_seconds": 300,         # 5-minute window for minute resets
        "rolling_window_hours": 5,           # Pro plan uses 5-hour windows
        "tokens_per_window": 10_000_000,     # ~10M tokens per 5-hour window
        "requests_per_window": 5_000,        # ~5K requests per 5-hour window
        "context_length": 200_000,
        "max_output": 16_000,
        "optimal_prompt_size": 80_000,       # Good balance for GLM
        "plan": "pro",
        "cost_per_month": 60,
    },
    
    # =========================================================================
    # Tier 4: The Librarian - Context, search, docs
    # =========================================================================
    "gemini": {
        "tokens_per_minute": 100_000,
        "tokens_per_day": 2_000_000,
        "requests_per_minute": 30,
        "requests_per_day": 5_000,
        "reset_window_seconds": 60,
        "context_length": 1_000_000,
        "max_output": 64_000,
        "optimal_prompt_size": 500_000,      # Can handle large context
    },
    "gemini_flash": {
        "tokens_per_minute": 150_000,
        "tokens_per_day": 2_000_000,
        "requests_per_minute": 50,
        "requests_per_day": 10_000,
        "reset_window_seconds": 60,
        "context_length": 1_000_000,
        "max_output": 8_000,
        "optimal_prompt_size": 200_000,      # Fast model, moderate context
    },
    "openrouter_free": {
        "tokens_per_minute": 50_000,        # Conservative for free tier
        "tokens_per_day": 500_000,
        "requests_per_minute": 20,
        "requests_per_day": 1_000,           # Free tier is limited
        "reset_window_seconds": 60,
        "context_length": 128_000,
        "max_output": 8_000,
        "optimal_prompt_size": 32_000,
        "plan": "free",
        "cost_per_month": 0,
    },
    
    # =========================================================================
    # Tier 3: Builder Mid - Standard development
    # =========================================================================
    "minimax": {
        "tokens_per_minute": 100_000,
        "tokens_per_day": 5_000_000,
        "requests_per_minute": 30,
        "requests_per_day": 5_000,
        "reset_window_seconds": 60,
        "context_length": 1_000_000,
        "max_output": 1_000_000,
        "optimal_prompt_size": 300_000,      # MiniMax excels at long context
    },
    
    # =========================================================================
    # Tier 2: Builder High - Complex coding, reasoning
    # =========================================================================
    "codex": {
        "tokens_per_minute": 200_000,
        "tokens_per_day": 10_000_000,
        "requests_per_minute": 60,
        "requests_per_day": 10_000,
        "reset_window_seconds": 60,
        "context_length": 400_000,
        "max_output": 32_000,
        "optimal_prompt_size": 100_000,
    },
    "gpt_5": {
        "tokens_per_minute": 200_000,
        "tokens_per_day": 10_000_000,
        "requests_per_minute": 60,
        "requests_per_day": 10_000,
        "reset_window_seconds": 60,
        "context_length": 400_000,
        "max_output": 32_000,
        "optimal_prompt_size": 100_000,
    },
    "deepseek": {
        "tokens_per_minute": 100_000,
        "tokens_per_day": 5_000_000,
        "requests_per_minute": 30,
        "requests_per_day": 5_000,
        "reset_window_seconds": 60,
        "context_length": 131_072,
        "max_output": 131_072,
        "optimal_prompt_size": 60_000,
    },
    "kimi": {
        "tokens_per_minute": 100_000,
        "tokens_per_day": 5_000_000,
        "requests_per_minute": 30,
        "requests_per_day": 5_000,
        "reset_window_seconds": 60,
        "context_length": 256_000,
        "max_output": 32_000,
        "optimal_prompt_size": 100_000,
    },
    "qwen": {
        "tokens_per_minute": 100_000,
        "tokens_per_day": 5_000_000,
        "requests_per_minute": 30,
        "requests_per_day": 5_000,
        "reset_window_seconds": 60,
        "context_length": 262_144,
        "max_output": 16_384,
        "optimal_prompt_size": 100_000,
    },
    "claude_sonnet": {
        "tokens_per_minute": 100_000,
        "tokens_per_day": 5_000_000,
        "requests_per_minute": 40,
        "requests_per_day": 8_000,
        "reset_window_seconds": 60,
        "context_length": 200_000,
        "max_output": 64_000,
        "optimal_prompt_size": 80_000,
    },
    
    # =========================================================================
    # Tier 1: The Architect - Planning, reasoning, orchestration
    # =========================================================================
    "claude_opus": {
        "tokens_per_minute": 50_000,        # Lower TPM for premium model
        "tokens_per_day": 1_000_000,
        "requests_per_minute": 20,
        "requests_per_day": 2_000,
        "reset_window_seconds": 60,
        "context_length": 200_000,
        "max_output": 64_000,
        "optimal_prompt_size": 80_000,
    },
    
    # =========================================================================
    # OAuth Providers - Subscription-based limits
    # =========================================================================
    # Antigravity Pro ($20/month) - Google Cloud Code via OAuth
    "antigravity": {
        "tokens_per_minute": 200_000,
        "tokens_per_day": 10_000_000,
        "requests_per_minute": 30,
        "requests_per_day": 5_000,
        "reset_window_seconds": 60,
        "context_length": 200_000,
        "max_output": 64_000,
        "optimal_prompt_size": 80_000,
        "plan": "pro",
        "cost_per_month": 20,
    },
    # Claude Max ($100/month) - High limits via OAuth
    "claude_code": {
        "tokens_per_minute": 200_000,
        "tokens_per_day": 20_000_000,
        "requests_per_minute": 50,
        "requests_per_day": 15_000,
        "reset_window_seconds": 60,
        "context_length": 200_000,
        "max_output": 64_000,
        "optimal_prompt_size": 80_000,
        "plan": "max",
        "cost_per_month": 100,
    },
    # ChatGPT Teams ($35/month) - Team tier via OAuth
    "chatgpt_teams": {
        "tokens_per_minute": 150_000,
        "tokens_per_day": 10_000_000,
        "requests_per_minute": 40,
        "requests_per_day": 8_000,
        "reset_window_seconds": 60,
        "context_length": 128_000,
        "max_output": 32_000,
        "optimal_prompt_size": 50_000,
        "plan": "teams",
        "cost_per_month": 35,
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


def get_chain_for_workload(workload: WorkloadType, filter_by_credentials: bool = True) -> List[str]:
    """Get the full failover chain for a workload type.
    
    Args:
        workload: The workload type (ORCHESTRATOR, REASONING, CODING, LIBRARIAN)
        filter_by_credentials: If True, exclude models without valid credentials
        
    Returns:
        Ordered list of models to try (filtered by credential availability).
    """
    chain = WORKLOAD_CHAINS.get(workload, WORKLOAD_CHAINS[WorkloadType.CODING])
    
    if filter_by_credentials:
        try:
            from code_puppy.core.credential_availability import filter_workload_chain
            filtered = filter_workload_chain(chain)
            if filtered:
                return filtered
            # If all filtered out, return original (will fail at runtime with clear error)
            import logging
            logging.getLogger(__name__).warning(
                f"No models with credentials for {workload.name}, returning unfiltered chain"
            )
        except ImportError:
            pass  # Module not available, return unfiltered
    
    return chain


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
    
    # Pattern matching for provider detection
    # OAuth providers first (check model name patterns)
    if "antigravity" in provider_lower:
        return PROVIDER_LIMITS["antigravity"]
    elif "claude_code" in provider_lower or "claude-code" in provider_lower:
        return PROVIDER_LIMITS["claude_code"]
    elif "chatgpt" in provider_lower or "teams" in provider_lower:
        return PROVIDER_LIMITS["chatgpt_teams"]
    
    # Tier 5: Sprinter
    elif "cerebras" in provider_lower:
        return PROVIDER_LIMITS["cerebras"]
    elif "synthetic" in provider_lower:
        return PROVIDER_LIMITS["synthetic_glm"]
    elif "glm" in provider_lower or "z.ai" in provider_lower:
        return PROVIDER_LIMITS["synthetic_glm"]
    
    # Tier 4: Librarian
    elif "openrouter" in provider_lower or "stepfun" in provider_lower or "arcee" in provider_lower:
        return PROVIDER_LIMITS["openrouter_free"]
    elif "flash" in provider_lower:
        return PROVIDER_LIMITS["gemini_flash"]
    elif "haiku" in provider_lower:
        return PROVIDER_LIMITS["gemini_flash"]
    elif "gemini" in provider_lower:
        return PROVIDER_LIMITS["gemini"]
    
    # Tier 3: Builder Mid
    elif "minimax" in provider_lower or "m2" in provider_lower:
        return PROVIDER_LIMITS["minimax"]
    
    # Tier 2: Builder High
    elif "deepseek" in provider_lower or "r1" in provider_lower:
        return PROVIDER_LIMITS["deepseek"]
    elif "kimi" in provider_lower or "k2" in provider_lower:
        return PROVIDER_LIMITS["kimi"]
    elif "qwen" in provider_lower:
        return PROVIDER_LIMITS["qwen"]
    elif "gpt" in provider_lower or "codex" in provider_lower:
        return PROVIDER_LIMITS["codex"]
    elif "sonnet" in provider_lower:
        return PROVIDER_LIMITS["claude_sonnet"]
    
    # Tier 1: Architect
    elif "opus" in provider_lower:
        return PROVIDER_LIMITS["claude_opus"]
    
    # Default to conservative limits (gemini-level)
    return PROVIDER_LIMITS["gemini"]
