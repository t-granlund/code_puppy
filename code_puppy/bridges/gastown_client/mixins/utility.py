"""Utility methods mixin for GastownClient."""

from typing import Any, Dict

from code_puppy.bridges.gastown_client.exceptions import GastownNotInstalledError


class UtilityMixin:
    """Utility methods for GastownClient."""

    async def version(self) -> str:
        """Get gt CLI version.

        Returns:
            Version string.
        """
        if self._version:
            return self._version

        result = await self._run_command(
            ["--version"],
            capture_json=False,
        )

        self._version = result.stdout.strip()
        return self._version

    async def is_available(self) -> bool:
        """Check if gt CLI is available.

        Returns:
            True if gt is installed and working.
        """
        try:
            await self._find_gt()
            return True
        except GastownNotInstalledError:
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on Gastown.

        Returns:
            Health check results.
        """
        health = {
            "available": False,
            "version": None,
            "error": None,
        }

        try:
            health["available"] = await self.is_available()
            if health["available"]:
                health["version"] = await self.version()
        except Exception as e:
            health["error"] = str(e)

        return health
