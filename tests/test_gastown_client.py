"""Tests for gastown_client package."""

import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from code_puppy.bridges.gastown_client import (
    GastownClient,
    GastownConfig,
    GastownError,
    GastownNotInstalledError,
    GastownCommandError,
    GastownParseError,
)
from code_puppy.bridges.gastown_client.models import (
    CommandResult,
    Convoy,
    ConvoyPriority,
    ConvoyState,
    Polecat,
    PolecatRole,
    PolecatState,
    Rig,
    RigState,
    Hook,
    HookState,
    Mail,
    MailPriority,
    MailStatus,
    Escalation,
    EscalationSeverity,
    _utcnow,
)
from code_puppy.bridges.gastown_client.helpers import coerce_enum, parse_model_list


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def gastown_config():
    return GastownConfig(gt_path="gt", default_timeout=5.0)


@pytest.fixture
def client(gastown_config):
    return GastownClient(config=gastown_config)


@pytest.fixture
def mock_process():
    proc = AsyncMock()
    proc.returncode = 0
    proc.communicate = AsyncMock(return_value=(b"{}", b""))
    proc.kill = MagicMock()
    proc.wait = AsyncMock()
    return proc


def make_result(parsed_output=None, success=True, stdout="", stderr=""):
    return CommandResult(
        command="gt test",
        exit_code=0 if success else 1,
        stdout=stdout or json.dumps(parsed_output or {}),
        stderr=stderr,
        parsed_output=parsed_output,
        success=success,
    )


# ============================================================================
# Test Helpers
# ============================================================================


class TestUtcNow:
    def test_returns_utc_datetime(self):
        result = _utcnow()
        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc


class TestCoerceEnum:
    def test_string_to_enum(self):
        assert coerce_enum("high", ConvoyPriority, "p") == ConvoyPriority.HIGH

    def test_case_insensitive(self):
        assert coerce_enum("HIGH", ConvoyPriority, "p") == ConvoyPriority.HIGH

    def test_enum_passthrough(self):
        assert (
            coerce_enum(ConvoyPriority.LOW, ConvoyPriority, "p") == ConvoyPriority.LOW
        )

    def test_invalid_raises(self):
        with pytest.raises(GastownError, match="Invalid p: banana"):
            coerce_enum("banana", ConvoyPriority, "p")

    def test_all_enum_types(self):
        assert coerce_enum("mayor", PolecatRole, "r") == PolecatRole.MAYOR
        assert (
            coerce_enum("critical", EscalationSeverity, "s")
            == EscalationSeverity.CRITICAL
        )
        assert coerce_enum("urgent", MailPriority, "p") == MailPriority.URGENT


class TestParseModelList:
    def test_direct_list(self):
        r = make_result(
            parsed_output=[
                {"id": "c1", "name": "convoy1", "state": "forming"},
            ]
        )
        assert len(parse_model_list(r, Convoy, "convoys")) == 1

    def test_keyed_dict(self):
        r = make_result(
            parsed_output={"convoys": [{"id": "c1", "name": "t", "state": "forming"}]}
        )
        assert len(parse_model_list(r, Convoy, "convoys")) == 1

    def test_returns_empty_on_none(self):
        r = make_result(parsed_output=None)
        assert parse_model_list(r, Convoy, "convoys") == []

    def test_returns_empty_on_wrong_key(self):
        r = make_result(parsed_output={"other": []})
        assert parse_model_list(r, Convoy, "convoys") == []


# ============================================================================
# Test Models
# ============================================================================


class TestModels:
    def test_convoy(self):
        c = Convoy(id="c1", name="test", state=ConvoyState.FORMING)
        assert c.priority == ConvoyPriority.NORMAL
        assert c.bead_ids == []
        assert c.created_at.tzinfo == timezone.utc

    def test_polecat(self):
        p = Polecat(id="p1", name="worker")
        assert p.role == PolecatRole.POLECAT
        assert p.state == PolecatState.IDLE

    def test_rig(self):
        r = Rig(id="r1", name="project")
        assert r.state == RigState.INITIALIZING

    def test_hook(self):
        h = Hook(id="h1", name="worktree")
        assert h.state == HookState.CREATING

    def test_mail(self):
        m = Mail(id="m1", from_agent="a1", to_agent="a2")
        assert m.status == MailStatus.DRAFT

    def test_escalation(self):
        e = Escalation(
            id="e1", issue_id="bd-1", severity=EscalationSeverity.HIGH, message="stuck"
        )
        assert e.from_agent is None

    def test_command_result_with_list(self):
        r = CommandResult(
            command="gt t",
            exit_code=0,
            stdout="[]",
            stderr="",
            parsed_output=[{"a": 1}],
        )
        assert isinstance(r.parsed_output, list)


# ============================================================================
# Test Exceptions
# ============================================================================


class TestExceptions:
    def test_hierarchy(self):
        assert issubclass(GastownNotInstalledError, GastownError)
        assert issubclass(GastownCommandError, GastownError)
        assert issubclass(GastownParseError, GastownError)

    def test_command_error_attrs(self):
        err = GastownCommandError(
            message="fail", command="gt x", exit_code=1, stderr="oops"
        )
        assert err.command == "gt x"
        assert err.exit_code == 1
        assert err.stderr == "oops"


# ============================================================================
# Test Client Core
# ============================================================================


class TestClientInit:
    def test_default_config(self):
        c = GastownClient()
        assert c.config.gt_path == "gt"
        assert c.config.default_timeout == 30.0

    def test_custom_config(self):
        c = GastownClient(
            config=GastownConfig(gt_path="/usr/bin/gt", default_timeout=60.0)
        )
        assert c.config.gt_path == "/usr/bin/gt"


class TestFindGt:
    async def test_finds_gt(self, client):
        with patch("shutil.which", return_value="/usr/bin/gt"):
            assert await client._find_gt() == "/usr/bin/gt"

    async def test_caches_result(self, client):
        with patch("shutil.which", return_value="/usr/bin/gt") as m:
            await client._find_gt()
            await client._find_gt()
            m.assert_called_once()

    async def test_raises_not_installed(self, client):
        with patch("shutil.which", return_value=None):
            with pytest.raises(GastownNotInstalledError):
                await client._find_gt()


class TestRunCommand:
    async def test_successful_json(self, client, mock_process):
        data = json.dumps({"id": "c1"}).encode()
        mock_process.communicate = AsyncMock(return_value=(data, b""))
        with (
            patch("shutil.which", return_value="/usr/bin/gt"),
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
        ):
            result = await client._run_command(["convoy", "list"])
            assert result.success
            assert result.parsed_output == {"id": "c1"}

    async def test_nonzero_exit_raises(self, client, mock_process):
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"err"))
        with (
            patch("shutil.which", return_value="/usr/bin/gt"),
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
        ):
            with pytest.raises(GastownCommandError):
                await client._run_command(["fail"])

    async def test_timeout_kills_process(self, client, mock_process):
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError)
        with (
            patch("shutil.which", return_value="/usr/bin/gt"),
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("asyncio.wait_for", side_effect=asyncio.TimeoutError),
        ):
            with pytest.raises(GastownCommandError, match="timed out"):
                await client._run_command(["slow"])
            mock_process.kill.assert_called_once()

    async def test_invalid_json_returns_none(self, client, mock_process):
        mock_process.communicate = AsyncMock(return_value=(b"not json", b""))
        with (
            patch("shutil.which", return_value="/usr/bin/gt"),
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
        ):
            result = await client._run_command(["test"])
            assert result.parsed_output is None

    async def test_json_flag_appended(self, client, mock_process):
        mock_process.communicate = AsyncMock(return_value=(b"{}", b""))
        with (
            patch("shutil.which", return_value="/usr/bin/gt"),
            patch("asyncio.create_subprocess_exec", return_value=mock_process) as m,
        ):
            await client._run_command(["test"])
            assert "--json" in m.call_args[0]

    async def test_no_json_flag_when_disabled(self, client, mock_process):
        mock_process.communicate = AsyncMock(return_value=(b"out", b""))
        with (
            patch("shutil.which", return_value="/usr/bin/gt"),
            patch("asyncio.create_subprocess_exec", return_value=mock_process) as m,
        ):
            await client._run_command(["--version"], capture_json=False)
            assert "--json" not in m.call_args[0]


# ============================================================================
# Test Convoy Mixin
# ============================================================================


class TestConvoyMixin:
    async def test_create(self, client):
        d = {"id": "c1", "name": "t", "state": "forming", "priority": "high"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            c = await client.convoy_create("t", priority="high")
            assert isinstance(c, Convoy)

    async def test_create_all_options(self, client):
        d = {"id": "c1", "name": "t", "state": "forming"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ) as m:
            await client.convoy_create(
                "t",
                priority=ConvoyPriority.HIGH,
                bead_ids=["b1"],
                rig_id="r1",
                notify_human=True,
                require_human_review=True,
                is_mountain=True,
            )
            args = m.call_args[0][0]
            assert "--priority" in args
            assert "--notify-human" in args
            assert "--" in args  # sentinel

    async def test_create_parse_failure(self, client):
        with patch.object(
            client,
            "_run_command",
            new_callable=AsyncMock,
            return_value=make_result(None),
        ):
            with pytest.raises(GastownParseError):
                await client.convoy_create("t")

    async def test_list(self, client):
        d = [{"id": "c1", "name": "t", "state": "active"}]
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert len(await client.convoy_list()) == 1

    async def test_list_with_filters(self, client):
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result([])
        ) as m:
            await client.convoy_list(state=ConvoyState.ACTIVE, rig_id="r1")
            args = m.call_args[0][0]
            assert "--state" in args and "--rig" in args

    async def test_status(self, client):
        d = {"id": "c1", "name": "t", "state": "active"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert (await client.convoy_status("c1")).state == ConvoyState.ACTIVE

    async def test_archive(self, client):
        d = {"id": "c1", "name": "t", "state": "archived"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert (await client.convoy_archive("c1")).state == ConvoyState.ARCHIVED

    async def test_add_bead(self, client):
        d = {"id": "c1", "name": "t", "state": "forming", "bead_ids": ["b1"]}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert "b1" in (await client.convoy_add_bead("c1", "b1")).bead_ids

    async def test_dispatch(self, client):
        d = {"id": "c1", "name": "t", "state": "dispatching"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert (await client.convoy_dispatch("c1")).state == ConvoyState.DISPATCHING


# ============================================================================
# Test Polecat Mixin
# ============================================================================


class TestPolecatMixin:
    async def test_spawn(self, client):
        d = {"id": "p1", "name": "w", "state": "spawning"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert isinstance(await client.polecat_spawn("w"), Polecat)

    async def test_spawn_invalid_role(self, client):
        with pytest.raises(GastownError, match="Invalid role"):
            await client.polecat_spawn("w", role="invalid")

    async def test_status(self, client):
        d = {"id": "p1", "name": "w", "state": "active"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert (await client.polecat_status("p1")).state == PolecatState.ACTIVE

    async def test_list(self, client):
        d = [{"id": "p1", "name": "w", "state": "active"}]
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert len(await client.polecat_list()) == 1

    async def test_archive(self, client):
        d = {"id": "p1", "name": "w", "state": "archived"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert (await client.polecat_archive("p1")).state == PolecatState.ARCHIVED

    async def test_pause(self, client):
        d = {"id": "p1", "name": "w", "state": "paused"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert (await client.polecat_pause("p1")).state == PolecatState.PAUSED

    async def test_resume(self, client):
        d = {"id": "p1", "name": "w", "state": "active"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert (await client.polecat_resume("p1")).state == PolecatState.ACTIVE


# ============================================================================
# Test Rig, Hook, Mail, Escalation, Utility Mixins
# ============================================================================


class TestRigMixin:
    async def test_list(self, client):
        d = [{"id": "r1", "name": "p"}]
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert len(await client.rig_list()) == 1

    async def test_status(self, client):
        d = {"id": "r1", "name": "p", "state": "active"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert (await client.rig_status("r1")).state == RigState.ACTIVE

    async def test_create(self, client):
        d = {"id": "r1", "name": "n"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert (await client.rig_create("n")).name == "n"

    async def test_archive(self, client):
        d = {"id": "r1", "name": "p", "state": "archived"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert (await client.rig_archive("r1")).state == RigState.ARCHIVED


class TestHookMixin:
    async def test_list(self, client):
        d = [{"id": "h1", "name": "h"}]
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert len(await client.hook_list()) == 1

    async def test_create(self, client):
        d = {"id": "h1", "name": "h"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert (await client.hook_create("h", rig_id="r1")).name == "h"

    async def test_status(self, client):
        d = {"id": "h1", "name": "h", "state": "active"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert (await client.hook_status("h1")).state == HookState.ACTIVE

    async def test_archive(self, client):
        d = {"id": "h1", "name": "h", "state": "archived"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert (await client.hook_archive("h1")).state == HookState.ARCHIVED


class TestMailMixin:
    async def test_send(self, client):
        d = {
            "id": "m1",
            "from_agent": "a1",
            "to_agent": "a2",
            "subject": "s",
            "body": "b",
        }
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert (
                await client.mail_send("a2", "s", "b", from_agent="a1")
            ).to_agent == "a2"

    async def test_send_invalid_priority(self, client):
        with pytest.raises(GastownError, match="Invalid priority"):
            await client.mail_send("a2", "s", "b", priority="super")

    async def test_list(self, client):
        d = [{"id": "m1", "from_agent": "a1", "to_agent": "a2"}]
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert len(await client.mail_list()) == 1

    async def test_read(self, client):
        d = {"id": "m1", "from_agent": "a1", "to_agent": "a2", "subject": "hi"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert (await client.mail_read("m1")).subject == "hi"


class TestEscalationMixin:
    async def test_escalate(self, client):
        d = {"id": "e1", "issue_id": "bd-42", "severity": "high", "message": "stuck"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert (
                await client.escalate("bd-42", "high", "stuck")
            ).severity == EscalationSeverity.HIGH

    async def test_escalate_sentinel(self, client):
        d = {"id": "e1", "issue_id": "--bad", "severity": "low", "message": "t"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ) as m:
            await client.escalate("--bad", EscalationSeverity.LOW, "t")
            args = m.call_args[0][0]
            assert args.index("--") < args.index("--bad")

    async def test_list(self, client):
        d = [{"id": "e1", "issue_id": "bd-1", "severity": "high", "message": "h"}]
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert len(await client.escalation_list()) == 1

    async def test_resolve(self, client):
        d = {"id": "e1", "issue_id": "bd-1", "severity": "high", "message": "done"}
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=make_result(d)
        ):
            assert isinstance(await client.escalation_resolve("e1"), Escalation)


class TestUtilityMixin:
    async def test_version(self, client):
        r = make_result(stdout="gt version 1.2.3")
        r.parsed_output = None
        with patch.object(
            client, "_run_command", new_callable=AsyncMock, return_value=r
        ):
            assert await client.version() == "gt version 1.2.3"

    async def test_version_cached(self, client):
        client._version = "cached"
        assert await client.version() == "cached"

    async def test_is_available_true(self, client):
        with patch.object(
            client, "_find_gt", new_callable=AsyncMock, return_value="/usr/bin/gt"
        ):
            assert await client.is_available() is True

    async def test_is_available_false(self, client):
        with patch.object(
            client, "_find_gt", side_effect=GastownNotInstalledError("nope")
        ):
            assert await client.is_available() is False

    async def test_health_check_ok(self, client):
        with (
            patch.object(
                client, "is_available", new_callable=AsyncMock, return_value=True
            ),
            patch.object(client, "version", new_callable=AsyncMock, return_value="1.0"),
        ):
            h = await client.health_check()
            assert h["available"] is True and h["version"] == "1.0"

    async def test_health_check_error(self, client):
        with patch.object(client, "is_available", side_effect=Exception("boom")):
            h = await client.health_check()
            assert h["error"] == "boom"
