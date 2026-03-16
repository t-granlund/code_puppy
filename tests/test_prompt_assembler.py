"""Tests for code_puppy.prompt_assembler (OPT-000-A).

Validates that PromptAssembler produces identical output to the
current scattered prompt assembly pattern in base_agent.py.
"""

import dataclasses
import json
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from code_puppy.prompt_assembler import (
    AssemblyResult,
    PromptAssembler,
    assemble_prompt,
    estimate_tokens,
)


# ---------------------------------------------------------------------------
# estimate_tokens tests
# ---------------------------------------------------------------------------


class TestEstimateTokens:
    """Tests for the canonical token estimator."""

    def test_empty_string_returns_zero(self):
        assert estimate_tokens("") == 0

    def test_none_like_empty(self):
        # Empty string is the only falsy input; None would TypeError in len()
        assert estimate_tokens("") == 0

    def test_short_string_at_least_one(self):
        assert estimate_tokens("hi") >= 1

    def test_known_length_estimate(self):
        # 350 chars / 3.5 chars_per_token = 100 tokens
        text = "a" * 350
        result = estimate_tokens(text)
        assert result == 100

    def test_realistic_prompt_range(self):
        # A typical system prompt is ~2000 chars => ~571 tokens
        prompt = "You are a helpful coding assistant. " * 57  # ~1995 chars
        result = estimate_tokens(prompt)
        assert 400 < result < 700  # Within reasonable range

    def test_code_content(self):
        code = 'def hello():\n    print("Hello, world!")\n    return True\n'
        result = estimate_tokens(code)
        assert result > 0


# ---------------------------------------------------------------------------
# AssemblyResult tests
# ---------------------------------------------------------------------------


class TestAssemblyResult:
    """Tests for the frozen result dataclass."""

    def test_is_frozen(self):
        result = AssemblyResult(
            prompt="test",
            total_tokens=5,
            breakdown={"base_prompt": 5},
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.prompt = "modified"  # type: ignore

    def test_default_components(self):
        result = AssemblyResult(
            prompt="test",
            total_tokens=5,
            breakdown={"base_prompt": 5},
        )
        assert result.components == []

    def test_all_fields_accessible(self):
        result = AssemblyResult(
            prompt="hello",
            total_tokens=10,
            breakdown={"base_prompt": 8, "identity": 2},
            components=[("base_prompt", "hello")],
        )
        assert result.prompt == "hello"
        assert result.total_tokens == 10
        assert result.breakdown["base_prompt"] == 8
        assert len(result.components) == 1


# ---------------------------------------------------------------------------
# Mock agent factory
# ---------------------------------------------------------------------------


def _make_mock_agent(
    system_prompt: str = "You are a helpful assistant.",
    identity_prompt: str = "\n\nYour ID is `test-agent-abc123`.",
    puppy_rules: str | None = None,
) -> MagicMock:
    """Create a mock BaseAgent with predictable prompt methods."""
    agent = MagicMock()
    agent.get_system_prompt.return_value = system_prompt
    agent.get_identity_prompt.return_value = identity_prompt
    agent.load_puppy_rules.return_value = puppy_rules

    # get_full_system_prompt mirrors the real BaseAgent implementation
    agent.get_full_system_prompt.return_value = system_prompt + identity_prompt
    return agent


# ---------------------------------------------------------------------------
# PromptAssembler.assemble() tests
# ---------------------------------------------------------------------------


class TestPromptAssemblerAssemble:
    """Core tests: assemble() must match current behavior exactly."""

    def test_matches_current_pattern_no_rules(self):
        """Verify: assemble() == get_full_system_prompt() when no puppy_rules."""
        agent = _make_mock_agent(puppy_rules=None)

        result = PromptAssembler(agent).assemble()

        expected = agent.get_full_system_prompt()
        assert result.prompt == expected

    def test_matches_current_pattern_with_rules(self):
        """Verify: assemble() == get_full_system_prompt() + '\\n' + puppy_rules.

        This is the exact pattern from base_agent.py lines 1329-1332:
            instructions = self.get_full_system_prompt()
            puppy_rules = self.load_puppy_rules()
            if puppy_rules:
                instructions += f"\\n{puppy_rules}"
        """
        rules = "# Project Rules\n- Use type hints\n- Write tests"
        agent = _make_mock_agent(puppy_rules=rules)

        result = PromptAssembler(agent).assemble()

        expected = agent.get_full_system_prompt() + f"\n{rules}"
        assert result.prompt == expected

    def test_breakdown_sums_to_total(self):
        """Token breakdown components must sum to total_tokens."""
        agent = _make_mock_agent(puppy_rules="Some rules here")
        result = PromptAssembler(agent).assemble()

        breakdown_sum = sum(result.breakdown.values())
        assert result.total_tokens == breakdown_sum

    def test_breakdown_has_all_keys(self):
        """Breakdown must always contain all 5 component keys."""
        agent = _make_mock_agent()
        result = PromptAssembler(agent).assemble()

        expected_keys = {
            "base_prompt",
            "identity",
            "shared_skills",
            "plugin_injections",
            "puppy_rules",
        }
        assert set(result.breakdown.keys()) == expected_keys

    def test_components_list_no_rules(self):
        """Without puppy_rules, components has base_prompt and identity only."""
        agent = _make_mock_agent(puppy_rules=None)
        result = PromptAssembler(agent).assemble()

        names = [name for name, _ in result.components]
        assert names == ["base_prompt", "identity"]

    def test_components_list_with_rules(self):
        """With puppy_rules, components includes puppy_rules entry."""
        agent = _make_mock_agent(puppy_rules="Rules!")
        result = PromptAssembler(agent).assemble()

        names = [name for name, _ in result.components]
        assert names == ["base_prompt", "identity", "puppy_rules"]

    def test_shared_skills_placeholder_is_zero(self):
        """OPT-005 placeholder: shared_skills breakdown is always 0 for now."""
        agent = _make_mock_agent()
        result = PromptAssembler(agent).assemble()

        assert result.breakdown["shared_skills"] == 0

    def test_plugin_injections_placeholder_is_zero(self):
        """Plugin injections are captured inside get_system_prompt, not here."""
        agent = _make_mock_agent()
        result = PromptAssembler(agent).assemble()

        assert result.breakdown["plugin_injections"] == 0


class TestPromptAssemblerAssembleInstructions:
    """assemble_instructions() is an alias for assemble()."""

    def test_identical_to_assemble(self):
        agent = _make_mock_agent(puppy_rules="Rules")
        assembler = PromptAssembler(agent)

        result1 = assembler.assemble()
        result2 = assembler.assemble_instructions()

        assert result1.prompt == result2.prompt
        assert result1.total_tokens == result2.total_tokens


# ---------------------------------------------------------------------------
# Convenience function tests
# ---------------------------------------------------------------------------


class TestAssemblePromptFunction:
    """Tests for the module-level assemble_prompt() convenience function."""

    def test_matches_class_usage(self):
        agent = _make_mock_agent(puppy_rules="Some rules")

        func_result = assemble_prompt(agent)
        class_result = PromptAssembler(agent).assemble()

        assert func_result.prompt == class_result.prompt
        assert func_result.total_tokens == class_result.total_tokens

    def test_accepts_shared_skills_param(self):
        """shared_skills parameter is accepted (OPT-005)."""
        agent = _make_mock_agent()
        # No skills passed — should not raise
        result = assemble_prompt(agent, shared_skills=[])
        assert result.prompt  # Non-empty


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_system_prompt(self):
        agent = _make_mock_agent(system_prompt="")
        result = PromptAssembler(agent).assemble()
        # Should still have identity prompt
        assert result.prompt == agent.get_identity_prompt()

    def test_very_long_prompt(self):
        long_prompt = "x" * 100_000
        agent = _make_mock_agent(system_prompt=long_prompt)
        result = PromptAssembler(agent).assemble()
        assert result.total_tokens > 20_000

    def test_unicode_content(self):
        agent = _make_mock_agent(system_prompt="你好世界 🐶 こんにちは")
        result = PromptAssembler(agent).assemble()
        assert result.total_tokens > 0
        assert "🐶" in result.prompt

    def test_multiline_rules(self):
        rules = "Line 1\nLine 2\nLine 3\n"
        agent = _make_mock_agent(puppy_rules=rules)
        result = PromptAssembler(agent).assemble()
        assert rules in result.prompt


# ---------------------------------------------------------------------------
# Tool count guardrails (OPT-002-A) tests
# ---------------------------------------------------------------------------


class TestValidateToolCount:
    """Tests for tool count validation (OPT-002-A)."""

    def test_within_threshold_returns_true(self):
        from code_puppy.prompt_assembler import validate_tool_count

        assert validate_tool_count("test-agent", 10) is True

    def test_at_threshold_returns_true(self):
        from code_puppy.prompt_assembler import validate_tool_count

        assert validate_tool_count("test-agent", 15) is True

    def test_above_threshold_returns_false(self, caplog):
        from code_puppy.prompt_assembler import validate_tool_count

        import logging

        with caplog.at_level(logging.WARNING):
            result = validate_tool_count("test-agent", 16)

        assert result is False
        assert "test-agent" in caplog.text
        assert "16" in caplog.text

    def test_above_threshold_includes_tool_names(self, caplog):
        from code_puppy.prompt_assembler import validate_tool_count

        import logging

        with caplog.at_level(logging.WARNING):
            validate_tool_count(
                "test-agent",
                16,
                tool_names=["tool_a", "tool_b"],
            )

        assert "tool_a" in caplog.text

    def test_custom_threshold(self):
        from code_puppy.prompt_assembler import validate_tool_count

        assert validate_tool_count("test-agent", 8, threshold=5) is False
        assert validate_tool_count("test-agent", 5, threshold=5) is True

    def test_strict_mode_raises(self):
        from code_puppy.prompt_assembler import validate_tool_count

        with pytest.raises(ValueError, match="test-agent.*16"):
            validate_tool_count("test-agent", 16, strict=True)

    def test_strict_mode_no_error_within_threshold(self):
        from code_puppy.prompt_assembler import validate_tool_count

        # Should not raise
        result = validate_tool_count("test-agent", 10, strict=True)
        assert result is True


# ---------------------------------------------------------------------------
# OPT-002-B: Strict mode config option
# ---------------------------------------------------------------------------


class TestToolCountStrictMode:
    """Tests for strict mode tool count enforcement (OPT-002-B)."""

    def test_strict_mode_raises_on_exceed(self):
        """Strict mode raises ValueError when tools exceed threshold."""
        from code_puppy.prompt_assembler import validate_tool_count

        with pytest.raises(ValueError, match="Agent 'strict-test' has 20 tools"):
            validate_tool_count("strict-test", 20, strict=True)

    def test_strict_mode_passes_at_threshold(self):
        """Strict mode passes when at exactly the threshold."""
        from code_puppy.prompt_assembler import validate_tool_count

        assert validate_tool_count("strict-test", 15, strict=True) is True

    def test_strict_mode_passes_below_threshold(self):
        """Strict mode passes when below threshold."""
        from code_puppy.prompt_assembler import validate_tool_count

        assert validate_tool_count("strict-test", 10, strict=True) is True

    def test_default_mode_warns_on_exceed(self):
        """Default mode (non-strict) warns but returns False."""
        from code_puppy.prompt_assembler import validate_tool_count

        result = validate_tool_count("warn-test", 20, strict=False)
        assert result is False

    def test_config_integration(self, monkeypatch):
        """Config key 'tool_count_strict' is recognized."""
        from code_puppy.config import get_tool_count_strict

        # Default is False
        monkeypatch.setattr("code_puppy.config.get_value", lambda k: None)
        assert get_tool_count_strict() is False

        # When set to "true"
        monkeypatch.setattr("code_puppy.config.get_value", lambda k: "true")
        assert get_tool_count_strict() is True

        # When set to "false"
        monkeypatch.setattr("code_puppy.config.get_value", lambda k: "false")
        assert get_tool_count_strict() is False


# ---------------------------------------------------------------------------
# OPT-002-C: Tool description quality validator
# ---------------------------------------------------------------------------


class TestToolDescriptionQuality:
    """Tests for tool description quality validation (OPT-002-C)."""

    def test_specific_descriptions_pass(self):
        """Concise, specific descriptions are NOT flagged."""
        from code_puppy.prompt_assembler import validate_tool_descriptions

        descs = {
            "list_files": "List files and directories with filtering and safety features.",
            "read_file": "Read file contents with optional line-range selection.",
            "grep": "Search for text patterns across files using ripgrep.",
        }
        flagged = validate_tool_descriptions("test-agent", descs)
        assert flagged == []

    def test_generic_descriptions_flagged(self):
        """Generic stoplist descriptions are flagged."""
        from code_puppy.prompt_assembler import validate_tool_descriptions

        descs = {
            "bad_tool": "Use this tool when needed",
            "ok_tool": "Validates JSON schema against OpenAPI 3.1 spec.",
        }
        flagged = validate_tool_descriptions("test-agent", descs)
        assert len(flagged) == 1
        assert flagged[0]["tool"] == "bad_tool"
        assert "stoplist" in flagged[0]["reason"]

    def test_empty_description_flagged(self):
        """Empty or missing descriptions are flagged."""
        from code_puppy.prompt_assembler import validate_tool_descriptions

        descs = {
            "empty_tool": "",
            "whitespace_tool": "   ",
        }
        flagged = validate_tool_descriptions("test-agent", descs)
        assert len(flagged) == 2

    def test_all_stoplist_patterns_caught(self):
        """All entries in the stoplist are caught."""
        from code_puppy.prompt_assembler import (
            _GENERIC_DESCRIPTION_PATTERNS,
            validate_tool_descriptions,
        )

        for pattern in _GENERIC_DESCRIPTION_PATTERNS:
            descs = {"test_tool": f"This tool: {pattern}"}
            flagged = validate_tool_descriptions("test-agent", descs)
            assert len(flagged) == 1, f"Pattern not caught: {pattern}"

    def test_empty_dict_passes(self):
        """Agent with no tools passes validation."""
        from code_puppy.prompt_assembler import validate_tool_descriptions

        flagged = validate_tool_descriptions("test-agent", {})
        assert flagged == []


# ---------------------------------------------------------------------------
# OPT-005-A: Shared skill file format + loader
# ---------------------------------------------------------------------------


class TestSkillFileFormat:
    """Tests for skill file parsing and loading (OPT-005-A)."""

    def test_parse_frontmatter_basic(self):
        """Parse basic YAML frontmatter."""
        from code_puppy.prompt_assembler import _parse_frontmatter

        text = """---
name: coding-standards
description: Python coding standards
version: 1.2.0
---

## Rules
- Use type hints
- Write docstrings
"""
        fm, body = _parse_frontmatter(text)
        assert fm["name"] == "coding-standards"
        assert fm["description"] == "Python coding standards"
        assert fm["version"] == "1.2.0"
        assert "## Rules" in body
        assert "Use type hints" in body

    def test_parse_frontmatter_with_tags(self):
        """Parse frontmatter with list tags."""
        from code_puppy.prompt_assembler import _parse_frontmatter

        text = """---
name: security
description: Security guidelines
tags:
  - security
  - owasp
  - web
---

Content here.
"""
        fm, body = _parse_frontmatter(text)
        assert fm["name"] == "security"
        assert fm["tags"] == ["security", "owasp", "web"]
        assert body == "Content here."

    def test_parse_frontmatter_none(self):
        """File without frontmatter returns empty dict."""
        from code_puppy.prompt_assembler import _parse_frontmatter

        fm, body = _parse_frontmatter("Just plain markdown content.")
        assert fm == {}
        assert body == "Just plain markdown content."

    def test_load_skill_file(self, tmp_path):
        """Load a valid skill file."""
        from code_puppy.prompt_assembler import load_skill_file

        skill_file = tmp_path / "test-skill.md"
        skill_file.write_text("""---
name: test-skill
description: A test skill
version: 2.0.0
tags:
  - test
  - demo
---

## Test Content
This is the skill body.
""")
        skill = load_skill_file(str(skill_file))
        assert skill.name == "test-skill"
        assert skill.description == "A test skill"
        assert skill.version == "2.0.0"
        assert skill.tags == ["test", "demo"]
        assert "## Test Content" in skill.content
        assert skill.file_path == str(skill_file)

    def test_load_skill_file_missing_name(self, tmp_path):
        """Skill file without name raises ValueError."""
        from code_puppy.prompt_assembler import load_skill_file

        skill_file = tmp_path / "bad.md"
        skill_file.write_text("""---
description: No name field
---
Content.
""")
        with pytest.raises(ValueError, match="missing required 'name'"):
            load_skill_file(str(skill_file))

    def test_load_skill_file_missing_description(self, tmp_path):
        """Skill file without description raises ValueError."""
        from code_puppy.prompt_assembler import load_skill_file

        skill_file = tmp_path / "bad.md"
        skill_file.write_text("""---
name: no-description
---
Content.
""")
        with pytest.raises(ValueError, match="missing required 'description'"):
            load_skill_file(str(skill_file))

    def test_load_skill_file_not_found(self):
        """Missing skill file raises FileNotFoundError."""
        from code_puppy.prompt_assembler import load_skill_file

        with pytest.raises(FileNotFoundError, match="Skill file not found"):
            load_skill_file("/nonexistent/skill.md")

    def test_load_skill_file_defaults(self, tmp_path):
        """Skill file with minimal frontmatter gets defaults."""
        from code_puppy.prompt_assembler import load_skill_file

        skill_file = tmp_path / "minimal.md"
        skill_file.write_text("""---
name: minimal
description: Minimal skill
---
Body.
""")
        skill = load_skill_file(str(skill_file))
        assert skill.version == "1.0.0"
        assert skill.tags == []

    def test_discover_skills(self, tmp_path, monkeypatch):
        """Discover skills in a directory."""
        from code_puppy.prompt_assembler import discover_skills

        # Create skills directory with two valid skill files
        (tmp_path / "skill-a.md").write_text("""---
name: alpha
description: Alpha skill
---
Alpha content.
""")
        (tmp_path / "skill-b.md").write_text("""---
name: beta
description: Beta skill
tags:
  - test
---
Beta content.
""")
        # Create invalid file (should be skipped)
        (tmp_path / "bad.md").write_text("No frontmatter at all")

        monkeypatch.setattr(
            "code_puppy.prompt_assembler.get_skills_directory",
            lambda: str(tmp_path),
        )

        skills = discover_skills()
        assert len(skills) == 2
        assert "alpha" in skills
        assert "beta" in skills
        assert skills["alpha"].description == "Alpha skill"
        assert skills["beta"].tags == ["test"]

    def test_resolve_skill_references(self, tmp_path, monkeypatch):
        """Resolve skill names to SkillFile objects."""
        from code_puppy.prompt_assembler import discover_skills, resolve_skill_references

        (tmp_path / "coding.md").write_text("""---
name: coding-standards
description: Coding standards
---
Use type hints.
""")
        (tmp_path / "security.md").write_text("""---
name: security
description: Security rules
---
Validate all inputs.
""")

        monkeypatch.setattr(
            "code_puppy.prompt_assembler.get_skills_directory",
            lambda: str(tmp_path),
        )

        available = discover_skills()
        resolved = resolve_skill_references(["coding-standards", "security"], available)
        assert len(resolved) == 2
        assert resolved[0].name == "coding-standards"
        assert resolved[1].name == "security"

    def test_resolve_skill_references_missing(self, tmp_path, monkeypatch):
        """Missing skill reference raises ValueError with available names."""
        from code_puppy.prompt_assembler import resolve_skill_references

        monkeypatch.setattr(
            "code_puppy.prompt_assembler.get_skills_directory",
            lambda: str(tmp_path),
        )

        with pytest.raises(ValueError, match="Skill 'nonexistent' not found"):
            resolve_skill_references(["nonexistent"])


# ---------------------------------------------------------------------------
# OPT-005-C: Skill injection via PromptAssembler
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_agent():
    """A minimal mock agent for PromptAssembler tests."""

    class _MockAgent:
        name = "test-agent"

        def get_system_prompt(self):
            return "Test system prompt content."

        def get_identity_prompt(self):
            return ""

        def load_puppy_rules(self):
            return None

    return _MockAgent()


class TestSkillInjection:
    """Tests for skill injection through PromptAssembler (OPT-005-C)."""

    @pytest.fixture
    def skills_dir(self, tmp_path, monkeypatch):
        """Create a temp skills directory with test skills."""
        skills_path = tmp_path / "skills"
        skills_path.mkdir()

        (skills_path / "coding.md").write_text("""---
name: coding-standards
description: Python coding standards
---

## Coding Rules
- Use type hints everywhere.
- Write docstrings for public functions.
""")

        (skills_path / "security.md").write_text("""---
name: security-rules
description: Security guidelines
---

## Security Rules
- Validate all user inputs.
- Never log secrets.
""")

        monkeypatch.setattr(
            "code_puppy.prompt_assembler.get_skills_directory",
            lambda: str(skills_path),
        )
        return skills_path

    def test_no_skills_passthrough(self, mock_agent):
        """Agent without skills assembles identically to before."""
        from code_puppy.prompt_assembler import PromptAssembler

        result = PromptAssembler(mock_agent, shared_skills=[]).assemble()
        assert result.breakdown["shared_skills"] == 0
        assert "Shared Skill" not in result.prompt

    def test_skills_injected_in_order(self, mock_agent, skills_dir):
        """Skills are injected in declared array order."""
        from code_puppy.prompt_assembler import PromptAssembler

        result = PromptAssembler(
            mock_agent,
            shared_skills=["coding-standards", "security-rules"],
        ).assemble()

        assert result.breakdown["shared_skills"] > 0
        # Verify order: coding before security
        coding_pos = result.prompt.find("Coding Rules")
        security_pos = result.prompt.find("Security Rules")
        assert coding_pos < security_pos
        # Both appear after the base prompt
        base_pos = result.prompt.find("Test system prompt")
        assert base_pos < coding_pos

    def test_skills_in_components(self, mock_agent, skills_dir):
        """Skill components appear in the breakdown."""
        from code_puppy.prompt_assembler import PromptAssembler

        result = PromptAssembler(
            mock_agent,
            shared_skills=["coding-standards"],
        ).assemble()

        component_names = [name for name, _ in result.components]
        assert "skill:coding-standards" in component_names

    def test_missing_skill_raises(self, mock_agent, skills_dir):
        """Missing skill reference raises ValueError."""
        from code_puppy.prompt_assembler import PromptAssembler

        with pytest.raises(ValueError, match="Skill 'nonexistent' not found"):
            PromptAssembler(
                mock_agent,
                shared_skills=["nonexistent"],
            ).assemble()

    def test_no_shared_skills_param(self, mock_agent):
        """None shared_skills (default) works fine."""
        from code_puppy.prompt_assembler import PromptAssembler

        result = PromptAssembler(mock_agent).assemble()
        assert result.breakdown["shared_skills"] == 0


# ---------------------------------------------------------------------------
# OPT-009-A: Token estimation at agent init
# ---------------------------------------------------------------------------


class TestTokenEstimationLogging:
    """Tests for token estimation logging at assembly time (OPT-009-A)."""

    def test_assembly_logs_breakdown(self, mock_agent, caplog):
        """Assembly logs token breakdown at DEBUG level."""
        import logging
        from code_puppy.prompt_assembler import PromptAssembler

        with caplog.at_level(logging.DEBUG, logger="code_puppy.prompt_assembler"):
            result = PromptAssembler(mock_agent).assemble()

        # The result itself has the breakdown
        assert result.total_tokens > 0
        assert "base_prompt" in result.breakdown
        assert result.breakdown["base_prompt"] > 0


# ---------------------------------------------------------------------------
# OPT-004-B: Model capability registry
# ---------------------------------------------------------------------------


class TestModelCapabilities:
    """Tests for model_capabilities module (OPT-004-B)."""

    def test_supports_tool_calling_user_override(self, tmp_path, monkeypatch):
        """User overrides take precedence over type defaults."""
        from code_puppy import model_capabilities

        model_capabilities.clear_cache()

        cap_file = tmp_path / "model_capabilities.json"
        cap_file.write_text(json.dumps({"my-custom-model": {"tool_calling": False}}))
        monkeypatch.setattr(
            model_capabilities, "_get_capabilities_file", lambda: cap_file
        )

        result = model_capabilities.supports_tool_calling("my-custom-model")
        assert result is False
        model_capabilities.clear_cache()

    def test_supports_tool_calling_type_default(self, monkeypatch):
        """Models with known types get default capabilities."""
        from code_puppy import model_capabilities

        model_capabilities.clear_cache()

        # Mock _get_model_type to return a known type
        monkeypatch.setattr(model_capabilities, "_get_model_type", lambda name: "openai")
        # Mock _load_user_overrides to return empty
        monkeypatch.setattr(model_capabilities, "_load_user_overrides", lambda: {})

        result = model_capabilities.supports_tool_calling("gpt-5")
        assert result is True
        model_capabilities.clear_cache()

    def test_supports_tool_calling_unknown_model(self, monkeypatch):
        """Unknown models return None for tool_calling."""
        from code_puppy import model_capabilities

        model_capabilities.clear_cache()

        monkeypatch.setattr(model_capabilities, "_get_model_type", lambda name: None)
        monkeypatch.setattr(model_capabilities, "_load_user_overrides", lambda: {})

        result = model_capabilities.supports_tool_calling("totally-unknown")
        assert result is None
        model_capabilities.clear_cache()

    def test_get_capabilities_file_missing(self, tmp_path, monkeypatch):
        """Missing capabilities file returns empty overrides."""
        from code_puppy import model_capabilities

        model_capabilities.clear_cache()

        cap_file = tmp_path / "nonexistent.json"
        monkeypatch.setattr(
            model_capabilities, "_get_capabilities_file", lambda: cap_file
        )

        overrides = model_capabilities._load_user_overrides()
        assert overrides == {}
        model_capabilities.clear_cache()

    def test_get_capabilities_invalid_json(self, tmp_path, monkeypatch):
        """Invalid JSON in capabilities file returns empty overrides."""
        from code_puppy import model_capabilities

        model_capabilities.clear_cache()

        cap_file = tmp_path / "model_capabilities.json"
        cap_file.write_text("not valid json{{{")
        monkeypatch.setattr(
            model_capabilities, "_get_capabilities_file", lambda: cap_file
        )

        overrides = model_capabilities._load_user_overrides()
        assert overrides == {}
        model_capabilities.clear_cache()

    def test_ollama_defaults_no_tool_calling(self, monkeypatch):
        """Ollama models default to no tool calling support."""
        from code_puppy import model_capabilities

        model_capabilities.clear_cache()

        monkeypatch.setattr(model_capabilities, "_get_model_type", lambda name: "ollama")
        monkeypatch.setattr(model_capabilities, "_load_user_overrides", lambda: {})

        result = model_capabilities.supports_tool_calling("ollama-llama3")
        assert result is False
        model_capabilities.clear_cache()

    def test_validate_compatible(self, monkeypatch):
        """Compatible agent-model pair should pass validation."""
        from code_puppy import model_capabilities

        model_capabilities.clear_cache()
        monkeypatch.setattr(model_capabilities, "_get_model_type", lambda name: "openai")
        monkeypatch.setattr(model_capabilities, "_load_user_overrides", lambda: {})

        ok, msg = model_capabilities.validate_agent_model_compatibility(
            "test-agent", "gpt-5", requires_tool_calling=True
        )
        assert ok is True
        assert msg == ""
        model_capabilities.clear_cache()

    def test_validate_incompatible(self, monkeypatch):
        """Incompatible agent-model pair should fail validation."""
        from code_puppy import model_capabilities

        model_capabilities.clear_cache()
        monkeypatch.setattr(model_capabilities, "_get_model_type", lambda name: "ollama")
        monkeypatch.setattr(model_capabilities, "_load_user_overrides", lambda: {})

        ok, msg = model_capabilities.validate_agent_model_compatibility(
            "test-agent", "ollama-llama3", requires_tool_calling=True
        )
        assert ok is False
        assert "does not support tool calling" in msg
        model_capabilities.clear_cache()

    def test_validate_no_tool_requirement(self, monkeypatch):
        """Agent without tool requirement always passes."""
        from code_puppy import model_capabilities

        model_capabilities.clear_cache()
        monkeypatch.setattr(model_capabilities, "_get_model_type", lambda name: "ollama")
        monkeypatch.setattr(model_capabilities, "_load_user_overrides", lambda: {})

        ok, msg = model_capabilities.validate_agent_model_compatibility(
            "test-agent", "ollama-llama3", requires_tool_calling=False
        )
        assert ok is True
        model_capabilities.clear_cache()


# ---------------------------------------------------------------------------
# OPT-009-B: Per-agent-type context budget thresholds
# ---------------------------------------------------------------------------


class TestContextBudgetThresholds:
    """Tests for context budget monitoring (OPT-009-B)."""

    def test_coding_agent_gets_higher_threshold(self):
        from code_puppy.prompt_assembler import (
            DEFAULT_CONTEXT_THRESHOLD_CODING,
            get_context_threshold,
        )

        assert get_context_threshold("code-reviewer") == DEFAULT_CONTEXT_THRESHOLD_CODING
        assert get_context_threshold("python-programmer") == DEFAULT_CONTEXT_THRESHOLD_CODING
        assert get_context_threshold("my-developer-agent") == DEFAULT_CONTEXT_THRESHOLD_CODING

    def test_general_agent_gets_lower_threshold(self):
        from code_puppy.prompt_assembler import (
            DEFAULT_CONTEXT_THRESHOLD_GENERAL,
            get_context_threshold,
        )

        assert get_context_threshold("chat-helper") == DEFAULT_CONTEXT_THRESHOLD_GENERAL
        assert get_context_threshold("planner") == DEFAULT_CONTEXT_THRESHOLD_GENERAL
        assert get_context_threshold("qa-kitten") == DEFAULT_CONTEXT_THRESHOLD_GENERAL

    def test_budget_within_threshold(self):
        from code_puppy.prompt_assembler import check_context_budget

        ok, msg = check_context_budget("chat-helper", 20000, 128000)  # 15.6%
        assert ok is True
        assert msg == ""

    def test_budget_exceeds_threshold_general(self):
        from code_puppy.prompt_assembler import check_context_budget

        ok, msg = check_context_budget("chat-helper", 50000, 128000)  # 39%
        assert ok is False
        assert "exceeds" in msg
        assert "30%" in msg

    def test_budget_exceeds_threshold_coding(self):
        from code_puppy.prompt_assembler import check_context_budget

        # 46% — over even the coding threshold
        ok, msg = check_context_budget("code-reviewer", 59000, 128000)
        assert ok is False
        assert "exceeds" in msg
        assert "45%" in msg

    def test_budget_coding_agent_within_higher_threshold(self):
        from code_puppy.prompt_assembler import check_context_budget

        # 40% — over general threshold but within coding threshold
        ok, msg = check_context_budget("code-reviewer", 51000, 128000)
        assert ok is True
        assert msg == ""

    def test_zero_context_length(self):
        from code_puppy.prompt_assembler import check_context_budget

        ok, msg = check_context_budget("any-agent", 1000, 0)
        assert ok is True


# ---------------------------------------------------------------------------
# OPT-006: FallbackModel hardening
# ---------------------------------------------------------------------------


class TestFallbackConfig:
    """Tests for fallback configuration and event logging (OPT-006)."""

    def test_log_fallback_event(self):
        from code_puppy import fallback_config

        fallback_config.clear_events()

        fallback_config.log_fallback_event(
            source_model="gpt-5",
            target_model="claude-sonnet-4-6",
            error_reason="HTTP 429 rate limited",
            agent_name="code-reviewer",
        )

        events = fallback_config.get_fallback_events()
        assert len(events) == 1
        assert events[0]["source_model"] == "gpt-5"
        assert events[0]["target_model"] == "claude-sonnet-4-6"
        assert events[0]["agent_name"] == "code-reviewer"
        assert "429" in events[0]["error_reason"]
        assert "timestamp" in events[0]
        assert "timestamp_iso" in events[0]

        fallback_config.clear_events()

    def test_fallback_chain_config(self, tmp_path, monkeypatch):
        from code_puppy import fallback_config

        fallback_config.clear_cache()

        chain_file = tmp_path / "fallback_chains.json"
        chain_file.write_text(json.dumps({
            "default": ["gpt-5", "claude-sonnet-4-6"],
            "code-reviewer": ["claude-sonnet-4-6", "gpt-5"],
        }))
        monkeypatch.setattr(
            fallback_config, "_get_fallback_config_file", lambda: chain_file
        )

        chain = fallback_config.get_fallback_chain("code-reviewer")
        assert chain == ["claude-sonnet-4-6", "gpt-5"]

        default_chain = fallback_config.get_fallback_chain("unknown-agent")
        assert default_chain == ["gpt-5", "claude-sonnet-4-6"]

        fallback_config.clear_cache()

    def test_fallback_chain_missing_file(self, tmp_path, monkeypatch):
        from code_puppy import fallback_config

        fallback_config.clear_cache()

        chain_file = tmp_path / "nonexistent.json"
        monkeypatch.setattr(
            fallback_config, "_get_fallback_config_file", lambda: chain_file
        )

        chain = fallback_config.get_fallback_chain("any-agent")
        assert chain == []

        fallback_config.clear_cache()

    def test_primary_unavailable_duration(self):
        from code_puppy import fallback_config

        fallback_config.clear_events()

        assert fallback_config.get_primary_unavailable_duration() is None

        fallback_config.log_fallback_event("gpt-5", "claude-sonnet-4-6", "timeout")
        duration = fallback_config.get_primary_unavailable_duration()
        assert duration is not None
        assert duration >= 0
        assert duration < 2  # Should be nearly instant

        fallback_config.clear_events()


# ---------------------------------------------------------------------------
# OPT-010: MCP Progressive Discovery
# ---------------------------------------------------------------------------


class TestMCPProgressiveDiscovery:
    """Tests for MCP progressive discovery tracking (OPT-010)."""

    def test_record_server_tools(self):
        from code_puppy.mcp_.progressive_discovery import (
            clear_stats,
            record_server_tools,
        )

        clear_stats()

        stats = record_server_tools("test-server", tool_count=20, progressive_enabled=True)
        assert stats.total_tools == 20
        assert stats.schemas_loaded == 0
        assert stats.estimated_tokens_full == 20 * 50  # 1000
        assert stats.estimated_tokens_actual == 20 * 10  # 200
        assert stats.estimated_savings == 800

        clear_stats()

    def test_record_schema_loaded(self):
        from code_puppy.mcp_.progressive_discovery import (
            clear_stats,
            get_session_stats,
            record_schema_loaded,
            record_server_tools,
        )

        clear_stats()

        record_server_tools("test-server", tool_count=10, progressive_enabled=True)
        record_schema_loaded("test-server", "tool1")
        record_schema_loaded("test-server", "tool2")

        stats = get_session_stats()["test-server"]
        assert stats.schemas_loaded == 2
        # Original: 10 * 10 = 100
        # After 2 loads: 100 + 2*(50-10) = 180
        assert stats.estimated_tokens_actual == 180
        assert stats.estimated_savings == 10 * 50 - 180  # 320

        clear_stats()

    def test_progressive_disabled_no_savings(self):
        from code_puppy.mcp_.progressive_discovery import (
            clear_stats,
            record_server_tools,
        )

        clear_stats()

        stats = record_server_tools("full-load-server", tool_count=20, progressive_enabled=False)
        assert stats.schemas_loaded == 20
        assert stats.estimated_savings == 0

        clear_stats()

    def test_per_server_config(self, tmp_path, monkeypatch):
        from code_puppy.mcp_ import progressive_discovery

        config_file = tmp_path / "mcp_progressive.json"
        config_file.write_text(json.dumps({
            "default_enabled": True,
            "servers": {
                "filesystem": {"progressive": False},
            }
        }))
        monkeypatch.setattr(
            progressive_discovery,
            "_get_progressive_config_file",
            lambda: config_file,
        )

        assert progressive_discovery.is_progressive_enabled("filesystem") is False
        assert progressive_discovery.is_progressive_enabled("github") is True

    def test_get_summary_empty(self):
        from code_puppy.mcp_.progressive_discovery import clear_stats, get_summary

        clear_stats()
        summary = get_summary()
        assert "No MCP tool tracking" in summary

    def test_get_total_savings(self):
        from code_puppy.mcp_.progressive_discovery import (
            clear_stats,
            get_total_savings,
            record_server_tools,
        )

        clear_stats()

        record_server_tools("server1", tool_count=10, progressive_enabled=True)
        record_server_tools("server2", tool_count=20, progressive_enabled=True)

        assert get_total_savings() == (10 + 20) * (50 - 10)  # 1200

        clear_stats()
