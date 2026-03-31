"""Callback registration for the Dashboard plugin.

Provides TUI dashboard for monitoring Orchestra.
"""

import logging

from code_puppy.callbacks import register_callback
from code_puppy.messaging import emit_info

logger = logging.getLogger(__name__)


def _on_startup() -> None:
    """Initialize dashboard on startup."""
    logger.debug("Dashboard plugin initialized")


register_callback("startup", _on_startup)


# Custom commands
def _handle_dashboard_command(command: str, name: str):
    """Handle dashboard slash commands."""
    if name == "dashboard":
        emit_info("Dashboard TUI: /dashboard open | /dashboard --plain")
        return True
    
    if name == "feed":
        emit_info("Event feed: /feed [agents|convoys|events|problems]")
        return True
    
    return None


def _custom_help():
    """Return dashboard command help."""
    return [
        ("dashboard", "Open TUI monitoring dashboard"),
        ("feed", "View real-time event feed"),
    ]


register_callback("custom_command", _handle_dashboard_command)
register_callback("custom_command_help", _custom_help)


# Tool registration (placeholder for TUI tools)
def _register_dashboard_tools(agent) -> None:
    """Register dashboard tools on an agent."""
    
    @agent.tool_plain
    async def dashboard_open(view: str = "agents") -> str:
        """Open the Orchestra dashboard (TUI).
        
        Note: Full TUI requires running in interactive terminal.
        This command provides status overview when TUI can't launch.
        
        Args:
            view: Initial view (agents, convoys, events, problems)
        """
        # Placeholder - full implementation would launch Rich/TC TUI
        return f"📊 Dashboard requested: {view} view\n\n(Note: Full TUI dashboard coming in next iteration)"
    
    @agent.tool_plain
    async def feed_events(limit: int = 50) -> str:
        """Show recent events from the feed.
        
        Args:
            limit: Number of events to show
        """
        # Placeholder - would read from event log
        return f"📰 Last {limit} events:\n\n(Note: Event feed integration coming soon)"


def _register_tools() -> list[dict]:
    return [
        {
            "name": "dashboard_open",
            "register_func": lambda agent: _register_dashboard_tools(agent),
        },
    ]


register_callback("register_tools", _register_tools)
