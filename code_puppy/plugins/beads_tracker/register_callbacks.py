"""Callback registration for the Beads Tracker plugin.
"""

import logging
from pathlib import Path

from code_puppy.callbacks import register_callback
from code_puppy.messaging import emit_info, emit_success, emit_error

from .client import BeadsClient, BeadsError

logger = logging.getLogger(__name__)


def _on_startup() -> None:
    """Initialize beads tracker on startup."""
    try:
        # Verify beads is available
        client = BeadsClient()
        logger.debug(f"Beads Tracker plugin initialized. Version check passed.")
    except BeadsError as e:
        logger.warning(f"Beads not available: {e}")


register_callback("startup", _on_startup)


# Custom commands
def _handle_beads_command(command: str, name: str):
    """Handle beads slash commands."""
    if name == "bd":
        emit_info("Beads integration commands: /bd ready | /bd create <title> | /bd show <id>")
        return True
    
    if name == "beads":
        emit_info("Alias for /bd - use /bd <command>")
        return True
    
    return None


def _custom_help():
    """Return beads command help."""
    return [
        ("bd", "Beads issue tracking (ready, create, show)"),
    ]


register_callback("custom_command", _handle_beads_command)
register_callback("custom_command_help", _custom_help)


# Tool registration
def _register_beads_tools(agent) -> None:
    """Register beads tools on an agent."""
    
    @agent.tool_plain
    async def bd_ready(assignee: str = "") -> str:
        """List beads that are ready to work (no blockers).
        
        Shows tasks with all dependencies resolved.
        
        Args:
            assignee: Filter by assignee (empty = all)
        """
        try:
            client = BeadsClient()
            beads = client.ready(assignee=assignee if assignee else None)
            
            if not beads:
                return "🎯 No ready beads found!"
            
            lines = [f"## Ready Beads ({len(beads)})", ""]
            for bead in beads:
                priority_emoji = ["🔴", "🟠", "🟡", "🟢"][min(bead.priority, 3)]
                lines.append(f"{priority_emoji} **{bead.id}**: {bead.title}")
                if bead.assignee:
                    lines.append(f"   Assigned: @{bead.assignee}")
                lines.append("")
            
            return "\n".join(lines)
            
        except BeadsError as e:
            return f"❌ Beads error: {e}"
    
    @agent.tool_plain
    async def bd_create(
        title: str,
        description: str = "",
        priority: int = 2,
        assignee: str = "",
        parent: str = "",
    ) -> str:
        """Create a new bead (issue).
        
        Args:
            title: Bead title
            description: Detailed description
            priority: 0=critical, 1=high, 2=normal, 3=low
            assignee: GitHub username or agent name
            parent: Parent bead ID for hierarchy
        """
        try:
            client = BeadsClient()
            bead = client.create(
                title=title,
                description=description,
                priority=priority,
                assignee=assignee if assignee else None,
                parent=parent if parent else None,
            )
            
            priority_name = ["Critical", "High", "Normal", "Low"][min(priority, 3)]
            return f"✅ Created bead: {bead.id}\n   Title: {bead.title}\n   Priority: {priority_name}"
            
        except BeadsError as e:
            return f"❌ Failed to create bead: {e}"
    
    @agent.tool_plain
    async def bd_show(bead_id: str) -> str:
        """Show details of a bead.
        
        Args:
            bead_id: Bead ID (e.g., 'bd-abc12')
        """
        try:
            client = BeadsClient()
            bead = client.show(bead_id)
            
            priority_name = ["Critical", "High", "Normal", "Low"][min(bead.priority, 3)]
            lines = [
                f"## Bead: {bead.id}",
                f"**{bead.title}**",
                "",
                f"Status: {bead.status}",
                f"Priority: {priority_name}",
            ]
            
            if bead.assignee:
                lines.append(f"Assignee: @{bead.assignee}")
            if bead.parent:
                lines.append(f"Parent: {bead.parent}")
            if bead.description:
                lines.extend(["", "Description:", bead.description])
            
            return "\n".join(lines)
            
        except BeadsError as e:
            return f"❌ Failed to show bead: {e}"
    
    @agent.tool_plain
    async def bd_claim(bead_id: str) -> str:
        """Claim a bead for yourself (atomically).
        
        Args:
            bead_id: Bead ID to claim
        """
        try:
            client = BeadsClient()
            bead = client.update(bead_id, claim=True)
            return f"✅ Claimed bead: {bead.id}\n   Status: {bead.status}"
            
        except BeadsError as e:
            return f"❌ Failed to claim bead: {e}"
    
    @agent.tool_plain
    async def bd_close(bead_id: str, message: str = "") -> str:
        """Close a bead as complete.
        
        Args:
            bead_id: Bead ID to close
            message: Closing message
        """
        try:
            client = BeadsClient()
            bead = client.close(bead_id, message=message)
            return f"✅ Closed bead: {bead.id}\n   Status: {bead.status}"
            
        except BeadsError as e:
            return f"❌ Failed to close bead: {e}"
    
    @agent.tool_plain
    async def bd_dep_add(
        child: str,
        parent: str,
        dep_type: str = "blocks",
    ) -> str:
        """Add a dependency between beads.
        
        Args:
            child: The blocked bead (can't start until parent done)
            parent: The blocking bead (must be done first)
            dep_type: blocks, relates_to, duplicates, supersedes
        """
        try:
            client = BeadsClient()
            client.dep_add(child, parent, dep_type)
            return f"✅ Added dependency: {parent} → {child} ({dep_type})"
            
        except BeadsError as e:
            return f"❌ Failed to add dependency: {e}"
    
    @agent.tool_plain
    async def bd_list(
        status: str = "open",
        assignee: str = "",
        limit: int = 20,
    ) -> str:
        """List beads.
        
        Args:
            status: open, closed, all
            assignee: Filter by assignee
            limit: Maximum to show
        """
        try:
            client = BeadsClient()
            beads = client.list(
                status=status if status != "all" else None,
                assignee=assignee if assignee else None,
                limit=limit,
            )
            
            if not beads:
                return f"No {status} beads found."
            
            lines = [f"## {status.title()} Beads ({len(beads)})", ""]
            for bead in beads:
                priority_emoji = ["🔴", "🟠", "🟡", "🟢"][min(bead.priority, 3)]
                assignee_tag = f" @{bead.assignee}" if bead.assignee else ""
                lines.append(f"{priority_emoji} **{bead.id}**{assignee_tag}: {bead.title}")
            
            return "\n".join(lines)
            
        except BeadsError as e:
            return f"❌ Failed to list beads: {e}"


def _register_tools() -> list[dict]:
    return [
        {
            "name": "bd_ready",
            "register_func": lambda agent: _register_beads_tools(agent),
        },
    ]


register_callback("register_tools", _register_tools)
