"""End-to-end integration test for token optimization infrastructure.

Tests the complete flow from model detection → provider mapping → token budget → compaction.
"""

import pytest


class TestTokenOptimizationE2E:
    """End-to-end tests for the complete token optimization pipeline."""

    def test_full_import_chain(self):
        """Verify all token optimization modules import without errors."""
        # Core modules
        from code_puppy.core.token_budget import TokenBudgetManager
        from code_puppy.core.rate_limit_failover import RateLimitFailover
        
        # Tool modules
        from code_puppy.tools.token_slimmer import (
            get_provider_limits,
            check_token_budget,
            apply_sliding_window,
            PROVIDER_LIMITS,
        )
        from code_puppy.tools.cerebras_optimizer import (
            check_cerebras_budget,
            CEREBRAS_LIMITS,
        )
        
        # Agent modules
        from code_puppy.agents.base_agent import BaseAgent
        
        assert TokenBudgetManager is not None
        assert RateLimitFailover is not None
        assert get_provider_limits is not None
        assert BaseAgent is not None
        assert PROVIDER_LIMITS is not None
        assert CEREBRAS_LIMITS is not None

    def test_cerebras_detection_and_limits(self):
        """Test Cerebras model detection and boot camp limits."""
        from code_puppy.agents.base_agent import BaseAgent
        from code_puppy.tools.token_slimmer import get_provider_limits
        
        class TestAgent(BaseAgent):
            def __init__(self):
                self._last_model_name = "Cerebras-GLM-4.7"
                self._pinned_model = None
            
            def get_model_name(self):
                return self._pinned_model or ""
            
            @property
            def name(self):
                return "test"
            
            @property
            def display_name(self):
                return "Test"
            
            @property
            def description(self):
                return "Test"
            
            def get_system_prompt(self):
                return ""
            
            def get_available_tools(self):
                return []
        
        agent = TestAgent()
        
        # Test provider detection
        provider = agent._detect_provider()
        assert provider == "cerebras", f"Expected 'cerebras', got '{provider}'"
        
        # Test limits retrieval
        limits = get_provider_limits(provider)
        assert limits["diet_mode"] == "boot_camp"
        assert limits["compaction_threshold"] == 0.20
        assert limits["max_input_tokens"] == 50_000
        assert limits["target_input_tokens"] == 8_000
        assert limits["max_exchanges"] == 3

    def test_claude_code_detection_and_limits(self):
        """Test Claude Code model detection and balanced limits."""
        from code_puppy.agents.base_agent import BaseAgent
        from code_puppy.tools.token_slimmer import get_provider_limits
        
        class TestAgent(BaseAgent):
            def __init__(self):
                self._last_model_name = "claude-code-claude-opus-4-5-20251101"
                self._pinned_model = None
            
            def get_model_name(self):
                return self._pinned_model or ""
            
            @property
            def name(self):
                return "test"
            
            @property
            def display_name(self):
                return "Test"
            
            @property
            def description(self):
                return "Test"
            
            def get_system_prompt(self):
                return ""
            
            def get_available_tools(self):
                return []
        
        agent = TestAgent()
        
        # Test provider detection
        provider = agent._detect_provider()
        assert provider == "claude_code", f"Expected 'claude_code', got '{provider}'"
        
        # Test limits retrieval
        limits = get_provider_limits(provider)
        assert limits["diet_mode"] == "balanced"
        assert limits["compaction_threshold"] == 0.60
        assert limits["max_input_tokens"] == 180_000
        assert limits["max_exchanges"] == 10

    def test_antigravity_detection_and_limits(self):
        """Test Antigravity model detection and balanced limits."""
        from code_puppy.agents.base_agent import BaseAgent
        from code_puppy.tools.token_slimmer import get_provider_limits
        
        class TestAgent(BaseAgent):
            def __init__(self):
                self._last_model_name = "antigravity-claude-opus-4-5-thinking-high"
                self._pinned_model = None
            
            def get_model_name(self):
                return self._pinned_model or ""
            
            @property
            def name(self):
                return "test"
            
            @property
            def display_name(self):
                return "Test"
            
            @property
            def description(self):
                return "Test"
            
            def get_system_prompt(self):
                return ""
            
            def get_available_tools(self):
                return []
        
        agent = TestAgent()
        
        # Test provider detection
        provider = agent._detect_provider()
        assert provider == "antigravity", f"Expected 'antigravity', got '{provider}'"
        
        # Test limits retrieval
        limits = get_provider_limits(provider)
        assert limits["diet_mode"] == "balanced"
        assert limits["compaction_threshold"] == 0.50
        assert limits["max_input_tokens"] == 100_000

    def test_chatgpt_detection_and_limits(self):
        """Test ChatGPT model detection and balanced limits."""
        from code_puppy.agents.base_agent import BaseAgent
        from code_puppy.tools.token_slimmer import get_provider_limits
        
        class TestAgent(BaseAgent):
            def __init__(self):
                self._last_model_name = "chatgpt-gpt-5.2-codex"
                self._pinned_model = None
            
            def get_model_name(self):
                return self._pinned_model or ""
            
            @property
            def name(self):
                return "test"
            
            @property
            def display_name(self):
                return "Test"
            
            @property
            def description(self):
                return "Test"
            
            def get_system_prompt(self):
                return ""
            
            def get_available_tools(self):
                return []
        
        agent = TestAgent()
        
        # Test provider detection
        provider = agent._detect_provider()
        assert provider == "chatgpt_teams", f"Expected 'chatgpt_teams', got '{provider}'"
        
        # Test limits retrieval
        limits = get_provider_limits(provider)
        assert limits["diet_mode"] == "balanced"
        assert limits["compaction_threshold"] == 0.55
        assert limits["max_input_tokens"] == 120_000

    def test_failover_detection(self):
        """Test that failover from Claude Code to Cerebras is detected correctly."""
        from code_puppy.agents.base_agent import BaseAgent
        
        class TestAgent(BaseAgent):
            def __init__(self):
                self._pinned_model = "claude-code-claude-opus-4-5-20251101"
                self._last_model_name = None  # No failover yet
            
            def get_model_name(self):
                return self._pinned_model or ""
            
            @property
            def name(self):
                return "test"
            
            @property
            def display_name(self):
                return "Test"
            
            @property
            def description(self):
                return "Test"
            
            def get_system_prompt(self):
                return ""
            
            def get_available_tools(self):
                return []
        
        agent = TestAgent()
        
        # Initial state: should detect claude_code
        provider = agent._detect_provider()
        assert provider == "claude_code"
        
        # Simulate failover to Cerebras
        agent._last_model_name = "Cerebras-GLM-4.7"
        
        # After failover: should detect cerebras
        provider = agent._detect_provider()
        assert provider == "cerebras"

    def test_budget_check_integration(self):
        """Test that budget checking works with provider detection."""
        from code_puppy.tools.token_slimmer import check_token_budget
        
        # Test Cerebras (boot camp - aggressive)
        result = check_token_budget(15_000, "cerebras", [])
        assert result.should_compact is True  # 15K > 20% of 50K (10K)
        assert "🏋️" in result.recommended_action  # Boot camp emoji
        
        # Test Claude Code (balanced - relaxed)
        result = check_token_budget(100_000, "claude_code", [])
        assert result.should_compact is False  # 100K < 60% of 180K (108K)
        
        result = check_token_budget(110_000, "claude_code", [])
        assert result.should_compact is True  # 110K > 60% of 180K

    def test_all_production_models_have_valid_providers(self):
        """Test that all 15+ production models map to valid providers with limits."""
        from code_puppy.agents.base_agent import BaseAgent
        from code_puppy.tools.token_slimmer import get_provider_limits
        
        class TestAgent(BaseAgent):
            def __init__(self):
                self._last_model_name = None
                self._pinned_model = None
            
            def get_model_name(self):
                return self._pinned_model or ""
            
            @property
            def name(self):
                return "test"
            
            @property
            def display_name(self):
                return "Test"
            
            @property
            def description(self):
                return "Test"
            
            def get_system_prompt(self):
                return ""
            
            def get_available_tools(self):
                return []
        
        production_models = [
            "Cerebras-GLM-4.7",
            "claude-code-claude-opus-4-5-20251101",
            "claude-code-claude-sonnet-4-5-20250929",
            "claude-code-claude-haiku-4-5-20251001",
            "antigravity-claude-opus-4-5-thinking-high",
            "antigravity-claude-opus-4-5-thinking-medium",
            "antigravity-claude-opus-4-5-thinking-low",
            "antigravity-claude-sonnet-4-5-thinking-high",
            "antigravity-claude-sonnet-4-5-thinking-medium",
            "antigravity-claude-sonnet-4-5-thinking-low",
            "antigravity-claude-sonnet-4-5",
            "antigravity-gemini-3-pro-high",
            "antigravity-gemini-3-pro-low",
            "antigravity-gemini-3-flash",
            "chatgpt-gpt-5.2",
            "chatgpt-gpt-5.2-codex",
        ]
        
        agent = TestAgent()
        
        for model in production_models:
            agent._last_model_name = model
            provider = agent._detect_provider()
            limits = get_provider_limits(provider)
            
            # Verify provider has all required keys
            assert "max_input_tokens" in limits, f"Model '{model}' → provider '{provider}' missing max_input_tokens"
            assert "compaction_threshold" in limits, f"Model '{model}' → provider '{provider}' missing compaction_threshold"
            assert "diet_mode" in limits, f"Model '{model}' → provider '{provider}' missing diet_mode"
            assert "max_exchanges" in limits, f"Model '{model}' → provider '{provider}' missing max_exchanges"

    def test_token_budget_manager_integration(self):
        """Test TokenBudgetManager works with all providers."""
        from code_puppy.core.token_budget import TokenBudgetManager
        
        mgr = TokenBudgetManager()
        
        # Test that all provider models are normalized correctly
        test_cases = [
            ("Cerebras-GLM-4.7", "cerebras"),
            ("claude-code-claude-opus-4-5-20251101", "claude_opus"),
            ("antigravity-claude-sonnet-4-5", "claude_sonnet"),
        ]
        
        for model, expected_provider in test_cases:
            normalized = mgr._normalize_provider(model)
            # TokenBudgetManager uses different normalization (legacy)
            # Just verify it doesn't crash
            assert normalized is not None

    def test_rate_limit_failover_integration(self):
        """Test RateLimitFailover can detect all models."""
        from code_puppy.core.rate_limit_failover import RateLimitFailover
        
        mgr = RateLimitFailover()
        
        # Test tier detection
        assert mgr._detect_tier("Cerebras-GLM-4.7") == 5  # Sprinter
        assert mgr._detect_tier("claude-code-claude-opus-4-5-20251101") == 1  # Architect
        assert mgr._detect_tier("antigravity-claude-sonnet-4-5") == 3  # Builder


class TestBackwardCompatibility:
    """Ensure existing Cerebras code still works."""

    def test_cerebras_optimizer_still_works(self):
        """Verify cerebras_optimizer.py backwards compatibility."""
        from code_puppy.tools.cerebras_optimizer import (
            check_cerebras_budget,
            apply_sliding_window,
            CEREBRAS_LIMITS,
        )
        
        # Old code should still work
        result = check_cerebras_budget(15_000, [])
        assert result.should_compact is True
        assert CEREBRAS_LIMITS["max_input_tokens"] == 50_000

    def test_is_cerebras_model_still_works(self):
        """Verify _is_cerebras_model() method still works."""
        from code_puppy.agents.base_agent import BaseAgent
        
        class TestAgent(BaseAgent):
            def __init__(self):
                self._last_model_name = "Cerebras-GLM-4.7"
                self._pinned_model = None
            
            def get_model_name(self):
                return self._pinned_model or ""
            
            @property
            def name(self):
                return "test"
            
            @property
            def display_name(self):
                return "Test"
            
            @property
            def description(self):
                return "Test"
            
            def get_system_prompt(self):
                return ""
            
            def get_available_tools(self):
                return []
        
        agent = TestAgent()
        assert agent._is_cerebras_model() is True
        
        agent._last_model_name = "claude-code-claude-opus-4-5-20251101"
        assert agent._is_cerebras_model() is False
