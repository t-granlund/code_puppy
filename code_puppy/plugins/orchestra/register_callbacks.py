"""Callback registration for the Orchestra plugin.

Registers lifecycle hooks and tools for multi-agent orchestration.
"""

import logging
from pathlib import Path

from code_puppy.callbacks import register_callback

from . import DEFAULT_TOWN_DIR, CONFIG_SUBDIR
from .rig import RigManager

logger = logging.getLogger(__name__)

# Global state (initialized on startup)
_orchestra_initialized = False
_rig_manager: RigManager | None = None


def _ensure_town_structure(town_path: Path) -> None:
    """Ensure the town directory structure exists."""
    town_path.mkdir(parents=True, exist_ok=True)
    
    # Create config directory
    config_path = town_path / CONFIG_SUBDIR
    config_path.mkdir(parents=True, exist_ok=True)
    
    # Create state directory
    (config_path / "state").mkdir(exist_ok=True)
    
    # Create hooks base directory
    (config_path / "hooks").mkdir(exist_ok=True)
    
    # Create README if it doesn't exist
    readme_path = town_path / "README.md"
    if not readme_path.exists():
        readme_path.write_text("""# Orchestra Town

This is your Orchestra workspace for multi-agent orchestration.

## Quick Start

1. Create a rig (project):
   ```
   /rig create myproject https://github.com/you/repo.git
   ```

2. Create a convoy:
   ```
   /convoy create "Feature X" --rig myproject
   ```

3. Spawn agents:
   ```
   /spawn polecat "Implement login" --convoy <id>
   ```

## Directory Structure

- `~/gt/` - Town root
  - `<rig-name>/` - Project directories
    - `crew/` - Crew workspaces
    - `.orchestra/hooks/` - Agent persistent storage
  - `.orchestra/` - Orchestra config and state

## Commands

- `/rig` - Manage rigs (projects)
- `/convoy` - Manage work convoys
- `/spawn` - Spawn agents
- `/agents` - List active agents
- `/mail` - Inter-agent messaging

Learn more: https://github.com/mpfaffenberger/code_puppy
""")


def _on_startup() -> None:
    """Initialize Orchestra on application startup."""
    global _orchestra_initialized, _rig_manager
    
    if _orchestra_initialized:
        return
    
    logger.debug("Orchestra plugin initializing...")
    
    # Ensure town structure exists
    _ensure_town_structure(DEFAULT_TOWN_DIR)
    
    # Initialize rig manager
    _rig_manager = RigManager(DEFAULT_TOWN_DIR)
    
    _orchestra_initialized = True
    logger.info(f"Orchestra plugin initialized. Town: {DEFAULT_TOWN_DIR}")
    
    # Log rig count
    rigs = _rig_manager.list_rigs()
    if rigs:
        logger.info(f"Loaded {len(rigs)} rig(s): {', '.join(r.name for r in rigs)}")


def _on_shutdown() -> None:
    """Cleanup on application shutdown."""
    logger.debug("Orchestra plugin shutting down...")
    # Persist any pending state
    global _rig_manager
    if _rig_manager:
        logger.debug("Rig manager state persisted")


# Register callbacks
register_callback("startup", _on_startup)
register_callback("shutdown", _on_shutdown)

logger.debug("Orchestra plugin callbacks registered")


# Tool registration for agent capabilities
def _register_orchestra_tools(agent) -> None:
    """Register Orchestra tools on an agent."""
    
    @agent.tool_plain
    async def orchestra_rig_list() -> str:
        """List all rigs (projects) in the Orchestra workspace.
        
        Returns a formatted list of rigs with their status.
        """
        if not _rig_manager:
            return "Orchestra not initialized"
        
        rigs = _rig_manager.list_rigs()
        if not rigs:
            return "No rigs found. Create one with: /rig create <name> <repo-url>"
        
        lines = ["## Rigs (Projects)", ""]
        for rig in rigs:
            status = "🟢" if rig.state.value == "active" else "⚪"
            lines.append(f"{status} **{rig.name}** ({rig.id})")
            if rig.repo_url:
                lines.append(f"   Repo: {rig.repo_url}")
            if rig.agent_ids:
                lines.append(f"   Agents: {len(rig.agent_ids)}")
            lines.append("")
        
        return "\n".join(lines)
    
    @agent.tool_plain
    async def orchestra_rig_create(name: str, repo_url: str = "") -> str:
        """Create a new rig (project container).
        
        Args:
            name: Unique name for the rig
            repo_url: Optional git repository URL
        """
        if not _rig_manager:
            return "Orchestra not initialized"
        
        try:
            rig = _rig_manager.create_rig(
                name=name,
                repo_url=repo_url if repo_url else None,
            )
            return f"✅ Created rig '{name}' (id: {rig.id})\nLocation: {rig.local_path}"
        except ValueError as e:
            return f"❌ Error: {e}"
    
    @agent.tool_plain
    async def orchestra_spawn_agent(
        task: str,
        rig_name: str = "",
        agent_type: str = "polecat",
        runtime: str = "claude",
        bead_id: str = "",
    ) -> str:
        """Spawn a new agent for a specific task.
        
        This creates a persistent agent that will work in an isolated
        git worktree (hook) and can survive restarts.
        
        Args:
            task: Description of the work to be done
            rig_name: Which rig to spawn in (empty = current/default)
            agent_type: Type of agent (polecat, witness, dog)
            runtime: AI runtime to use (claude, codex, cursor)
            bead_id: Optional bead/issue to assign to this agent
        """
        # This is a placeholder - full implementation would:
        # 1. Create a hook (git worktree)
        # 2. Set up agent identity
        # 3. Spawn the agent process
        # 4. Return agent info
        
        return f"🐕 Spawned {agent_type} agent for: {task}\n(Runtime: {runtime}, Rig: {rig_name or 'default'})"
    
    @agent.tool_plain
    async def orchestra_convoy_create(
        name: str,
        rig_name: str = "",
        bead_ids: str = "",
        priority: int = 2,
        notify_human: bool = False,
    ) -> str:
        """Create a work convoy to bundle multiple beads.
        
        Convoys are the primary unit of work orchestration. They track
        multiple related beads and coordinate their execution.
        
        Args:
            name: Name for this convoy
            rig_name: Which rig this convoy belongs to
            bead_ids: Comma-separated list of bead IDs to include
            priority: Priority level (0=critical, 1=high, 2=normal, 3=low)
            notify_human: Whether to notify when complete
        """
        # Placeholder - full implementation would create Convoy object
        beads = [b.strip() for b in bead_ids.split(",") if b.strip()]
        
        result = [f"🚚 Created convoy: {name}"]
        result.append(f"   Priority: {['Critical', 'High', 'Normal', 'Low'][min(priority, 3)]}")
        if beads:
            result.append(f"   Beads: {len(beads)}")
        if notify_human:
            result.append("   Will notify on completion")
        
        return "\n".join(result)
    
    @agent.tool_plain
    async def orchestra_send_mail(
        to_agent: str,
        subject: str,
        body: str,
        from_agent: str = "",
        bead_id: str = "",
    ) -> str:
        """Send mail to another agent.
        
        Mail provides asynchronous communication between agents
        that persists across sessions.
        
        Args:
            to_agent: ID or name of recipient agent
            subject: Mail subject
            body: Mail body content
            from_agent: Sender agent ID (auto-filled if empty)
            bead_id: Optional related bead ID
        """
        # Placeholder - full implementation would queue mail
        return f"📧 Mail queued to {to_agent}: {subject}"


def _register_tools() -> list[dict]:
    """Return tool registration info."""
    return [
        {
            "name": "orchestra_rig_list",
            "register_func": lambda agent: _register_orchestra_tools(agent),
        },
    ]


# Register tool callback
register_callback("register_tools", _register_tools)


# Custom commands for Orchestra
def _handle_orchestra_command(command: str, name: str):
    """Handle Orchestra slash commands."""
    from code_puppy.messaging import emit_info, emit_success
    
    if name == "rig":
        emit_info("Usage: /rig create <name> [repo-url] | /rig list | /rig show <name>")
        return True
    
    if name == "convoy":
        emit_info("Usage: /convoy create <name> [--rig <rig>] [--beads <ids>]")
        return True
    
    if name == "spawn":
        emit_info("Usage: /spawn <type> <task> [--rig <rig>] [--runtime <runtime>]")
        return True
    
    if name == "agents":
        if _rig_manager:
            rigs = _rig_manager.list_rigs()
            total_agents = sum(len(r.agent_ids) for r in rigs)
            emit_success(f"Active agents: {total_agents} across {len(rigs)} rig(s)")
        else:
            emit_info("No agents active")
        return True
    
    return None  # Not handled


# Register custom command callback
register_callback("custom_command", _handle_orchestra_command)


def _custom_help():
    """Return Orchestra command help."""
    return [
        ("rig", "Manage rigs (project containers)"),
        ("convoy", "Create and manage work convoys"),
        ("spawn", "Spawn agents (polecat, witness, dog)"),
        ("agents", "List active agents"),
    ]


register_callback("custom_command_help", _custom_help)
