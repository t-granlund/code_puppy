"""Tests for JSON agent functionality."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from code_puppy.agents.base_agent import BaseAgent
from code_puppy.agents.json_agent import JSONAgent, discover_json_agents
from code_puppy.config import get_user_agents_directory


class TestJSONAgent:
    """Test JSON agent functionality."""

    @pytest.fixture
    def sample_json_config(self):
        """Sample JSON agent configuration."""
        return {
            "name": "test-agent",
            "display_name": "Test Agent 🧪",
            "description": "A test agent for unit testing",
            "system_prompt": "You are a test agent.",
            "tools": ["list_files", "read_file", "edit_file"],
            "user_prompt": "Enter your test request:",
            "tools_config": {"timeout": 30},
        }

    @pytest.fixture
    def sample_json_config_with_list_prompt(self):
        """Sample JSON agent configuration with list-based system prompt."""
        return {
            "name": "list-prompt-agent",
            "description": "Agent with list-based system prompt",
            "system_prompt": [
                "You are a helpful assistant.",
                "You help users with coding tasks.",
                "Always be polite and professional.",
            ],
            "tools": ["list_files", "read_file"],
        }

    @pytest.fixture
    def temp_json_file(self, sample_json_config):
        """Create a temporary JSON file with sample config."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="-agent.json", delete=False
        ) as f:
            json.dump(sample_json_config, f)
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_json_agent_loading(self, temp_json_file):
        """Test loading a JSON agent from file."""
        agent = JSONAgent(temp_json_file)

        assert agent.name == "test-agent"
        assert agent.display_name == "Test Agent 🧪"
        assert agent.description == "A test agent for unit testing"
        assert agent.get_system_prompt() == "You are a test agent."
        assert agent.get_user_prompt() == "Enter your test request:"
        assert agent.get_tools_config() == {"timeout": 30}

    def test_json_agent_with_list_prompt(self, sample_json_config_with_list_prompt):
        """Test JSON agent with list-based system prompt."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="-agent.json", delete=False
        ) as f:
            json.dump(sample_json_config_with_list_prompt, f)
            temp_path = f.name

        try:
            agent = JSONAgent(temp_path)

            assert agent.name == "list-prompt-agent"
            assert agent.display_name == "List-Prompt-Agent 🤖"  # Fallback display name

            # List-based prompt should be joined with newlines
            expected_prompt = "\n".join(
                [
                    "You are a helpful assistant.",
                    "You help users with coding tasks.",
                    "Always be polite and professional.",
                ]
            )
            assert agent.get_system_prompt() == expected_prompt

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_json_agent_available_tools(self, temp_json_file):
        """Test that JSON agent filters tools correctly."""
        agent = JSONAgent(temp_json_file)
        tools = agent.get_available_tools()

        # Should only return tools that exist in our registry
        # "final_result" from JSON should be filtered out
        expected_tools = ["list_files", "read_file", "edit_file"]
        assert tools == expected_tools

    def test_json_agent_inheritance(self, temp_json_file):
        """Test that JSONAgent properly inherits from BaseAgent."""
        agent = JSONAgent(temp_json_file)

        assert isinstance(agent, BaseAgent)
        assert hasattr(agent, "name")
        assert hasattr(agent, "display_name")
        assert hasattr(agent, "description")
        assert callable(agent.get_system_prompt)
        assert callable(agent.get_available_tools)

    def test_invalid_json_file(self):
        """Test handling of invalid JSON files."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="-agent.json", delete=False
        ) as f:
            f.write("invalid json content")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Failed to load JSON agent config"):
                JSONAgent(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_missing_required_fields(self):
        """Test handling of JSON with missing required fields."""
        incomplete_config = {
            "name": "incomplete-agent"
            # Missing description, system_prompt, tools
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix="-agent.json", delete=False
        ) as f:
            json.dump(incomplete_config, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Missing required field"):
                JSONAgent(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_invalid_tools_field(self):
        """Test handling of invalid tools field."""
        invalid_config = {
            "name": "invalid-tools-agent",
            "description": "Test agent",
            "system_prompt": "Test prompt",
            "tools": "not a list",  # Should be a list
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix="-agent.json", delete=False
        ) as f:
            json.dump(invalid_config, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="'tools' must be a list"):
                JSONAgent(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestJSONAgentDiscovery:
    """Test JSON agent discovery functionality."""

    def test_discover_json_agents(self, monkeypatch):
        """Test discovering JSON agents in the user directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the agents directory to use our temp directory
            monkeypatch.setattr(
                "code_puppy.config.get_user_agents_directory", lambda: temp_dir
            )
            # Change to temp directory to avoid finding project .code_puppy
            monkeypatch.chdir(temp_dir)

            # Create valid JSON agent
            agent1_config = {
                "name": "agent1",
                "description": "First agent",
                "system_prompt": "Agent 1 prompt",
                "tools": ["list_files"],
            }
            agent1_path = (
                Path(temp_dir) / "agent1.json"
            )  # Changed from agent1-agent.json
            with open(agent1_path, "w") as f:
                json.dump(agent1_config, f)

            # Create another valid JSON agent
            agent2_config = {
                "name": "agent2",
                "description": "Second agent",
                "system_prompt": "Agent 2 prompt",
                "tools": ["read_file"],
            }
            agent2_path = Path(temp_dir) / "custom-agent.json"
            with open(agent2_path, "w") as f:
                json.dump(agent2_config, f)

            # Create invalid JSON file (should be skipped)
            invalid_path = (
                Path(temp_dir) / "invalid.json"
            )  # Changed from invalid-agent.json
            with open(invalid_path, "w") as f:
                f.write("invalid json")

            # Create non-agent JSON file (should be skipped)
            other_path = Path(temp_dir) / "other.json"
            with open(other_path, "w") as f:
                json.dump({"not": "an agent"}, f)

            # Discover agents
            agents = discover_json_agents()

            # Should find only the two valid agents
            assert len(agents) == 2
            assert "agent1" in agents
            assert "agent2" in agents
            assert agents["agent1"] == str(agent1_path)
            assert agents["agent2"] == str(agent2_path)

    def test_discover_nonexistent_directory(self, monkeypatch, tmp_path):
        """Test discovering agents when directory doesn't exist."""
        # Mock the agents directory to point to non-existent directory
        monkeypatch.setattr(
            "code_puppy.config.get_user_agents_directory",
            lambda: "/nonexistent/directory",
        )
        # Change to temp directory to avoid finding project .code_puppy
        monkeypatch.chdir(tmp_path)
        agents = discover_json_agents()
        assert agents == {}

    def test_get_user_agents_directory(self):
        """Test getting user agents directory."""
        user_dir = get_user_agents_directory()

        assert isinstance(user_dir, str)
        # Should contain code_puppy (either legacy .code_puppy or XDG code_puppy)
        assert "code_puppy" in user_dir
        assert "agents" in user_dir

        # Directory should be created
        assert Path(user_dir).exists()
        assert Path(user_dir).is_dir()

    def test_user_agents_directory_windows(self, monkeypatch):
        """Test user agents directory cross-platform consistency."""
        mock_agents_dir = "/fake/home/.code_puppy/agents"

        # Override the AGENTS_DIR constant directly
        monkeypatch.setattr("code_puppy.config.AGENTS_DIR", mock_agents_dir)

        with patch("code_puppy.config.os.makedirs") as mock_makedirs:
            user_dir = get_user_agents_directory()

            assert user_dir == mock_agents_dir
            mock_makedirs.assert_called_once_with(mock_agents_dir, exist_ok=True)

    def test_user_agents_directory_macos(self, monkeypatch):
        """Test user agents directory on macOS."""
        mock_agents_dir = "/fake/home/.code_puppy/agents"

        # Override the AGENTS_DIR constant directly
        monkeypatch.setattr("code_puppy.config.AGENTS_DIR", mock_agents_dir)

        with patch("code_puppy.config.os.makedirs") as mock_makedirs:
            user_dir = get_user_agents_directory()

            assert user_dir == mock_agents_dir
            mock_makedirs.assert_called_once_with(mock_agents_dir, exist_ok=True)


# ---------------------------------------------------------------------------
# OPT-001-A: skill_metadata field
# ---------------------------------------------------------------------------


class TestSkillMetadata:
    """Tests for the optional skill_metadata field (OPT-001-A)."""

    def test_absent_auto_generates(self, tmp_path):
        """Agents without skill_metadata get auto-generated metadata (OPT-001-B)."""
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "You are helpful.",
            "tools": [],
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        agent = JSONAgent(str(agent_file))
        # Short prompt auto-generates as the full text
        assert agent.skill_metadata == "You are helpful."

    def test_present_returns_value(self, tmp_path):
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "You are a Python specialist with deep expertise.",
            "tools": [],
            "skill_metadata": "Python specialist for code review and refactoring.",
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        agent = JSONAgent(str(agent_file))
        assert agent.skill_metadata == "Python specialist for code review and refactoring."

    def test_invalid_type_raises(self, tmp_path):
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "You are helpful.",
            "tools": [],
            "skill_metadata": 42,  # Not a string
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        with pytest.raises(ValueError, match="skill_metadata.*must be a string"):
            JSONAgent(str(agent_file))


# ---------------------------------------------------------------------------
# OPT-001-B: Auto-generated skill_metadata
# ---------------------------------------------------------------------------


class TestSkillMetadataAutoGeneration:
    """Tests for auto-generated skill_metadata from system_prompt (OPT-001-B)."""

    def test_auto_generates_from_short_prompt(self, tmp_path):
        """Short prompt (under 75 tokens) returned in full."""
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "You are a Python specialist. You review code carefully.",
            "tools": [],
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        agent = JSONAgent(str(agent_file))
        assert agent.skill_metadata == "You are a Python specialist. You review code carefully."

    def test_auto_generates_respects_sentence_boundary(self, tmp_path):
        """Long prompt truncated at sentence boundary, never mid-sentence."""
        # Build a prompt that exceeds 75 tokens (~262 chars)
        long_prompt = (
            "You are an expert security auditor. "
            "You specialize in finding vulnerabilities in web applications. "
            "You have deep expertise in OWASP Top 10 threats. "
            "Your reviews cover authentication, authorization, and input validation. "
            "You also check for SQL injection, XSS, and CSRF vulnerabilities. "
            "Always provide remediation steps with your findings."
        )
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": long_prompt,
            "tools": [],
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        agent = JSONAgent(str(agent_file))
        metadata = agent.skill_metadata
        # Must end at a sentence boundary
        assert metadata is not None
        assert metadata.endswith(".")
        # Must be shorter than the full prompt
        assert len(metadata) < len(long_prompt)
        # Must not truncate mid-sentence
        assert not metadata.endswith("...")

    def test_auto_generates_with_info_log(self, tmp_path, caplog):
        """Auto-generation emits info-level log."""
        import logging
        config = {
            "name": "log-test-agent",
            "description": "A test agent",
            "system_prompt": "You are a helpful assistant.",
            "tools": [],
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        with caplog.at_level(logging.INFO, logger="code_puppy.agents.json_agent"):
            agent = JSONAgent(str(agent_file))
            _ = agent.skill_metadata
        assert "skill_metadata auto-generated for agent 'log-test-agent'" in caplog.text

    def test_explicit_metadata_not_auto_generated(self, tmp_path, caplog):
        """When skill_metadata is set, no auto-generation occurs."""
        import logging
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "You are a very long and detailed system prompt." * 10,
            "tools": [],
            "skill_metadata": "Curated summary.",
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        with caplog.at_level(logging.INFO, logger="code_puppy.agents.json_agent"):
            agent = JSONAgent(str(agent_file))
            assert agent.skill_metadata == "Curated summary."
        assert "auto-generated" not in caplog.text

    def test_empty_system_prompt_returns_none(self, tmp_path):
        """Empty system_prompt produces None metadata."""
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "",
            "tools": [],
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        agent = JSONAgent(str(agent_file))
        assert agent.skill_metadata is None



# ---------------------------------------------------------------------------
# OPT-001-C: Planning-agent prefers metadata
# ---------------------------------------------------------------------------


class TestSkillMetadataPreference:
    """Tests that skill_metadata is preferred over description (OPT-001-C)."""

    def test_metadata_preferred_over_description(self, tmp_path):
        """When skill_metadata is set, it should be returned instead of description."""
        config = {
            "name": "expert-agent",
            "description": "An expert agent for various tasks.",
            "system_prompt": "You are an expert.",
            "tools": [],
            "skill_metadata": "Python specialist for code review and refactoring.",
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        agent = JSONAgent(str(agent_file))

        # skill_metadata should be preferred
        metadata = agent.skill_metadata
        assert metadata == "Python specialist for code review and refactoring."
        assert metadata != agent.description

    def test_no_metadata_uses_description(self, tmp_path):
        """When no skill_metadata, auto-generated metadata comes from system_prompt."""
        config = {
            "name": "basic-agent",
            "description": "A basic agent.",
            "system_prompt": "You are a basic assistant that helps with tasks.",
            "tools": [],
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        agent = JSONAgent(str(agent_file))

        # Auto-generated metadata comes from system_prompt, not description
        metadata = agent.skill_metadata
        assert metadata is not None
        assert "basic assistant" in metadata


# ---------------------------------------------------------------------------
# OPT-001-D: Lightweight metadata loading
# ---------------------------------------------------------------------------


class TestLightweightMetadataLoading:
    """Tests that read_metadata() provides lightweight agent discovery."""

    def test_read_metadata_returns_all_fields(self, tmp_path):
        """read_metadata should return all discovery fields without full init."""
        config = {
            "name": "test-agent",
            "display_name": "Test Agent 🧪",
            "description": "A test agent for testing.",
            "system_prompt": "You are a test agent.",
            "tools": ["read_file", "edit_file"],
            "skill_metadata": "Testing specialist for unit and integration tests.",
            "delegation_mode": "handoff",
            "skills": ["python-style"],
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))

        meta = JSONAgent.read_metadata(str(agent_file))

        assert meta["name"] == "test-agent"
        assert meta["display_name"] == "Test Agent 🧪"
        assert meta["description"] == "A test agent for testing."
        assert meta["skill_metadata"] == "Testing specialist for unit and integration tests."
        assert meta["delegation_mode"] == "handoff"
        assert meta["tool_count"] == 2
        assert meta["skills"] == ["python-style"]
        assert meta["requires_tool_calling"] is True

    def test_read_metadata_auto_generates_skill_metadata(self, tmp_path):
        """When no skill_metadata, auto-generate from system_prompt."""
        config = {
            "name": "basic-agent",
            "description": "Basic agent.",
            "system_prompt": "You are a Python expert. You help with code review and refactoring.",
            "tools": [],
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))

        meta = JSONAgent.read_metadata(str(agent_file))

        assert meta["skill_metadata"] is not None
        assert "Python expert" in meta["skill_metadata"]

    def test_read_metadata_defaults_on_missing_fields(self, tmp_path):
        """Minimal config should get sensible defaults."""
        config = {
            "name": "minimal",
            "description": "Minimal agent.",
            "system_prompt": "You help.",
            "tools": [],
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))

        meta = JSONAgent.read_metadata(str(agent_file))

        assert meta["name"] == "minimal"
        assert meta["display_name"] == "Minimal 🤖"
        assert meta["delegation_mode"] == "subtask"
        assert meta["tool_count"] == 0
        assert meta["requires_tool_calling"] is False
        assert meta["skills"] == []

    def test_read_metadata_handles_invalid_file(self, tmp_path):
        """Invalid JSON should return empty dict, not crash."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json{{{")

        meta = JSONAgent.read_metadata(str(bad_file))

        assert meta == {}

    def test_read_metadata_handles_missing_file(self):
        """Missing file should return empty dict."""
        meta = JSONAgent.read_metadata("/nonexistent/path/agent.json")

        assert meta == {}


# ---------------------------------------------------------------------------
# OPT-007-A: delegation_mode field
# ---------------------------------------------------------------------------


class TestDelegationMode:
    """Tests for the optional delegation_mode field (OPT-007-A)."""

    def test_absent_defaults_to_subtask(self, tmp_path):
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "You are helpful.",
            "tools": [],
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        agent = JSONAgent(str(agent_file))
        assert agent.delegation_mode == "subtask"

    def test_subtask_accepted(self, tmp_path):
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "You are helpful.",
            "tools": [],
            "delegation_mode": "subtask",
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        agent = JSONAgent(str(agent_file))
        assert agent.delegation_mode == "subtask"

    def test_handoff_accepted(self, tmp_path):
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "You are helpful.",
            "tools": [],
            "delegation_mode": "handoff",
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        agent = JSONAgent(str(agent_file))
        assert agent.delegation_mode == "handoff"

    def test_invalid_value_raises(self, tmp_path):
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "You are helpful.",
            "tools": [],
            "delegation_mode": "invalid_mode",
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        with pytest.raises(ValueError, match="delegation_mode.*must be"):
            JSONAgent(str(agent_file))


# ---------------------------------------------------------------------------
# OPT-004-A: requires_tool_calling field
# ---------------------------------------------------------------------------


class TestRequiresToolCalling:
    """Tests for the optional requires_tool_calling field (OPT-004-A)."""

    def test_no_tools_no_field_returns_false(self, tmp_path):
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "You are helpful.",
            "tools": [],
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        agent = JSONAgent(str(agent_file))
        assert agent.requires_tool_calling is False

    def test_has_tools_no_field_infers_true(self, tmp_path):
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "You are helpful.",
            "tools": ["list_files", "read_file"],
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        agent = JSONAgent(str(agent_file))
        assert agent.requires_tool_calling is True

    def test_explicit_true(self, tmp_path):
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "You are helpful.",
            "tools": ["list_files"],
            "requires_tool_calling": True,
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        agent = JSONAgent(str(agent_file))
        assert agent.requires_tool_calling is True

    def test_explicit_false_with_tools(self, tmp_path):
        """Agent can explicitly opt out even with tools (graceful degradation)."""
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "You are helpful.",
            "tools": ["list_files"],
            "requires_tool_calling": False,
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        agent = JSONAgent(str(agent_file))
        assert agent.requires_tool_calling is False


# ---------------------------------------------------------------------------
# OPT-005-B: skills array field
# ---------------------------------------------------------------------------


class TestSkillsArray:
    """Tests for the optional skills array field (OPT-005-B)."""

    def test_absent_returns_empty_list(self, tmp_path):
        """Existing agents without skills array work unchanged."""
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "You are helpful.",
            "tools": [],
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        agent = JSONAgent(str(agent_file))
        assert agent.skills == []

    def test_valid_skills_array(self, tmp_path):
        """Skills array with valid string entries."""
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "You are helpful.",
            "tools": [],
            "skills": ["coding-standards", "security-guidelines"],
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        agent = JSONAgent(str(agent_file))
        assert agent.skills == ["coding-standards", "security-guidelines"]

    def test_empty_skills_array(self, tmp_path):
        """Empty skills array is valid."""
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "You are helpful.",
            "tools": [],
            "skills": [],
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        agent = JSONAgent(str(agent_file))
        assert agent.skills == []

    def test_invalid_skills_not_list(self, tmp_path):
        """Non-list skills field raises ValueError."""
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "You are helpful.",
            "tools": [],
            "skills": "not-a-list",
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        with pytest.raises(ValueError, match="'skills' must be a list"):
            JSONAgent(str(agent_file))

    def test_invalid_skills_entry_type(self, tmp_path):
        """Non-string entry in skills array raises ValueError."""
        config = {
            "name": "test-agent",
            "description": "A test agent",
            "system_prompt": "You are helpful.",
            "tools": [],
            "skills": ["valid-skill", 42],
        }
        agent_file = tmp_path / "test.json"
        agent_file.write_text(json.dumps(config))
        with pytest.raises(ValueError, match="skills\\[1\\].*must be a string"):
            JSONAgent(str(agent_file))
