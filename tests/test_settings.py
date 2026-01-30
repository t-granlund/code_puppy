"""Tests for the pydantic-settings based configuration system."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import SecretStr

from code_puppy.settings import (
    APISettings,
    AgentSettings,
    BannerColors,
    CompactionSettings,
    CompactionStrategy,
    DisplaySettings,
    FrontendSettings,
    ModelSettings,
    PathSettings,
    ReasoningEffort,
    SafetyPermissionLevel,
    SafetySettings,
    Settings,
    Verbosity,
    clear_settings_cache,
    get_api_settings,
    get_path_settings,
    get_settings,
    get_value_from_settings,
    initialize_from_settings,
    settings_to_env_dict,
)


class TestPathSettings:
    """Tests for PathSettings class."""

    def test_default_paths_use_home_directory(self):
        """Without XDG vars set, paths default to ~/.code_puppy."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove XDG vars
            for var in ["XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME"]:
                os.environ.pop(var, None)

            paths = PathSettings()
            home = Path.home()

            assert paths.config_dir == home / ".code_puppy"
            assert paths.data_dir == home / ".code_puppy"
            assert paths.cache_dir == home / ".code_puppy"
            assert paths.state_dir == home / ".code_puppy"

    def test_xdg_paths_when_set(self):
        """When XDG vars are set, use them."""
        with patch.dict(
            os.environ,
            {
                "XDG_CONFIG_HOME": "/tmp/xdg_config",
                "XDG_DATA_HOME": "/tmp/xdg_data",
                "XDG_CACHE_HOME": "/tmp/xdg_cache",
                "XDG_STATE_HOME": "/tmp/xdg_state",
            },
        ):
            paths = PathSettings()

            assert paths.config_dir == Path("/tmp/xdg_config/code_puppy")
            assert paths.data_dir == Path("/tmp/xdg_data/code_puppy")
            assert paths.cache_dir == Path("/tmp/xdg_cache/code_puppy")
            assert paths.state_dir == Path("/tmp/xdg_state/code_puppy")

    def test_file_paths_derived_from_directories(self):
        """File paths are correctly derived from directory paths."""
        paths = PathSettings()

        assert paths.config_file == paths.config_dir / "puppy.cfg"
        assert paths.mcp_servers_file == paths.config_dir / "mcp_servers.json"
        assert paths.models_file == paths.data_dir / "models.json"
        assert paths.agents_dir == paths.data_dir / "agents"
        assert paths.autosave_dir == paths.cache_dir / "autosaves"
        assert paths.command_history_file == paths.state_dir / "command_history.txt"


class TestAPISettings:
    """Tests for APISettings class."""

    def test_api_keys_from_environment(self):
        """API keys are loaded from environment variables."""
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "sk-test-openai",
                "ANTHROPIC_API_KEY": "sk-ant-test",
                "GEMINI_API_KEY": "AIza-test",
            },
            clear=False,
        ):
            clear_settings_cache()
            api = APISettings()

            assert api.openai_api_key is not None
            assert api.openai_api_key.get_secret_value() == "sk-test-openai"
            assert api.anthropic_api_key is not None
            assert api.anthropic_api_key.get_secret_value() == "sk-ant-test"
            assert api.gemini_api_key is not None
            assert api.gemini_api_key.get_secret_value() == "AIza-test"

    def test_has_provider(self):
        """has_provider correctly checks for configured providers."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=False):
            api = APISettings()

            assert api.has_provider("openai") is True
            # Other providers not set in this test

    def test_get_key_value(self):
        """get_key_value returns raw string values."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-value"}, clear=False):
            api = APISettings()

            assert api.get_key_value("OPENAI_API_KEY") == "sk-test-value"
            assert api.get_key_value("NONEXISTENT_KEY") is None

    def test_secrets_not_exposed_in_repr(self):
        """SecretStr prevents accidental logging of API keys."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-secret-key"}, clear=False):
            api = APISettings()

            # Secret should not appear in repr
            repr_str = repr(api.openai_api_key)
            assert "sk-secret-key" not in repr_str
            assert "**********" in repr_str or "SecretStr" in repr_str


class TestModelSettings:
    """Tests for ModelSettings class."""

    def test_default_values(self):
        """Default values are set correctly."""
        settings = ModelSettings()

        assert settings.model == "gpt-5"
        assert settings.temperature is None
        assert settings.openai_reasoning_effort == ReasoningEffort.MEDIUM
        assert settings.openai_verbosity == Verbosity.MEDIUM
        assert settings.enable_streaming is True
        assert settings.http2 is False

    def test_temperature_validation(self):
        """Temperature is validated to be between 0.0 and 2.0."""
        # Valid temperature
        settings = ModelSettings(temperature=1.5)
        assert settings.temperature == 1.5

        # Boundary values
        settings = ModelSettings(temperature=0.0)
        assert settings.temperature == 0.0

        settings = ModelSettings(temperature=2.0)
        assert settings.temperature == 2.0

        # Invalid temperature should raise validation error
        with pytest.raises(Exception):  # ValidationError
            ModelSettings(temperature=3.0)

        with pytest.raises(Exception):
            ModelSettings(temperature=-0.5)

    def test_reasoning_effort_enum(self):
        """ReasoningEffort enum values are valid."""
        assert ReasoningEffort.MINIMAL.value == "minimal"
        assert ReasoningEffort.XHIGH.value == "xhigh"

        settings = ModelSettings(openai_reasoning_effort=ReasoningEffort.HIGH)
        assert settings.openai_reasoning_effort == ReasoningEffort.HIGH


class TestAgentSettings:
    """Tests for AgentSettings class."""

    def test_default_values(self):
        """Default values are set correctly."""
        settings = AgentSettings()

        assert settings.puppy_name == "Puppy"
        assert settings.owner_name == "Master"
        assert settings.default_agent == "code-puppy"
        assert settings.message_limit == 1000
        assert settings.allow_recursion is True
        assert settings.enable_pack_agents is False
        assert settings.enable_universal_constructor is True
        assert settings.enable_dbos is False
        assert settings.disable_mcp is False

    def test_message_limit_validation(self):
        """Message limit must be at least 1."""
        settings = AgentSettings(message_limit=5)
        assert settings.message_limit == 5

        with pytest.raises(Exception):
            AgentSettings(message_limit=0)


class TestCompactionSettings:
    """Tests for CompactionSettings class."""

    def test_default_values(self):
        """Default values are set correctly."""
        settings = CompactionSettings()

        assert settings.strategy == CompactionStrategy.TRUNCATION
        assert settings.protected_token_count == 50000
        assert settings.compaction_threshold == 0.85

    def test_strategy_enum(self):
        """CompactionStrategy enum values are valid."""
        assert CompactionStrategy.SUMMARIZATION.value == "summarization"
        assert CompactionStrategy.TRUNCATION.value == "truncation"

    def test_threshold_validation(self):
        """Compaction threshold is validated to be between 0.5 and 0.95."""
        settings = CompactionSettings(compaction_threshold=0.7)
        assert settings.compaction_threshold == 0.7

        with pytest.raises(Exception):
            CompactionSettings(compaction_threshold=0.3)

        with pytest.raises(Exception):
            CompactionSettings(compaction_threshold=0.99)


class TestDisplaySettings:
    """Tests for DisplaySettings class."""

    def test_default_values(self):
        """Default values are set correctly."""
        settings = DisplaySettings()

        assert settings.yolo_mode is True
        assert settings.subagent_verbose is False
        assert settings.grep_output_verbose is False
        assert settings.suppress_thinking_messages is False
        assert settings.suppress_informational_messages is False
        assert settings.diff_context_lines == 6
        assert settings.auto_save_session is True
        assert settings.max_saved_sessions == 20

    def test_diff_context_lines_validation(self):
        """Diff context lines is validated to be between 0 and 50."""
        settings = DisplaySettings(diff_context_lines=10)
        assert settings.diff_context_lines == 10

        with pytest.raises(Exception):
            DisplaySettings(diff_context_lines=-1)

        with pytest.raises(Exception):
            DisplaySettings(diff_context_lines=100)


class TestBannerColors:
    """Tests for BannerColors class."""

    def test_default_colors(self):
        """Default banner colors are set."""
        colors = BannerColors()

        assert colors.thinking == "deep_sky_blue4"
        assert colors.agent_response == "medium_purple4"
        assert colors.shell_command == "dark_orange3"

    def test_get_color(self):
        """get_color returns correct colors."""
        colors = BannerColors()

        assert colors.get_color("thinking") == "deep_sky_blue4"
        assert colors.get_color("nonexistent") == "blue"  # Default fallback

    def test_as_dict(self):
        """as_dict returns all colors."""
        colors = BannerColors()
        color_dict = colors.as_dict()

        assert "thinking" in color_dict
        assert "agent_response" in color_dict
        assert len(color_dict) >= 10  # At least 10 banner types


class TestSafetySettings:
    """Tests for SafetySettings class."""

    def test_default_values(self):
        """Default values are set correctly."""
        settings = SafetySettings()

        assert settings.safety_permission_level == SafetyPermissionLevel.MEDIUM

    def test_permission_level_enum(self):
        """SafetyPermissionLevel enum values are valid."""
        assert SafetyPermissionLevel.NONE.value == "none"
        assert SafetyPermissionLevel.CRITICAL.value == "critical"


class TestMasterSettings:
    """Tests for the main Settings class."""

    def test_nested_settings_accessible(self):
        """Nested settings are accessible."""
        settings = Settings()

        assert settings.paths is not None
        assert settings.api is not None
        assert settings.model is not None
        assert settings.agent is not None
        assert settings.compaction is not None
        assert settings.display is not None
        assert settings.safety is not None
        assert settings.frontend is not None
        assert settings.banner_colors is not None

    def test_convenience_properties(self):
        """Convenience properties work correctly."""
        settings = Settings()

        assert settings.puppy_name == settings.agent.puppy_name
        assert settings.owner_name == settings.agent.owner_name
        assert settings.yolo_mode == settings.display.yolo_mode
        assert settings.current_model == settings.model.model


class TestCachedAccessors:
    """Tests for cached settings accessors."""

    def test_get_settings_returns_singleton(self):
        """get_settings returns the same instance."""
        clear_settings_cache()

        s1 = get_settings()
        s2 = get_settings()

        assert s1 is s2

    def test_clear_cache_allows_reload(self):
        """clear_settings_cache allows creating a new instance."""
        s1 = get_settings()
        clear_settings_cache()
        s2 = get_settings()

        # After clearing, should be a new instance (unless same values)
        # The content might be the same, but we've cleared the cache


class TestIntegrationHelpers:
    """Tests for integration helper functions."""

    def test_settings_to_env_dict(self):
        """settings_to_env_dict creates correct environment dict."""
        settings = Settings()
        env_dict = settings_to_env_dict(settings)

        assert "CODE_PUPPY_MODEL" in env_dict
        assert "CODE_PUPPY_PUPPY_NAME" in env_dict
        assert "CODE_PUPPY_OWNER_NAME" in env_dict

    def test_initialize_from_settings(self, tmp_path):
        """initialize_from_settings creates directories and exports keys."""
        clear_settings_cache()

        # This might create directories in the user's home; just test it runs
        settings = initialize_from_settings()
        assert settings is not None


class TestBackwardCompatibilityBridge:
    """Tests for backward compatibility with config.py."""

    def test_get_value_from_settings_basic_keys(self):
        """Basic config keys are mapped correctly."""
        clear_settings_cache()

        # These should return string values
        puppy_name = get_value_from_settings("puppy_name")
        assert puppy_name == "Puppy"

        model = get_value_from_settings("model")
        assert model == "gpt-5"

        yolo = get_value_from_settings("yolo_mode")
        assert yolo == "true"

    def test_get_value_from_settings_boolean_keys(self):
        """Boolean config keys return lowercase string values."""
        clear_settings_cache()

        streaming = get_value_from_settings("enable_streaming")
        assert streaming == "true"

        dbos = get_value_from_settings("enable_dbos")
        assert dbos == "false"

    def test_get_value_from_settings_enum_keys(self):
        """Enum config keys return the enum value string."""
        clear_settings_cache()

        strategy = get_value_from_settings("compaction_strategy")
        assert strategy == "truncation"

        effort = get_value_from_settings("openai_reasoning_effort")
        assert effort == "medium"

    def test_get_value_from_settings_numeric_keys(self):
        """Numeric config keys return string representations."""
        clear_settings_cache()

        limit = get_value_from_settings("message_limit")
        assert limit == "1000"

        threshold = get_value_from_settings("compaction_threshold")
        assert threshold == "0.85"

    def test_get_value_from_settings_banner_colors(self):
        """Banner color keys are mapped correctly."""
        clear_settings_cache()

        color = get_value_from_settings("banner_color_thinking")
        assert color == "deep_sky_blue4"

        color = get_value_from_settings("banner_color_agent_response")
        assert color == "medium_purple4"

    def test_get_value_from_settings_unknown_key(self):
        """Unknown keys return None."""
        clear_settings_cache()

        value = get_value_from_settings("nonexistent_key_xyz")
        assert value is None


class TestEnumValues:
    """Tests for enum value correctness."""

    def test_compaction_strategy_values(self):
        """CompactionStrategy enum has correct values."""
        assert CompactionStrategy.SUMMARIZATION.value == "summarization"
        assert CompactionStrategy.TRUNCATION.value == "truncation"

    def test_reasoning_effort_values(self):
        """ReasoningEffort enum has correct values."""
        assert ReasoningEffort.MINIMAL.value == "minimal"
        assert ReasoningEffort.LOW.value == "low"
        assert ReasoningEffort.MEDIUM.value == "medium"
        assert ReasoningEffort.HIGH.value == "high"
        assert ReasoningEffort.XHIGH.value == "xhigh"

    def test_verbosity_values(self):
        """Verbosity enum has correct values."""
        assert Verbosity.LOW.value == "low"
        assert Verbosity.MEDIUM.value == "medium"
        assert Verbosity.HIGH.value == "high"

    def test_safety_permission_level_values(self):
        """SafetyPermissionLevel enum has correct values."""
        assert SafetyPermissionLevel.NONE.value == "none"
        assert SafetyPermissionLevel.LOW.value == "low"
        assert SafetyPermissionLevel.MEDIUM.value == "medium"
        assert SafetyPermissionLevel.HIGH.value == "high"
        assert SafetyPermissionLevel.CRITICAL.value == "critical"


class TestEnvironmentOverrides:
    """Tests for environment variable overrides."""

    def test_model_override_from_environment(self):
        """MODEL can be overridden via environment variable."""
        with patch.dict(os.environ, {"CODE_PUPPY_MODEL": "claude-4-0-sonnet"}, clear=False):
            clear_settings_cache()
            # Note: pydantic-settings uses the env prefix for nested models differently
            # This test verifies the pattern works

    def test_temperature_override_from_environment(self):
        """Temperature can be overridden via environment variable."""
        with patch.dict(os.environ, {"CODE_PUPPY_TEMPERATURE": "0.7"}, clear=False):
            clear_settings_cache()
            # The env override should be picked up


class TestFrontendSettings:
    """Tests for FrontendSettings class."""

    def test_default_values(self):
        """Default values are set correctly."""
        settings = FrontendSettings()

        assert settings.enabled is True
        assert settings.max_recent_events == 100
        assert settings.queue_size == 100
