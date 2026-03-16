"""Agent Registry plugin — registers /agents slash command.

Provides:
    /agents list  — Show all registered agents with metadata
    /agents info <name> — Show detailed agent information
    /agents validate — Run schema and anti-pattern checks

OPT-003-A, OPT-003-B, OPT-003-C, OPT-003-D
"""

import logging

from code_puppy.callbacks import register_callback
from code_puppy.messaging import emit_error, emit_info, emit_warning

logger = logging.getLogger(__name__)


def _custom_help():
    """Register /agents in the help menu."""
    return [
        ("agents", "List, inspect, and validate registered agents"),
    ]


def _handle_agents_command(command: str, name: str):
    """Handle /agents slash command.

    Subcommands:
        /agents list     — Show all registered agents
        /agents info X   — Show details for agent X
        /agents validate — Run validation checks
        /agents          — Alias for /agents list
    """
    if name != "agents":
        return None  # Not our command

    # Parse subcommand
    parts = command.strip().split(maxsplit=2)
    # parts[0] = "/agents", parts[1] = subcommand, parts[2] = args
    subcommand = parts[1] if len(parts) > 1 else "list"
    args = parts[2] if len(parts) > 2 else ""

    if subcommand == "list":
        _handle_list()
        return True
    elif subcommand == "info":
        if not args:
            emit_error("Usage: /agents info <agent-name>")
            return True
        _handle_info(args.strip())
        return True
    elif subcommand == "validate":
        _handle_validate(command)
        return True
    else:
        emit_error(
            f"Unknown subcommand: '{subcommand}'. Use: list, info, validate"
        )
        return True


def _load_agent_entry(agent_name, agent_ref):
    """Load a single agent entry from the registry, returning a metadata dict.

    Returns a dict with keys: name, display, description, tools, type,
    and optionally: path, metadata, delegation.
    Returns None if the agent couldn't be loaded.
    """
    # Lazy imports to avoid circular deps at module scope
    from code_puppy.agents.json_agent import JSONAgent

    try:
        if isinstance(agent_ref, str):
            agent = JSONAgent(agent_ref)
            tool_count = len(agent.get_available_tools())
            return {
                "name": agent_name,
                "display": agent.display_name,
                "description": agent.description[:80],
                "tools": tool_count,
                "type": "JSON",
                "path": agent_ref,
                "metadata": getattr(agent, "skill_metadata", None),
                "delegation": getattr(agent, "delegation_mode", "subtask"),
            }
        else:
            agent = agent_ref()
            tool_count = len(agent.get_available_tools())
            return {
                "name": agent_name,
                "display": agent.display_name,
                "description": agent.description[:80],
                "tools": tool_count,
                "type": "Python",
            }
    except Exception as e:
        logger.debug("Failed to load agent '%s': %s", agent_name, e)
        return {
            "name": agent_name,
            "display": agent_name,
            "description": f"(failed to load: {e})",
            "tools": 0,
            "type": "Unknown",
        }


def _format_agent_list(python_agents, json_agents):
    """Build the formatted output lines for /agents list."""
    lines = ["📋 **Registered Agents**\n"]

    if python_agents:
        lines.append("**Python Agents:**")
        for a in python_agents:
            lines.append(
                f"  {a['display']} (`{a['name']}`) — "
                f"{a['description']} [{a['tools']} tools]"
            )
        lines.append("")

    if json_agents:
        lines.append("**JSON Agents:**")
        for a in json_agents:
            meta_tag = " [metadata: ✓]" if a.get("metadata") else ""
            deleg_tag = " [handoff]" if a.get("delegation") == "handoff" else ""
            lines.append(
                f"  {a['display']} (`{a['name']}`) — "
                f"{a['description']} [{a['tools']} tools]"
                f"{meta_tag}{deleg_tag}"
            )
            lines.append(f"    📁 {a['path']}")
        lines.append("")

    total = len(python_agents) + len(json_agents)
    lines.append(
        f"**Total: {total} agents** "
        f"({len(python_agents)} Python, {len(json_agents)} JSON)"
    )

    return "\n".join(lines)


def _handle_list():
    """Show all registered agents with metadata (OPT-003-A)."""
    try:
        from code_puppy.agents.agent_manager import (
            _AGENT_REGISTRY,
            _discover_agents,
        )

        _discover_agents()

        if not _AGENT_REGISTRY:
            emit_info("No agents registered.")
            return

        python_agents = []
        json_agents = []

        for agent_name, agent_ref in sorted(_AGENT_REGISTRY.items()):
            entry = _load_agent_entry(agent_name, agent_ref)
            if entry is None:
                continue
            if entry["type"] == "JSON":
                json_agents.append(entry)
            else:
                python_agents.append(entry)

        emit_info(_format_agent_list(python_agents, json_agents))

    except Exception as e:
        emit_error(f"Failed to list agents: {e}")
        logger.exception("Agent list failed")


def _handle_info(agent_name: str):
    """Show detailed info for a specific agent (OPT-003-B)."""
    try:
        from code_puppy.agents.agent_manager import (
            _AGENT_REGISTRY,
            _discover_agents,
        )
        from code_puppy.agents.json_agent import JSONAgent

        _discover_agents()

        if agent_name not in _AGENT_REGISTRY:
            emit_error(
                f"Agent '{agent_name}' not found. "
                f"Use /agents list to see available agents."
            )
            return

        agent_ref = _AGENT_REGISTRY[agent_name]

        try:
            if isinstance(agent_ref, str):
                agent = JSONAgent(agent_ref)
                agent_type = "JSON"
                file_path = agent_ref
            else:
                agent = agent_ref()
                agent_type = "Python"
                file_path = None
        except Exception as e:
            emit_error(f"Failed to load agent '{agent_name}': {e}")
            return

        # Gather info
        tools = agent.get_available_tools()
        system_prompt = agent.get_system_prompt()
        prompt_preview = system_prompt[:200]
        if len(system_prompt) > 200:
            prompt_preview += "..."

        # Build output
        lines = [f"📋 **Agent: {agent.display_name}**\n"]
        lines.append(f"  **Name:** `{agent_name}`")
        lines.append(f"  **Type:** {agent_type}")
        lines.append(f"  **Description:** {agent.description}")

        # Delegation mode (JSON agents)
        if hasattr(agent, "delegation_mode"):
            lines.append(f"  **Delegation Mode:** {agent.delegation_mode}")

        # Tool calling requirement (JSON agents)
        if hasattr(agent, "requires_tool_calling"):
            lines.append(
                f"  **Requires Tool Calling:** {agent.requires_tool_calling}"
            )

        # Skill metadata
        if hasattr(agent, "skill_metadata") and agent.skill_metadata:
            lines.append(f"  **Skill Metadata:** {agent.skill_metadata}")

        # Tools
        lines.append(f"\n  **Tools ({len(tools)}):**")
        if tools:
            for tool in sorted(tools):
                lines.append(f"    - `{tool}`")
        else:
            lines.append("    (none)")

        # File path for JSON agents
        if file_path:
            lines.append(f"\n  **File:** `{file_path}`")

        # System prompt preview
        lines.append(f"\n  **System Prompt Preview:**")
        # Indent the preview
        for pline in prompt_preview.split("\n"):
            lines.append(f"    {pline}")

        emit_info("\n".join(lines))

    except Exception as e:
        emit_error(f"Failed to get agent info: {e}")
        logger.exception("Agent info failed for '%s'", agent_name)


def _handle_validate(command=""):
    """Run validation checks on all agents (OPT-003-C)."""
    try:
        from code_puppy.agents.agent_manager import (
            _AGENT_REGISTRY,
            _discover_agents,
        )
        from code_puppy.agents.json_agent import JSONAgent
        from code_puppy.config import get_tool_count_strict
        from code_puppy.prompt_assembler import (
            DEFAULT_TOOL_COUNT_THRESHOLD,
            validate_tool_count,
        )

        _discover_agents()

        if not _AGENT_REGISTRY:
            emit_info("No agents to validate.")
            return

        issues_by_agent: dict = {}  # agent_name -> list of (level, message)
        agents_checked = 0

        for agent_name, agent_ref in sorted(_AGENT_REGISTRY.items()):
            agent_issues: list = []

            try:
                if isinstance(agent_ref, str):
                    agent = JSONAgent(agent_ref)
                    agent_type = "JSON"
                else:
                    agent = agent_ref()
                    agent_type = "Python"
            except Exception as e:
                agent_issues.append(("FAIL", f"Failed to load: {e}"))
                issues_by_agent[agent_name] = agent_issues
                agents_checked += 1
                continue

            agents_checked += 1

            # --- Check 1: Tool count ---
            tools = agent.get_available_tools()
            tool_count = len(tools)
            if tool_count > DEFAULT_TOOL_COUNT_THRESHOLD:
                agent_issues.append((
                    "WARN",
                    f"Tool count ({tool_count}) exceeds threshold "
                    f"({DEFAULT_TOOL_COUNT_THRESHOLD})",
                ))

            # --- Check 2: requires_tool_calling inference (JSON agents) ---
            if agent_type == "JSON" and hasattr(agent, "_config"):
                has_tools = bool(agent._config.get("tools", []))
                explicit_flag = agent._config.get("requires_tool_calling")
                if has_tools and explicit_flag is None:
                    agent_issues.append((
                        "INFO",
                        "Has tools but requires_tool_calling not set "
                        "(inferred true — set explicitly to suppress)",
                    ))

            # --- Check 3: Missing skill_metadata (JSON agents) ---
            if agent_type == "JSON":
                explicit_meta = agent._config.get("skill_metadata")
                if explicit_meta is None:
                    agent_issues.append((
                        "INFO",
                        "No explicit skill_metadata — auto-generated from "
                        "system_prompt (consider adding a curated summary)",
                    ))

            # --- Check 4: Empty system prompt ---
            try:
                prompt = agent.get_system_prompt()
                if not prompt or not prompt.strip():
                    agent_issues.append(("WARN", "System prompt is empty"))
            except Exception as e:
                agent_issues.append(("FAIL", f"Failed to get system prompt: {e}"))

            # --- Check 5: Empty tools list on agent that should have tools ---
            if agent_type == "JSON" and not tools:
                declared_tools = agent._config.get("tools", [])
                if declared_tools:
                    agent_issues.append((
                        "WARN",
                        f"Declares {len(declared_tools)} tool(s) in config but "
                        f"none resolved — check tool names: "
                        f"{', '.join(declared_tools[:5])}",
                    ))

            # --- Check 6: Shared skill content overlap with system prompt ---
            if agent_type == "JSON" and hasattr(agent, "skills") and agent.skills:
                try:
                    from code_puppy.prompt_assembler import discover_skills
                    available_skills = discover_skills()
                    prompt_lower = prompt.lower() if prompt else ""
                    for skill_name in agent.skills:
                        if skill_name in available_skills:
                            skill = available_skills[skill_name]
                            # Check for significant content overlap
                            # Use first 200 chars of skill content as fingerprint
                            fingerprint = skill.content[:200].strip().lower()
                            if fingerprint and len(fingerprint) > 50 and fingerprint in prompt_lower:
                                agent_issues.append((
                                    "WARN",
                                    f"Shared skill '{skill_name}' content appears "
                                    f"duplicated in agent's system prompt — "
                                    f"consider removing the duplicate",
                                ))
                except Exception as e:
                    logger.debug("Skill overlap check failed: %s", e)

            if agent_issues:
                issues_by_agent[agent_name] = agent_issues

        # --- Cross-agent duplicate detection (OPT-003-D) ---
        # Hash system prompt content to detect near-duplicates
        import hashlib
        prompt_hashes: dict = {}  # hash -> list of agent names

        for a_name, a_ref in sorted(_AGENT_REGISTRY.items()):
            try:
                if isinstance(a_ref, str):
                    a = JSONAgent(a_ref)
                else:
                    a = a_ref()
                p = a.get_system_prompt()
                if p and len(p) > 100:
                    # Hash first 500 chars as fingerprint
                    h = hashlib.md5(p[:500].lower().encode()).hexdigest()[:12]
                    if h not in prompt_hashes:
                        prompt_hashes[h] = []
                    prompt_hashes[h].append(a_name)
            except Exception:
                continue

        for h, names in prompt_hashes.items():
            if len(names) > 1:
                dup_msg = (
                    f"Near-duplicate system prompts detected: "
                    f"{', '.join(names)} — consider extracting to a shared skill"
                )
                # Add to first agent's issues
                first_name = names[0]
                if first_name not in issues_by_agent:
                    issues_by_agent[first_name] = []
                issues_by_agent[first_name].append(("WARN", dup_msg))

        # --- Format output ---
        lines = ["🔍 **Agent Validation Results**\n"]

        total_fail = 0
        total_warn = 0
        total_info = 0

        if issues_by_agent:
            for name, issues in sorted(issues_by_agent.items()):
                lines.append(f"  **`{name}`:**")
                for level, msg in issues:
                    if level == "FAIL":
                        icon = "❌"
                        total_fail += 1
                    elif level == "WARN":
                        icon = "⚠️"
                        total_warn += 1
                    else:
                        icon = "ℹ️"
                        total_info += 1
                    lines.append(f"    {icon} [{level}] {msg}")
                lines.append("")
        else:
            lines.append("  ✅ All agents passed validation!\n")

        clean_count = agents_checked - len(issues_by_agent)
        lines.append(
            f"**Summary:** {agents_checked} agents checked — "
            f"{clean_count} clean, "
            f"{total_fail} errors, {total_warn} warnings, {total_info} info"
        )

        if total_fail > 0:
            emit_warning("\n".join(lines))
        else:
            emit_info("\n".join(lines))

        # OPT-008-C: Mention behavioral tests if available
        try:
            parts = command.split()
            has_behavioral_flag = "--behavioral" in parts

            if has_behavioral_flag:
                from code_puppy.plugins.behavioral_tests.test_cases import (
                    get_default_test_suite,
                )

                suite = get_default_test_suite()
                tests_by_cat = suite.get_tests_by_category()

                emit_info("")
                emit_info("🧪 Behavioral Tests (Phase 1: Descriptive Metrics)")
                emit_info(f"{'─' * 45}")
                emit_info(
                    f"  {len(suite.tests)} test cases available across "
                    f"{len(tests_by_cat)} categories"
                )
                for category, tests in sorted(tests_by_cat.items()):
                    emit_info(f"    {category}: {len(tests)} tests")
                emit_info("")
                emit_info(
                    "  Note: Phase 1 collects metrics only — no pass/fail thresholds.\n"
                    "  Run /behavioral for details or use the API:\n"
                    "    from code_puppy.plugins.behavioral_tests.test_cases import get_default_test_suite"
                )
            else:
                emit_info("")
                emit_info(
                    "  💡 Tip: Run `/agents validate --behavioral` to include "
                    "behavioral test suite info"
                )
        except ImportError:
            pass  # behavioral_tests plugin not available
        except Exception:
            pass  # Don't block validation output

    except Exception as e:
        emit_error(f"Validation failed: {e}")
        logger.exception("Agent validation failed")


register_callback("custom_command_help", _custom_help)
register_callback("custom_command", _handle_agents_command)
