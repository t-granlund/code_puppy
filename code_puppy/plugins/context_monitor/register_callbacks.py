"""Context budget monitor — /context command (OPT-009-C).

Shows the current agent's context utilization breakdown including
system prompt, shared skills, estimated tool schemas, and remaining budget.
"""

from code_puppy.callbacks import register_callback


def _handle_custom_command(command, name):
    """Handle /context command."""
    if name != "context":
        return None

    from code_puppy.messaging import emit_info, emit_warning

    try:
        from code_puppy.agents import get_current_agent
        from code_puppy.config import get_model_context_length
        from code_puppy.prompt_assembler import (
            PromptAssembler,
            check_context_budget,
            estimate_tokens,
            get_context_threshold,
        )

        agent = get_current_agent()
        agent_name = agent.name
        context_length = get_model_context_length()

        # Assemble prompt to get breakdown
        shared_skills = []
        if hasattr(agent, "skills"):
            shared_skills = agent.skills

        result = PromptAssembler(agent, shared_skills=shared_skills).assemble_instructions()

        # Estimate tool schema tokens
        tool_tokens = 0
        try:
            tools = agent.get_available_tools()
            # Rough estimate: ~50 tokens per tool for schema
            tool_tokens = len(tools) * 50
        except Exception:
            pass

        total_static = result.total_tokens + tool_tokens
        threshold = get_context_threshold(agent_name)
        threshold_pct = f"{threshold:.0%}"
        usage_pct = (total_static / context_length * 100) if context_length > 0 else 0
        remaining = context_length - total_static

        # Header
        emit_info(f"📊 Context Budget for '{agent_name}'")
        emit_info(f"{'─' * 50}")

        # Breakdown
        emit_info(f"  System prompt:     ~{result.breakdown.get('base_prompt', 0):>6,} tokens")

        skills_tokens = result.breakdown.get("shared_skills", 0)
        if skills_tokens > 0:
            emit_info(f"  Shared skills:     ~{skills_tokens:>6,} tokens")

        plugin_tokens = result.breakdown.get("plugin_injections", 0)
        if plugin_tokens > 0:
            emit_info(f"  Plugin injections: ~{plugin_tokens:>6,} tokens")

        if tool_tokens > 0:
            emit_info(f"  Tool schemas:      ~{tool_tokens:>6,} tokens (estimated)")

        emit_info(f"{'─' * 50}")
        emit_info(f"  Total static:      ~{total_static:>6,} tokens ({usage_pct:.1f}%)")
        emit_info(f"  Context window:     {context_length:>6,} tokens")
        emit_info(f"  Remaining:         ~{remaining:>6,} tokens")
        emit_info(f"  Threshold:          {threshold_pct} ({('coding' if threshold > 0.35 else 'general')} agent)")

        # Budget check
        within_budget, warning = check_context_budget(
            agent_name, total_static, context_length
        )
        if not within_budget:
            emit_warning(f"⚠️  {warning}")
        else:
            headroom = threshold * context_length - total_static
            emit_info(f"  ✅ Within budget ({headroom:,.0f} tokens of headroom)")

    except Exception as e:
        emit_warning(f"Could not compute context budget: {e}")

    return True


def _custom_help():
    """Register /context in help menu."""
    return [
        ("context", "Show current agent's context utilization breakdown"),
    ]


register_callback("custom_command", _handle_custom_command)
register_callback("custom_command_help", _custom_help)
