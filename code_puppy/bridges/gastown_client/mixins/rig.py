"""Rig management mixin for GastownClient."""

from typing import List, Optional

from code_puppy.bridges.gastown_client.exceptions import GastownParseError
from code_puppy.bridges.gastown_client.models import Rig, RigState


class RigMixin:
    """Rig management operations."""

    async def rig_list(self) -> List[Rig]:
        """List all rigs.

        Returns:
            List of Rig instances.
        """
        result = await self._run_command(["rig", "list"])

        if result.parsed_output:
            if isinstance(result.parsed_output, list):
                return [Rig.model_validate(item) for item in result.parsed_output]
            elif "rigs" in result.parsed_output:
                return [
                    Rig.model_validate(item) for item in result.parsed_output["rigs"]
                ]

        return []

    async def rig_status(self, name_or_id: str) -> Rig:
        """Get rig status.

        Args:
            name_or_id: Rig name or ID.

        Returns:
            Rig instance with current status.
        """
        result = await self._run_command(["rig", "status", name_or_id])

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
        args = ["rig", "create", name]

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

        result = await self._run_command(args)

        if result.parsed_output:
            return Rig.model_validate(result.parsed_output)

        return Rig(
            id="",
            name=name,
            repo_url=repo_url,
            local_path=local_path,
            runtime_provider=runtime_provider,
        )

    async def rig_archive(self, name_or_id: str) -> Rig:
        """Archive a rig.

        Args:
            name_or_id: Rig name or ID to archive.

        Returns:
            Updated Rig instance.
        """
        result = await self._run_command(["rig", "archive", name_or_id])

        if result.parsed_output:
            return Rig.model_validate(result.parsed_output)

        return Rig(
            id=name_or_id,
            name=name_or_id,
            state=RigState.ARCHIVED,
        )
