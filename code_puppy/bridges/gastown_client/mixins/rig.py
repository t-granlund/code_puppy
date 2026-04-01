"""Rig management mixin for GastownClient."""

from typing import Optional

from code_puppy.bridges.gastown_client.exceptions import GastownParseError
from code_puppy.bridges.gastown_client.helpers import parse_model_list
from code_puppy.bridges.gastown_client.models import Rig


class RigMixin:
    """Rig management operations."""

    async def rig_list(self) -> list[Rig]:
        """List all rigs.

        Returns:
            List of Rig instances.
        """
        result = await self._run_command(["rig", "list"])

        return parse_model_list(result, Rig, "rigs")

    async def rig_status(self, name_or_id: str) -> Rig:
        """Get rig status.

        Args:
            name_or_id: Rig name or ID.

        Returns:
            Rig instance with current status.
        """
        result = await self._run_command(["rig", "status", "--", name_or_id])

        if result.parsed_output:
            return Rig.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to parse rig status for {name_or_id}")

    async def rig_create(
        self,
        name: str,
        repo_url: Optional[str] = None,
        local_path: Optional[str] = None,
        runtime_provider: str = "claude",
        **options,
    ) -> Rig:
        """Create a new rig.

        Args:
            name: Rig name.
            repo_url: Repository URL.
            local_path: Local path to repository.
            runtime_provider: Default runtime provider.
            **options: Additional options.

        Returns:
            Created Rig instance.
        """
        args = ["rig", "create"]

        if repo_url:
            args.extend(["--repo", repo_url])

        if local_path:
            args.extend(["--path", local_path])

        if runtime_provider:
            args.extend(["--runtime", runtime_provider])

        for key, value in options.items():
            if value is True:
                args.append(f"--{key.replace('_', '-')}")
            elif value is not None:
                args.extend([f"--{key.replace('_', '-')}", str(value)])

        args.append("--")
        args.append(name)

        result = await self._run_command(args)

        if result.parsed_output:
            return Rig.model_validate(result.parsed_output)

        raise GastownParseError("Failed to parse rig create response")

    async def rig_archive(self, name_or_id: str) -> Rig:
        """Archive a rig.

        Args:
            name_or_id: Rig name or ID to archive.

        Returns:
            Updated Rig instance.
        """
        result = await self._run_command(["rig", "archive", "--", name_or_id])

        if result.parsed_output:
            return Rig.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to parse rig archive for {name_or_id}")
