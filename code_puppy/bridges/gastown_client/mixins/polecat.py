"""Polecat (agent) operations mixin for GastownClient."""

from typing import Optional, Union

from code_puppy.bridges.gastown_client.exceptions import GastownParseError
from code_puppy.bridges.gastown_client.helpers import coerce_enum, parse_model_list
from code_puppy.bridges.gastown_client.models import Polecat, PolecatRole, PolecatState


class PolecatMixin:
    """Polecat (agent) lifecycle operations."""

    async def polecat_spawn(
        self,
        name: str,
        role: Union[PolecatRole, str] = PolecatRole.POLECAT,
        rig_id: Optional[str] = None,
        specialty: Optional[str] = None,
        runtime: str = "claude",
        convoy_id: Optional[str] = None,
        bead_id: Optional[str] = None,
        **options,
    ) -> Polecat:
        """Spawn a new polecat (agent).

        Args:
            name: Polecat name.
            role: Agent role.
            rig_id: Associated rig ID.
            specialty: Agent specialty (e.g., "rust", "frontend").
            runtime: Runtime provider (claude, codex, cursor).
            convoy_id: Convoy to assign to.
            bead_id: Bead to work on.
            **options: Additional options.

        Returns:
            Created Polecat instance.
        """
        role = coerce_enum(role, PolecatRole, "role")

        args = ["polecat", "spawn"]
        args.extend(["--role", role.value])

        if rig_id:
            args.extend(["--rig", rig_id])

        if specialty:
            args.extend(["--specialty", specialty])

        if runtime:
            args.extend(["--runtime", runtime])

        if convoy_id:
            args.extend(["--convoy", convoy_id])

        if bead_id:
            args.extend(["--bead", bead_id])

        for key, value in options.items():
            if value is True:
                args.append(f"--{key.replace('_', '-')}")
            elif value is not None:
                args.extend([f"--{key.replace('_', '-')}", str(value)])

        args.append("--")
        args.append(name)

        result = await self._run_command(args)

        if result.parsed_output:
            return Polecat.model_validate(result.parsed_output)

        raise GastownParseError("Failed to parse polecat spawn response")

    async def polecat_status(self, name_or_id: str) -> Polecat:
        """Get polecat status.

        Args:
            name_or_id: Polecat name or ID.

        Returns:
            Polecat instance with current status.
        """
        result = await self._run_command(["polecat", "status", "--", name_or_id])

        if result.parsed_output:
            return Polecat.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to parse polecat status for {name_or_id}")

    async def polecat_list(
        self,
        state: Optional[Union[PolecatState, str]] = None,
        rig_id: Optional[str] = None,
    ) -> list[Polecat]:
        """List all polecats.

        Args:
            state: Filter by state.
            rig_id: Filter by rig.

        Returns:
            List of Polecat instances.
        """
        args = ["polecat", "list"]

        if state:
            if isinstance(state, PolecatState):
                state = state.value
            args.extend(["--state", state])

        if rig_id:
            args.extend(["--rig", rig_id])

        result = await self._run_command(args)

        return parse_model_list(result, Polecat, "polecats")

    async def polecat_archive(self, name_or_id: str) -> Polecat:
        """Archive a polecat.

        Args:
            name_or_id: Polecat name or ID to archive.

        Returns:
            Updated Polecat instance.
        """
        result = await self._run_command(["polecat", "archive", "--", name_or_id])

        if result.parsed_output:
            return Polecat.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to parse polecat archive for {name_or_id}")

    async def polecat_pause(self, name_or_id: str) -> Polecat:
        """Pause a polecat.

        Args:
            name_or_id: Polecat name or ID.

        Returns:
            Updated Polecat instance.
        """
        result = await self._run_command(["polecat", "pause", "--", name_or_id])

        if result.parsed_output:
            return Polecat.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to pause polecat {name_or_id}")

    async def polecat_resume(self, name_or_id: str) -> Polecat:
        """Resume a paused polecat.

        Args:
            name_or_id: Polecat name or ID.

        Returns:
            Updated Polecat instance.
        """
        result = await self._run_command(["polecat", "resume", "--", name_or_id])

        if result.parsed_output:
            return Polecat.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to resume polecat {name_or_id}")
