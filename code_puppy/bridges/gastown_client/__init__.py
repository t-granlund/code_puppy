"""Gastown Client - Python wrapper for Gastown (gt) CLI commands.

This client provides a Python interface to the Gastown multi-agent workspace
manager, enabling convoy management, polecat lifecycle operations, rig
management, hook operations, mail handling, and escalation from Python code.

Usage:
    ```python
    client = GastownClient()

    # Convoy management
    convoy = await client.convoy_create("feature-auth", priority="high")
    convoys = await client.convoy_list()
    status = await client.convoy_status("feature-auth")

    # Polecat (agent) operations
    polecat = await client.polecat_spawn("auth-worker", role="reviewer")
    await client.polecat_status("auth-worker")

    # Rig management
    rigs = await client.rig_list()

    # Escalations
    await client.escalate("issue-123", severity="high", message="Stuck on auth flow")
    ```
"""

from code_puppy.bridges.gastown_client.client import GastownClient, GastownConfig
from code_puppy.bridges.gastown_client.exceptions import (
    GastownCommandError,
    GastownError,
    GastownNotInstalledError,
    GastownParseError,
)
from code_puppy.bridges.gastown_client.models import (
    CommandResult,
    Convoy,
    ConvoyPriority,
    ConvoyState,
    Escalation,
    EscalationSeverity,
    Hook,
    HookState,
    Mail,
    MailPriority,
    MailStatus,
    Polecat,
    PolecatRole,
    PolecatState,
    Rig,
    RigState,
)

__all__ = [
    # Client
    "GastownClient",
    "GastownConfig",
    # Convoy models
    "Convoy",
    "ConvoyState",
    "ConvoyPriority",
    # Polecat models
    "Polecat",
    "PolecatRole",
    "PolecatState",
    # Rig models
    "Rig",
    "RigState",
    # Hook models
    "Hook",
    "HookState",
    # Mail models
    "Mail",
    "MailStatus",
    "MailPriority",
    # Escalation models
    "Escalation",
    "EscalationSeverity",
    # Utility
    "CommandResult",
    # Exceptions
    "GastownError",
    "GastownNotInstalledError",
    "GastownCommandError",
    "GastownParseError",
]
