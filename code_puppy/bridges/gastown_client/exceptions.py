"""Exceptions for Gastown Client."""


class GastownError(Exception):
    """Base exception for Gastown client errors."""

    pass


class GastownNotInstalledError(GastownError):
    """Raised when gt CLI is not installed."""

    pass


class GastownCommandError(GastownError):
    """Raised when a gt command fails."""

    def __init__(self, message: str, command: str, exit_code: int, stderr: str = ""):
        super().__init__(message)
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr


class GastownParseError(GastownError):
    """Raised when parsing gt output fails."""

    pass
