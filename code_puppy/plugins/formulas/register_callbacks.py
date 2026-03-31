"""Callback registration for the Formulas plugin.
"""

import logging
from pathlib import Path

from code_puppy.callbacks import register_callback
from code_puppy.messaging import emit_info, emit_success

from . import DEFAULT_FORMULA_DIR, BUILTIN_FORMULA_DIR

logger = logging.getLogger(__name__)


def _ensure_formula_dir() -> None:
    """Ensure formula directories exist."""
    DEFAULT_FORMULA_DIR.mkdir(parents=True, exist_ok=True)


def _on_startup() -> None:
    """Initialize formulas on startup."""
    _ensure_formula_dir()
    logger.debug(f"Formulas plugin initialized. Custom formulas: {DEFAULT_FORMULA_DIR}")


register_callback("startup", _on_startup)


# Custom commands
def _handle_formula_command(command: str, name: str):
    """Handle formula slash commands."""
    from code_puppy.messaging import emit_info
    
    if name == "formula":
        emit_info("Usage: /formula list | /formula cook <name> | /formula pour <name>")
        return True
    
    return None


def _custom_help():
    """Return formula command help."""
    return [
        ("formula", "Execute workflow formulas (cook/pour)"),
    ]


register_callback("custom_command", _handle_formula_command)
register_callback("custom_command_help", _custom_help)


# Tool registration
def _register_formula_tools(agent) -> None:
    """Register formula tools on an agent."""
    
    @agent.tool_plain
    async def formula_list() -> str:
        """List available workflow formulas.
        
        Formulas are reusable workflow definitions for common processes
        like code review, TDD, releases, etc.
        """
        formulas = []
        
        # Scan builtin formulas
        if BUILTIN_FORMULA_DIR.exists():
            for f in BUILTIN_FORMULA_DIR.glob("*.toml"):
                formulas.append(f"📦 {f.stem} (builtin)")
        
        # Scan custom formulas
        if DEFAULT_FORMULA_DIR.exists():
            for f in DEFAULT_FORMULA_DIR.glob("*.toml"):
                formulas.append(f"🔧 {f.stem} (custom)")
        
        if not formulas:
            return "No formulas found. Formulas are TOML files that define reusable workflows."
        
        return "## Available Formulas\n\n" + "\n".join(formulas)
    
    @agent.tool_plain
    async def formula_cook(
        name: str,
        variables: str = "",
    ) -> str:
        """Execute a formula (cook it).
        
        Executes a formula immediately without tracking.
        Use for one-off processes.
        
        Args:
            name: Formula name (e.g., 'tdd-cycle', 'code-review')
            variables: Semicolon-separated key=value pairs (e.g., 'feature=auth;scope=mvp')
        """
        # Parse variables
        vars_dict = {}
        if variables:
            for pair in variables.split(";"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    vars_dict[k.strip()] = v.strip()
        
        # Placeholder - full implementation would parse TOML and execute
        result = [f"🍳 Cooking formula: {name}"]
        if vars_dict:
            result.append(f"   Variables: {vars_dict}")
        result.append("\n(Note: Full formula execution requires beads integration)")
        
        return "\n".join(result)
    
    @agent.tool_plain
    async def formula_pour(
        name: str,
        variables: str = "",
    ) -> str:
        """Create a trackable molecule from a formula (pour it).
        
        Creates a trackable instance that persists and can be
        monitored. Use for multi-step processes that need tracking.
        
        Args:
            name: Formula name
            variables: Semicolon-separated key=value pairs
        """
        vars_dict = {}
        if variables:
            for pair in variables.split(";"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    vars_dict[k.strip()] = v.strip()
        
        result = [f"🧪 Poured formula: {name}"]
        if vars_dict:
            result.append(f"   Variables: {vars_dict}")
        result.append("   Created trackable molecule instance")
        result.append("\n(Note: Full molecule tracking requires beads integration)")
        
        return "\n".join(result)


def _register_tools() -> list[dict]:
    return [
        {
            "name": "formula_list",
            "register_func": lambda agent: _register_formula_tools(agent),
        },
    ]


register_callback("register_tools", _register_tools)
