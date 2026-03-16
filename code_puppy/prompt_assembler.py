"""Prompt Assembly Pipeline for Code Puppy agents.

This module owns the complete prompt assembly sequence for all agents.
It enforces a consistent assembly order and provides token estimation
with per-component breakdowns.

Assembly order (enforced):
    1. Base agent system_prompt (from JSON or Python agent definition)
    2. Identity prompt (agent ID suffix)
    3. Shared skill prompt fragments (OPT-005, future — placeholder slot)
    4. Plugin prompt injections (on_load_prompt callbacks — currently handled
       inside some agents' get_system_prompt(); will be centralized here)
    5. Puppy rules (AGENTS.md from global config + project directory)

Steps 4-5 of the external pipeline (prepare_prompt_for_model, extended
thinking notes) remain outside PromptAssembler and are applied by callers.

OPT-000 — Prerequisite for OPT-001, OPT-005, OPT-009.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from code_puppy.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------

# Default chars-per-token ratio. Calibrated against tiktoken cl100k_base on
# mixed English/code corpora — intentionally conservative (overestimates).
_CHARS_PER_TOKEN: float = 3.5


def estimate_tokens(text: str) -> int:
    """Estimate token count for a string.

    Uses a character-ratio heuristic (~3.5 chars/token). This is the single
    canonical tokenizer for all prompt budget calculations. OPT-009 MUST
    use this function — do not introduce a second estimator.

    Args:
        text: The string to estimate.

    Returns:
        Estimated token count (always >= 0).
    """
    if not text:
        return 0
    return max(1, int(len(text) / _CHARS_PER_TOKEN))


# ---------------------------------------------------------------------------
# Assembly result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AssemblyResult:
    """Result of prompt assembly with per-component token breakdown.

    Attributes:
        prompt: The fully assembled prompt string.
        total_tokens: Estimated total token count.
        breakdown: Per-component breakdown mapping component name to
            its estimated token count. Keys are stable across versions:
            "base_prompt", "identity", "shared_skills", "plugin_injections",
            "puppy_rules".
        components: Ordered list of (name, content) tuples for each
            non-empty component that was assembled.
    """

    prompt: str
    total_tokens: int
    breakdown: Dict[str, int]
    components: List[tuple] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Assembler
# ---------------------------------------------------------------------------


class PromptAssembler:
    """Assembles system prompts from ordered components.

    This class enforces a single, well-defined assembly order. All prompt
    composition for agents MUST go through this class. Direct string
    concatenation of prompt components elsewhere is an anti-pattern that
    future OPT-003 validation will flag.

    Usage (Phase 1 — thin passthrough, identical to current behavior)::

        assembler = PromptAssembler(agent)
        result = assembler.assemble()
        # result.prompt == agent.get_full_system_prompt() + puppy_rules

    Usage (Phase 2 — with shared skills, OPT-005)::

        assembler = PromptAssembler(agent, shared_skills=["coding-standards"])
        result = assembler.assemble()
    """

    def __init__(
        self,
        agent: "BaseAgent",
        shared_skills: Optional[List[str]] = None,
    ):
        """Initialize the assembler for a specific agent.

        Args:
            agent: The agent whose prompt is being assembled.
            shared_skills: Optional list of shared skill file names to
                inject (OPT-005 — not yet implemented, placeholder).
        """
        self._agent = agent
        self._shared_skills = shared_skills or []

    def assemble(self) -> AssemblyResult:
        """Assemble the complete system prompt.

        Follows the enforced assembly order:
            1. Base system prompt (agent.get_system_prompt())
            2. Identity prompt (agent.get_identity_prompt())
            3. Shared skill fragments (OPT-005, in declared array order)
            4. Plugin injections (currently inside some agents' get_system_prompt,
               will be centralized in future OPT)
            5. Puppy rules (AGENTS.md)

        Returns:
            AssemblyResult with assembled prompt, token estimate, and breakdown.
        """
        breakdown: Dict[str, int] = {}
        components: List[tuple] = []
        parts: List[str] = []

        # --- 1. Base system prompt ---
        base_prompt = self._agent.get_system_prompt()
        base_tokens = estimate_tokens(base_prompt)
        breakdown["base_prompt"] = base_tokens
        components.append(("base_prompt", base_prompt))
        parts.append(base_prompt)

        # --- 2. Identity prompt ---
        identity = self._agent.get_identity_prompt()
        identity_tokens = estimate_tokens(identity)
        breakdown["identity"] = identity_tokens
        components.append(("identity", identity))
        parts.append(identity)

        # --- 3. Shared skill fragments (OPT-005-C) ---
        # Skills are injected in declared array order.
        # Precedence rule: agent's base prompt (step 1) overrides shared
        # skills on conflict — local specialization wins.
        skill_tokens = 0
        if self._shared_skills:
            try:
                resolved = resolve_skill_references(self._shared_skills)
                for skill in resolved:
                    skill_content = f"\n\n<!-- Shared Skill: {skill.name} -->\n{skill.content}"
                    skill_part_tokens = estimate_tokens(skill_content)
                    skill_tokens += skill_part_tokens
                    components.append((f"skill:{skill.name}", skill_content))
                    parts.append(skill_content)
                    logger.debug(
                        "Injected shared skill '%s' (%d tokens) into %s",
                        skill.name,
                        skill_part_tokens,
                        getattr(self._agent, 'name', 'unknown'),
                    )
            except ValueError as e:
                logger.error("Failed to resolve skills for agent: %s", e)
                raise
        breakdown["shared_skills"] = skill_tokens

        # --- 4. Plugin injections ---
        # NOTE: Currently, on_load_prompt() is called inside some agents'
        # get_system_prompt() methods (10 Python agents do this). This means
        # plugin injections are already captured in step 1 for those agents.
        # For consistency, we record 0 here until the centralization refactor.
        breakdown["plugin_injections"] = 0

        # --- 5. Puppy rules (AGENTS.md) ---
        puppy_rules = self._agent.load_puppy_rules()
        if puppy_rules:
            rules_tokens = estimate_tokens(puppy_rules)
            breakdown["puppy_rules"] = rules_tokens
            components.append(("puppy_rules", puppy_rules))
            parts.append(f"\n{puppy_rules}")
        else:
            breakdown["puppy_rules"] = 0

        # --- Assemble final prompt ---
        assembled = "".join(parts)
        total_tokens = sum(breakdown.values())

        return AssemblyResult(
            prompt=assembled,
            total_tokens=total_tokens,
            breakdown=breakdown,
            components=components,
        )

    def assemble_instructions(self) -> AssemblyResult:
        """Convenience method matching the current base_agent pattern.

        This produces the same output as the repeated pattern in base_agent.py:
            instructions = self.get_full_system_prompt()
            puppy_rules = self.load_puppy_rules()
            if puppy_rules:
                instructions += f"\\n{puppy_rules}"

        Returns:
            AssemblyResult equivalent to the above code.
        """
        return self.assemble()


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------


def assemble_prompt(
    agent: "BaseAgent",
    shared_skills: Optional[List[str]] = None,
) -> AssemblyResult:
    """Assemble a system prompt for an agent.

    Convenience function wrapping PromptAssembler. Prefer this for one-shot
    assembly; use the class directly when you need to inspect or customize.

    Args:
        agent: The agent whose prompt is being assembled.
        shared_skills: Optional shared skill file names (OPT-005 placeholder).

    Returns:
        AssemblyResult with assembled prompt, token estimate, and breakdown.
    """
    return PromptAssembler(agent, shared_skills=shared_skills).assemble()


# ---------------------------------------------------------------------------
# Tool count guardrails (OPT-002)
# ---------------------------------------------------------------------------

# Default threshold — configurable via config
DEFAULT_TOOL_COUNT_THRESHOLD = 15

# OPT-009-B: Per-agent-type context budget thresholds (as fraction of context window)
DEFAULT_CONTEXT_THRESHOLD_GENERAL = 0.30  # 30% for chat/general agents
DEFAULT_CONTEXT_THRESHOLD_CODING = 0.45  # 45% for coding agents with large skills

# Heuristic: agent names matching these patterns are "coding" agents
_CODING_AGENT_PATTERNS = frozenset({
    "code", "coder", "coding", "programmer", "developer",
    "reviewer", "refactor", "debug", "devops", "engineer",
})


def get_context_threshold(agent_name: str) -> float:
    """Get the static context budget threshold for an agent (OPT-009-B).

    Coding agents get a higher threshold (45%) because they legitimately
    need more static context for shared skills. General/chat agents get 30%.

    Args:
        agent_name: Name of the agent.

    Returns:
        Threshold as a fraction (0.0–1.0).
    """
    name_lower = agent_name.lower()
    for pattern in _CODING_AGENT_PATTERNS:
        if pattern in name_lower:
            return DEFAULT_CONTEXT_THRESHOLD_CODING
    return DEFAULT_CONTEXT_THRESHOLD_GENERAL


def check_context_budget(
    agent_name: str,
    static_tokens: int,
    context_length: int,
) -> tuple[bool, str]:
    """Check if static context exceeds the per-agent-type threshold (OPT-009-B).

    Args:
        agent_name: Name of the agent.
        static_tokens: Estimated tokens in static context (prompt + skills).
        context_length: Model's advertised context window.

    Returns:
        Tuple of (within_budget, warning_message).
        If within budget, warning_message is empty.
    """
    if context_length <= 0:
        return True, ""

    threshold = get_context_threshold(agent_name)
    usage_pct = static_tokens / context_length

    if usage_pct > threshold:
        pct_str = f"{usage_pct:.0%}"
        thresh_str = f"{threshold:.0%}"
        return False, (
            f"Agent '{agent_name}' static context ({static_tokens} tokens, {pct_str}) "
            f"exceeds {thresh_str} threshold for this agent type. "
            f"Consider splitting skills or reducing system prompt size."
        )

    return True, ""

# Stoplist of generic/low-signal tool descriptions (OPT-002-C placeholder)
_GENERIC_DESCRIPTION_PATTERNS = [
    "use this tool when needed",
    "general purpose tool",
    "does something useful",
    "a helpful tool",
    "tool for doing things",
]


def validate_tool_count(
    agent_name: str,
    tool_count: int,
    tool_names: list | None = None,
    threshold: int | None = None,
    strict: bool = False,
) -> bool:
    """Validate an agent's tool count against the threshold.

    Emits a warning when tool count exceeds the threshold. In strict mode,
    raises ValueError instead.

    Args:
        agent_name: Name of the agent being validated.
        tool_count: Total number of tools (core + MCP + plugin).
        tool_names: Optional list of tool names for the warning message.
        threshold: Tool count threshold. Defaults to DEFAULT_TOOL_COUNT_THRESHOLD.
        strict: If True, raise ValueError instead of warning.

    Returns:
        True if within threshold, False if exceeded (warning emitted).

    Raises:
        ValueError: If strict=True and tool count exceeds threshold.
    """
    if threshold is None:
        threshold = DEFAULT_TOOL_COUNT_THRESHOLD

    if tool_count <= threshold:
        return True

    tool_list_str = ""
    if tool_names:
        tool_list_str = f" Tools: {', '.join(sorted(tool_names))}"

    message = (
        f"Agent '{agent_name}' has {tool_count} tools (threshold: {threshold})."
        f"{tool_list_str} "
        f"Consider consolidating related tools or splitting into sub-agents."
    )

    if strict:
        raise ValueError(message)

    logger.warning(message)
    return False


def validate_tool_descriptions(
    agent_name: str,
    tool_descriptions: Dict[str, str],
) -> List[Dict[str, str]]:
    """Validate tool descriptions for quality signals (OPT-002-C).

    Checks each tool description against a stoplist of generic/low-signal
    patterns. Concise but specific descriptions are NOT flagged — only
    vague, generic ones.

    Args:
        agent_name: Name of the agent being validated.
        tool_descriptions: Dict mapping tool name to its description string.

    Returns:
        List of dicts with "tool" and "reason" keys for each flagged tool.
        Empty list means all descriptions pass quality checks.
    """
    flagged = []

    for tool_name, description in tool_descriptions.items():
        if not description or not description.strip():
            flagged.append({
                "tool": tool_name,
                "reason": "Empty or missing description",
            })
            continue

        desc_lower = description.lower().strip()

        # Check against stoplist patterns
        for pattern in _GENERIC_DESCRIPTION_PATTERNS:
            if pattern in desc_lower:
                flagged.append({
                    "tool": tool_name,
                    "reason": f"Generic description matches stoplist: '{pattern}'",
                })
                break  # One flag per tool is enough

    if flagged:
        tool_names = [f["tool"] for f in flagged]
        logger.warning(
            "Agent '%s' has %d tool(s) with low-quality descriptions: %s",
            agent_name,
            len(flagged),
            ", ".join(tool_names),
        )

    return flagged


# ---------------------------------------------------------------------------
# Shared skill file format + loader (OPT-005)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SkillFile:
    """A parsed shared skill file.

    Attributes:
        name: Skill name from frontmatter.
        description: Skill description from frontmatter.
        version: Skill version (default "1.0.0").
        tags: Optional list of tags for categorization.
        content: The markdown body (everything after frontmatter).
        file_path: Path to the source .md file.
    """

    name: str
    description: str
    version: str
    tags: List[str]
    content: str
    file_path: str


def get_skills_directory() -> str:
    """Get the shared skills directory path.

    Returns ~/.code_puppy/skills/, creating it if it doesn't exist.

    Returns:
        Absolute path to the skills directory.
    """
    from code_puppy.config import SKILLS_DIR

    Path(SKILLS_DIR).mkdir(parents=True, exist_ok=True)
    return SKILLS_DIR


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from a markdown file.

    Expects the file to start with ``---`` and have a closing ``---``.
    Returns (frontmatter_dict, body_content).

    Args:
        text: Full file contents.

    Returns:
        Tuple of (parsed frontmatter dict, remaining body text).
        If no frontmatter found, returns ({}, full text).
    """
    text = text.strip()
    if not text.startswith("---"):
        return {}, text

    # Find closing ---
    end_idx = text.find("---", 3)
    if end_idx == -1:
        return {}, text

    frontmatter_str = text[3:end_idx].strip()
    body = text[end_idx + 3 :].strip()

    # Parse YAML frontmatter (simple key: value parsing, no external deps)
    frontmatter: dict = {}
    current_key: str | None = None
    current_list: list | None = None

    for line in frontmatter_str.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Check for list item
        if stripped.startswith("- ") and current_key is not None:
            if current_list is None:
                current_list = []
                frontmatter[current_key] = current_list
            current_list.append(stripped[2:].strip().strip('"').strip("'"))
            continue

        # Check for key: value
        if ":" in stripped:
            current_list = None
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            current_key = key
            if value:
                frontmatter[key] = value
            # If no value, might be followed by a list

    return frontmatter, body


def load_skill_file(file_path: str) -> SkillFile:
    """Load and parse a single skill file.

    Args:
        file_path: Path to the .md skill file.

    Returns:
        Parsed SkillFile object.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If required frontmatter fields are missing.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Skill file not found: {file_path}")

    text = path.read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(text)

    # Validate required fields
    if "name" not in frontmatter:
        raise ValueError(
            f"Skill file missing required 'name' in frontmatter: {file_path}"
        )
    if "description" not in frontmatter:
        raise ValueError(
            f"Skill file missing required 'description' in frontmatter: {file_path}"
        )

    # Parse tags
    tags_raw = frontmatter.get("tags", [])
    if isinstance(tags_raw, str):
        tags = [t.strip() for t in tags_raw.split(",")]
    elif isinstance(tags_raw, list):
        tags = tags_raw
    else:
        tags = []

    return SkillFile(
        name=frontmatter["name"],
        description=frontmatter["description"],
        version=frontmatter.get("version", "1.0.0"),
        tags=tags,
        content=body,
        file_path=str(path),
    )


def discover_skills() -> Dict[str, SkillFile]:
    """Discover all skill files in the skills directory.

    Scans ~/.code_puppy/skills/ for .md files with valid frontmatter.
    Invalid files are logged and skipped (never crash the app).

    Returns:
        Dict mapping skill name to SkillFile object.
    """
    skills_dir = Path(get_skills_directory())
    skills: Dict[str, SkillFile] = {}

    if not skills_dir.exists():
        return skills

    for md_file in sorted(skills_dir.glob("*.md")):
        try:
            skill = load_skill_file(str(md_file))
            if skill.name in skills:
                logger.warning(
                    "Duplicate skill name '%s' — %s shadows %s",
                    skill.name,
                    md_file,
                    skills[skill.name].file_path,
                )
            skills[skill.name] = skill
        except (ValueError, FileNotFoundError) as exc:
            logger.warning("Skipping invalid skill file %s: %s", md_file, exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Unexpected error loading skill %s: %s", md_file, exc)

    return skills


def resolve_skill_references(
    skill_names: List[str],
    available_skills: Dict[str, SkillFile] | None = None,
) -> List[SkillFile]:
    """Resolve a list of skill names to SkillFile objects.

    Used by PromptAssembler to resolve an agent's ``skills`` array.

    Args:
        skill_names: List of skill names to resolve (in declared order).
        available_skills: Pre-loaded skill map. If None, calls discover_skills().

    Returns:
        Ordered list of resolved SkillFile objects.

    Raises:
        ValueError: If any skill name cannot be resolved.
    """
    if available_skills is None:
        available_skills = discover_skills()

    resolved: List[SkillFile] = []
    for name in skill_names:
        if name not in available_skills:
            raise ValueError(
                f"Skill '{name}' not found. Available skills: "
                f"{', '.join(sorted(available_skills.keys())) or '(none)'}"
            )
        resolved.append(available_skills[name])

    return resolved
