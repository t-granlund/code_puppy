"""Core GastownClient implementation."""

from __future__ import annotations

import asyncio
import json
import logging
import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from code_puppy.bridges.gastown_client.exceptions import (
    GastownCommandError,
    GastownNotInstalledError,
)
from code_puppy.bridges.gastown_client.mixins import (
    ConvoyMixin,
    EscalationMixin,
    HookMixin,
    MailMixin,
    PolecatMixin,
    RigMixin,
    UtilityMixin,
)
from code_puppy.bridges.gastown_client.models import CommandResult

logger = logging.getLogger(__name__)


@dataclass
class GastownConfig:
    """Configuration for Gastown client."""

    gt_path: str = "gt"
    default_timeout: float = 30.0
    json_output: bool = True


class GastownClient(
    ConvoyMixin,
    PolecatMixin,
    RigMixin,
    HookMixin,
    MailMixin,
    EscalationMixin,
    UtilityMixin,
):
    """Python wrapper for Gastown (gt) CLI commands.

    Provides async interface to:
    - Convoy management (create, list, status, archive)
    - Polecat lifecycle operations (spawn, status, archive)
    - Rig management operations
    - Hook management
    - Mail operations
    - Escalation handling
    """

    def __init__(self, config: Optional[GastownConfig] = None):
        """Initialize Gastown client.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or GastownConfig()
        self._gt_path: Optional[str] = None
        self._version: Optional[str] = None

    async def _find_gt(self) -> str:
        """Find the gt executable.

        Returns:
            Path to gt executable.

        Raises:
            GastownNotInstalledError: If gt is not found.
        """
        if self._gt_path:
            return self._gt_path

        gt_path = shutil.which(self.config.gt_path)
        if not gt_path:
            raise GastownNotInstalledError(
                "Gastown CLI (gt) not found. "
                "Please install from https://github.com/steveyegge/gastown"
            )

        self._gt_path = gt_path
        return gt_path

    async def _run_command(
        self,
        args: list[str],
        cwd: Optional[Path] = None,
        timeout: Optional[float] = None,
        capture_json: bool = True,
    ) -> CommandResult:
        """Run a gt CLI command.

        Args:
            args: Command arguments (after 'gt').
            cwd: Working directory.
            timeout: Command timeout in seconds.
            capture_json: Whether to parse output as JSON.

        Returns:
            CommandResult with output and parsed data.

        Raises:
            GastownCommandError: If the command fails.
        """
        gt_path = await self._find_gt()

        cmd = [gt_path]
        if capture_json and self.config.json_output:
            cmd.append("--json")
        cmd.extend(args)

        cmd_str = shlex.join(cmd)
        logger.debug("Running: %s", cmd_str)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout or self.config.default_timeout,
            )

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            parsed_output = None
            if capture_json and stdout.strip():
                try:
                    parsed_output = json.loads(stdout)
                except json.JSONDecodeError as e:
                    logger.warning("Failed to parse JSON output: %s", e)

            result = CommandResult(
                command=cmd_str,
                exit_code=proc.returncode or 0,
                stdout=stdout,
                stderr=stderr,
                parsed_output=parsed_output,
                success=proc.returncode == 0,
            )

            if proc.returncode != 0:
                error_msg = (
                    stderr.strip() or f"Command failed with exit code {proc.returncode}"
                )
                result.error_message = error_msg
                raise GastownCommandError(
                    message=error_msg,
                    command=cmd_str,
                    exit_code=proc.returncode or -1,
                    stderr=stderr,
                )

            return result

        except asyncio.TimeoutError:
            try:
                proc.kill()
                await proc.wait()
            except ProcessLookupError:
                pass
            error_msg = (
                f"Command timed out after {timeout or self.config.default_timeout}s"
            )
            raise GastownCommandError(
                message=error_msg,
                command=cmd_str,
                exit_code=-1,
                stderr="Timeout",
            )
        except GastownCommandError:
            raise
        except Exception as e:
            raise GastownCommandError(
                message=str(e),
                command=cmd_str,
                exit_code=-1,
                stderr=str(e),
            )
