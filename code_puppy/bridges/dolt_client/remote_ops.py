"""Remote operations for Dolt client."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Union

if TYPE_CHECKING:
    from .client import DoltClient


class RemoteOperations:
    """Handles remote-related operations for DoltClient."""

    def __init__(self, client: "DoltClient"):
        self._client = client

    async def remote_add(self, name: str, url: str) -> str:
        """Add a remote.

        Args:
            name: Remote name
            url: Remote URL

        Returns:
            Command output
        """
        result = await self._client._run_cmd(
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
        result = await self._client._run_cmd(
            ["remote", "remove", name],
            json_output=False,
        )
        return result.strip()

    async def remote_list(self) -> List[Dict[str, str]]:
        """List remotes.

        Returns:
            List of remote info dicts
        """
        result = await self._client._run_cmd(["remote", "-v"], json_output=False)
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

        result = await self._client._run_cmd(args, json_output=False)
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

        result = await self._client._run_cmd(args, json_output=False)
        return result.strip()

    async def fetch(self, remote: str = "origin") -> str:
        """Fetch from remote.

        Args:
            remote: Remote name

        Returns:
            Fetch output
        """
        result = await self._client._run_cmd(
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

        result = await self._client._run_cmd(args, json_output=False, check_init=False)
        return result.strip()
