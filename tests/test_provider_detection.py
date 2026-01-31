"""Tests for _detect_provider() method in BaseAgent.

Verifies that all production model names are correctly mapped to their provider keys.
"""

import pytest


class TestProviderDetection:
    """Tests for BaseAgent._detect_provider() method."""

    @pytest.fixture
    def mock_agent(self):
        """Create a minimal agent for testing _detect_provider."""
        from code_puppy.agents.base_agent import BaseAgent
        
        class TestAgent(BaseAgent):
            def __init__(self):
                # Skip full init to avoid dependencies
                self._last_model_name = None
                self._pinned_model = None
            
            def get_model_name(self):
                return self._pinned_model or ""
            
            # Abstract methods required by BaseAgent
            @property
            def name(self):
                return "test_agent"
            
            @property
            def display_name(self):
                return "Test Agent"
            
            @property
            def description(self):
                return "Test agent for provider detection"
            
            def get_system_prompt(self):
                return "Test system prompt"
            
            def get_available_tools(self):
                return []
        
        return TestAgent()
    
    # =================================================================
    # Cerebras Models (Boot Camp - most aggressive)
    # =================================================================
    
    def test_cerebras_glm_4_7(self, mock_agent):
        """Cerebras-GLM-4.7 -> cerebras"""
        mock_agent._last_model_name = "Cerebras-GLM-4.7"
        assert mock_agent._detect_provider() == "cerebras"
    
    def test_cerebras_lowercase(self, mock_agent):
        """cerebras-glm-4.7 -> cerebras (case insensitive)"""
        mock_agent._last_model_name = "cerebras-glm-4.7"
        assert mock_agent._detect_provider() == "cerebras"
    
    # =================================================================
    # Claude Code OAuth Models (Balanced)
    # =================================================================
    
    def test_claude_code_opus(self, mock_agent):
        """claude-code-claude-opus-4-5-20251101 -> claude_code"""
        mock_agent._last_model_name = "claude-code-claude-opus-4-5-20251101"
        assert mock_agent._detect_provider() == "claude_code"
    
    def test_claude_code_sonnet(self, mock_agent):
        """claude-code-claude-sonnet-4-5-20250929 -> claude_code"""
        mock_agent._last_model_name = "claude-code-claude-sonnet-4-5-20250929"
        assert mock_agent._detect_provider() == "claude_code"
    
    def test_claude_code_haiku(self, mock_agent):
        """claude-code-claude-haiku-4-5-20251001 -> claude_code"""
        mock_agent._last_model_name = "claude-code-claude-haiku-4-5-20251001"
        assert mock_agent._detect_provider() == "claude_code"
    
    # =================================================================
    # Antigravity OAuth Models (Balanced)
    # =================================================================
    
    def test_antigravity_opus_thinking_high(self, mock_agent):
        """antigravity-claude-opus-4-5-thinking-high -> antigravity"""
        mock_agent._last_model_name = "antigravity-claude-opus-4-5-thinking-high"
        assert mock_agent._detect_provider() == "antigravity"
    
    def test_antigravity_opus_thinking_medium(self, mock_agent):
        """antigravity-claude-opus-4-5-thinking-medium -> antigravity"""
        mock_agent._last_model_name = "antigravity-claude-opus-4-5-thinking-medium"
        assert mock_agent._detect_provider() == "antigravity"
    
    def test_antigravity_opus_thinking_low(self, mock_agent):
        """antigravity-claude-opus-4-5-thinking-low -> antigravity"""
        mock_agent._last_model_name = "antigravity-claude-opus-4-5-thinking-low"
        assert mock_agent._detect_provider() == "antigravity"
    
    def test_antigravity_sonnet_thinking_high(self, mock_agent):
        """antigravity-claude-sonnet-4-5-thinking-high -> antigravity"""
        mock_agent._last_model_name = "antigravity-claude-sonnet-4-5-thinking-high"
        assert mock_agent._detect_provider() == "antigravity"
    
    def test_antigravity_sonnet_thinking_medium(self, mock_agent):
        """antigravity-claude-sonnet-4-5-thinking-medium -> antigravity"""
        mock_agent._last_model_name = "antigravity-claude-sonnet-4-5-thinking-medium"
        assert mock_agent._detect_provider() == "antigravity"
    
    def test_antigravity_sonnet_thinking_low(self, mock_agent):
        """antigravity-claude-sonnet-4-5-thinking-low -> antigravity"""
        mock_agent._last_model_name = "antigravity-claude-sonnet-4-5-thinking-low"
        assert mock_agent._detect_provider() == "antigravity"
    
    def test_antigravity_sonnet_plain(self, mock_agent):
        """antigravity-claude-sonnet-4-5 -> antigravity"""
        mock_agent._last_model_name = "antigravity-claude-sonnet-4-5"
        assert mock_agent._detect_provider() == "antigravity"
    
    def test_antigravity_gemini_pro_high(self, mock_agent):
        """antigravity-gemini-3-pro-high -> antigravity"""
        mock_agent._last_model_name = "antigravity-gemini-3-pro-high"
        assert mock_agent._detect_provider() == "antigravity"
    
    def test_antigravity_gemini_pro_low(self, mock_agent):
        """antigravity-gemini-3-pro-low -> antigravity"""
        mock_agent._last_model_name = "antigravity-gemini-3-pro-low"
        assert mock_agent._detect_provider() == "antigravity"
    
    def test_antigravity_gemini_flash(self, mock_agent):
        """antigravity-gemini-3-flash -> antigravity"""
        mock_agent._last_model_name = "antigravity-gemini-3-flash"
        assert mock_agent._detect_provider() == "antigravity"
    
    # =================================================================
    # ChatGPT OAuth Models (Balanced)
    # =================================================================
    
    def test_chatgpt_gpt_5_2(self, mock_agent):
        """chatgpt-gpt-5.2 -> chatgpt_teams"""
        mock_agent._last_model_name = "chatgpt-gpt-5.2"
        assert mock_agent._detect_provider() == "chatgpt_teams"
    
    def test_chatgpt_gpt_5_2_codex(self, mock_agent):
        """chatgpt-gpt-5.2-codex -> chatgpt_teams"""
        mock_agent._last_model_name = "chatgpt-gpt-5.2-codex"
        assert mock_agent._detect_provider() == "chatgpt_teams"
    
    # =================================================================
    # Failover Detection (uses _last_model_name over pinned)
    # =================================================================
    
    def test_failover_detection_uses_last_model(self, mock_agent):
        """Failover should use _last_model_name, not pinned model."""
        mock_agent._pinned_model = "claude-code-claude-opus-4-5-20251101"
        mock_agent._last_model_name = "Cerebras-GLM-4.7"
        # Should detect Cerebras (failover), not Claude Code (original)
        assert mock_agent._detect_provider() == "cerebras"
    
    def test_no_failover_uses_pinned(self, mock_agent):
        """When no failover, should use pinned model."""
        mock_agent._pinned_model = "antigravity-claude-opus-4-5-thinking-high"
        mock_agent._last_model_name = None
        assert mock_agent._detect_provider() == "antigravity"
    
    # =================================================================
    # Edge Cases
    # =================================================================
    
    def test_empty_model_returns_default(self, mock_agent):
        """Empty model name -> default"""
        mock_agent._last_model_name = ""
        mock_agent._pinned_model = ""
        assert mock_agent._detect_provider() == "default"
    
    def test_unknown_model_returns_default(self, mock_agent):
        """Unknown model -> default"""
        mock_agent._last_model_name = "some-unknown-model"
        assert mock_agent._detect_provider() == "default"


class TestProviderLimitsIntegration:
    """Tests that provider detection integrates with token_slimmer limits."""
    
    def test_all_providers_have_limits(self):
        """All detected providers should have limits in token_slimmer."""
        from code_puppy.tools.token_slimmer import get_provider_limits
        
        providers = [
            "cerebras",
            "claude_code", 
            "antigravity",
            "chatgpt_teams",
            "anthropic",
            "openai",
            "default",
        ]
        
        for provider in providers:
            limits = get_provider_limits(provider)
            assert limits is not None, f"No limits for provider: {provider}"
            assert "max_input_tokens" in limits
            assert "compaction_threshold" in limits
            assert "diet_mode" in limits
    
    def test_cerebras_is_boot_camp(self):
        """Cerebras should be in boot_camp mode (most aggressive)."""
        from code_puppy.tools.token_slimmer import get_provider_limits
        
        limits = get_provider_limits("cerebras")
        assert limits["diet_mode"] == "boot_camp"
        assert limits["compaction_threshold"] == 0.20
    
    def test_claude_code_is_balanced(self):
        """Claude Code should be in balanced mode."""
        from code_puppy.tools.token_slimmer import get_provider_limits
        
        limits = get_provider_limits("claude_code")
        assert limits["diet_mode"] == "balanced"
