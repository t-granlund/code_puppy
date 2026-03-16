"""JSON-based agent configuration system."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class JSONAgent(BaseAgent):
    """Agent configured from a JSON file."""

    def __init__(self, json_path: str):
        """Initialize agent from JSON file.

        Args:
            json_path: Path to the JSON configuration file.
        """
        super().__init__()
        self.json_path = json_path
        self._config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise ValueError(
                f"Failed to load JSON agent config from {self.json_path}: {e}"
            ) from e

    def _validate_config(self) -> None:
        """Validate required fields in configuration."""
        required_fields = ["name", "description", "system_prompt", "tools"]
        for field in required_fields:
            if field not in self._config:
                raise ValueError(
                    f"Missing required field '{field}' in JSON agent config: {self.json_path}"
                )

        # Validate tools is a list
        if not isinstance(self._config["tools"], list):
            raise ValueError(
                f"'tools' must be a list in JSON agent config: {self.json_path}"
            )

        # Validate system_prompt is string or list
        system_prompt = self._config["system_prompt"]
        if not isinstance(system_prompt, (str, list)):
            raise ValueError(
                f"'system_prompt' must be a string or list in JSON agent config: {self.json_path}"
            )

        # Validate optional fields if present
        skill_metadata = self._config.get("skill_metadata")
        if skill_metadata is not None and not isinstance(skill_metadata, str):
            raise ValueError(
                f"'skill_metadata' must be a string in JSON agent config: {self.json_path}"
            )

        delegation_mode = self._config.get("delegation_mode")
        if delegation_mode is not None and delegation_mode not in ("subtask", "handoff"):
            raise ValueError(
                f"'delegation_mode' must be 'subtask' or 'handoff' in JSON agent config: "
                f"{self.json_path} (got '{delegation_mode}')"
            )

        # Validate skills array if present (OPT-005-B)
        skills = self._config.get("skills")
        if skills is not None:
            if not isinstance(skills, list):
                raise ValueError(
                    f"'skills' must be a list in JSON agent config: {self.json_path}"
                )
            for i, skill_name in enumerate(skills):
                if not isinstance(skill_name, str):
                    raise ValueError(
                        f"'skills[{i}]' must be a string in JSON agent config: "
                        f"{self.json_path} (got {type(skill_name).__name__})"
                    )

    @property
    def name(self) -> str:
        """Get agent name from JSON config."""
        return self._config["name"]

    @property
    def display_name(self) -> str:
        """Get display name from JSON config, fallback to name with emoji."""
        return self._config.get("display_name", f"{self.name.title()} 🤖")

    @property
    def description(self) -> str:
        """Get description from JSON config."""
        return self._config["description"]

    @property
    def skill_metadata(self) -> str | None:
        """Get skill metadata for progressive loading (OPT-001).

        When present in config, returns the curated metadata string.
        When absent, auto-generates from the first ~75 tokens of system_prompt
        with sentence boundary awareness (OPT-001-B).

        Returns:
            Metadata string (curated or auto-generated), or None only if
            system_prompt is empty.
        """
        explicit = self._config.get("skill_metadata")
        if explicit is not None:
            return explicit

        # Auto-generate from system_prompt (OPT-001-B)
        generated = self._auto_generate_metadata()
        if generated:
            logger.info(
                "skill_metadata auto-generated for agent '%s' — "
                "consider replacing with a curated summary",
                self._config.get("name", "unknown"),
            )
            return generated
        return None

    def _auto_generate_metadata(self) -> str:
        """Auto-generate skill_metadata from system_prompt.

        Extracts the first ~75 tokens (using PromptAssembler's estimator)
        with sentence boundary awareness — never truncates mid-sentence.

        Returns:
            Auto-generated metadata string ending at a sentence boundary.
        """
        from code_puppy.prompt_assembler import estimate_tokens

        prompt = self.get_system_prompt()
        if not prompt:
            return ""

        target_tokens = 75

        # If entire prompt fits, use it all
        if estimate_tokens(prompt) <= target_tokens:
            return prompt.strip()

        # Find last sentence boundary within token budget
        # Approximate character limit from token target
        char_limit = int(target_tokens * 3.5)  # matches _CHARS_PER_TOKEN
        candidate = prompt[:char_limit]

        # Find the last sentence-ending punctuation
        last_boundary = -1
        for i, ch in enumerate(candidate):
            if ch in '.!?' and i > 0:
                # Accept as boundary if followed by space, newline, or end of string
                next_idx = i + 1
                if next_idx >= len(candidate) or candidate[next_idx] in ' \n\r\t':
                    last_boundary = i

        if last_boundary > 0:
            result = prompt[:last_boundary + 1].strip()
        else:
            # No sentence boundary found — take whole candidate and add ellipsis
            # Find last space to avoid mid-word truncation
            last_space = candidate.rfind(' ')
            if last_space > 0:
                result = candidate[:last_space].strip() + "..."
            else:
                result = candidate.strip() + "..."

        return result

    @staticmethod
    def read_metadata(json_path: str) -> dict:
        """Read only metadata fields from a JSON agent file (lightweight).

        This avoids full agent instantiation for discovery/listing operations.
        Only reads: name, display_name, description, skill_metadata, delegation_mode,
        requires_tool_calling, tools (count only), skills.

        Returns:
            Dict with metadata fields. Empty dict on read failure.
        """
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            return {}

        name = config.get("name", "")

        # Build metadata dict with only what's needed for listing/selection
        metadata = {
            "name": name,
            "display_name": config.get("display_name", f"{name.title()} 🤖"),
            "description": config.get("description", ""),
            "delegation_mode": config.get("delegation_mode", "subtask"),
            "tool_count": len(config.get("tools", [])),
            "skills": config.get("skills", []),
        }

        # Prefer explicit skill_metadata; auto-generate only if absent
        explicit_metadata = config.get("skill_metadata")
        if explicit_metadata:
            metadata["skill_metadata"] = explicit_metadata
        else:
            # Auto-generate from system_prompt without full agent init
            system_prompt = config.get("system_prompt", "")
            if isinstance(system_prompt, list):
                system_prompt = "\n".join(system_prompt)
            if system_prompt:
                from code_puppy.prompt_assembler import estimate_tokens

                target_tokens = 75
                if estimate_tokens(system_prompt) <= target_tokens:
                    metadata["skill_metadata"] = system_prompt.strip()
                else:
                    char_limit = int(target_tokens * 3.5)
                    candidate = system_prompt[:char_limit]
                    last_boundary = -1
                    for i, ch in enumerate(candidate):
                        if ch in ".!?" and i > 0:
                            next_idx = i + 1
                            if next_idx >= len(candidate) or candidate[next_idx] in " \n\r\t":
                                last_boundary = i
                    if last_boundary > 0:
                        metadata["skill_metadata"] = system_prompt[:last_boundary + 1].strip()
                    else:
                        last_space = candidate.rfind(" ")
                        if last_space > 0:
                            metadata["skill_metadata"] = candidate[:last_space].strip() + "..."
                        else:
                            metadata["skill_metadata"] = candidate.strip() + "..."

                logger.debug(
                    "Metadata read from file for agent '%s' (lightweight, no full init)",
                    name,
                )
            else:
                metadata["skill_metadata"] = None

        # Infer requires_tool_calling
        explicit_rtc = config.get("requires_tool_calling")
        if explicit_rtc is not None:
            metadata["requires_tool_calling"] = bool(explicit_rtc)
        else:
            metadata["requires_tool_calling"] = len(config.get("tools", [])) > 0

        return metadata

    @property
    def delegation_mode(self) -> str:
        """Get delegation mode for planning-agent orchestration (OPT-007).

        Values:
            "subtask" (default): Agent-as-tool, returns results to parent.
            "handoff": Specialist takes over the user conversation.

        Returns:
            Delegation mode string. Defaults to "subtask".
        """
        return self._config.get("delegation_mode", "subtask")

    @property
    def skills(self) -> list[str]:
        """Get shared skill references for prompt assembly (OPT-005).

        Returns the list of skill file names to be injected into the
        system prompt via PromptAssembler. Order matters — skills are
        injected in declared array order.

        Returns:
            List of skill name strings. Empty list if not specified.
        """
        return self._config.get("skills", [])

    @property
    def requires_tool_calling(self) -> bool:
        """Check if this agent requires tool-calling model support (OPT-004).

        Inference rule: If the agent has tools but doesn't explicitly set
        this field, it's inferred as True. Agents that can degrade gracefully
        without tools should set this to false explicitly.

        Returns:
            Whether this agent requires tool-calling support.
        """
        explicit = self._config.get("requires_tool_calling")
        if explicit is not None:
            return bool(explicit)

        # Infer from tools list: if agent has tools, infer True
        tools = self._config.get("tools", [])
        if tools:
            logger.info(
                "Agent '%s' uses tools but does not explicitly set "
                "requires_tool_calling — inferring true. "
                "Set explicitly to suppress this message.",
                self._config.get("name", "unknown"),
            )
            return True
        return False

    def get_system_prompt(self) -> str:
        """Get system prompt from JSON config."""
        system_prompt = self._config["system_prompt"]

        # If it's a list, join with newlines
        if isinstance(system_prompt, list):
            return "\n".join(system_prompt)

        return system_prompt

    def get_available_tools(self) -> List[str]:
        """Get available tools from JSON config.

        Supports both built-in tools and Universal Constructor (UC) tools.
        UC tools are identified by checking the UC registry.
        """
        from code_puppy.tools import get_available_tool_names

        available_tools = get_available_tool_names()

        # Also get UC tool names
        uc_tool_names = set()
        try:
            from code_puppy.plugins.universal_constructor.registry import get_registry

            registry = get_registry()
            for tool in registry.list_tools():
                if tool.meta.enabled:
                    uc_tool_names.add(tool.full_name)
        except ImportError:
            pass  # UC module not available
        except Exception as e:
            # Log unexpected errors but don't fail
            import logging

            logging.debug(f"UC registry access failed: {e}")

        # Return tools that are either built-in OR UC tools
        requested_tools = []
        for tool in self._config["tools"]:
            if tool in available_tools:
                requested_tools.append(tool)
            elif tool in uc_tool_names:
                # UC tool - mark it specially so base_agent knows to handle it
                requested_tools.append(f"uc:{tool}")

        return requested_tools

    def get_user_prompt(self) -> Optional[str]:
        """Get custom user prompt from JSON config."""
        return self._config.get("user_prompt")

    def get_tools_config(self) -> Optional[Dict]:
        """Get tool configuration from JSON config."""
        return self._config.get("tools_config")

    def refresh_config(self) -> None:
        """Reload the agent configuration from disk.

        This keeps long-lived agent instances in sync after external edits.
        """
        self._config = self._load_config()
        self._validate_config()

    def get_model_name(self) -> Optional[str]:
        """Get pinned model name from JSON config, if specified.

        Returns:
            Model name to use for this agent, or None to use global default.
        """
        result = self._config.get("model")
        if result is None:
            result = super().get_model_name()
        return result


def discover_json_agents() -> Dict[str, str]:
    """Discover JSON agent files in the user's and project's agents directories.

    Searches two locations:
    1. User agents directory (~/.code_puppy/agents/)
    2. Project agents directory (<CWD>/.code_puppy/agents/) - if it exists

    Project agents take priority over user agents when names collide.

    Returns:
        Dict mapping agent names to their JSON file paths.
    """
    from code_puppy.config import (
        get_project_agents_directory,
        get_user_agents_directory,
    )

    agents: Dict[str, str] = {}

    # 1. Discover user-level agents first
    user_agents_dir = Path(get_user_agents_directory())
    if user_agents_dir.exists() and user_agents_dir.is_dir():
        for json_file in user_agents_dir.glob("*.json"):
            try:
                agent = JSONAgent(str(json_file))
                agents[agent.name] = str(json_file)
            except Exception as e:
                logger.debug(
                    "Skipping invalid user agent file: %s (reason: %s: %s)",
                    json_file,
                    type(e).__name__,
                    str(e),
                )
                continue

    # 2. Discover project-level agents (overrides user agents on name collision)
    project_agents_dir_str = get_project_agents_directory()
    if project_agents_dir_str is not None:
        project_agents_dir = Path(project_agents_dir_str)
        for json_file in project_agents_dir.glob("*.json"):
            try:
                agent = JSONAgent(str(json_file))
                agents[agent.name] = str(json_file)
            except Exception as e:
                logger.debug(
                    "Skipping invalid project agent file: %s (reason: %s: %s)",
                    json_file,
                    type(e).__name__,
                    str(e),
                )
                continue

    return agents
