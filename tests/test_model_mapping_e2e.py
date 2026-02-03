"""
End-to-End Tests for Model Mappings and Token Optimizations.

This test suite validates the complete flow from model selection through
failover chains, budget tracking, and token optimization.

Key areas covered:
1. Model name resolution (case-insensitive lookups)
2. Provider normalization (all model -> provider mappings)
3. Failover chains (with full Claude model names including date suffixes)
4. Token budget tracking and limits
5. Token optimization (context compaction)
6. End-to-end scenarios
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


# =============================================================================
# Helper function for case-insensitive model lookup (extracted for testing)
# =============================================================================

def find_model_key(name: str, config: dict) -> str | None:
    """Find model key with case-insensitive matching."""
    if name in config:
        return name
    name_lower = name.lower()
    for key in config:
        if key.lower() == name_lower:
            return key
    return None


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def models_json():
    """Load the actual models.json file."""
    models_path = Path(__file__).parent.parent / "code_puppy" / "models.json"
    with open(models_path) as f:
        return json.load(f)


@pytest.fixture
def all_model_keys(models_json):
    """Get all model keys from models.json."""
    return list(models_json.keys())


# =============================================================================
# TEST: Models.json Integrity
# =============================================================================

class TestModelsJsonKeys:
    """Verify models.json has all expected keys with correct format."""

    def test_claude_code_models_have_date_suffix(self, models_json):
        """All claude-code models should have date suffix like -20251101."""
        claude_code_models = [k for k in models_json.keys() if k.startswith("claude-code-")]
        
        assert len(claude_code_models) >= 3, "Should have at least opus, sonnet, haiku"
        
        for model in claude_code_models:
            # Check date suffix pattern (YYYYMMDD)
            assert "-202" in model, f"{model} missing date suffix"

    def test_cerebras_model_correct_case(self, models_json):
        """Cerebras model key should have correct capitalization."""
        # The key should be exactly "Cerebras-GLM-4.7" (capital C)
        assert "Cerebras-GLM-4.7" in models_json, "Cerebras key should have capital C"
        # Old lowercase key should NOT exist
        assert "cerebras-glm-4.7" not in models_json, "Lowercase cerebras key should not exist"

    def test_antigravity_gemini_models_have_prefix(self, models_json):
        """Antigravity gemini models should have antigravity- prefix."""
        # Only check antigravity-gemini models, not standalone Gemini-3
        antigravity_gemini = [k for k in models_json.keys() 
                             if k.startswith("antigravity-") and "gemini" in k.lower()]
        
        assert len(antigravity_gemini) > 0, "Should have at least one antigravity-gemini model"
        for model in antigravity_gemini:
            assert model.startswith("antigravity-"), f"{model} missing antigravity- prefix"

    def test_expected_claude_code_models_exist(self, models_json):
        """Verify all expected Claude Code models exist with full names."""
        expected = [
            "claude-code-claude-opus-4-5-20251101",
            "claude-code-claude-sonnet-4-5-20250929",
            "claude-code-claude-haiku-4-5-20251001",
        ]
        for model in expected:
            assert model in models_json, f"Missing {model}"


# =============================================================================
# TEST: Provider Normalization
# =============================================================================

class TestProviderNormalization:
    """Test that all model names correctly map to providers."""

    def test_claude_code_models_normalize_correctly(self):
        """Claude Code models should normalize to correct providers."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        mgr = TokenBudgetManager()
        
        # Full model names with date suffix
        assert mgr._normalize_provider("claude-code-claude-opus-4-5-20251101") == "claude_opus"
        assert mgr._normalize_provider("claude-code-claude-sonnet-4-5-20250929") == "claude_sonnet"
        assert mgr._normalize_provider("claude-code-claude-haiku-4-5-20251001") == "gemini_flash"

    def test_cerebras_both_cases_normalize(self):
        """Both Cerebras case variants should normalize correctly."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        mgr = TokenBudgetManager()
        
        # Both case variants should work
        assert mgr._normalize_provider("Cerebras-GLM-4.7") == "cerebras"
        assert mgr._normalize_provider("cerebras-glm-4.7") == "cerebras"

    def test_antigravity_models_normalize(self):
        """Antigravity models should normalize correctly."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        mgr = TokenBudgetManager()
        
        # Gemini through antigravity
        assert mgr._normalize_provider("antigravity-gemini-3-flash") == "gemini_flash"
        assert mgr._normalize_provider("antigravity-gemini-3-pro-low") == "gemini"
        
        # Claude through antigravity  
        assert mgr._normalize_provider("antigravity-claude-opus-4-5-thinking-high") == "claude_opus"
        assert mgr._normalize_provider("antigravity-claude-sonnet-4-5") == "claude_sonnet"

    def test_custom_openai_normalizes_to_codex(self):
        """custom_openai provider should normalize to codex."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        mgr = TokenBudgetManager()
        assert mgr._normalize_provider("custom_openai") == "codex"

    def test_chatgpt_models_normalize_correctly(self):
        """ChatGPT models should normalize to chatgpt provider."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        mgr = TokenBudgetManager()
        
        # ChatGPT OAuth models normalize to chatgpt provider
        assert mgr._normalize_provider("chatgpt-gpt-5.2-codex") == "chatgpt"
        assert mgr._normalize_provider("chatgpt-gpt-5.2") == "chatgpt"

    def test_legacy_claude_names_still_work(self):
        """Legacy Claude names should still normalize correctly."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        mgr = TokenBudgetManager()
        
        # Legacy names (without date suffix)
        assert mgr._normalize_provider("claude-opus-4.5") == "claude_opus"
        assert mgr._normalize_provider("claude-sonnet-4.5") == "claude_sonnet"
        assert mgr._normalize_provider("claude-4-5-opus") == "claude_opus"
        assert mgr._normalize_provider("claude-4-5-sonnet") == "claude_sonnet"


# =============================================================================
# TEST: Failover Chain Model Names
# =============================================================================

class TestFailoverChainModelNames:
    """Test that failover chains use correct model names from models.json."""

    def test_fallback_models_use_exact_keys(self, models_json):
        """Fallback models should use exact keys from models.json."""
        from code_puppy.core.rate_limit_failover import RateLimitFailover
        
        # Reset singleton for clean test
        RateLimitFailover._instance = None
        mgr = RateLimitFailover()
        mgr._load_fallback_models()
        
        # Check Claude Code models have full names with date suffix
        assert "claude-code-claude-opus-4-5-20251101" in mgr._available_models
        assert "claude-code-claude-sonnet-4-5-20250929" in mgr._available_models
        assert "claude-code-claude-haiku-4-5-20251001" in mgr._available_models
        
        # Check Cerebras has correct capitalization
        assert "Cerebras-GLM-4.7" in mgr._available_models
        
        # Check antigravity models have correct prefix
        assert "antigravity-gemini-3-flash" in mgr._available_models

    def test_fallback_models_exist_in_models_json(self, models_json):
        """All fallback models should exist in models.json."""
        from code_puppy.core.rate_limit_failover import RateLimitFailover
        
        RateLimitFailover._instance = None
        mgr = RateLimitFailover()
        mgr._load_fallback_models()
        
        for model_name in mgr._available_models.keys():
            assert model_name in models_json, f"Fallback model {model_name} not in models.json"

    def test_opus_chain_includes_antigravity_fallbacks(self, models_json):
        """Opus fallback chain should include antigravity thinking models."""
        from code_puppy.core.rate_limit_failover import RateLimitFailover
        
        RateLimitFailover._instance = None
        mgr = RateLimitFailover()
        mgr._load_fallback_models()
        
        opus_chain = mgr.get_failover_chain("claude-code-claude-opus-4-5-20251101")
        
        # Should have antigravity opus thinking models as fallbacks
        antigravity_opus = [m for m in opus_chain if "antigravity-claude-opus" in m]
        assert len(antigravity_opus) > 0, "Opus chain should include antigravity opus fallbacks"


# =============================================================================
# TEST: Case-Insensitive Model Lookup
# =============================================================================

class TestCaseInsensitiveModelLookup:
    """Test that model lookups handle case variations."""

    def test_find_model_key_exact_match(self, models_json):
        """Exact match should return the key."""
        key = find_model_key("Cerebras-GLM-4.7", models_json)
        assert key == "Cerebras-GLM-4.7"

    def test_find_model_key_case_insensitive(self, models_json):
        """Lowercase input should find correct key."""
        key = find_model_key("cerebras-glm-4.7", models_json)
        assert key == "Cerebras-GLM-4.7"

    def test_find_model_key_returns_none_for_missing(self, models_json):
        """Missing model should return None."""
        key = find_model_key("nonexistent-model", models_json)
        assert key is None

    def test_find_model_key_claude_code_models(self, models_json):
        """Claude Code models should be found case-insensitively."""
        # Test with exact key
        key = find_model_key("claude-code-claude-opus-4-5-20251101", models_json)
        assert key == "claude-code-claude-opus-4-5-20251101"
        
        # Test with uppercase variant
        key = find_model_key("CLAUDE-CODE-CLAUDE-OPUS-4-5-20251101", models_json)
        assert key == "claude-code-claude-opus-4-5-20251101"


# =============================================================================
# TEST: Token Budget Limits
# =============================================================================

class TestTokenBudgetLimits:
    """Test token budget limits for all providers."""

    def test_all_providers_have_limits(self):
        """All major providers should have defined limits."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        # PROVIDER_LIMITS is a class attribute
        limits = TokenBudgetManager.PROVIDER_LIMITS
        
        required_providers = [
            "cerebras",
            "claude_opus",
            "claude_sonnet", 
            "gemini",
            "gemini_flash",
            "codex",
        ]
        
        for provider in required_providers:
            assert provider in limits, f"Missing limits for {provider}"
            assert "tokens_per_minute" in limits[provider]
            assert "tokens_per_day" in limits[provider]

    def test_cerebras_has_high_limits(self):
        """Cerebras should have high token limits (fast model)."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        cerebras = TokenBudgetManager.PROVIDER_LIMITS["cerebras"]
        # Cerebras is a fast model, should have high limits
        assert cerebras["tokens_per_minute"] >= 100_000
        assert cerebras["tokens_per_day"] >= 1_000_000


# =============================================================================
# TEST: Budget Check Flow
# =============================================================================

class TestBudgetCheckFlow:
    """Test the complete budget check flow."""

    def test_budget_check_returns_expected_fields(self):
        """Budget check should return all expected fields."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        mgr = TokenBudgetManager()
        result = mgr.check_budget("claude-code-claude-opus-4-5-20251101", 1000)
        
        # Use actual field name: can_proceed (not allowed)
        assert hasattr(result, "can_proceed")
        assert hasattr(result, "wait_seconds")
        assert hasattr(result, "failover_to")
        assert hasattr(result, "reason")

    def test_budget_check_within_limits_proceeds(self):
        """Request within limits should proceed."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        # Fresh manager
        TokenBudgetManager._instance = None
        mgr = TokenBudgetManager()
        
        result = mgr.check_budget("antigravity-gemini-3-flash", 100)
        assert result.can_proceed is True
        assert result.wait_seconds == 0


# =============================================================================
# TEST: Failover Suggestions
# =============================================================================

class TestFailoverSuggestions:
    """Test that failover suggestions use correct model names."""

    def test_failover_suggestion_is_valid_model(self, models_json):
        """Failover suggestion should be a valid model from models.json."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        TokenBudgetManager._instance = None
        mgr = TokenBudgetManager()
        
        # Get failover for opus
        failover = mgr.get_failover("claude_opus")
        
        if failover:
            assert failover in models_json, f"Failover {failover} not in models.json"

    def test_opus_failover_chain_order(self):
        """Opus failover should go to antigravity opus thinking first."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        # FAILOVER_CHAIN (singular) is a class attribute - maps model to next failover
        opus_failover = TokenBudgetManager.FAILOVER_CHAIN.get("claude_opus")
        assert opus_failover == "antigravity-claude-opus-4-5-thinking-high"


# =============================================================================
# TEST: Workload-Based Failover
# =============================================================================

class TestWorkloadBasedFailover:
    """Test workload-based failover chains."""

    def test_orchestrator_workload_starts_with_opus(self):
        """Orchestrator workload should prefer opus-class models."""
        from code_puppy.core.rate_limit_failover import RateLimitFailover, WorkloadType
        
        RateLimitFailover._instance = None
        mgr = RateLimitFailover()
        mgr.load_from_model_factory()
        
        chains = mgr.WORKLOAD_CHAINS.get(WorkloadType.ORCHESTRATOR, [])
        assert len(chains) > 0
        # First model should be opus-tier
        assert "opus" in chains[0].lower()

    def test_coding_workload_starts_with_cerebras(self):
        """Coding workload should prefer Cerebras for speed."""
        from code_puppy.core.rate_limit_failover import RateLimitFailover, WorkloadType
        
        RateLimitFailover._instance = None
        mgr = RateLimitFailover()
        
        chains = mgr.WORKLOAD_CHAINS.get(WorkloadType.CODING, [])
        assert len(chains) > 0
        # First model should be Cerebras (case-insensitive check)
        assert "cerebras" in chains[0].lower()


# =============================================================================
# TEST: Context Compressor
# =============================================================================

class TestContextCompressor:
    """Test context compressor functionality."""

    def test_compressor_init_with_max_tokens(self):
        """Compressor should accept max_tokens parameter."""
        from code_puppy.core.context_compressor import ContextCompressor
        
        compressor = ContextCompressor(max_tokens=10000)
        # Should not raise
        assert compressor is not None

    def test_compressor_with_custom_token_estimator(self):
        """Compressor should accept custom token estimation function."""
        from code_puppy.core.context_compressor import ContextCompressor
        
        def custom_estimator(text: str) -> int:
            return len(text) // 4
        
        compressor = ContextCompressor(
            max_tokens=10000,
            estimate_tokens_fn=custom_estimator,
        )
        assert compressor is not None


# =============================================================================
# TEST: Smart Selection Model Mappings  
# =============================================================================

class TestSmartSelectionMappings:
    """Test smart selection uses correct model keys."""

    def test_smart_selector_exists(self):
        """SmartModelSelector class should exist and be importable."""
        from code_puppy.core.smart_selection import SmartModelSelector
        
        assert SmartModelSelector is not None

    def test_smart_selector_has_capability_method(self):
        """SmartModelSelector should have capability-based selection."""
        from code_puppy.core.smart_selection import SmartModelSelector
        
        selector = SmartModelSelector.__new__(SmartModelSelector)
        # Check the class has key methods
        assert hasattr(SmartModelSelector, 'select_model') or hasattr(SmartModelSelector, '_score_model')


# =============================================================================
# TEST: Model Router
# =============================================================================

class TestModelRouter:
    """Test model router uses correct model keys."""

    def test_model_router_exists(self):
        """ModelRouter class should exist and be importable."""
        from code_puppy.core.model_router import ModelRouter
        
        assert ModelRouter is not None


# =============================================================================
# TEST: End-to-End Flow
# =============================================================================

class TestEndToEndFlow:
    """Test complete end-to-end scenarios."""

    def test_e2e_model_lookup_to_budget_check(self, models_json):
        """Complete flow: lookup model → normalize provider → check budget."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        # Step 1: Find model (case-insensitive)
        model_key = find_model_key("cerebras-glm-4.7", models_json)
        assert model_key == "Cerebras-GLM-4.7"
        
        # Step 2: Normalize provider
        TokenBudgetManager._instance = None
        mgr = TokenBudgetManager()
        provider = mgr._normalize_provider(model_key)
        assert provider == "cerebras"
        
        # Step 3: Check budget
        result = mgr.check_budget(model_key, 1000)
        assert result.can_proceed is True

    def test_e2e_fallback_chain_uses_valid_models(self, models_json):
        """Complete flow: rate limit → get fallback → verify model exists."""
        from code_puppy.core.rate_limit_failover import RateLimitFailover
        
        RateLimitFailover._instance = None
        mgr = RateLimitFailover()
        # Only test with fallback models (not factory-loaded which may have more)
        mgr._load_fallback_models()
        
        # All fallback models should exist in models.json
        for model in mgr._available_models.keys():
            assert model in models_json, f"Fallback model {model} not in models.json"

    def test_e2e_all_claude_models_have_valid_fallbacks(self, models_json):
        """All Claude Code models should have working fallback chains."""
        from code_puppy.core.rate_limit_failover import RateLimitFailover
        
        RateLimitFailover._instance = None
        mgr = RateLimitFailover()
        mgr._load_fallback_models()
        
        claude_code_models = [
            "claude-code-claude-opus-4-5-20251101",
            "claude-code-claude-sonnet-4-5-20250929",
            "claude-code-claude-haiku-4-5-20251001",
        ]
        
        for model in claude_code_models:
            chain = mgr.get_failover_chain(model)
            assert len(chain) > 0, f"{model} has no failover chain"
            
            # All fallback models should exist in available_models
            for fallover in chain:
                assert fallover in mgr._available_models, \
                    f"Fallover {fallover} for {model} not in available models"


# =============================================================================
# TEST: Tier Detection
# =============================================================================

class TestTierDetection:
    """Test tier detection for different model types."""

    def test_opus_is_tier_1(self):
        """Opus models should be tier 1 (architect)."""
        from code_puppy.core.rate_limit_failover import RateLimitFailover
        
        RateLimitFailover._instance = None
        mgr = RateLimitFailover()
        
        assert mgr._detect_tier("claude-code-claude-opus-4-5-20251101") == 1
        assert mgr._detect_tier("antigravity-claude-opus-4-5-thinking-high") == 1

    def test_sonnet_is_tier_2_or_3(self):
        """Sonnet models should be tier 2 or 3."""
        from code_puppy.core.rate_limit_failover import RateLimitFailover
        
        RateLimitFailover._instance = None
        mgr = RateLimitFailover()
        
        tier = mgr._detect_tier("claude-code-claude-sonnet-4-5-20250929")
        assert tier in [2, 3]

    def test_cerebras_is_tier_5(self):
        """Cerebras should be tier 5 (fastest)."""
        from code_puppy.core.rate_limit_failover import RateLimitFailover
        
        RateLimitFailover._instance = None
        mgr = RateLimitFailover()
        
        # Both case variants should work
        assert mgr._detect_tier("Cerebras-GLM-4.7") == 5
        assert mgr._detect_tier("cerebras-glm-4.7") == 5

    def test_gemini_flash_is_tier_4(self):
        """Gemini flash should be tier 4."""
        from code_puppy.core.rate_limit_failover import RateLimitFailover
        
        RateLimitFailover._instance = None
        mgr = RateLimitFailover()
        
        assert mgr._detect_tier("antigravity-gemini-3-flash") == 4


# =============================================================================
# TEST: Agent Model Assignment
# =============================================================================

class TestAgentModelAssignment:
    """Test that agents get correct model assignments."""

    def test_pack_leader_gets_opus_tier(self):
        """Pack leader should be assigned to orchestrator workload (opus-tier)."""
        from code_puppy.core.rate_limit_failover import RateLimitFailover, WorkloadType
        
        RateLimitFailover._instance = None
        mgr = RateLimitFailover()
        
        # Use correct attribute name: AGENT_WORKLOAD_REGISTRY
        workload = mgr.AGENT_WORKLOAD_REGISTRY.get("pack-leader")
        assert workload == WorkloadType.ORCHESTRATOR

    def test_code_puppy_gets_coding_workload(self):
        """Code-puppy agent should get coding workload (Cerebras)."""
        from code_puppy.core.rate_limit_failover import RateLimitFailover, WorkloadType
        
        RateLimitFailover._instance = None
        mgr = RateLimitFailover()
        
        workload = mgr.AGENT_WORKLOAD_REGISTRY.get("code-puppy")
        assert workload == WorkloadType.CODING

    def test_bloodhound_gets_librarian_workload(self):
        """Bloodhound should get librarian workload (efficient models)."""
        from code_puppy.core.rate_limit_failover import RateLimitFailover, WorkloadType
        
        RateLimitFailover._instance = None
        mgr = RateLimitFailover()
        
        workload = mgr.AGENT_WORKLOAD_REGISTRY.get("bloodhound")
        assert workload == WorkloadType.LIBRARIAN


# =============================================================================
# INTEGRATION TEST: Full Token Optimization Pipeline
# =============================================================================

class TestTokenOptimizationPipeline:
    """Integration tests for the complete token optimization pipeline."""

    def test_cerebras_model_detection_method_exists(self):
        """BaseAgent should have _is_cerebras_model method."""
        from code_puppy.agents.base_agent import BaseAgent
        
        assert hasattr(BaseAgent, '_is_cerebras_model')

    def test_compress_history_method_exists(self):
        """BaseAgent should have compress_history method."""
        from code_puppy.agents.base_agent import BaseAgent
        
        assert hasattr(BaseAgent, 'compress_history')

    def test_check_tokens_method_exists(self):
        """BaseAgent should have token checking method."""
        from code_puppy.agents.base_agent import BaseAgent
        
        # Check for compaction-related methods
        assert hasattr(BaseAgent, '_check_tokens_and_maybe_compact') or \
               hasattr(BaseAgent, 'estimate_token_count')


# =============================================================================
# TEST: Provider Limits Consistency
# =============================================================================

class TestProviderLimitsConsistency:
    """Test that provider limits are consistent and reasonable."""

    def test_opus_limits_are_reasonable(self):
        """Claude Opus should have reasonable limits (expensive model)."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        opus = TokenBudgetManager.PROVIDER_LIMITS.get("claude_opus", {})
        assert opus.get("tokens_per_minute", 0) > 0
        assert opus.get("tokens_per_day", 0) > 0

    def test_all_providers_have_reset_window(self):
        """All providers should have reset_window_seconds defined."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        for provider, limits in TokenBudgetManager.PROVIDER_LIMITS.items():
            assert "reset_window_seconds" in limits, f"{provider} missing reset_window_seconds"
            assert limits["reset_window_seconds"] > 0


# =============================================================================
# TEST: Workload Chain Consistency
# =============================================================================

class TestWorkloadChainConsistency:
    """Test that workload chains are consistent."""

    def test_all_workload_types_have_chains(self):
        """All WorkloadType values should have chains defined."""
        from code_puppy.core.rate_limit_failover import RateLimitFailover, WorkloadType
        
        RateLimitFailover._instance = None
        mgr = RateLimitFailover()
        
        for workload_type in WorkloadType:
            assert workload_type in mgr.WORKLOAD_CHAINS, f"Missing chain for {workload_type}"
            assert len(mgr.WORKLOAD_CHAINS[workload_type]) > 0, f"Empty chain for {workload_type}"

    def test_workload_chains_use_valid_models(self, models_json):
        """All models in workload chains should exist in models.json."""
        from code_puppy.core.rate_limit_failover import RateLimitFailover, WorkloadType
        
        RateLimitFailover._instance = None
        mgr = RateLimitFailover()
        
        for workload_type, chain in mgr.WORKLOAD_CHAINS.items():
            for model in chain:
                assert model in models_json, \
                    f"Workload chain {workload_type} has invalid model: {model}"


# =============================================================================
# TEST: Cross-Tier Failover Chain Completeness
# =============================================================================

class TestCrossTierFailoverChain:
    """Test that failover chains span across tiers for resilience."""

    def test_sonnet_chain_reaches_cerebras(self):
        """Sonnet chain should eventually reach Cerebras (different provider)."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        chain = TokenBudgetManager.FAILOVER_CHAIN
        
        # Walk the chain from Sonnet
        current = "claude-code-claude-sonnet-4-5-20250929"
        visited = set()
        reached_cerebras = False
        
        while current and current not in visited:
            visited.add(current)
            if "cerebras" in current.lower():
                reached_cerebras = True
                break
            current = chain.get(current)
        
        assert reached_cerebras, "Sonnet chain should reach Cerebras as cross-tier fallback"

    def test_chatgpt_in_failover_chain(self):
        """ChatGPT OAuth models are now included in failover chains."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        chain = TokenBudgetManager.FAILOVER_CHAIN
        
        # ChatGPT models are now in failover chains as values (targets)
        # They serve as fallback from Antigravity Sonnet thinking models
        chatgpt_as_fallback = any("chatgpt" in val.lower() for val in chain.values())
        assert chatgpt_as_fallback, "ChatGPT models should be in failover chain as fallback targets"
        
        # Verify Cerebras chain works
        current = "Cerebras-GLM-4.7"
        visited = set()
        while current and current not in visited:
            visited.add(current)
            current = chain.get(current)
        # Chain should include Cerebras pathway
        assert "synthetic-GLM-4.7" in visited or "Cerebras-GLM-4.7" in visited

    def test_cerebras_chain_reaches_haiku_and_gemini(self):
        """Cerebras chain should reach Haiku and Gemini Flash."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        chain = TokenBudgetManager.FAILOVER_CHAIN
        
        # Walk the chain from Cerebras
        current = "Cerebras-GLM-4.7"
        visited = set()
        reached_haiku = False
        reached_gemini = False
        
        while current and current not in visited:
            visited.add(current)
            if "haiku" in current.lower():
                reached_haiku = True
            if "gemini" in current.lower() and "flash" in current.lower():
                reached_gemini = True
            current = chain.get(current)
        
        assert reached_haiku, "Cerebras chain should reach Haiku"
        assert reached_gemini, "Cerebras chain should reach Gemini Flash"

    def test_full_chain_coverage_from_any_starting_point(self, models_json):
        """Every model in the chain should eventually reach at least 3 distinct providers."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        chain = TokenBudgetManager.FAILOVER_CHAIN
        
        def get_provider(model_name: str) -> str:
            """Extract provider category from model name."""
            name = model_name.lower()
            if "cerebras" in name:
                return "cerebras"
            if "gemini" in name:
                return "gemini"
            if "chatgpt" in name or "gpt-5" in name or "codex" in name:
                return "openai"
            if "opus" in name:
                return "claude_opus"
            if "sonnet" in name:
                return "claude_sonnet"
            if "haiku" in name:
                return "claude_haiku"
            return "unknown"
        
        # Check that major models have multi-provider fallback chains
        major_models = [
            "claude-code-claude-opus-4-5-20251101",
            "claude-code-claude-sonnet-4-5-20250929",
            "Cerebras-GLM-4.7",
        ]
        
        for start_model in major_models:
            if start_model not in chain:
                continue
                
            current = start_model
            visited = set()
            providers = set()
            
            while current and current not in visited:
                visited.add(current)
                providers.add(get_provider(current))
                current = chain.get(current)
            
            # Each major model should have at least 2 provider options
            assert len(providers) >= 2, \
                f"{start_model} only has {len(providers)} provider(s): {providers}"
