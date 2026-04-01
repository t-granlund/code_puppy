"""Convoy management mixin for GastownClient."""

from typing import Optional, Union

from code_puppy.bridges.gastown_client.exceptions import GastownParseError
from code_puppy.bridges.gastown_client.helpers import (
    coerce_enum,
    parse_model_list,
    validate_options,
)
from code_puppy.bridges.gastown_client.models import Convoy, ConvoyPriority, ConvoyState

_CONVOY_CREATE_OPTIONS: frozenset[str] = frozenset(
    {
        "auto_close",
        "max_stall_minutes",
    }
)


class ConvoyMixin:
    """Convoy management operations."""

    async def convoy_create(
        self,
        name: str,
        priority: Union[ConvoyPriority, str] = ConvoyPriority.NORMAL,
        bead_ids: Optional[list[str]] = None,
        rig_id: Optional[str] = None,
        notify_human: bool = False,
        require_human_review: bool = False,
        is_mountain: bool = False,
        **options,
    ) -> Convoy:
        """Create a new convoy.

        Args:
            name: Convoy name.
            priority: Priority level.
            bead_ids: List of bead/issue IDs to include.
            rig_id: Associated rig ID.
            notify_human: Whether to notify human on completion.
            require_human_review: Whether to require human review.
            is_mountain: Enable mountain mode for autonomous execution.
            **options: Additional options (auto_close, max_stall_minutes).

        Returns:
            Created Convoy instance.
        """
        validate_options(options, _CONVOY_CREATE_OPTIONS, "convoy_create")
        priority = coerce_enum(priority, ConvoyPriority, "priority")

        args = ["convoy", "create"]
        args.extend(["--priority", priority.value])

        if bead_ids:
            for bead_id in bead_ids:
                args.extend(["--bead", bead_id])

        if rig_id:
            args.extend(["--rig", rig_id])

        if notify_human:
            args.append("--notify-human")

        if require_human_review:
            args.append("--require-review")

        if is_mountain:
            args.append("--mountain")

        for key, value in options.items():
            if value is True:
                args.append(f"--{key.replace('_', '-')}")
            elif value is not None:
                args.extend([f"--{key.replace('_', '-')}", str(value)])

        args.append("--")
        args.append(name)

        result = await self._run_command(args)

        if result.parsed_output:
            return Convoy.model_validate(result.parsed_output)

        raise GastownParseError("Failed to parse convoy create response")

    async def convoy_list(
        self,
        state: Optional[Union[ConvoyState, str]] = None,
        rig_id: Optional[str] = None,
    ) -> list[Convoy]:
        """List all convoys.

        Args:
            state: Filter by state.
            rig_id: Filter by rig.

        Returns:
            List of Convoy instances.
        """
        args = ["convoy", "list"]

        if state:
            if isinstance(state, ConvoyState):
                state = state.value
            args.extend(["--state", state])

        if rig_id:
            args.extend(["--rig", rig_id])

        result = await self._run_command(args)

        return parse_model_list(result, Convoy, "convoys")

    async def convoy_status(self, name_or_id: str) -> Convoy:
        """Get convoy status.

        Args:
            name_or_id: Convoy name or ID.

        Returns:
            Convoy instance with current status.
        """
        result = await self._run_command(["convoy", "status", "--", name_or_id])

        if result.parsed_output:
            return Convoy.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to parse convoy status for {name_or_id}")

    async def convoy_archive(self, name_or_id: str) -> Convoy:
        """Archive a convoy.

        Args:
            name_or_id: Convoy name or ID to archive.

        Returns:
            Updated Convoy instance.
        """
        result = await self._run_command(["convoy", "archive", "--", name_or_id])

        if result.parsed_output:
            return Convoy.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to parse convoy archive for {name_or_id}")

    async def convoy_add_bead(self, convoy_id: str, bead_id: str) -> Convoy:
        """Add a bead to a convoy.

        Args:
            convoy_id: Convoy ID.
            bead_id: Bead ID to add.

        Returns:
            Updated Convoy instance.
        """
        result = await self._run_command(["convoy", "add", "--", convoy_id, bead_id])

        if result.parsed_output:
            return Convoy.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to add bead {bead_id} to convoy {convoy_id}")

    async def convoy_dispatch(self, convoy_id: str) -> Convoy:
        """Dispatch a convoy (start execution).

        Args:
            convoy_id: Convoy ID to dispatch.

        Returns:
            Updated Convoy instance.
        """
        result = await self._run_command(["convoy", "dispatch", "--", convoy_id])

        if result.parsed_output:
            return Convoy.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to dispatch convoy {convoy_id}")
