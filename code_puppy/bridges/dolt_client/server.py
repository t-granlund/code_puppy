"""SQL server management for Dolt client."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .models import DoltServerInfo

logger = logging.getLogger(__name__)


class DoltSQLServerManager:
    """Manages Dolt SQL server lifecycle with health checking."""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self._server_process: Optional[asyncio.subprocess.Process] = None
        self._server_info: "DoltServerInfo" = None  # Will be set by client

    def set_server_info(self, info: "DoltServerInfo") -> None:
        """Set the server info reference from client."""
        self._server_info = info

    async def _wait_for_server_health(
        self,
        process: asyncio.subprocess.Process,
        host: str,
        port: int,
        timeout: float = 30.0,
        check_interval: float = 0.5,
    ) -> tuple[bool, str]:
        """Wait for server to be healthy by checking port.

        Args:
            process: Server subprocess
            host: Server host
            port: Server port
            timeout: Maximum time to wait
            check_interval: Time between health checks

        Returns:
            Tuple of (success, error_message)
        """
        import errno
        import socket

        start_time = asyncio.get_event_loop().time()
        last_error = ""

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            # Check if process died
            if process.returncode is not None:
                stdout, stderr = "", ""
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(), timeout=5.0
                    )
                except asyncio.TimeoutError:
                    pass
                return (
                    False,
                    f"Server process exited with code {process.returncode}. "
                    f"stdout: {stdout.decode()[:500] if stdout else 'N/A'}, "
                    f"stderr: {stderr.decode()[:500] if stderr else 'N/A'}",
                )

            # Try to connect to the port
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(check_interval)
                result = sock.connect_ex((host, port))
                sock.close()

                if result == 0:
                    # Port is open, server is healthy
                    return True, ""
                elif result == errno.ECONNREFUSED:
                    last_error = "Connection refused"
                else:
                    last_error = f"Socket error: {result}"

            except socket.error as e:
                last_error = f"Socket error: {e}"

            await asyncio.sleep(check_interval)

        return False, f"Server health check timeout after {timeout}s. Last error: {last_error}"

    async def start(
        self,
        port: int = 3306,
        host: str = "localhost",
        user: str = "root",
        password: str = "",
        readonly: bool = False,
        log_level: str = "info",
        health_timeout: float = 30.0,
    ) -> "DoltServerInfo":
        """Start the Dolt SQL server with health checking.

        Args:
            port: Server port
            host: Server host
            user: Database user
            password: Database password
            readonly: Start in read-only mode
            log_level: Logging level
            health_timeout: Max time to wait for server to be healthy

        Returns:
            DoltServerInfo with server status

        Raises:
            DoltSQLServerError: If server fails to start or health check fails
        """
        from .exceptions import DoltSQLServerError
        from .models import DoltServerInfo

        if self._server_process and self._server_process.returncode is None:
            logger.warning("Dolt SQL server already running")
            return self._server_info

        args = [
            "sql-server",
            "--port", str(port),
            "--host", host,
            "-u", user,
        ]

        if password:
            args.extend(["-p", password])
        if readonly:
            args.append("--readonly")
        if log_level:
            args.extend(["--loglevel", log_level])

        try:
            self._server_process = await asyncio.create_subprocess_exec(
                "dolt",
                *args,
                cwd=str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait for server to be healthy (replaces fixed sleep)
            is_healthy, error_msg = await self._wait_for_server_health(
                self._server_process, host, port, timeout=health_timeout
            )

            if not is_healthy:
                # Capture output before killing for debugging
                stdout, stderr = "", ""
                try:
                    stdout, stderr = await asyncio.wait_for(
                        self._server_process.communicate(), timeout=5.0
                    )
                except asyncio.TimeoutError:
                    pass

                # Kill the process
                try:
                    self._server_process.kill()
                    await asyncio.wait_for(self._server_process.wait(), timeout=5.0)
                except (ProcessLookupError, asyncio.TimeoutError):
                    pass

                self._server_process = None

                raise DoltSQLServerError(
                    f"Failed to start SQL server: {error_msg}",
                    stderr=stderr.decode() if stderr else "",
                    stdout=stdout.decode() if stdout else "",
                )

            self._server_info = DoltServerInfo(
                running=True,
                pid=self._server_process.pid,
                port=port,
                host=host,
            )

            logger.info(f"Dolt SQL server started on {host}:{port}")
            return self._server_info

        except DoltSQLServerError:
            raise
        except Exception as e:
            raise DoltSQLServerError(f"Failed to start SQL server: {e}")

    async def stop(self, force: bool = False) -> "DoltServerInfo":
        """Stop the Dolt SQL server.

        Args:
            force: Force kill the server

        Returns:
            DoltServerInfo with updated status
        """
        from .models import DoltServerInfo

        if not self._server_process:
            logger.warning("No SQL server running")
            return DoltServerInfo(running=False)

        try:
            if force:
                self._server_process.kill()
            else:
                self._server_process.terminate()

            await asyncio.wait_for(self._server_process.wait(), timeout=5.0)

        except asyncio.TimeoutError:
            self._server_process.kill()
            await self._server_process.wait()
        except ProcessLookupError:
            pass  # Already terminated

        self._server_process = None
        self._server_info = DoltServerInfo(running=False)

        logger.info("Dolt SQL server stopped")
        return self._server_info

    async def status(self) -> "DoltServerInfo":
        """Check SQL server status.

        Returns:
            DoltServerInfo with current status
        """
        from .models import DoltServerInfo

        if not self._server_process:
            return DoltServerInfo(running=False)

        # Check if still running
        if self._server_process.returncode is None:
            return self._server_info
        else:
            self._server_process = None
            self._server_info = DoltServerInfo(running=False)
            return self._server_info
