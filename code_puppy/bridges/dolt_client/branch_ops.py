"""Branch operations for Dolt client."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from .exceptions import DoltBranchError, DoltError
from .models import DoltBranch, DoltMergeResult

if TYPE_CHECKING:
    from .client import DoltClient


class BranchOperations:
    """Handles branch-related operations for DoltClient."""

    def __init__(self, client: "DoltClient"):
        self._client = client

    async def list_branches(self) -> List[DoltBranch]:
        """List all branches.

        Returns:
            List of DoltBranch objects
        """
        result = await self._client._run_cmd(["branch", "--verbose"], json_output=False)
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

    async def create_branch(
        self,
        name: str,
        from_branch: Optional[str] = None,
        copy: bool = False,
    ) -> DoltBranch:
        """Create a new branch.

        Args:
            name: Branch name
            from_branch: Source branch (default: current)
            copy: Copy branch

        Returns:
            Newly created DoltBranch

        Raises:
            DoltBranchError: If branch creation fails
        """
        args = ["branch"]
        if copy:
            args.append("-c")
        if from_branch:
            args.extend([name, from_branch])
        else:
            args.append(name)

        try:
            await self._client._run_cmd(args, json_output=False)
        except DoltError as e:
            raise DoltBranchError(
                f"Failed to create branch '{name}': {e}", command=e.command
            )

        # Return new branch info
        branches = await self.list_branches()
        for b in branches:
            if b.name == name:
                return b
        return DoltBranch(name=name, hash="", current=False)

    async def delete_branch(
        self,
        name: str,
        force: bool = False,
    ) -> str:
        """Delete a branch.

        Args:
            name: Branch name to delete
            force: Force delete (even if not merged)

        Returns:
            Status message

        Raises:
            DoltBranchError: If branch deletion fails
        """
        flag = "-D" if force else "-d"
        try:
            result = await self._client._run_cmd(
                ["branch", flag, name],
                json_output=False,
            )
            return result.strip()
        except DoltError as e:
            raise DoltBranchError(
                f"Failed to delete branch '{name}': {e}", command=e.command
            )

    async def rename_branch(self, name: str) -> str:
        """Rename the current branch.

        Args:
            name: New branch name

        Returns:
            Status message
        """
        result = await self._client._run_cmd(
            ["branch", "-m", name],
            json_output=False,
        )
        return result.strip()

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

        result = await self._client._run_cmd(args, json_output=False)
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
            result = await self._client._run_cmd(args, json_output=False)
            return DoltMergeResult(
                success=True,
                message=result.strip(),
            )
        except DoltError as e:
            # Check if there are conflicts
            if "conflict" in e.stderr.lower():
                # Get conflicting tables
                status_result = await self._client._run_cmd(
                    ["status"], json_output=False
                )
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
