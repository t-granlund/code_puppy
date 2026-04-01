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
    # Pydantic models
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

__all__ = [
    # Binary Manager
    "GoBinaryManager",
    "BinaryConfig",
    "BinaryInfo",
    # Dolt Client
    "DoltClient",
    # Exceptions
    "DoltError",
    "DoltNotInitializedError",
    "DoltBranchError",
    "DoltSQLServerError",
    # Models
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
]
