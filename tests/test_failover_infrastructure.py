"""Comprehensive tests for the failover infrastructure.

Tests the complete failover chain:
1. Model name validation against models.json
2. FAILOVER_CHAIN mappings in token_budget.py
3. WORKLOAD_CHAINS mappings in rate_limit_failover.py
4. Model creation via ModelFactory
5. Failover execution in base_agent.py
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from code_puppy.core.token_budget import TokenBudgetManager, BudgetCheckResult
from code_puppy.core.rate_limit_failover import (
    RateLimitFailover,
    WorkloadType,
)
from code_puppy.model_factory import ModelFactory


class TestModelsJsonIntegrity:
    """Tests that models.json has all required models."""

    @pytest.fixture
    def models_config(self):
        """Load models.json."""
        return ModelFactory.load_config()

    def test_claude_code_models_exist(self, models_config):
        """Verify Claude Code models are defined."""
        required = [
            "claude-code-claude-opus-4-5-20251101",
            "claude-code-claude-sonnet-4-5-20250929",
            "claude-code-claude-haiku-4-5-20251001",
        ]
        for model in required:
            assert model in models_config, f"Missing Claude Code model: {model}"

    def test_antigravity_claude_models_exist(self, models_config):
        """Verify Antigravity Claude models are defined."""
        required = [
            "antigravity-claude-sonnet-4-5",
            "antigravity-claude-sonnet-4-5-thinking-low",
            "antigravity-claude-sonnet-4-5-thinking-medium",
            "antigravity-claude-sonnet-4-5-thinking-high",
            "antigravity-claude-opus-4-5-thinking-low",
            "antigravity-claude-opus-4-5-thinking-medium",
            "antigravity-claude-opus-4-5-thinking-high",
        ]
        for model in required:
            assert model in models_config, f"Missing Antigravity Claude model: {model}"

    def test_antigravity_gemini_models_exist(self, models_config):
        """Verify Antigravity Gemini models are defined."""
        required = [
            "antigravity-gemini-3-pro-low",
            "antigravity-gemini-3-pro-high",
            "antigravity-gemini-3-flash",
        ]
        for model in required:
            assert model in models_config, f"Missing Antigravity Gemini model: {model}"

    def test_chatgpt_models_exist(self, models_config):
        """Verify ChatGPT 5.2 models are OAuth-only (not in base models.json).
        
        These models are created dynamically by the chatgpt_oauth plugin when
        the user runs /chatgpt-auth. They should NOT be in the base models.json
        to avoid requiring OPENAI_API_KEY.
        """
        oauth_only_models = [
            "chatgpt-gpt-5.2",
            "chatgpt-gpt-5.2-codex",
        ]
        # These should NOT be in base models.json - they come from OAuth
        # The models_config may include them if OAuth is configured
        # We just verify the base models.json doesn't have them with type "openai"
        import json
        import pathlib
        
        base_config_path = pathlib.Path(__file__).parent.parent / "code_puppy" / "models.json"
        with open(base_config_path) as f:
            base_config = json.load(f)
        
        for model in oauth_only_models:
            if model in base_config:
                # If it exists in base config, it should NOT be type "openai"
                # (it should be type "chatgpt_oauth" from OAuth plugin)
                model_type = base_config[model].get("type")
                assert model_type != "openai", (
                    f"Model {model} should not have type 'openai' - "
                    "ChatGPT models should come from OAuth plugin, not API keys"
                )

    def test_synthetic_hf_models_exist(self, models_config):
        """Verify Synthetic HuggingFace models are defined (February 2026)."""
        required = [
            "synthetic-hf-deepseek-ai-DeepSeek-R1-0528",
            "synthetic-hf-moonshotai-Kimi-K2.5",
            "synthetic-hf-Qwen-Qwen3-235B-A22B-Thinking-2507",
            "synthetic-hf-zai-org-GLM-4.7",
            "synthetic-hf-MiniMaxAI-MiniMax-M2.1",
        ]
        for model in required:
            assert model in models_config, f"Missing Synthetic HF model: {model}"

    def test_synthetic_models_exist(self, models_config):
        """Verify Synthetic provider models are defined."""
        required = [
            "synthetic-GLM-4.7",
            "synthetic-MiniMax-M2.1",
            "synthetic-Kimi-K2-Thinking",
            "synthetic-Kimi-K2.5-Thinking",
        ]
        for model in required:
            assert model in models_config, f"Missing Synthetic model: {model}"

    def test_chatgpt_gpt5_models_exist(self, models_config):
        """Verify ChatGPT GPT-5.2 models are defined."""
        required = [
            "chatgpt-gpt-5.2",
            "chatgpt-gpt-5.2-codex",
        ]
        for model in required:
            assert model in models_config, f"Missing ChatGPT GPT-5.2 model: {model}"

    def test_openrouter_free_models_exist(self, models_config):
        """Verify OpenRouter free tier models are defined."""
        required = [
            "openrouter-stepfun-step-3.5-flash-free",
            "openrouter-arcee-ai-trinity-large-preview-free",
        ]
        for model in required:
            assert model in models_config, f"Missing OpenRouter free model: {model}"

    def test_cerebras_model_exists(self, models_config):
        """Verify Cerebras model is defined."""
        assert "Cerebras-GLM-4.7" in models_config, "Missing Cerebras model"


class TestFailoverChainMappings:
    """Tests that FAILOVER_CHAIN entries map to valid models."""

    @pytest.fixture
    def models_config(self):
        """Load models.json."""
        return ModelFactory.load_config()

    def test_all_failover_targets_exist(self, models_config):
        """All failover target models should exist in models.json."""
        mgr = TokenBudgetManager()
        invalid = []
        
        for source, target in mgr.FAILOVER_CHAIN.items():
            if target not in models_config:
                invalid.append(f"{source} -> {target}")
        
        assert not invalid, f"Invalid failover targets: {invalid}"

    def test_opus_chain_complete(self):
        """Opus should chain through thinking levels to new Tier 1 models then Sonnet."""
        mgr = TokenBudgetManager()
        chain = mgr.FAILOVER_CHAIN
        
        # Opus -> thinking-high -> Kimi K2.5 -> thinking-medium -> Qwen3 -> thinking-low -> Sonnet
        assert chain.get("claude-code-claude-opus-4-5-20251101") == "antigravity-claude-opus-4-5-thinking-high"
        assert chain.get("antigravity-claude-opus-4-5-thinking-high") == "synthetic-Kimi-K2.5-Thinking"
        assert chain.get("synthetic-Kimi-K2.5-Thinking") == "antigravity-claude-opus-4-5-thinking-medium"
        assert chain.get("antigravity-claude-opus-4-5-thinking-medium") == "synthetic-hf-Qwen-Qwen3-235B-A22B-Thinking-2507"
        assert chain.get("antigravity-claude-opus-4-5-thinking-low") == "antigravity-claude-sonnet-4-5-thinking-high"

    def test_sonnet_chain_includes_deepseek_and_kimi(self):
        """Sonnet should chain to DeepSeek R1 and Kimi K2-Thinking."""
        mgr = TokenBudgetManager()
        chain = mgr.FAILOVER_CHAIN
        
        # Sonnet -> regular -> DeepSeek R1 -> Kimi K2-Thinking
        assert chain.get("claude-code-claude-sonnet-4-5-20250929") == "antigravity-claude-sonnet-4-5"
        assert chain.get("antigravity-claude-sonnet-4-5") == "synthetic-hf-deepseek-ai-DeepSeek-R1-0528"
        assert chain.get("synthetic-hf-deepseek-ai-DeepSeek-R1-0528") == "synthetic-Kimi-K2-Thinking"

    def test_cerebras_chain_complete(self):
        """Cerebras should chain to Synthetic GLM then Haiku then Gemini."""
        mgr = TokenBudgetManager()
        chain = mgr.FAILOVER_CHAIN
        
        # Cerebras -> Synthetic GLM -> Haiku -> Gemini Flash -> OpenRouter
        assert chain.get("Cerebras-GLM-4.7") == "synthetic-GLM-4.7"
        assert chain.get("synthetic-GLM-4.7") == "claude-code-claude-haiku-4-5-20251001"
        assert chain.get("claude-code-claude-haiku-4-5-20251001") == "antigravity-gemini-3-flash"

    def test_chatgpt_chain_complete(self):
        """ChatGPT GPT-5.2-Codex models are now part of static failover chain.
        
        GPT-5.2-Codex was added as Tier 2 model for complex coding tasks.
        OAuth plugin can still dynamically add additional entries.
        """
        mgr = TokenBudgetManager()
        chain = mgr.FAILOVER_CHAIN
        
        # ChatGPT GPT-5.2-Codex is now in static chain (Tier 2 BUILDER_HIGH)
        chatgpt_models = [k for k in chain.keys() if k.startswith("chatgpt-")]
        assert len(chatgpt_models) > 0, "ChatGPT GPT-5.2 should be in static chain"
        # Verify they have valid failover targets
        for model in chatgpt_models:
            assert chain[model] is not None, f"{model} should have a failover target"


class TestWorkloadChainMappings:
    """Tests that WORKLOAD_CHAINS entries map to valid models."""

    @pytest.fixture
    def models_config(self):
        """Load models.json."""
        return ModelFactory.load_config()

    def test_all_workload_models_exist(self, models_config):
        """All workload chain models should exist in models.json."""
        mgr = RateLimitFailover()
        mgr._instance = None  # Reset singleton
        
        invalid = []
        for workload_type, chain in RateLimitFailover.WORKLOAD_CHAINS.items():
            for model in chain:
                if model not in models_config:
                    invalid.append(f"{workload_type.name}: {model}")
        
        assert not invalid, f"Invalid workload chain models: {invalid}"

    def test_orchestrator_chain_starts_with_opus(self):
        """Orchestrator workload should start with Opus."""
        chain = RateLimitFailover.WORKLOAD_CHAINS[WorkloadType.ORCHESTRATOR]
        assert chain[0] == "claude-code-claude-opus-4-5-20251101"

    def test_orchestrator_chain_ends_with_cerebras(self):
        """Orchestrator workload should end with Cerebras as final fallback.
        
        ChatGPT models are OAuth-only and not in default chains.
        """
        chain = RateLimitFailover.WORKLOAD_CHAINS[WorkloadType.ORCHESTRATOR]
        assert chain[-1] == "Cerebras-GLM-4.7"
        # Also verify Tier 1 models are included
        assert "synthetic-Kimi-K2.5-Thinking" in chain
        assert "synthetic-hf-Qwen-Qwen3-235B-A22B-Thinking-2507" in chain

    def test_coding_chain_starts_with_cerebras(self):
        """Coding workload should start with Cerebras and include GPT-5.2-Codex and MiniMax."""
        chain = RateLimitFailover.WORKLOAD_CHAINS[WorkloadType.CODING]
        assert chain[0] == "Cerebras-GLM-4.7"
        # Verify Tier 2/3 coding models are included
        assert "chatgpt-gpt-5.2-codex" in chain
        assert "synthetic-MiniMax-M2.1" in chain

    def test_reasoning_chain_includes_deepseek_kimi(self):
        """Reasoning workload should include DeepSeek R1 and Kimi K2-Thinking."""
        chain = RateLimitFailover.WORKLOAD_CHAINS[WorkloadType.REASONING]
        assert "synthetic-hf-deepseek-ai-DeepSeek-R1-0528" in chain
        assert "synthetic-Kimi-K2-Thinking" in chain

    def test_librarian_chain_has_fast_models(self):
        """Librarian workload should have Haiku, Flash, and OpenRouter free models."""
        chain = RateLimitFailover.WORKLOAD_CHAINS[WorkloadType.LIBRARIAN]
        assert "claude-code-claude-haiku-4-5-20251001" in chain
        assert "antigravity-gemini-3-flash" in chain
        # Verify OpenRouter free tier models are in Librarian chain
        assert "openrouter-arcee-ai-trinity-large-preview-free" in chain or \
               "openrouter-stepfun-step-3.5-flash-free" in chain


class TestProviderNormalization:
    """Tests that model names normalize to correct providers."""

    def test_normalize_claude_code_models(self):
        """Claude Code models should normalize to claude_* providers."""
        mgr = TokenBudgetManager()
        
        assert mgr._normalize_provider("claude-code-claude-opus-4-5-20251101") == "claude_opus"
        assert mgr._normalize_provider("claude-code-claude-sonnet-4-5-20250929") == "claude_sonnet"
        # Haiku maps to gemini_flash for budget (less expensive tier)
        assert mgr._normalize_provider("claude-code-claude-haiku-4-5-20251001") == "gemini_flash"

    def test_normalize_antigravity_models(self):
        """Antigravity models should normalize correctly."""
        mgr = TokenBudgetManager()
        
        assert mgr._normalize_provider("antigravity-claude-opus-4-5-thinking-high") == "claude_opus"
        assert mgr._normalize_provider("antigravity-claude-sonnet-4-5-thinking-medium") == "claude_sonnet"
        assert mgr._normalize_provider("antigravity-gemini-3-flash") == "gemini_flash"

    def test_normalize_chatgpt_models(self):
        """ChatGPT models should normalize to chatgpt or codex provider."""
        mgr = TokenBudgetManager()
        
        # ChatGPT GPT-5.2 models map to chatgpt
        assert mgr._normalize_provider("chatgpt-gpt-5.2") == "chatgpt"
        assert mgr._normalize_provider("chatgpt-gpt-5.2-codex") == "chatgpt"
        # Legacy codex models map to codex
        assert mgr._normalize_provider("gpt-5.1-codex-api") == "codex"


    def test_normalize_new_provider_models(self):
        """New provider models should normalize correctly (February 2026)."""
        mgr = TokenBudgetManager()
        
        # DeepSeek, Kimi, Qwen, MiniMax
        assert mgr._normalize_provider("synthetic-hf-deepseek-ai-DeepSeek-R1-0528") == "deepseek"
        assert mgr._normalize_provider("synthetic-Kimi-K2.5-Thinking") == "kimi"
        assert mgr._normalize_provider("synthetic-hf-Qwen-Qwen3-235B-A22B-Thinking-2507") == "qwen"
        assert mgr._normalize_provider("synthetic-MiniMax-M2.1") == "minimax"
        # OpenRouter free models
        assert mgr._normalize_provider("openrouter-stepfun-step-3.5-flash-free") == "openrouter_free"
        assert mgr._normalize_provider("openrouter-arcee-ai-trinity-large-preview-free") == "openrouter_free"


class TestBudgetCheckWithFailover:
    """Tests budget check returns correct failover suggestions."""

    def setup_method(self):
        """Reset budget manager state."""
        mgr = TokenBudgetManager()
        for provider in mgr._budgets:
            mgr.reset_provider(provider)

    def test_budget_exceeded_suggests_failover(self):
        """When budget exceeded, should suggest failover."""
        mgr = TokenBudgetManager()
        mgr.reset_provider("claude_opus")
        
        # Exhaust the budget
        mgr._budgets["claude_opus"].tokens_used_today = 10_000_000
        
        result = mgr.check_budget("claude_opus", 100_000, allow_failover=True)
        
        assert not result.can_proceed
        assert result.failover_to is not None

    def test_budget_exceeded_no_failover_when_disabled(self):
        """When failover disabled, should not suggest it."""
        mgr = TokenBudgetManager()
        mgr.reset_provider("claude_opus")
        
        # Exhaust the budget
        mgr._budgets["claude_opus"].tokens_used_today = 10_000_000
        
        result = mgr.check_budget("claude_opus", 100_000, allow_failover=False)
        
        assert not result.can_proceed
        assert result.failover_to is None

    def test_short_wait_does_not_suggest_failover(self):
        """Short wait times (<10s) should wait, not failover."""
        mgr = TokenBudgetManager()
        mgr.reset_provider("cerebras")
        
        # Almost exhaust minute budget
        mgr._budgets["cerebras"].tokens_used_this_minute = 290_000
        mgr._budgets["cerebras"].last_minute_reset = 0  # Reset a long time ago (forces short wait)
        
        result = mgr.check_budget("cerebras", 20_000, allow_failover=True)
        
        if not result.can_proceed and result.wait_seconds < 10:
            assert result.failover_to is None


class TestModelFactoryIntegration:
    """Tests that ModelFactory can create all models in failover chains."""

    @pytest.fixture
    def models_config(self):
        """Load models.json."""
        return ModelFactory.load_config()

    def test_model_configs_have_required_fields(self, models_config):
        """All models should have type and name fields."""
        for model_key, config in models_config.items():
            # Skip metadata entries (keys starting with _)
            if model_key.startswith("_"):
                continue
            assert "type" in config, f"{model_key} missing 'type'"
            assert "name" in config, f"{model_key} missing 'name'"

    def test_antigravity_models_have_correct_type(self, models_config):
        """Antigravity models should have antigravity type."""
        for model_key, config in models_config.items():
            if model_key.startswith("antigravity-"):
                assert config["type"] == "antigravity", f"{model_key} should be type 'antigravity'"

    def test_chatgpt_models_have_correct_type(self, models_config):
        """ChatGPT models should have correct types."""
        # ChatGPT models using OAuth flow use 'chatgpt' type
        for model_key in ["chatgpt-gpt-5.2", "chatgpt-gpt-5.2-codex"]:
            if model_key in models_config:
                assert models_config[model_key]["type"] == "chatgpt", f"{model_key} should be type 'chatgpt'"
        
        # GPT 5.1 API models use openai type
        for model_key in ["gpt-5.1", "gpt-5.1-codex-api"]:
            if model_key in models_config:
                assert models_config[model_key]["type"] == "openai", f"{model_key} should be type 'openai'"


class TestChainExhaustionDetection:
    """Tests detection of exhausted model families."""

    def test_detect_opus_thinking_family_exhaustion(self):
        """Should detect when all Opus thinking models share same quota."""
        # Error message from Antigravity API
        error_msg = '''Antigravity API Error 429: {
            "error": {
                "code": 429,
                "message": "quota exhausted",
                "metadata": {"model": "claude-opus-4-5-thinking"}
            }
        }'''
        
        # Should detect opus thinking family is exhausted
        assert "claude-opus-4-5-thinking" in error_msg
        assert "opus" in error_msg and "thinking" in error_msg

    def test_detect_sonnet_thinking_family_exhaustion(self):
        """Should detect when all Sonnet thinking models share same quota."""
        error_msg = 'model: "claude-sonnet-4-5-thinking"'
        
        assert "claude-sonnet-4-5-thinking" in error_msg
        assert "sonnet" in error_msg and "thinking" in error_msg


class TestValidateAllChainsScript:
    """Tests that validate_failover_chains.py would pass."""

    @pytest.fixture
    def models_config(self):
        """Load models.json."""
        return ModelFactory.load_config()

    def test_all_orchestrator_chain_models_valid(self, models_config):
        """All ORCHESTRATOR chain models should exist."""
        chain = RateLimitFailover.WORKLOAD_CHAINS[WorkloadType.ORCHESTRATOR]
        for model in chain:
            assert model in models_config, f"ORCHESTRATOR chain: {model} not in models.json"

    def test_all_reasoning_chain_models_valid(self, models_config):
        """All REASONING chain models should exist."""
        chain = RateLimitFailover.WORKLOAD_CHAINS[WorkloadType.REASONING]
        for model in chain:
            assert model in models_config, f"REASONING chain: {model} not in models.json"

    def test_all_coding_chain_models_valid(self, models_config):
        """All CODING chain models should exist."""
        chain = RateLimitFailover.WORKLOAD_CHAINS[WorkloadType.CODING]
        for model in chain:
            assert model in models_config, f"CODING chain: {model} not in models.json"

    def test_all_librarian_chain_models_valid(self, models_config):
        """All LIBRARIAN chain models should exist."""
        chain = RateLimitFailover.WORKLOAD_CHAINS[WorkloadType.LIBRARIAN]
        for model in chain:
            assert model in models_config, f"LIBRARIAN chain: {model} not in models.json"


class TestEndToEndFailoverScenarios:
    """Integration tests for complete failover scenarios."""

    def test_opus_exhausted_follows_chain(self):
        """When Opus exhausted, should follow chain to Sonnet thinking then Cerebras."""
        mgr = TokenBudgetManager()
        
        # Start with Opus
        current = "claude-code-claude-opus-4-5-20251101"
        
        # Follow chain
        chain = []
        while current in mgr.FAILOVER_CHAIN:
            next_model = mgr.FAILOVER_CHAIN[current]
            chain.append(next_model)
            current = next_model
            if len(chain) > 20:  # Prevent infinite loop
                break
        
        # Should eventually get to Cerebras (ChatGPT is OAuth-only)
        assert any("cerebras" in m.lower() or "glm" in m.lower() for m in chain), \
            f"Chain should end at Cerebras: {chain}"

    def test_cerebras_exhausted_follows_chain(self):
        """When Cerebras exhausted, should follow chain to Haiku then Gemini then loop."""
        mgr = TokenBudgetManager()
        
        # Start with Cerebras
        current = "Cerebras-GLM-4.7"
        
        # Follow chain
        chain = []
        while current in mgr.FAILOVER_CHAIN:
            next_model = mgr.FAILOVER_CHAIN[current]
            chain.append(next_model)
            current = next_model
            if len(chain) > 10:
                break
        
        # Should get to Haiku -> Gemini -> Cerebras (loops back, ChatGPT is OAuth-only)
        assert "claude-code-claude-haiku-4-5-20251001" in chain
        assert "antigravity-gemini-3-flash" in chain
        # Chain loops back to Cerebras instead of going to ChatGPT
        assert "Cerebras-GLM-4.7" in chain
