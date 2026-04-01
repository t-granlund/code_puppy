"""Commit operations for Dolt client."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Union

from .models import DoltCommit

if TYPE_CHECKING:
    from .client import DoltClient


class CommitOperations:
    """Handles commit-related operations for DoltClient."""

    def __init__(self, client: "DoltClient"):
        self._client = client

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

        result = await self._client._run_cmd(args, json_output=False)
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

        await self._client._run_cmd(args, json_output=False)

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

        result = await self._client._run_cmd(args, json_output=False)

        commits = []
        current_commit = {}

        for line in result.strip().split("\n"):
            line = line.strip()
            if line.startswith("commit "):
                if current_commit:
                    commits.append(self._client._parse_commit(current_commit))
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
            elif (
                line
                and not line.startswith("Merge:")
                and "message" not in current_commit
            ):
                current_commit["message"] = line

        if current_commit:
            commits.append(self._client._parse_commit(current_commit))

        return commits

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

        result = await self._client._run_cmd(args, json_output=False)
        return result.strip()
