"""Bridges module for external binary integration.

This module provides interfaces to external Go binaries (bd, dolt, gt)
used by Code Puppy for issue tracking, database management, and git operations.
"""

from code_puppy.bridges.go_binary_manager import (
    GoBinaryManager,
    BinaryConfig,
    BinaryInfo,
)

from code_puppy.bridges.dolt_client import (
    DoltClient,
    DoltError,
    DoltNotInitializedError,
    DoltBranchError,
    DoltSQLServerError,
    DoltBranch,
    DoltCommit,
    DoltStatus,
    DoltDiffLine,
    DoltTableDiff,
    DoltSchemaColumn,
    DoltTableSchema,
    DoltMergeResult,
    DoltSQLResult,
    DoltServerInfo,
)

from code_puppy.bridges.gastown_client import (
    GastownClient,
    GastownConfig,
    GastownError,
    GastownNotInstalledError,
    GastownCommandError,
    GastownParseError,
)

__all__ = [
    # Binary Manager
    "GoBinaryManager",
    "BinaryConfig",
    "BinaryInfo",
    # Dolt Client
    "DoltClient",
    "DoltError",
    "DoltNotInitializedError",
    "DoltBranchError",
    "DoltSQLServerError",
    "DoltBranch",
    "DoltCommit",
    "DoltStatus",
    "DoltDiffLine",
    "DoltTableDiff",
    "DoltSchemaColumn",
    "DoltTableSchema",
    "DoltMergeResult",
    "DoltSQLResult",
    "DoltServerInfo",
    # Gastown Client
    "GastownClient",
    "GastownConfig",
    "GastownError",
    "GastownNotInstalledError",
    "GastownCommandError",
    "GastownParseError",
]
