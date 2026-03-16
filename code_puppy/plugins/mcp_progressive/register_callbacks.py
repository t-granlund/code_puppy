"""MCP Progressive Discovery plugin — integrates with /mcp and server lifecycle (OPT-010).

Hooks into server startup to track tool counts and token estimates.
Provides per-server opt-out via config file.
"""

from code_puppy.callbacks import register_callback


def _on_startup():
    """Initialize progressive discovery tracking on app startup."""
    import logging

    logging.getLogger(__name__).debug("MCP progressive discovery tracking initialized")


def _handle_custom_command(command, name):
    """Handle /mcp_stats command for progressive discovery metrics."""
    if name != "mcp_stats":
        return None

    from code_puppy.messaging import emit_info

    try:
        from code_puppy.mcp_.progressive_discovery import get_summary

        summary = get_summary()
        emit_info("🔧 MCP Progressive Discovery")
        emit_info(summary)
    except Exception as e:
        from code_puppy.messaging import emit_warning

        emit_warning(f"Could not load MCP stats: {e}")

    return True


def _custom_help():
    """Register /mcp_stats in help menu."""
    return [
        ("mcp_stats", "Show MCP progressive discovery token savings"),
    ]


register_callback("startup", _on_startup)
register_callback("custom_command", _handle_custom_command)
register_callback("custom_command_help", _custom_help)
