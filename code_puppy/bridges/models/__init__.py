"""Pydantic models for Go binary CLI responses.

This package provides type-safe representations of responses from
various Go-based CLI tools used by Code Puppy.
"""

# Beads (bd) CLI models
from .beads_models import (
    Issue,
    Molecule,
    Gate,
    Formula,
    Wisp,
    BeadListResult,
    BeadStatus,
    Priority,
)

# Dolt CLI models
from .dolt_models import (
    Commit,
    Branch,
    Diff,
    Table,
    QueryResult,
    DoltStatus,
    Schema,
    MergeResult,
    RepositoryStatus,
)

# Gastown (gt) CLI models
from .gastown_models import (
    Polecat,
    Convoy,
    Rig,
    Hook,
    Mail,
    AgentRole,
    AgentState,
    ConvoyState,
    Escalation,
)

__all__ = [
    # Beads models
    "Issue",
    "Molecule",
    "Gate",
    "Formula",
    "Wisp",
    "BeadListResult",
    "BeadStatus",
    "Priority",
    # Dolt models
    "Commit",
    "Branch",
    "Diff",
    "Table",
    "QueryResult",
    "DoltStatus",
    "Schema",
    "MergeResult",
    "RepositoryStatus",
    # Gastown models
    "Polecat",
    "Convoy",
    "Rig",
    "Hook",
    "Mail",
    "AgentRole",
    "AgentState",
    "ConvoyState",
    "Escalation",
]
