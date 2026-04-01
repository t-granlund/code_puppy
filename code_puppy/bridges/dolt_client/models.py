"""Pydantic models for Dolt client responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DoltBranch(BaseModel):
    """Represents a Dolt branch."""

    name: str = Field(description="Branch name")
    hash: str = Field(description="Commit hash")
    current: bool = Field(default=False, description="Is this the active branch")


class DoltCommit(BaseModel):
    """Represents a Dolt commit."""

    commit_hash: str = Field(description="Commit hash")
    parent_hashes: List[str] = Field(default_factory=list, description="Parent commit hashes")
    author: str = Field(description="Commit author")
    email: str = Field(description="Author email")
    date: datetime = Field(description="Commit date")
    message: str = Field(description="Commit message")


class DoltStatus(BaseModel):
    """Represents the working tree status."""

    staged_tables: Dict[str, str] = Field(default_factory=dict, description="Tables staged for commit")
    unstaged_tables: Dict[str, str] = Field(default_factory=dict, description="Modified but not staged")
    untracked_tables: List[str] = Field(default_factory=list, description="New tables not tracked")
    branch: str = Field(description="Current branch name")
    ahead: int = Field(default=0, description="Commits ahead of remote")
    behind: int = Field(default=0, description="Commits behind remote")


class DoltDiffLine(BaseModel):
    """Represents a single line in a diff."""

    type: str = Field(description="Line type: added, removed, unchanged")
    content: str = Field(description="Line content")
    old_row_num: Optional[int] = Field(default=None, description="Old row number")
    new_row_num: Optional[int] = Field(default=None, description="New row number")


class DoltTableDiff(BaseModel):
    """Represents diff for a single table."""

    table_name: str = Field(description="Name of the table")
    diff_type: str = Field(description="Type of change: schema, data, both")
    lines: List[DoltDiffLine] = Field(default_factory=list, description="Diff lines")
    rows_added: int = Field(default=0, description="Number of rows added")
    rows_deleted: int = Field(default=0, description="Number of rows deleted")
    rows_modified: int = Field(default=0, description="Number of rows modified")


class DoltSchemaColumn(BaseModel):
    """Represents a column in a table schema."""

    name: str = Field(description="Column name")
    type: str = Field(description="SQL data type")
    nullable: bool = Field(default=True, description="Whether column allows NULL")
    default: Optional[str] = Field(default=None, description="Default value")
    primary_key: bool = Field(default=False, description="Whether column is primary key")


class DoltTableSchema(BaseModel):
    """Represents a table schema."""

    table_name: str = Field(description="Name of the table")
    columns: List[DoltSchemaColumn] = Field(default_factory=list, description="Table columns")
    primary_key: List[str] = Field(default_factory=list, description="Primary key column names")


class DoltMergeResult(BaseModel):
    """Represents the result of a merge operation."""

    success: bool = Field(description="Whether merge succeeded")
    fast_forward: bool = Field(default=False, description="Was this a fast-forward merge")
    conflicts: List[str] = Field(default_factory=list, description="Tables with conflicts")
    message: str = Field(default="", description="Status message")


class DoltSQLResult(BaseModel):
    """Represents the result of a SQL query."""

    success: bool = Field(description="Whether query succeeded")
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="Query results")
    columns: List[str] = Field(default_factory=list, description="Column names")
    rows_affected: int = Field(default=0, description="Number of rows affected")
    execution_time_ms: Optional[int] = Field(default=None, description="Query execution time")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class DoltServerInfo(BaseModel):
    """Represents SQL server status."""

    running: bool = Field(description="Whether server is running")
    pid: Optional[int] = Field(default=None, description="Server process ID")
    port: int = Field(default=3306, description="Server port")
    host: str = Field(default="localhost", description="Server host")
