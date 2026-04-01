"""Mail operations mixin for GastownClient."""

from typing import List, Optional, Union

from code_puppy.bridges.gastown_client.exceptions import GastownError, GastownParseError
from code_puppy.bridges.gastown_client.models import Mail, MailPriority, MailStatus


class MailMixin:
    """Mail operations."""

    async def mail_send(
        self,
        to_agent: str,
        subject: str,
        body: str,
        from_agent: Optional[str] = None,
        priority: Union[MailPriority, str] = MailPriority.NORMAL,
        bead_id: Optional[str] = None,
        convoy_id: Optional[str] = None,
        **options,
    ) -> Mail:
        """Send mail to an agent.

        Args:
            to_agent: Recipient agent ID.
            subject: Mail subject.
            body: Mail body.
            from_agent: Sender agent ID.
            priority: Mail priority.
            bead_id: Related bead ID.
            convoy_id: Related convoy ID.
            **options: Additional options.

        Returns:
            Sent Mail instance.
        """
        if isinstance(priority, str):
            try:
                priority = MailPriority(priority.lower())
            except ValueError:
                raise GastownError(f"Invalid priority: {priority}")

        args = ["mail", "send", to_agent]
        args.extend(["--subject", subject])
        args.extend(["--body", body])

        if from_agent:
            args.extend(["--from", from_agent])

        if priority != MailPriority.NORMAL:
            args.extend(["--priority", priority.value])

        if bead_id:
            args.extend(["--bead", bead_id])

        if convoy_id:
            args.extend(["--convoy", convoy_id])

        result = await self._run_command(args)

        if result.parsed_output:
            return Mail.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to send mail to {to_agent}")

    async def mail_list(
        self,
        agent_id: Optional[str] = None,
        status: Optional[Union[MailStatus, str]] = None,
    ) -> List[Mail]:
        """List mail messages.

        Args:
            agent_id: Filter by agent (inbox).
            status: Filter by status.

        Returns:
            List of Mail instances.
        """
        args = ["mail", "list"]

        if agent_id:
            args.extend(["--agent", agent_id])

        if status:
            if isinstance(status, MailStatus):
                status = status.value
            args.extend(["--status", status])

        result = await self._run_command(args)

        if result.parsed_output:
            if isinstance(result.parsed_output, list):
                return [Mail.model_validate(item) for item in result.parsed_output]
            elif "mail" in result.parsed_output:
                return [
                    Mail.model_validate(item) for item in result.parsed_output["mail"]
                ]

        return []

    async def mail_read(self, mail_id: str) -> Mail:
        """Read a mail message.

        Args:
            mail_id: Mail ID to read.

        Returns:
            Mail instance.
        """
        result = await self._run_command(["mail", "read", mail_id])

        if result.parsed_output:
            return Mail.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to read mail {mail_id}")
