"""Bridges module for external integrations.

This module provides Python wrappers for external CLI tools and services,
enabling seamless integration with Code Puppy's multi-agent orchestration.
"""

from code_puppy.bridges.gastown_client import (
    GastownClient,
    GastownConfig,
    # Models
    Convoy,
    ConvoyState,
    ConvoyPriority,
    Polecat,
    PolecatRole,
    PolecatState,
    Rig,
    RigState,
    Hook,
    HookState,
    Mail,
    MailStatus,
    MailPriority,
    Escalation,
    EscalationSeverity,
    CommandResult,
    # Exceptions
    GastownError,
    GastownNotInstalledError,
    GastownCommandError,
    GastownParseError,
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
