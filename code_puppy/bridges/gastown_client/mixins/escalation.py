"""Escalation handling mixin for GastownClient."""

from typing import List, Optional, Union

from code_puppy.bridges.gastown_client.exceptions import GastownError, GastownParseError
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
        if isinstance(severity, str):
            try:
                severity = EscalationSeverity(severity.lower())
            except ValueError:
                raise GastownError(f"Invalid severity: {severity}")

        args = ["escalate", issue_id]
        args.extend(["--severity", severity.value])
        args.extend(["--message", message])

        if from_agent:
            args.extend(["--from", from_agent])

        result = await self._run_command(args)

        if result.parsed_output:
            return Escalation.model_validate(result.parsed_output)

        return Escalation(
            id="",
            issue_id=issue_id,
            severity=severity,
            message=message,
            from_agent=from_agent,
        )

    async def escalation_list(
        self,
        severity: Optional[Union[EscalationSeverity, str]] = None,
        resolved: Optional[bool] = None,
    ) -> List[Escalation]:
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

        if result.parsed_output:
            if isinstance(result.parsed_output, list):
                return [
                    Escalation.model_validate(item) for item in result.parsed_output
                ]
            elif "escalations" in result.parsed_output:
                return [
                    Escalation.model_validate(item)
                    for item in result.parsed_output["escalations"]
                ]

        return []

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
        args = ["escalation", "resolve", escalation_id]

        if resolution_notes:
            args.extend(["--notes", resolution_notes])

        if resolved_by:
            args.extend(["--by", resolved_by])

        result = await self._run_command(args)

        if result.parsed_output:
            return Escalation.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to resolve escalation {escalation_id}")
