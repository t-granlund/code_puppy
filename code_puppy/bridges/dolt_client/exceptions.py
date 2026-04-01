"""Exception classes for Dolt client."""

from __future__ import annotations

from typing import Optional


class DoltError(Exception):
    """Base exception for Dolt operations."""

    def __init__(
        self,
        message: str,
        command: Optional[str] = None,
        stderr: str = "",
        stdout: str = "",
    ):
        super().__init__(message)
        self.command = command
        self.stderr = stderr
        self.stdout = stdout


class DoltNotInitializedError(DoltError):
    """Raised when dolt repository is not initialized."""
    pass


class DoltBranchError(DoltError):
    """Raised when a branch operation fails."""
    pass


class DoltSQLServerError(DoltError):
    """Raised when SQL server operation fails."""
    pass
