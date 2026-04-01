"""Dolt client wrapper for Code Puppy.

Provides a Python interface to the Dolt CLI and SQL server for state management.
Dolt is a SQL database with Git-like version control.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Pydantic Models for Dolt Responses
# =============================================================================


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


# =============================================================================
# Exception Classes
# =============================================================================


class DoltError(Exception):
    """Base exception for Dolt operations."""

    def __init__(self, message: str, command: Optional[str] = None, stderr: str = ""):
        super().__init__(message)
        self.command = command
        self.stderr = stderr


class DoltNotInitializedError(DoltError):
    """Raised when dolt repository is not initialized."""
    pass


class DoltBranchError(DoltError):
    """Raised when a branch operation fails."""
    pass


class DoltSQLServerError(DoltError):
    """Raised when SQL server operation fails."""
    pass


# =============================================================================
# Dolt Client
# =============================================================================


class DoltClient:
    """Async client for Dolt CLI operations.
    
    Wraps Dolt commands for:
    - SQL query execution
    - Branch management (create, checkout, merge, delete)
    - Commit operations and history
    - Diff and schema inspection
    - Table operations (create, drop, import, export)
    - SQL server management (start/stop)
    
    All operations are async to prevent blocking during CLI subprocess calls.
    
    Example:
        client = DoltClient("/path/to/repo")
        await client.init()
        await client.sql("CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(255))")
        await client.sql("INSERT INTO users VALUES (1, 'Alice')")
        await client.commit("Initial commit")
    """

    def __init__(
        self,
        repo_path: Union[str, Path],
        timeout: int = 60,
    ):
        """Initialize the Dolt client.
        
        Args:
            repo_path: Path to the Dolt repository
            timeout: Default timeout for CLI operations in seconds
        """
        self.repo_path = Path(repo_path)
        self.timeout = timeout
        self._server_process: Optional[asyncio.subprocess.Process] = None
        self._server_info: DoltServerInfo = DoltServerInfo(running=False, port=3306)
        self._init_checked = False

    # ==========================================================================
    # Internal Methods
    # ==========================================================================

    async def _check_dolt(self) -> None:
        """Verify Dolt CLI is available."""
        try:
            result = await self._run_cmd(["version"], json_output=False)
            if "dolt" not in result.lower():
                raise DoltError("dolt CLI not properly installed")
        except FileNotFoundError:
            raise DoltError(
                "dolt CLI not found. Install from https://www.dolthub.com/"
            )

    async def _ensure_init(self) -> None:
        """Ensure repository is initialized."""
        if not self._init_checked:
            dot_dolt = self.repo_path / ".dolt"
            if not dot_dolt.exists():
                raise DoltNotInitializedError(
                    f"Dolt repository not initialized at {self.repo_path}. "
                    "Run 'dolt init' or await client.init()"
                )
            self._init_checked = True

    async def _run_cmd(
        self,
        args: List[str],
        json_output: bool = True,
        timeout: Optional[int] = None,
        check_init: bool = True,
    ) -> Union[Dict[str, Any], str]:
        """Run a dolt command asynchronously.
        
        Args:
            args: Command arguments
            json_output: Whether to expect and parse JSON output
            timeout: Override default timeout
            check_init: Whether to check if repo is initialized first
            
        Returns:
            Parsed JSON dict or raw string output
            
        Raises:
            DoltError: If command fails
            DoltNotInitializedError: If repo not initialized and check_init=True
        """
        if check_init and args[0] not in ("init", "version", "config"):
            await self._ensure_init()

        cmd = ["dolt"] + args
        if json_output and "--result-format" not in " ".join(args):
            cmd.extend(["--result-format", "json"])

        effective_timeout = timeout or self.timeout

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=effective_timeout,
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                raise DoltError(
                    f"Dolt command timed out after {effective_timeout}s: {' '.join(cmd)}"
                )

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            if proc.returncode != 0:
                error_msg = stderr or stdout
                raise DoltError(
                    f"Dolt command failed: {' '.join(cmd)}\nError: {error_msg}",
                    command=" ".join(cmd),
                    stderr=stderr,
                )

            if json_output:
                try:
                    return json.loads(stdout)
                except json.JSONDecodeError:
                    return {"raw": stdout, "parsed": None}

            return stdout

        except FileNotFoundError:
            raise DoltError(
                "dolt CLI not found. Is Dolt installed and in PATH?"
            )

    # ==========================================================================
    # Repository Operations
    # ==========================================================================

    async def init(
        self,
        name: Optional[str] = None,
        email: Optional[str] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """Initialize a new Dolt repository.
        
        Args:
            name: Author name for config
            email: Author email for config
            force: Overwrite existing repo
            
        Returns:
            Result of init command
        """
        self.repo_path.mkdir(parents=True, exist_ok=True)
        
        args = ["init"]
        if force:
            args.append("--force")

        result = await self._run_cmd(args, json_output=False, check_init=False)
        self._init_checked = True

        # Configure if provided
        if name:
            await self.config("user.name", name)
        if email:
            await self.config("user.email", email)

        return {"message": result.strip(), "path": str(self.repo_path)}

    async def config(self, key: str, value: str, global_: bool = False) -> str:
        """Set a Dolt configuration value.
        
        Args:
            key: Config key (e.g., 'user.name')
            value: Config value
            global_: Set in global config
            
        Returns:
            Config command output
        """
        scope = "--global" if global_ else "--local"
        return await self._run_cmd(
            ["config", scope, "--add", key, value],
            json_output=False,
        )

    async def status(self) -> DoltStatus:
        """Get the current repository status.
        
        Returns:
            DoltStatus with staged, unstaged, and untracked tables
        """
        result = await self._run_cmd(["status"])
        
        if isinstance(result, dict) and "tables" in result:
            data = result
        else:
            # Parse text output if JSON not available
            data = {"tables": {}, "branch": "main"}

        return DoltStatus(
            staged_tables=data.get("staged_tables", {}),
            unstaged_tables=data.get("unstaged_tables", {}),
            untracked_tables=data.get("untracked_tables", []),
            branch=data.get("branch", "main"),
            ahead=data.get("ahead", 0),
            behind=data.get("behind", 0),
        )

    # ==========================================================================
    # SQL Operations
    # ==========================================================================

    async def sql(
        self,
        query: str,
        database: Optional[str] = None,
        use_db: bool = True,
    ) -> DoltSQLResult:
        """Execute a SQL query.
        
        Args:
            query: SQL query to execute
            database: Database name (optional)
            use_db: Whether to use the current database
            
        Returns:
            DoltSQLResult with rows, columns, and status
        """
        args = ["sql"]
        
        if database:
            args.extend(["-d", database])
        elif use_db:
            args.append("-u")
            
        args.extend(["-q", query, "--result-format", "json"])

        try:
            start_time = asyncio.get_event_loop().time()
            result = await self._run_cmd(args)
            elapsed_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

            if isinstance(result, dict):
                if "error" in result:
                    return DoltSQLResult(
                        success=False,
                        error=result["error"],
                        execution_time_ms=elapsed_ms,
                    )
                
                return DoltSQLResult(
                    success=True,
                    rows=result.get("rows", []),
                    columns=result.get("columns", []),
                    rows_affected=result.get("rows_affected", 0),
                    execution_time_ms=elapsed_ms,
                )
            else:
                # Try to parse as JSON
                try:
                    data = json.loads(result) if isinstance(result, str) else result
                    return DoltSQLResult(
                        success=True,
                        rows=data.get("rows", []),
                        columns=data.get("columns", []),
                        rows_affected=data.get("rows_affected", 0),
                        execution_time_ms=elapsed_ms,
                    )
                except json.JSONDecodeError:
                    return DoltSQLResult(
                        success=True,
                        error=None,
                        execution_time_ms=elapsed_ms,
                    )

        except DoltError as e:
            return DoltSQLResult(success=False, error=str(e))

    async def sql_batch(self, queries: List[str]) -> List[DoltSQLResult]:
        """Execute multiple SQL queries.
        
        Args:
            queries: List of SQL queries
            
        Returns:
            List of DoltSQLResult for each query
        """
        results = []
        for query in queries:
            result = await self.sql(query)
            results.append(result)
            if not result.success:
                # Stop on first error
                break
        return results

    # ==========================================================================
    # Branch Operations
    # ==========================================================================

    async def branch(
        self,
        name: Optional[str] = None,
        from_branch: Optional[str] = None,
        copy: bool = False,
        move: bool = False,
        delete: bool = False,
        force_delete: bool = False,
        list_branches: bool = False,
    ) -> Union[DoltBranch, List[DoltBranch], str]:
        """Manage branches.
        
        Args:
            name: Branch name (for create/delete/checkout)
            from_branch: Source branch for new branch
            copy: Copy a branch
            move: Move/rename a branch
            delete: Delete a branch
            force_delete: Force delete a branch
            list_branches: List all branches
            
        Returns:
            Single branch, list of branches, or status message
        """
        if list_branches or name is None:
            result = await self._run_cmd(["branch", "--verbose"], json_output=False)
            branches = []
            
            for line in result.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                # Parse branch line: "* main    abc123" or "  feature xyz789"
                is_current = line.startswith("*")
                parts = line.replace("*", "").strip().split()
                if len(parts) >= 2:
                    branch_name = parts[0]
                    commit_hash = parts[1] if len(parts) > 1 else ""
                    branches.append(DoltBranch(
                        name=branch_name,
                        hash=commit_hash,
                        current=is_current,
                    ))
            
            return branches

        if delete or force_delete:
            flag = "-D" if force_delete else "-d"
            result = await self._run_cmd(
                ["branch", flag, name],
                json_output=False,
            )
            return result.strip()

        if move:
            result = await self._run_cmd(
                ["branch", "-m", name],
                json_output=False,
            )
            return result.strip()

        # Create branch
        args = ["branch"]
        if copy:
            args.append("-c")
        if from_branch:
            args.extend([name, from_branch])
        else:
            args.append(name)

        result = await self._run_cmd(args, json_output=False)
        
        # Return new branch info
        branches = await self.branch(list_branches=True)
        for b in branches:
            if b.name == name:
                return b
        return DoltBranch(name=name, hash="", current=False)

    async def checkout(
        self,
        branch: str,
        create: bool = False,
    ) -> str:
        """Switch to a branch.
        
        Args:
            branch: Branch name to checkout
            create: Create the branch if it doesn't exist
            
        Returns:
            Checkout result message
        """
        args = ["checkout"]
        if create:
            args.append("-b")
        args.append(branch)

        result = await self._run_cmd(args, json_output=False)
        return result.strip()

    async def merge(
        self,
        branch: str,
        message: Optional[str] = None,
        no_ff: bool = False,
    ) -> DoltMergeResult:
        """Merge a branch into the current branch.
        
        Args:
            branch: Branch to merge
            message: Merge commit message
            no_ff: Force a merge commit even if fast-forward is possible
            
        Returns:
            DoltMergeResult with success status and conflicts
        """
        args = ["merge"]
        if message:
            args.extend(["-m", message])
        if no_ff:
            args.append("--no-ff")
        args.append(branch)

        try:
            result = await self._run_cmd(args, json_output=False)
            return DoltMergeResult(
                success=True,
                message=result.strip(),
            )
        except DoltError as e:
            # Check if there are conflicts
            if "conflict" in e.stderr.lower():
                # Get conflicting tables
                status_result = await self._run_cmd(["status"], json_output=False)
                conflicts = []
                for line in status_result.split("\n"):
                    if "conflict" in line.lower():
                        # Extract table name
                        parts = line.split()
                        if parts:
                            conflicts.append(parts[0])
                
                return DoltMergeResult(
                    success=False,
                    conflicts=conflicts,
                    message=str(e),
                )
            raise

    # ==========================================================================
    # Commit Operations
    # ==========================================================================

    async def add(self, tables: Optional[Union[str, List[str]]] = None) -> str:
        """Stage tables for commit.
        
        Args:
            tables: Table name(s) to stage, or None for all changes
            
        Returns:
            Add command output
        """
        args = ["add"]
        if tables is None:
            args.append("-A")  # All changes
        elif isinstance(tables, str):
            args.append(tables)
        else:
            args.extend(tables)

        result = await self._run_cmd(args, json_output=False)
        return result.strip()

    async def commit(
        self,
        message: str,
        tables: Optional[Union[str, List[str]]] = None,
        allow_empty: bool = False,
    ) -> DoltCommit:
        """Create a commit.
        
        Args:
            message: Commit message
            tables: Specific tables to commit (stages them first)
            allow_empty: Allow empty commits
            
        Returns:
            DoltCommit with commit details
        """
        # Stage tables if specified
        if tables:
            await self.add(tables)

        args = ["commit", "-m", message]
        if allow_empty:
            args.append("--allow-empty")

        await self._run_cmd(args, json_output=False)
        
        # Get the new commit
        log_result = await self.log(limit=1)
        if log_result:
            return log_result[0]
        
        return DoltCommit(
            commit_hash="",
            message=message,
            author="",
            email="",
            date=datetime.now(),
        )

    async def log(
        self,
        limit: int = 10,
        branch: Optional[str] = None,
        table: Optional[str] = None,
    ) -> List[DoltCommit]:
        """Get commit history.
        
        Args:
            limit: Maximum number of commits
            branch: Specific branch (default: current)
            table: Filter to specific table history
            
        Returns:
            List of DoltCommit
        """
        if table:
            args = ["log", table, "-n", str(limit)]
        else:
            args = ["log", "-n", str(limit)]
        if branch:
            args.append(branch)

        result = await self._run_cmd(args, json_output=False)
        
        commits = []
        current_commit = {}
        
        for line in result.strip().split("\n"):
            line = line.strip()
            if line.startswith("commit "):
                if current_commit:
                    commits.append(self._parse_commit(current_commit))
                current_commit = {"hash": line.split()[1]}
            elif line.startswith("Author: "):
                author_part = line[8:]
                if "<" in author_part:
                    name, email = author_part.rsplit("<", 1)
                    current_commit["author"] = name.strip()
                    current_commit["email"] = email.rstrip(">")
                else:
                    current_commit["author"] = author_part
                    current_commit["email"] = ""
            elif line.startswith("Date: "):
                date_str = line[6:].strip()
                try:
                    current_commit["date"] = datetime.strptime(
                        date_str, "%a %b %d %H:%M:%S %Y %z"
                    )
                except ValueError:
                    current_commit["date"] = datetime.now()
            elif line and not line.startswith("Merge:") and "message" not in current_commit:
                current_commit["message"] = line

        if current_commit:
            commits.append(self._parse_commit(current_commit))

        return commits

    def _parse_commit(self, data: Dict[str, Any]) -> DoltCommit:
        """Parse commit data into DoltCommit."""
        return DoltCommit(
            commit_hash=data.get("hash", ""),
            parent_hashes=data.get("parents", []),
            author=data.get("author", ""),
            email=data.get("email", ""),
            date=data.get("date", datetime.now()),
            message=data.get("message", ""),
        )

    async def reset(
        self,
        hard: bool = False,
        soft: bool = False,
        commit: Optional[str] = None,
    ) -> str:
        """Reset repository state.
        
        Args:
            hard: Hard reset (discard changes)
            soft: Soft reset (keep staged)
            commit: Commit to reset to
            
        Returns:
            Reset output
        """
        args = ["reset"]
        if hard:
            args.append("--hard")
        elif soft:
            args.append("--soft")
        if commit:
            args.append(commit)

        result = await self._run_cmd(args, json_output=False)
        return result.strip()

    # ==========================================================================
    # Diff Operations
    # ==========================================================================

    async def diff(
        self,
        from_branch: Optional[str] = None,
        to_branch: Optional[str] = None,
        table: Optional[str] = None,
        staged: bool = False,
        summary: bool = False,
    ) -> Union[List[DoltTableDiff], Dict[str, Any]]:
        """Get differences between commits or branches.
        
        Args:
            from_branch: Source branch/commit
            to_branch: Target branch/commit
            table: Specific table to diff
            staged: Show staged changes
            summary: Return summary only
            
        Returns:
            List of table diffs or summary dict
        """
        args = ["diff"]
        
        if summary:
            args.append("--stat")
        if staged:
            args.append("--staged")
        if table:
            args.append(table)
        if from_branch and to_branch:
            args.extend([from_branch, to_branch])
        elif from_branch:
            args.append(from_branch)

        result = await self._run_cmd(args, json_output=False)
        
        if summary:
            # Parse summary format
            summary_data = {"tables": {}, "total_changes": 0}
            for line in result.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|")
                    if len(parts) >= 2:
                        table_name = parts[0].strip()
                        changes = parts[1].strip()
                        summary_data["tables"][table_name] = changes
            return summary_data

        # Parse diff output
        diffs = []
        current_table = None
        current_lines = []

        for line in result.strip().split("\n"):
            if line.startswith("diff --dolt"):
                if current_table:
                    diffs.append(current_table)
                current_table = DoltTableDiff(
                    table_name=line.split()[-1] if len(line.split()) > 2 else "unknown",
                    diff_type="data",
                    lines=[],
                )
            elif line.startswith("+") and not line.startswith("+++"):
                current_lines.append(DoltDiffLine(
                    type="added",
                    content=line[1:],
                ))
            elif line.startswith("-") and not line.startswith("---"):
                current_lines.append(DoltDiffLine(
                    type="removed",
                    content=line[1:],
                ))

        if current_table:
            current_table.lines = current_lines
            diffs.append(current_table)

        return diffs

    async def schema_diff(
        self,
        from_branch: Optional[str] = None,
        to_branch: Optional[str] = None,
        table: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get schema differences.
        
        Args:
            from_branch: Source branch/commit
            to_branch: Target branch/commit
            table: Specific table
            
        Returns:
            Schema diff information
        """
        args = ["diff", "--schema"]
        if table:
            args.append(table)
        if from_branch and to_branch:
            args.extend([from_branch, to_branch])
        elif from_branch:
            args.append(from_branch)

        result = await self._run_cmd(args, json_output=False)
        return {"diff": result.strip()}

    # ==========================================================================
    # Table Operations
    # ==========================================================================

    async def table_create(
        self,
        name: str,
        schema: Union[str, List[DoltSchemaColumn]],
        as_select: Optional[str] = None,
    ) -> DoltSQLResult:
        """Create a table.
        
        Args:
            name: Table name
            schema: SQL schema definition or list of columns
            as_select: Create from SELECT query
            
        Returns:
            DoltSQLResult
        """
        if isinstance(schema, list):
            # Build CREATE TABLE from columns
            columns_sql = ", ".join(
                f"{col.name} {col.type}" +
                (" NOT NULL" if not col.nullable else "") +
                (f" DEFAULT {col.default}" if col.default else "") +
                (" PRIMARY KEY" if col.primary_key else "")
                for col in schema
            )
            query = f"CREATE TABLE {name} ({columns_sql})"
        else:
            query = f"CREATE TABLE {name} ({schema})"

        if as_select:
            query += f" AS {as_select}"

        return await self.sql(query)

    async def table_drop(self, name: str, if_exists: bool = True) -> DoltSQLResult:
        """Drop a table.
        
        Args:
            name: Table name
            if_exists: Only drop if exists
            
        Returns:
            DoltSQLResult
        """
        query = "DROP TABLE "
        if if_exists:
            query += "IF EXISTS "
        query += name
        return await self.sql(query)

    async def table_import(
        self,
        table: str,
        file_path: Union[str, Path],
        file_format: str = "csv",
        continue_on_error: bool = False,
    ) -> str:
        """Import data into a table.
        
        Args:
            table: Target table name
            file_path: Path to import file
            file_format: File format (csv, json, parquet)
            continue_on_error: Continue on import errors
            
        Returns:
            Import result
        """
        args = ["table", "import", "-u", table, str(file_path)]
        
        if file_format == "json":
            args.append("--json")
        elif file_format == "parquet":
            args.append("--parquet")
        if continue_on_error:
            args.append("--continue")

        result = await self._run_cmd(args, json_output=False)
        return result.strip()

    async def table_export(
        self,
        table: str,
        file_path: Union[str, Path],
        file_format: str = "csv",
    ) -> str:
        """Export table data.
        
        Args:
            table: Table name to export
            file_path: Output file path
            file_format: Export format (csv, json, parquet, sql)
            
        Returns:
            Export result
        """
        args = ["table", "export", table, str(file_path)]
        
        if file_format == "json":
            args.append("--json")
        elif file_format == "parquet":
            args.append("--parquet")
        elif file_format == "sql":
            args.append("--sql")

        result = await self._run_cmd(args, json_output=False)
        return result.strip()

    async def table_ls(self) -> List[str]:
        """List all tables.
        
        Returns:
            List of table names
        """
        result = await self._run_cmd(["table", "ls"], json_output=False)
        tables = []
        for line in result.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("Tables"):
                tables.append(line)
        return tables

    async def schema_show(
        self,
        table: Optional[str] = None,
    ) -> Union[DoltTableSchema, Dict[str, DoltTableSchema]]:
        """Show table schema.
        
        Args:
            table: Specific table, or None for all tables
            
        Returns:
            Single schema or dict of all schemas
        """
        args = ["schema", "show"]
        if table:
            args.append(table)

        result = await self._run_cmd(args, json_output=False)
        
        # Parse schema output
        schemas = {}
        current_table = None
        columns = []
        primary_keys = []

        for line in result.strip().split("\n"):
            line = line.strip()
            if line.startswith("CREATE TABLE"):
                if current_table:
                    schemas[current_table] = DoltTableSchema(
                        table_name=current_table,
                        columns=columns,
                        primary_key=primary_keys,
                    )
                current_table = line.split()[-1].rstrip("(")
                columns = []
                primary_keys = []
            elif line and current_table:
                # Parse column definition
                parts = line.rstrip(",").split()
                if len(parts) >= 2:
                    col_name = parts[0]
                    col_type = " ".join(parts[1:]).upper()
                    nullable = "NOT NULL" not in col_type
                    default = None
                    is_pk = "PRIMARY KEY" in col_type
                    
                    col_type = col_type.replace("NOT NULL", "").replace("PRIMARY KEY", "").strip()
                    
                    if "DEFAULT" in col_type:
                        type_parts = col_type.split("DEFAULT")
                        col_type = type_parts[0].strip()
                        default = type_parts[1].strip() if len(type_parts) > 1 else None
                    
                    columns.append(DoltSchemaColumn(
                        name=col_name,
                        type=col_type,
                        nullable=nullable,
                        default=default,
                        primary_key=is_pk,
                    ))

        if current_table:
            schemas[current_table] = DoltTableSchema(
                table_name=current_table,
                columns=columns,
                primary_key=primary_keys,
            )

        if table:
            return schemas.get(table, DoltTableSchema(table_name=table, columns=[]))
        return schemas

    # ==========================================================================
    # SQL Server Operations
    # ==========================================================================

    async def start_server(
        self,
        port: int = 3306,
        host: str = "localhost",
        user: str = "root",
        password: str = "",
        readonly: bool = False,
        log_level: str = "info",
    ) -> DoltServerInfo:
        """Start the Dolt SQL server.
        
        Args:
            port: Server port
            host: Server host
            user: Database user
            password: Database password
            readonly: Start in read-only mode
            log_level: Logging level
            
        Returns:
            DoltServerInfo with server status
            
        Raises:
            DoltSQLServerError: If server fails to start
        """
        if self._server_process and self._server_process.returncode is None:
            logger.warning("Dolt SQL server already running")
            return self._server_info

        args = [
            "sql-server",
            "--port", str(port),
            "--host", host,
            "-u", user,
        ]
        
        if password:
            args.extend(["-p", password])
        if readonly:
            args.append("--readonly")
        if log_level:
            args.extend(["--loglevel", log_level])

        try:
            self._server_process = await asyncio.create_subprocess_exec(
                "dolt",
                *args,
                cwd=str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait a moment for server to start
            await asyncio.sleep(2)
            
            if self._server_process.returncode is not None:
                stdout, stderr = await self._server_process.communicate()
                raise DoltSQLServerError(
                    f"Failed to start SQL server: {stderr.decode()}",
                    stderr=stderr.decode(),
                )

            self._server_info = DoltServerInfo(
                running=True,
                pid=self._server_process.pid,
                port=port,
                host=host,
            )
            
            logger.info(f"Dolt SQL server started on {host}:{port}")
            return self._server_info

        except Exception as e:
            raise DoltSQLServerError(f"Failed to start SQL server: {e}")

    async def stop_server(self, force: bool = False) -> DoltServerInfo:
        """Stop the Dolt SQL server.
        
        Args:
            force: Force kill the server
            
        Returns:
            DoltServerInfo with updated status
        """
        if not self._server_process:
            logger.warning("No SQL server running")
            return DoltServerInfo(running=False)

        try:
            if force:
                self._server_process.kill()
            else:
                self._server_process.terminate()
            
            await asyncio.wait_for(self._server_process.wait(), timeout=5.0)
            
        except asyncio.TimeoutError:
            self._server_process.kill()
            await self._server_process.wait()
        except ProcessLookupError:
            pass  # Already terminated

        self._server_process = None
        self._server_info = DoltServerInfo(running=False)
        
        logger.info("Dolt SQL server stopped")
        return self._server_info

    async def server_status(self) -> DoltServerInfo:
        """Check SQL server status.
        
        Returns:
            DoltServerInfo with current status
        """
        if not self._server_process:
            return DoltServerInfo(running=False)

        # Check if still running
        if self._server_process.returncode is None:
            return self._server_info
        else:
            self._server_process = None
            self._server_info = DoltServerInfo(running=False)
            return self._server_info

    # ==========================================================================
    # Remote Operations
    # ==========================================================================

    async def remote_add(self, name: str, url: str) -> str:
        """Add a remote.
        
        Args:
            name: Remote name
            url: Remote URL
            
        Returns:
            Command output
        """
        result = await self._run_cmd(
            ["remote", "add", name, url],
            json_output=False,
        )
        return result.strip()

    async def remote_remove(self, name: str) -> str:
        """Remove a remote.
        
        Args:
            name: Remote name
            
        Returns:
            Command output
        """
        result = await self._run_cmd(
            ["remote", "remove", name],
            json_output=False,
        )
        return result.strip()

    async def remote_list(self) -> List[Dict[str, str]]:
        """List remotes.
        
        Returns:
            List of remote info dicts
        """
        result = await self._run_cmd(["remote", "-v"], json_output=False)
        remotes = []
        for line in result.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 2:
                remotes.append({"name": parts[0], "url": parts[1]})
        return remotes

    async def push(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        force: bool = False,
        set_upstream: bool = False,
    ) -> str:
        """Push to remote.
        
        Args:
            remote: Remote name
            branch: Branch to push
            force: Force push
            set_upstream: Set upstream tracking
            
        Returns:
            Push output
        """
        args = ["push"]
        if force:
            args.append("-f")
        if set_upstream:
            args.append("-u")
        args.append(remote)
        if branch:
            args.append(branch)

        result = await self._run_cmd(args, json_output=False)
        return result.strip()

    async def pull(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
    ) -> str:
        """Pull from remote.
        
        Args:
            remote: Remote name
            branch: Branch to pull
            
        Returns:
            Pull output
        """
        args = ["pull", remote]
        if branch:
            args.append(branch)

        result = await self._run_cmd(args, json_output=False)
        return result.strip()

    async def fetch(self, remote: str = "origin") -> str:
        """Fetch from remote.
        
        Args:
            remote: Remote name
            
        Returns:
            Fetch output
        """
        result = await self._run_cmd(
            ["fetch", remote],
            json_output=False,
        )
        return result.strip()

    async def clone(
        self,
        url: str,
        target_path: Optional[Union[str, Path]] = None,
        branch: Optional[str] = None,
    ) -> str:
        """Clone a remote repository.
        
        Args:
            url: Remote URL
            target_path: Local path (default: repo name)
            branch: Specific branch to clone
            
        Returns:
            Clone output
        """
        args = ["clone", url]
        if target_path:
            args.append(str(target_path))
        if branch:
            args.extend(["-b", branch])

        result = await self._run_cmd(args, json_output=False, check_init=False)
        return result.strip()

    # ==========================================================================
    # Cleanup
    # ==========================================================================

    async def close(self) -> None:
        """Clean up resources.
        
        Stops the SQL server if running.
        """
        if self._server_process:
            await self.stop_server()

    async def __aenter__(self) -> DoltClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
