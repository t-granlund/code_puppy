"""Bridges module for Code Puppy.

Provides client wrappers for external tools and services.
"""

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
    # Client
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
