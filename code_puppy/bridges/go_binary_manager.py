"""Go binary management module for Code Puppy.

Handles installation, updates, and version checking for Go binaries:
- bd (beads): Issue tracking
- dolt: Database management
- gt (gastown): Git operations

Supports both npm-installed and system binaries with graceful degradation.
"""

from __future__ import annotations

import asyncio
import os
import platform
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from code_puppy.messaging import emit_error, emit_info, emit_warning


class BinarySource(str, Enum):
    """Source type for Go binaries."""

    NPM = "npm"  # Installed via npm (e.g., @dolthub/dolt)
    GITHUB_RELEASE = "github"  # Downloaded from GitHub releases
    SYSTEM = "system"  # System package manager (apt, brew, etc.)
    MANUAL = "manual"  # Manually installed


class BinaryConfig(BaseModel):
    """Configuration for a Go binary.

    Attributes:
        name: Binary identifier (bd, dolt, gt)
        display_name: Human-readable name
        npm_package: NPM package name if applicable
        github_repo: GitHub repository (owner/repo) if applicable
        min_version: Minimum required version
        recommended_version: Recommended version
        install_args: Additional arguments for installation
    """

    name: str
    display_name: str
    npm_package: Optional[str] = None
    github_repo: Optional[str] = None
    min_version: Optional[str] = None
    recommended_version: Optional[str] = None
    install_args: list[str] = Field(default_factory=list)
    source: BinarySource = BinarySource.NPM

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate binary name is supported."""
        supported = {"bd", "dolt", "gt"}
        if v not in supported:
            raise ValueError(f"Unsupported binary: {v}. Must be one of: {supported}")
        return v


@dataclass
class BinaryInfo:
    """Information about an installed binary.

    Attributes:
        name: Binary identifier
        path: Resolved path to binary
        version: Installed version string
        available: Whether binary is available
        source: Installation source
    """

    name: str
    path: Optional[Path]
    version: Optional[str]
    available: bool
    source: BinarySource


class GoBinaryManager:
    """Manager for Go binaries used by Code Puppy.

    Handles:
    - Binary path resolution
    - Version checking
    - Async subprocess execution
    - Graceful degradation when binaries unavailable

    Usage:
        manager = GoBinaryManager()
        await manager.ensure_all_binaries()

        # Run a command
        result = await manager.run_command("bd", ["show", "123"])

        # Check availability
        if manager.check_binary_available("dolt"):
            version = await manager.get_version("dolt")
    """

    # Default binary configurations
    DEFAULT_BINARIES: dict[str, BinaryConfig] = {
        "bd": BinaryConfig(
            name="bd",
            display_name="Beads",
            npm_package="@beads/cli",
            github_repo="beadsio/beads",
            min_version="0.1.0",
            source=BinarySource.NPM,
        ),
        "dolt": BinaryConfig(
            name="dolt",
            display_name="Dolt",
            npm_package="@dolthub/dolt",
            github_repo="dolthub/dolt",
            min_version="1.0.0",
            source=BinarySource.NPM,
        ),
        "gt": BinaryConfig(
            name="gt",
            display_name="Gastown",
            npm_package="@gastown/cli",
            github_repo="gastown/gt",
            min_version="0.1.0",
            source=BinarySource.NPM,
        ),
    }

    def __init__(
        self,
        binary_dir: Optional[Path] = None,
        configs: Optional[dict[str, BinaryConfig]] = None,
        auto_install: bool = True,
    ):
        """Initialize the Go binary manager.

        Args:
            binary_dir: Directory for binary storage. Defaults to ~/.code_puppy/bin
            configs: Custom binary configurations. Uses defaults if not provided.
            auto_install: Whether to auto-install missing binaries.
        """
        self._binary_dir = binary_dir or self._get_default_binary_dir()
        self._configs = configs or self.DEFAULT_BINARIES.copy()
        self._auto_install = auto_install
        self._binary_cache: dict[str, Optional[Path]] = {}
        self._version_cache: dict[str, Optional[str]] = {}

    def _get_default_binary_dir(self) -> Path:
        """Get default binary directory following XDG conventions."""
        xdg_data = os.getenv("XDG_DATA_HOME")
        if xdg_data:
            return Path(xdg_data) / "code_puppy" / "bin"
        return Path.home() / ".code_puppy" / "bin"

    @property
    def binary_dir(self) -> Path:
        """Binary installation directory."""
        return self._binary_dir

    def _get_npm_global_dir(self) -> Optional[Path]:
        """Get npm global installation directory."""
        try:
            result = shutil.which("npm")
            if not result:
                return None
            # Common npm global paths
            paths = [
                Path.home() / ".npm-global" / "bin",
                Path.home() / ".local" / "bin",
                Path("/usr/local/bin"),
                Path("/opt/homebrew/bin"),  # macOS Homebrew
            ]
            for path in paths:
                if path.exists():
                    return path
            return None
        except Exception:
            return None

    async def _run_subprocess(
        self,
        cmd: list[str],
        cwd: Optional[Path] = None,
        env: Optional[dict[str, str]] = None,
        timeout: float = 30.0,
        capture_output: bool = True,
    ) -> tuple[int, str, str]:
        """Run a subprocess asynchronously.

        Args:
            cmd: Command and arguments
            cwd: Working directory
            env: Environment variables
            timeout: Timeout in seconds
            capture_output: Whether to capture stdout/stderr

        Returns:
            Tuple of (returncode, stdout, stderr)
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                cmd[0],
                *cmd[1:],
                stdout=asyncio.subprocess.PIPE if capture_output else None,
                stderr=asyncio.subprocess.PIPE if capture_output else None,
                cwd=cwd,
                env={**os.environ, **(env or {})},
            )

            stdout_data = b""
            stderr_data = b""

            if capture_output:
                try:
                    stdout_data, stderr_data = await asyncio.wait_for(
                        proc.communicate(), timeout=timeout
                    )
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                    return -1, "", f"Command timed out after {timeout}s"
            else:
                await asyncio.wait_for(proc.wait(), timeout=timeout)

            return (
                proc.returncode or 0,
                stdout_data.decode("utf-8", errors="replace").strip(),
                stderr_data.decode("utf-8", errors="replace").strip(),
            )

        except FileNotFoundError:
            return -1, "", f"Command not found: {cmd[0]}"
        except asyncio.TimeoutError:
            return -1, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return -1, "", f"Error running command: {e}"

    async def ensure_all_binaries(self) -> dict[str, BinaryInfo]:
        """Check and ensure all required binaries are available.

        Attempts to install missing binaries if auto_install is enabled.

        Returns:
            Dictionary mapping binary names to their info.
        """
        results = {}
        for name in self._configs:
            info = await self._ensure_binary(name)
            results[name] = info
        return results

    async def _ensure_binary(self, name: str) -> BinaryInfo:
        """Ensure a single binary is available.

        Args:
            name: Binary identifier

        Returns:
            BinaryInfo for the binary
        """
        path = self.get_binary_path(name)
        if path:
            version = await self.get_version(name)
            return BinaryInfo(
                name=name,
                path=path,
                version=version,
                available=True,
                source=self._configs[name].source,
            )

        if self._auto_install:
            emit_info(f"Binary '{name}' not found. Attempting installation...")
            success = await self._install_binary(name)
            if success:
                path = self.get_binary_path(name)
                version = await self.get_version(name) if path else None
                return BinaryInfo(
                    name=name,
                    path=path,
                    version=version,
                    available=path is not None,
                    source=self._configs[name].source,
                )

        emit_warning(f"Binary '{name}' is not available. Some features may be limited.")
        return BinaryInfo(
            name=name,
            path=None,
            version=None,
            available=False,
            source=self._configs[name].source,
        )

    async def _install_binary(self, name: str) -> bool:
        """Install a binary from its configured source.

        Args:
            name: Binary identifier

        Returns:
            True if installation succeeded
        """
        config = self._configs.get(name)
        if not config:
            emit_error(f"No configuration found for binary: {name}")
            return False

        if config.source == BinarySource.NPM and config.npm_package:
            return await self._install_from_npm(config)
        elif config.source == BinarySource.GITHUB_RELEASE and config.github_repo:
            return await self._install_from_github(config)
        else:
            emit_warning(f"Auto-install not supported for {name} from {config.source}")
            return False

    async def _install_from_npm(self, config: BinaryConfig) -> bool:
        """Install a binary via npm.

        Args:
            config: Binary configuration

        Returns:
            True if installation succeeded
        """
        try:
            # Check if npm is available
            npm_path = shutil.which("npm")
            if not npm_path:
                emit_error("npm not found. Cannot install npm packages.")
                return False

            # Create binary directory
            self._binary_dir.mkdir(parents=True, exist_ok=True)

            # Install globally or locally
            cmd = [npm_path, "install", "-g", config.npm_package]
            if config.install_args:
                cmd.extend(config.install_args)

            emit_info(f"Installing {config.display_name} via npm...")
            returncode, stdout, stderr = await self._run_subprocess(cmd, timeout=120.0)

            if returncode != 0:
                emit_error(f"npm install failed: {stderr}")
                return False

            # Clear cache to re-detect
            self._binary_cache.pop(config.name, None)
            emit_info(f"Successfully installed {config.display_name}")
            return True

        except Exception as e:
            emit_error(f"Error installing {config.name}: {e}")
            return False

    async def _install_from_github(self, config: BinaryConfig) -> bool:
        """Install a binary from GitHub releases.

        Args:
            config: Binary configuration

        Returns:
            True if installation succeeded
        """
        # TODO: Implement GitHub release download
        # This would require platform detection, asset download, extraction
        emit_warning(
            f"GitHub release installation not yet implemented for {config.name}"
        )
        return False

    def get_binary_path(self, name: str) -> Optional[Path]:
        """Resolve the path to a binary.

        Checks in order:
        1. Cache
        2. Custom binary directory
        3. npm global directory
        4. System PATH

        Args:
            name: Binary identifier

        Returns:
            Path to binary if found, None otherwise
        """
        # Check cache
        if name in self._binary_cache:
            path = self._binary_cache[name]
            return path

        config = self._configs.get(name)
        if not config:
            return None

        # Check custom binary directory
        custom_path = self._binary_dir / name
        if custom_path.exists():
            self._binary_cache[name] = custom_path
            return custom_path

        # On Windows, check with .exe extension
        if platform.system() == "Windows":
            custom_path_exe = self._binary_dir / f"{name}.exe"
            if custom_path_exe.exists():
                self._binary_cache[name] = custom_path_exe
                return custom_path_exe

        # Check npm global directory
        npm_dir = self._get_npm_global_dir()
        if npm_dir:
            npm_path = npm_dir / name
            if npm_path.exists():
                self._binary_cache[name] = npm_path
                return npm_path

            if platform.system() == "Windows":
                npm_path_exe = npm_dir / f"{name}.exe"
                if npm_path_exe.exists():
                    self._binary_cache[name] = npm_path_exe
                    return npm_path_exe

        # Check system PATH
        system_path = shutil.which(name)
        if system_path:
            path = Path(system_path)
            self._binary_cache[name] = path
            return path

        # Not found
        self._binary_cache[name] = None
        return None

    async def get_version(self, name: str) -> Optional[str]:
        """Get the installed version of a binary.

        Args:
            name: Binary identifier

        Returns:
            Version string if available, None otherwise
        """
        # Check cache
        if name in self._version_cache:
            return self._version_cache[name]

        path = self.get_binary_path(name)
        if not path:
            self._version_cache[name] = None
            return None

        # Try common version flags
        version_flags = [["--version"], ["-v"], ["version"]]

        for flags in version_flags:
            returncode, stdout, _ = await self._run_subprocess(
                [str(path)] + flags, timeout=10.0
            )
            if returncode == 0 and stdout:
                # Extract version from output (e.g., "dolt version 1.0.0" -> "1.0.0")
                version = self._parse_version(stdout)
                self._version_cache[name] = version
                return version

        self._version_cache[name] = None
        return None

    def _parse_version(self, output: str) -> Optional[str]:
        """Parse version string from command output.

        Args:
            output: Command output containing version

        Returns:
            Extracted version string
        """
        import re

        # Common patterns: "1.0.0", "v1.0.0", "version 1.0.0"
        patterns = [
            r"v?(\d+\.\d+\.\d+(?:-[\w.]+)?)",  # semver
            r"version\s+v?(\d+\.\d+\.\d+)",  # "version X.Y.Z"
            r"(\d+\.\d+\.\d+)",  # plain semver
        ]

        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1)

        # Return first line as fallback
        lines = output.strip().split("\n")
        return lines[0] if lines else None

    def check_binary_available(self, name: str) -> bool:
        """Check if a binary is available without running it.

        Args:
            name: Binary identifier

        Returns:
            True if binary exists and is executable
        """
        path = self.get_binary_path(name)
        if not path:
            return False
        return os.access(path, os.X_OK)

    async def run_command(
        self,
        name: str,
        args: list[str],
        cwd: Optional[Path] = None,
        env: Optional[dict[str, str]] = None,
        timeout: float = 60.0,
        capture_output: bool = True,
    ) -> tuple[int, str, str]:
        """Execute a binary with arguments.

        Args:
            name: Binary identifier
            args: Command arguments
            cwd: Working directory
            env: Environment variables
            timeout: Timeout in seconds
            capture_output: Whether to capture stdout/stderr

        Returns:
            Tuple of (returncode, stdout, stderr)

        Raises:
            BinaryNotAvailableError: If binary is not available
        """
        path = self.get_binary_path(name)
        if not path:
            raise BinaryNotAvailableError(f"Binary '{name}' is not available")

        cmd = [str(path)] + args
        return await self._run_subprocess(
            cmd, cwd=cwd, env=env, timeout=timeout, capture_output=capture_output
        )

    async def check_version_compatibility(
        self, name: str
    ) -> tuple[bool, Optional[str]]:
        """Check if installed version meets minimum requirements.

        Args:
            name: Binary identifier

        Returns:
            Tuple of (is_compatible, current_version)
        """
        config = self._configs.get(name)
        if not config or not config.min_version:
            return True, None

        version = await self.get_version(name)
        if not version:
            return False, None

        # Simple version comparison (assumes semver)
        is_compatible = self._compare_versions(version, config.min_version) >= 0
        return is_compatible, version

    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compare two version strings.

        Args:
            v1: First version
            v2: Second version

        Returns:
            -1 if v1 < v2, 0 if equal, 1 if v1 > v2
        """
        try:
            parts1 = [int(x) for x in v1.split(".")[:3]]
            parts2 = [int(x) for x in v2.split(".")[:3]]

            # Pad with zeros
            while len(parts1) < 3:
                parts1.append(0)
            while len(parts2) < 3:
                parts2.append(0)

            for a, b in zip(parts1, parts2):
                if a < b:
                    return -1
                if a > b:
                    return 1
            return 0
        except (ValueError, AttributeError):
            # Fall back to string comparison
            return (v1 > v2) - (v1 < v2)

    def clear_cache(self) -> None:
        """Clear cached binary paths and versions."""
        self._binary_cache.clear()
        self._version_cache.clear()

    def get_config(self, name: str) -> Optional[BinaryConfig]:
        """Get configuration for a binary.

        Args:
            name: Binary identifier

        Returns:
            BinaryConfig if found, None otherwise
        """
        return self._configs.get(name)

    def update_config(self, name: str, config: BinaryConfig) -> None:
        """Update configuration for a binary.

        Args:
            name: Binary identifier
            config: New configuration
        """
        self._configs[name] = config
        # Clear cache for this binary
        self._binary_cache.pop(name, None)
        self._version_cache.pop(name, None)


class BinaryNotAvailableError(Exception):
    """Raised when a binary is required but not available."""

    pass


# Singleton instance for convenience
_default_manager: Optional[GoBinaryManager] = None


def get_binary_manager() -> GoBinaryManager:
    """Get the default binary manager singleton.

    Returns:
        GoBinaryManager instance
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = GoBinaryManager()
    return _default_manager


def reset_binary_manager() -> None:
    """Reset the default binary manager singleton.

    Useful for testing or when configuration changes.
    """
    global _default_manager
    _default_manager = None
