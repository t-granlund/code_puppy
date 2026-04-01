"""Dolt client for Code Puppy.

Provides a Python interface to the Dolt CLI and SQL server for state management.
Dolt is a SQL database with Git-like version control.

Example:
    from code_puppy.bridges.dolt_client import DoltClient

    async with DoltClient("/path/to/repo") as client:
        await client.init()
        await client.sql("CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(255))")
        await client.commit("Initial commit")
"""

from .branch_ops import BranchOperations
from .client import DoltClient
from .commit_ops import CommitOperations
from .diff_ops import DiffOperations
from .exceptions import (
    DoltBranchError,
    DoltError,
    DoltNotInitializedError,
    DoltSQLServerError,
)
from .models import (
    DoltBranch,
    DoltCommit,
    DoltDiffLine,
    DoltMergeResult,
    DoltSchemaColumn,
    DoltServerInfo,
    DoltSQLResult,
    DoltStatus,
    DoltTableDiff,
    DoltTableSchema,
)
from .remote_ops import RemoteOperations
from .server import DoltSQLServerManager
from .table_ops import TableOperations

__all__ = [
    # Client
    "DoltClient",
    "DoltSQLServerManager",
    # Operations
    "BranchOperations",
    "CommitOperations",
    "DiffOperations",
    "RemoteOperations",
    "TableOperations",
    # Models
    "DoltBranch",
    "DoltCommit",
    "DoltDiffLine",
    "DoltMergeResult",
    "DoltSchemaColumn",
    "DoltServerInfo",
    "DoltSQLResult",
    "DoltStatus",
    "DoltTableDiff",
    "DoltTableSchema",
    # Exceptions
    "DoltError",
    "DoltBranchError",
    "DoltNotInitializedError",
    "DoltSQLServerError",
]
