"""Tests for GitHub Copilot model integration."""

import pytest
from unittest.mock import MagicMock, patch

from code_puppy.github_copilot_model import (
    GitHubCopilotModel,
    check_copilot_cli_installed,
    check_copilot_auth,
    get_premium_request_multiplier,
)


class TestPremiumRequestMultipliers:
    """Test premium request multiplier calculation."""

    def test_claude_opus_multiplier(self):
        """Claude Opus models should have 3x multiplier."""
        assert get_premium_request_multiplier("claude-opus-4.5") == 3.0
        assert get_premium_request_multiplier("claude-opus-4.1") == 3.0

    def test_claude_haiku_multiplier(self):
        """Claude Haiku models should have 0.33x multiplier."""
        assert get_premium_request_multiplier("claude-haiku-4.5") == 0.33
        assert get_premium_request_multiplier("claude-haiku-4") == 0.33

    def test_grok_multiplier(self):
        """Grok models should have 0.25x multiplier."""
        assert get_premium_request_multiplier("grok-code-fast-1") == 0.25

    def test_free_models(self):
        """Free models should have 0 multiplier."""
        assert get_premium_request_multiplier("gpt-4.1") == 0.0
        assert get_premium_request_multiplier("gpt-5-mini") == 0.0
        assert get_premium_request_multiplier("raptor-mini") == 0.0

    def test_default_multiplier(self):
        """Unknown models should have 1.0 default multiplier."""
        assert get_premium_request_multiplier("unknown-model") == 1.0

    def test_case_insensitive(self):
        """Multiplier lookup should be case-insensitive."""
        assert get_premium_request_multiplier("CLAUDE-OPUS-4.5") == 3.0
        assert get_premium_request_multiplier("GPT-5.2") == 1.0


@patch("code_puppy.github_copilot_model.subprocess.run")
class TestCopilotPrerequisites:
    """Test Copilot prerequisite checks."""

    def test_copilot_cli_installed(self, mock_run):
        """Test checking if Copilot CLI is installed."""
        mock_run.return_value = MagicMock(returncode=0, stdout="gh copilot version 1.0.0")
        assert check_copilot_cli_installed() is True

    def test_copilot_cli_not_installed(self, mock_run):
        """Test when Copilot CLI is not installed."""
        mock_run.side_effect = FileNotFoundError()
        assert check_copilot_cli_installed() is False

    def test_copilot_auth_success(self, mock_run):
        """Test successful authentication check."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="✓ Logged in to github.com as user"
        )
        assert check_copilot_auth() is True

    def test_copilot_not_authenticated(self, mock_run):
        """Test when user is not authenticated."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert check_copilot_auth() is False


class TestGitHubCopilotModel:
    """Test GitHub Copilot model creation and usage."""

    @patch("code_puppy.github_copilot_model.check_copilot_cli_installed")
    @patch("code_puppy.github_copilot_model.check_copilot_auth")
    def test_model_init_missing_cli(self, mock_auth, mock_cli):
        """Test model initialization when CLI is missing."""
        mock_cli.return_value = False
        mock_auth.return_value = True

        with pytest.raises(RuntimeError, match="GitHub Copilot CLI is not installed"):
            GitHubCopilotModel(model_name="gpt-5.2")

    @patch("code_puppy.github_copilot_model.check_copilot_cli_installed")
    @patch("code_puppy.github_copilot_model.check_copilot_auth")
    def test_model_init_not_authenticated(self, mock_auth, mock_cli):
        """Test model initialization when not authenticated."""
        mock_cli.return_value = True
        mock_auth.return_value = False

        with pytest.raises(RuntimeError, match="Not authenticated with GitHub"):
            GitHubCopilotModel(model_name="gpt-5.2")

    @patch("code_puppy.github_copilot_model.check_copilot_cli_installed")
    @patch("code_puppy.github_copilot_model.check_copilot_auth")
    def test_model_init_missing_sdk(self, mock_auth, mock_cli):
        """Test model initialization when SDK is not installed."""
        mock_cli.return_value = True
        mock_auth.return_value = True

        with pytest.raises(RuntimeError, match="GitHub Copilot SDK is not installed"):
            GitHubCopilotModel(model_name="gpt-5.2")

    @patch("code_puppy.github_copilot_model.check_copilot_cli_installed")
    @patch("code_puppy.github_copilot_model.check_copilot_auth")
    def test_model_name(self, mock_auth, mock_cli):
        """Test model name property."""
        mock_cli.return_value = True
        mock_auth.return_value = True

        # Mock the SDK import
        with patch.dict("sys.modules", {"github_copilot_sdk": MagicMock()}):
            model = GitHubCopilotModel(model_name="gpt-5.2")
            assert model.name() == "gpt-5.2"


class TestModelFactoryIntegration:
    """Test GitHub Copilot model integration with model factory."""

    def test_github_copilot_config(self):
        """Test loading GitHub Copilot model from config."""
        from code_puppy.model_factory import ModelFactory

        config = {
            "copilot-gpt52": {
                "type": "github-copilot",
                "name": "gpt-5.2",
                "context_length": 128000,
            }
        }

        # Mock the prerequisites and SDK
        with patch("code_puppy.github_copilot_model.check_copilot_cli_installed") as mock_cli:
            with patch("code_puppy.github_copilot_model.check_copilot_auth") as mock_auth:
                with patch.dict("sys.modules", {"github_copilot_sdk": MagicMock()}):
                    mock_cli.return_value = True
                    mock_auth.return_value = True

                    model = ModelFactory.get_model("copilot-gpt52", config)
                    assert model is not None
                    assert model.model_name == "gpt-5.2"

    def test_github_copilot_missing_prerequisites(self):
        """Test graceful handling when prerequisites are missing."""
        from code_puppy.model_factory import ModelFactory

        config = {
            "copilot-gpt52": {
                "type": "github-copilot",
                "name": "gpt-5.2",
                "context_length": 128000,
            }
        }

        # Mock missing CLI
        with patch("code_puppy.github_copilot_model.check_copilot_cli_installed") as mock_cli:
            mock_cli.return_value = False

            model = ModelFactory.get_model("copilot-gpt52", config)
            # Should return None instead of raising
            assert model is None
