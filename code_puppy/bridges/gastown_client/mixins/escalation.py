"""Escalation handling mixin for GastownClient."""

from typing import Optional, Union

from code_puppy.bridges.gastown_client.exceptions import GastownParseError
from code_puppy.bridges.gastown_client.helpers import coerce_enum, parse_model_list
from code_puppy.bridges.gastown_client.models import Escalation, EscalationSeverity


class EscalationMixin:
    """Escalation handling operations."""

    async def escalate(
        self,
        issue_id: str,
        severity: Union[EscalationSeverity, str],
        message: str,
        from_agent: Optional[str] = None,
    ) -> Escalation:
        """Escalate an issue.

        Args:
            issue_id: Issue/Bead ID being escalated.
            severity: Escalation severity level.
            message: Escalation message/description.
            from_agent: Agent escalating the issue.

        Returns:
            Created Escalation instance.

        Example:
            ```python
            escalation = await client.escalate(
                issue_id="bd-42",
                severity="high",
                message="Agent stuck on complex refactoring",
                from_agent="polecat-1"
            )
            ```
        """
        severity = coerce_enum(severity, EscalationSeverity, "severity")

        args = ["escalate"]
        args.extend(["--severity", severity.value])
        args.extend(["--message", message])

        if from_agent:
            args.extend(["--from", from_agent])

        args.append("--")
        args.append(issue_id)

        result = await self._run_command(args)

        if result.parsed_output:
            return Escalation.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to parse escalation for {issue_id}")

    async def escalation_list(
        self,
        severity: Optional[Union[EscalationSeverity, str]] = None,
        resolved: Optional[bool] = None,
    ) -> list[Escalation]:
        """List escalations.

        Args:
            severity: Filter by severity.
            resolved: Filter by resolved status.

        Returns:
            List of Escalation instances.
        """
        args = ["escalation", "list"]

        if severity:
            if isinstance(severity, EscalationSeverity):
                severity = severity.value
            args.extend(["--severity", severity])

        if resolved is not None:
            args.append("--resolved" if resolved else "--unresolved")

        result = await self._run_command(args)

        return parse_model_list(result, Escalation, "escalations")

    async def escalation_resolve(
        self,
        escalation_id: str,
        resolution_notes: Optional[str] = None,
        resolved_by: Optional[str] = None,
    ) -> Escalation:
        """Resolve an escalation.

        Args:
            escalation_id: Escalation ID to resolve.
            resolution_notes: Notes about the resolution.
            resolved_by: Agent resolving the escalation.

        Returns:
            Updated Escalation instance.
        """
        args = ["escalation", "resolve"]

        if resolution_notes:
            args.extend(["--notes", resolution_notes])

        if resolved_by:
            args.extend(["--by", resolved_by])

        args.append("--")
        args.append(escalation_id)

        result = await self._run_command(args)

        if result.parsed_output:
            return Escalation.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to resolve escalation {escalation_id}")
