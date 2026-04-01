"""Pydantic models for Dolt CLI responses.

This module provides type-safe representations of all Go binary responses
from the dolt command-line tool (Git-style versioned database).
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DoltStatus(str, Enum):
    """Repository status enumeration."""

    CLEAN = "clean"
    DIRTY = "dirty"
    MERGING = "merging"
    REBASING = "rebasing"
    BISECTING = "bisecting"


class Commit(BaseModel):
    """Git-style commit info from Dolt CLI.

    Represents a commit in the Dolt versioned database.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    hash: str = Field(description="Commit hash")
    short_hash: str = Field(description="Abbreviated commit hash")

    # Author info
    author: str = Field(description="Commit author name")
    author_email: Optional[str] = Field(default=None, description="Author email")

    # Commit info
    message: str = Field(description="Commit message")

    # Timestamps
    timestamp: datetime = Field(description="Commit timestamp")

    # Relationships
    parents: List[str] = Field(default_factory=list, description="Parent commit hashes")
    branch: Optional[str] = Field(
        default=None, description="Branch containing this commit"
    )

    # Stats
    insertions: int = Field(default=0, description="Lines inserted")
    deletions: int = Field(default=0, description="Lines deleted")
    files_changed: int = Field(default=0, description="Files changed")


class Branch(BaseModel):
    """Branch information from Dolt CLI.

    Represents a database branch.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    name: str = Field(description="Branch name")
    hash: Optional[str] = Field(default=None, description="Branch head commit hash")

    # State
    is_current: bool = Field(
        default=False, description="Whether this is the current branch"
    )
    is_remote: bool = Field(
        default=False, description="Whether this is a remote branch"
    )

    # Remote info
    remote: Optional[str] = Field(
        default=None, description="Remote name if remote branch"
    )
    tracking_branch: Optional[str] = Field(
        default=None, description="Upstream tracking branch"
    )

    # Metadata
    ahead: int = Field(default=0, description="Commits ahead of upstream")
    behind: int = Field(default=0, description="Commits behind upstream")
    last_commit_at: Optional[datetime] = Field(
        default=None, description="Last commit timestamp"
    )


class Diff(BaseModel):
    """Diff between branches/commits from Dolt CLI.

    Represents changes between two points in the database history.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    # Diff targets
    from_commit: str = Field(description="Source commit/branch")
    to_commit: str = Field(description="Target commit/branch")

    # Table info
    table_name: str = Field(description="Table being compared")

    # Diff type
    diff_type: str = Field(description="Type of diff (schema, data, both)")

    # Changes
    rows_added: int = Field(default=0, description="Rows added")
    rows_deleted: int = Field(default=0, description="Rows deleted")
    rows_modified: int = Field(default=0, description="Rows modified")

    # Schema changes
    schema_changed: bool = Field(default=False, description="Whether schema changed")
    columns_added: List[str] = Field(default_factory=list, description="Columns added")
    columns_dropped: List[str] = Field(
        default_factory=list, description="Columns dropped"
    )
    columns_modified: List[str] = Field(
        default_factory=list, description="Columns modified"
    )

    # Raw diff (optional, for detailed diffs)
    diff_data: Optional[str] = Field(default=None, description="Raw diff output")


class Table(BaseModel):
    """Database table metadata from Dolt CLI.

    Represents a table in the Dolt database.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    name: str = Field(description="Table name")

    # Schema
    columns: List[str] = Field(default_factory=list, description="Column names")
    primary_key: List[str] = Field(
        default_factory=list, description="Primary key columns"
    )

    # Stats
    row_count: Optional[int] = Field(default=None, description="Approximate row count")
    size_bytes: Optional[int] = Field(default=None, description="Table size in bytes")

    # State
    is_system_table: bool = Field(
        default=False, description="Whether this is a system table"
    )
    is_temporary: bool = Field(
        default=False, description="Whether this is a temporary table"
    )

    # Metadata
    created_at: Optional[datetime] = Field(
        default=None, description="Creation timestamp"
    )
    last_modified: Optional[datetime] = Field(
        default=None, description="Last modification"
    )


class QueryResult(BaseModel):
    """SQL query result from Dolt CLI.

    Represents the result of executing a SQL query.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    # Query info
    query: str = Field(description="Executed query")

    # Results
    columns: List[str] = Field(default_factory=list, description="Column names")
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="Result rows")
    row_count: int = Field(default=0, description="Number of rows")

    # Execution info
    execution_time_ms: Optional[int] = Field(
        default=None, description="Query execution time"
    )

    # For DML queries
    rows_affected: Optional[int] = Field(
        default=None, description="Rows affected (for INSERT/UPDATE/DELETE)"
    )
    last_insert_id: Optional[int] = Field(default=None, description="Last insert ID")

    # Status
    success: bool = Field(default=True, description="Whether query succeeded")
    error_message: Optional[str] = Field(
        default=None, description="Error message if failed"
    )


class Schema(BaseModel):
    """Table schema info from Dolt CLI.

    Represents the detailed schema of a database table.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    table_name: str = Field(description="Table name")

    # Column definitions
    columns: List[Dict[str, Any]] = Field(
        default_factory=list, description="Column definitions"
    )
    # Each column dict has: name, type, nullable, default, extra

    # Keys
    primary_key: List[str] = Field(
        default_factory=list, description="Primary key columns"
    )
    unique_keys: List[List[str]] = Field(
        default_factory=list, description="Unique key column sets"
    )
    foreign_keys: List[Dict[str, Any]] = Field(
        default_factory=list, description="Foreign key definitions"
    )

    # Indexes
    indexes: List[Dict[str, Any]] = Field(
        default_factory=list, description="Index definitions"
    )

    # Constraints
    constraints: List[Dict[str, Any]] = Field(
        default_factory=list, description="Table constraints"
    )

    # DDL
    create_statement: Optional[str] = Field(
        default=None, description="CREATE TABLE statement"
    )


class MergeResult(BaseModel):
    """Merge operation result from Dolt CLI.

    Represents the result of a merge operation.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    # Merge info
    source_branch: str = Field(description="Source branch/commit")
    target_branch: str = Field(description="Target branch")

    # Result
    success: bool = Field(description="Whether merge succeeded")
    fast_forward: bool = Field(
        default=False, description="Whether fast-forward was possible"
    )

    # Conflicts
    has_conflicts: bool = Field(
        default=False, description="Whether there are conflicts"
    )
    conflicted_tables: List[str] = Field(
        default_factory=list, description="Tables with conflicts"
    )

    # Stats
    tables_added: List[str] = Field(default_factory=list, description="Tables added")
    tables_deleted: List[str] = Field(
        default_factory=list, description="Tables deleted"
    )
    tables_modified: List[str] = Field(
        default_factory=list, description="Tables modified"
    )

    # Result commit
    commit_hash: Optional[str] = Field(default=None, description="Merge commit hash")

    # Error info
    error_message: Optional[str] = Field(
        default=None, description="Error message if failed"
    )


class RepositoryStatus(BaseModel):
    """Repository status from Dolt CLI.

    Represents the overall status of a Dolt repository.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    current_branch: str = Field(description="Current branch name")
    head_commit: Optional[str] = Field(default=None, description="Current HEAD commit")

    # Status
    status: DoltStatus = Field(
        default=DoltStatus.CLEAN, description="Repository status"
    )

    # Working tree
    staged_tables: List[str] = Field(default_factory=list, description="Staged tables")
    unstaged_tables: List[str] = Field(
        default_factory=list, description="Unstaged modified tables"
    )
    untracked_tables: List[str] = Field(
        default_factory=list, description="Untracked tables"
    )

    # Merge state
    merge_in_progress: bool = Field(
        default=False, description="Whether merge is in progress"
    )
    merge_source: Optional[str] = Field(
        default=None, description="Merge source if in progress"
    )

    # Stash
    stash_count: int = Field(default=0, description="Number of stashed changes")

    # Remote
    ahead: int = Field(default=0, description="Commits ahead of remote")
    behind: int = Field(default=0, description="Commits behind remote")
