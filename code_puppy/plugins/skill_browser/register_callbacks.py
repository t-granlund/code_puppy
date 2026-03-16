"""Skill Browser plugin — registers /skills slash command.

Provides:
    /skills list  — Show all discovered shared skills
    /skills info <name> — Show detailed skill information

OPT-005-D
"""

import logging

from code_puppy.callbacks import register_callback
from code_puppy.messaging import emit_error, emit_info

logger = logging.getLogger(__name__)


def _custom_help():
    """Register /skills in the help menu."""
    return [
        ("skills", "List and inspect shared skill files"),
    ]


def _handle_skills_command(command: str, name: str):
    """Handle /skills slash command."""
    if name != "skills":
        return None  # Not our command

    parts = command.strip().split(maxsplit=2)
    subcommand = parts[1] if len(parts) > 1 else "list"
    args = parts[2] if len(parts) > 2 else ""

    if subcommand == "list":
        _handle_list()
        return True
    elif subcommand == "info":
        if not args:
            emit_error("Usage: /skills info <skill-name>")
            return True
        _handle_info(args.strip())
        return True
    else:
        emit_error(
            f"Unknown subcommand: '{subcommand}'. Use: list, info"
        )
        return True


def _handle_list():
    """Show all discovered shared skills (OPT-005-D)."""
    try:
        from code_puppy.prompt_assembler import discover_skills, get_skills_directory

        skills_dir = get_skills_directory()
        skills = discover_skills()

        lines = [f"📚 **Shared Skills**\n"]
        lines.append(f"  **Directory:** `{skills_dir}`\n")

        if not skills:
            lines.append("  No skill files found.")
            lines.append(
                "  Create `.md` files with YAML frontmatter in the directory above."
            )
            emit_info("\n".join(lines))
            return

        for skill_name in sorted(skills.keys()):
            skill = skills[skill_name]
            tags_str = (
                f" [{', '.join(skill.tags)}]" if skill.tags else ""
            )
            lines.append(
                f"  **{skill.name}** (v{skill.version}){tags_str}"
            )
            lines.append(f"    {skill.description}")
            lines.append(f"    📁 `{skill.file_path}`")
            lines.append("")

        lines.append(f"**Total: {len(skills)} skill(s)**")

        emit_info("\n".join(lines))

    except Exception as e:
        emit_error(f"Failed to list skills: {e}")
        logger.exception("Skills list failed")


def _handle_info(skill_name: str):
    """Show detailed info for a specific skill (OPT-005-D)."""
    try:
        from code_puppy.prompt_assembler import (
            discover_skills,
            estimate_tokens,
        )

        skills = discover_skills()

        if skill_name not in skills:
            available = ", ".join(sorted(skills.keys())) or "(none)"
            emit_error(
                f"Skill '{skill_name}' not found. "
                f"Available: {available}"
            )
            return

        skill = skills[skill_name]
        content_preview = skill.content[:500]
        if len(skill.content) > 500:
            content_preview += "\n..."

        token_count = estimate_tokens(skill.content)

        lines = [f"📚 **Skill: {skill.name}**\n"]
        lines.append(f"  **Description:** {skill.description}")
        lines.append(f"  **Version:** {skill.version}")
        if skill.tags:
            lines.append(f"  **Tags:** {', '.join(skill.tags)}")
        lines.append(f"  **File:** `{skill.file_path}`")
        lines.append(f"  **Content Size:** ~{token_count} tokens")
        lines.append(f"\n  **Content Preview:**")
        for pline in content_preview.split("\n"):
            lines.append(f"    {pline}")

        emit_info("\n".join(lines))

    except Exception as e:
        emit_error(f"Failed to get skill info: {e}")
        logger.exception("Skill info failed for '%s'", skill_name)


register_callback("custom_command_help", _custom_help)
register_callback("custom_command", _handle_skills_command)
