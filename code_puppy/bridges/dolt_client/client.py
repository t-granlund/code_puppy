"""Dolt client for database operations with Git-like version control."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .branch_ops import BranchOperations
from .commit_ops import CommitOperations
from .diff_ops import DiffOperations
from .exceptions import DoltError, DoltNotInitializedError
from .models import (
    DoltCommit,
    DoltServerInfo,
    DoltSQLResult,
    DoltStatus,
)
from .remote_ops import RemoteOperations
from .server import DoltSQLServerManager
from .table_ops import TableOperations

logger = logging.getLogger(__name__)


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
        self._server_manager = DoltSQLServerManager(self.repo_path)
        self._server_info: DoltServerInfo = DoltServerInfo(running=False, port=3306)
        self._server_manager.set_server_info(self._server_info)
        self._init_checked = False
        self._branch_ops = BranchOperations(self)
        self._table_ops = TableOperations(self)
        self._commit_ops = CommitOperations(self)
        self._diff_ops = DiffOperations(self)
        self._remote_ops = RemoteOperations(self)

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
            raise DoltError("dolt CLI not found. Install from https://www.dolthub.com/")

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
                # Capture output before killing (fixed: capture stderr/stdout)
                stdout_bytes, stderr_bytes = b"", b""
                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        proc.communicate(), timeout=5.0
                    )
                except asyncio.TimeoutError:
                    pass
                proc.kill()
                await proc.wait()
                raise DoltError(
                    f"Dolt command timed out after {effective_timeout}s: {' '.join(cmd)}",
                    command=" ".join(cmd),
                    stderr=stderr_bytes.decode("utf-8", errors="replace"),
                    stdout=stdout_bytes.decode("utf-8", errors="replace"),
                )

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            if proc.returncode != 0:
                error_msg = stderr or stdout
                raise DoltError(
                    f"Dolt command failed: {' '.join(cmd)}\nError: {error_msg}",
                    command=" ".join(cmd),
                    stderr=stderr,
                    stdout=stdout,
                )

            if json_output:
                try:
                    return json.loads(stdout)
                except json.JSONDecodeError:
                    return {"raw": stdout, "parsed": None}

            return stdout

        except FileNotFoundError:
            raise DoltError("dolt CLI not found. Is Dolt installed and in PATH?")

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
    # Branch Operations (Delegated)
    # ==========================================================================

    async def list_branches(self):
        """List all branches."""
        return await self._branch_ops.list_branches()

    async def create_branch(self, name, from_branch=None, copy=False):
        """Create a new branch."""
        return await self._branch_ops.create_branch(name, from_branch, copy)

    async def delete_branch(self, name, force=False):
        """Delete a branch."""
        return await self._branch_ops.delete_branch(name, force)

    async def rename_branch(self, name):
        """Rename the current branch."""
        return await self._branch_ops.rename_branch(name)

    async def checkout(self, branch, create=False):
        """Switch to a branch."""
        return await self._branch_ops.checkout(branch, create)

    async def merge(self, branch, message=None, no_ff=False):
        """Merge a branch into the current branch."""
        return await self._branch_ops.merge(branch, message, no_ff)

    # ==========================================================================
    # Commit Operations (Delegated)
    # ==========================================================================

    async def add(self, tables=None):
        """Stage tables for commit."""
        return await self._commit_ops.add(tables)

    async def commit(self, message, tables=None, allow_empty=False):
        """Create a commit."""
        return await self._commit_ops.commit(message, tables, allow_empty)

    async def log(self, limit=10, branch=None, table=None):
        """Get commit history."""
        return await self._commit_ops.log(limit, branch, table)

    async def reset(self, hard=False, soft=False, commit=None):
        """Reset repository state."""
        return await self._commit_ops.reset(hard, soft, commit)

    # ==========================================================================
    # Diff Operations (Delegated)
    # ==========================================================================

    async def diff(
        self, from_branch=None, to_branch=None, table=None, staged=False, summary=False
    ):
        """Get differences between commits or branches."""
        return await self._diff_ops.diff(from_branch, to_branch, table, staged, summary)

    async def schema_diff(self, from_branch=None, to_branch=None, table=None):
        """Get schema differences."""
        return await self._diff_ops.schema_diff(from_branch, to_branch, table)

    # ==========================================================================
    # Table Operations (Delegated)
    # ==========================================================================

    async def table_create(self, name, schema, as_select=None):
        """Create a table."""
        return await self._table_ops.create(name, schema, as_select)

    async def table_drop(self, name, if_exists=True):
        """Drop a table."""
        return await self._table_ops.drop(name, if_exists)

    async def table_import(
        self, table, file_path, file_format="csv", continue_on_error=False
    ):
        """Import data into a table."""
        return await self._table_ops.import_data(
            table, file_path, file_format, continue_on_error
        )

    async def table_export(self, table, file_path, file_format="csv"):
        """Export table data."""
        return await self._table_ops.export_data(table, file_path, file_format)

    async def table_ls(self):
        """List all tables."""
        return await self._table_ops.list_tables()

    async def schema_show(self, table=None):
        """Show table schema."""
        return await self._table_ops.show_schema(table)

    # ==========================================================================
    # SQL Server Operations (Delegated to manager)
    # ==========================================================================

    async def start_server(
        self,
        port: int = 3306,
        host: str = "localhost",
        user: str = "root",
        password: str = "",
        readonly: bool = False,
        log_level: str = "info",
        health_timeout: float = 30.0,
    ) -> DoltServerInfo:
        """Start the Dolt SQL server.

        Args:
            port: Server port
            host: Server host
            user: Database user
            password: Database password
            readonly: Start in read-only mode
            log_level: Logging level
            health_timeout: Max time to wait for server to be healthy

        Returns:
            DoltServerInfo with server status
        """
        self._server_info = await self._server_manager.start(
            port=port,
            host=host,
            user=user,
            password=password,
            readonly=readonly,
            log_level=log_level,
            health_timeout=health_timeout,
        )
        return self._server_info

    async def stop_server(self, force: bool = False) -> DoltServerInfo:
        """Stop the Dolt SQL server.

        Args:
            force: Force kill the server

        Returns:
            DoltServerInfo with updated status
        """
        return await self._server_manager.stop(force=force)

    async def server_status(self) -> DoltServerInfo:
        """Check SQL server status.

        Returns:
            DoltServerInfo with current status
        """
        return await self._server_manager.status()

    # ==========================================================================
    # Remote Operations (Delegated)
    # ==========================================================================

    async def remote_add(self, name, url):
        """Add a remote."""
        return await self._remote_ops.remote_add(name, url)

    async def remote_remove(self, name):
        """Remove a remote."""
        return await self._remote_ops.remote_remove(name)

    async def remote_list(self):
        """List remotes."""
        return await self._remote_ops.remote_list()

    async def push(self, remote="origin", branch=None, force=False, set_upstream=False):
        """Push to remote."""
        return await self._remote_ops.push(remote, branch, force, set_upstream)

    async def pull(self, remote="origin", branch=None):
        """Pull from remote."""
        return await self._remote_ops.pull(remote, branch)

    async def fetch(self, remote="origin"):
        """Fetch from remote."""
        return await self._remote_ops.fetch(remote)

    async def clone(self, url, target_path=None, branch=None):
        """Clone a remote repository."""
        return await self._remote_ops.clone(url, target_path, branch)

    # ==========================================================================
    # Cleanup
    # ==========================================================================

    async def close(self) -> None:
        """Clean up resources.

        Stops the SQL server if running.
        """
        if self._server_manager:
            await self._server_manager.stop()

    async def __aenter__(self) -> "DoltClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
