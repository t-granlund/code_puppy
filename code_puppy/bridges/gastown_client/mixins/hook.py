"""Hook management mixin for GastownClient."""

from typing import Optional, Union

from code_puppy.bridges.gastown_client.exceptions import GastownParseError
from code_puppy.bridges.gastown_client.helpers import parse_model_list
from code_puppy.bridges.gastown_client.models import Hook, HookState


class HookMixin:
    """Hook management operations."""

    async def hook_list(
        self,
        rig_id: Optional[str] = None,
        state: Optional[Union[HookState, str]] = None,
    ) -> list[Hook]:
        """List all hooks.

        Args:
            rig_id: Filter by rig.
            state: Filter by state.

        Returns:
            List of Hook instances.
        """
        args = ["hook", "list"]

        if rig_id:
            args.extend(["--rig", rig_id])

        if state:
            if isinstance(state, HookState):
                state = state.value
            args.extend(["--state", state])

        result = await self._run_command(args)

        return parse_model_list(result, Hook, "hooks")

    async def hook_create(
        self,
        name: str,
        rig_id: str,
        base_branch: str = "main",
        agent_id: Optional[str] = None,
        **options,
    ) -> Hook:
        """Create a new hook.

        Args:
            name: Hook name.
            rig_id: Associated rig ID.
            base_branch: Base branch for the worktree.
            agent_id: Agent to assign to this hook.
            **options: Additional options.

        Returns:
            Created Hook instance.
        """
        args = ["hook", "create"]
        args.extend(["--rig", rig_id])
        args.extend(["--branch", base_branch])

        if agent_id:
            args.extend(["--agent", agent_id])

        for key, value in options.items():
            if value is True:
                args.append(f"--{key.replace('_', '-')}")
            elif value is not None:
                args.extend([f"--{key.replace('_', '-')}", str(value)])

        args.append("--")
        args.append(name)

        result = await self._run_command(args)

        if result.parsed_output:
            return Hook.model_validate(result.parsed_output)

        raise GastownParseError("Failed to parse hook create response")

    async def hook_status(self, name_or_id: str) -> Hook:
        """Get hook status.

        Args:
            name_or_id: Hook name or ID.

        Returns:
            Hook instance with current status.
        """
        result = await self._run_command(["hook", "status", "--", name_or_id])

        if result.parsed_output:
            return Hook.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to parse hook status for {name_or_id}")

    async def hook_archive(self, name_or_id: str) -> Hook:
        """Archive a hook.

        Args:
            name_or_id: Hook name or ID to archive.

        Returns:
            Updated Hook instance.
        """
        result = await self._run_command(["hook", "archive", "--", name_or_id])

        if result.parsed_output:
            return Hook.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to parse hook archive for {name_or_id}")
