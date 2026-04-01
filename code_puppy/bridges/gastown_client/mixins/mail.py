"""Mail operations mixin for GastownClient."""

from typing import Optional, Union

from code_puppy.bridges.gastown_client.exceptions import GastownParseError
from code_puppy.bridges.gastown_client.helpers import (
    coerce_enum,
    parse_model_list,
    validate_options,
)
from code_puppy.bridges.gastown_client.models import Mail, MailPriority, MailStatus

_MAIL_SEND_OPTIONS: frozenset[str] = frozenset(
    {
        "cc_agents",
        "thread_id",
        "in_reply_to",
        "rig_id",
    }
)


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
            **options: Additional options (cc_agents, thread_id, in_reply_to, rig_id).

        Returns:
            Sent Mail instance.
        """
        validate_options(options, _MAIL_SEND_OPTIONS, "mail_send")
        priority = coerce_enum(priority, MailPriority, "priority")

        args = ["mail", "send"]
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

        args.append("--")
        args.append(to_agent)

        result = await self._run_command(args)

        if result.parsed_output:
            return Mail.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to send mail to {to_agent}")

    async def mail_list(
        self,
        agent_id: Optional[str] = None,
        status: Optional[Union[MailStatus, str]] = None,
    ) -> list[Mail]:
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

        return parse_model_list(result, Mail, "mail")

    async def mail_read(self, mail_id: str) -> Mail:
        """Read a mail message.

        Args:
            mail_id: Mail ID to read.

        Returns:
            Mail instance.
        """
        result = await self._run_command(["mail", "read", "--", mail_id])

        if result.parsed_output:
            return Mail.model_validate(result.parsed_output)

        raise GastownParseError(f"Failed to read mail {mail_id}")
