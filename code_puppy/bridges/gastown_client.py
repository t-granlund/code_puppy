"""Gastown Client - Python wrapper for Gastown (gt) CLI commands.

This client provides a Python interface to the Gastown multi-agent workspace
manager, enabling convoy management, polecat lifecycle operations, rig
management, hook operations, mail handling, and escalation from Python code.

Usage:
    ```python
    client = GastownClient()
    
    # Convoy management
    convoy = await client.convoy_create("feature-auth", priority="high")
    convoys = await client.convoy_list()
    status = await client.convoy_status("feature-auth")
    
    # Polecat (agent) operations
    polecat = await client.polecat_spawn("auth-worker", role="reviewer")
    await client.polecat_status("auth-worker")
    
    # Rig management
    rigs = await client.rig_list()
    
    # Escalations
    await client.escalate("issue-123", severity="high", message="Stuck on auth flow")
    ```
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class ConvoyState(str, Enum):
    """Lifecycle states for a convoy."""
    FORMING = "forming"
    MOUNTAIN = "mountain"
    DISPATCHING = "dispatching"
    ACTIVE = "active"
    STALLED = "stalled"
    COMPLETING = "completing"
    ARCHIVED = "archived"


class ConvoyPriority(str, Enum):
    """Priority levels for convoys."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class PolecatRole(str, Enum):
    """Orchestra agent roles (inspired by Gastown)."""
    MAYOR = "mayor"
    POLECAT = "polecat"
    CREW = "crew"
    WITNESS = "witness"
    DEACON = "deacon"
    DOG = "dog"
    REFINERY = "refinery"


class PolecatState(str, Enum):
    """Lifecycle states for a polecat (agent)."""
    IDLE = "idle"
    SPAWNING = "spawning"
    ACTIVE = "active"
    PAUSED = "paused"
    STUCK = "stuck"
    COMPLETING = "completing"
    ARCHIVED = "archived"


class RigState(str, Enum):
    """Lifecycle states for a rig."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class HookState(str, Enum):
    """Lifecycle states for a hook."""
    CREATING = "creating"
    READY = "ready"
    ACTIVE = "active"
    STALE = "stale"
    ARCHIVED = "archived"


class MailStatus(str, Enum):
    """Status of a mail message."""
    DRAFT = "draft"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    REPLIED = "replied"
    ARCHIVED = "archived"


class MailPriority(str, Enum):
    """Priority levels for mail."""
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class EscalationSeverity(str, Enum):
    """Escalation severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================================
# Pydantic Models for Responses
# ============================================================================

class Convoy(BaseModel):
    """A work convoy - bundles multiple beads for coordinated execution."""
    id: str
    name: str
    state: ConvoyState
    priority: ConvoyPriority = ConvoyPriority.NORMAL
    bead_ids: List[str] = Field(default_factory=list)
    completed_beads: List[str] = Field(default_factory=list)
    rig_id: Optional[str] = None
    agent_ids: List[str] = Field(default_factory=list)
    notify_human: bool = False
    require_human_review: bool = False
    auto_close: bool = True
    is_mountain: bool = False
    max_stall_minutes: int = 30
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    progress_pct: float = 0.0
    last_update: Optional[datetime] = None
    notes: List[str] = Field(default_factory=list)


class Polecat(BaseModel):
    """A polecat (agent) in the Gastown system."""
    id: str
    name: str
    role: PolecatRole = PolecatRole.POLECAT
    state: PolecatState = PolecatState.IDLE
    rig_id: Optional[str] = None
    specialty: Optional[str] = None
    runtime: str = "claude"
    bead_id: Optional[str] = None
    convoy_id: Optional[str] = None
    spawned_at: datetime = Field(default_factory=datetime.now)
    activated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    working_dir: Optional[str] = None


class Rig(BaseModel):
    """A project container (rig) in the Gastown system."""
    id: str
    name: str
    repo_url: Optional[str] = None
    local_path: Optional[str] = None
    state: RigState = RigState.INITIALIZING
    runtime_provider: str = "claude"
    max_polecats: int = 5
    auto_spawn_witness: bool = True
    hooks_enabled: bool = True
    beads_project: Optional[str] = None
    agent_ids: List[str] = Field(default_factory=list)
    crew_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    last_active: Optional[datetime] = None


class Hook(BaseModel):
    """A git worktree-based persistent storage for agent work."""
    id: str
    name: str
    state: HookState = HookState.CREATING
    worktree_path: Optional[str] = None
    base_branch: str = "main"
    current_branch: Optional[str] = None
    agent_id: Optional[str] = None
    rig_id: Optional[str] = None
    bead_ids: List[str] = Field(default_factory=list)
    context_files: List[str] = Field(default_factory=list)
    mail_inbox: List[str] = Field(default_factory=list)
    mail_sent: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    last_commit: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    commit_count: int = 0


class Mail(BaseModel):
    """An inter-agent mail message."""
    id: str
    from_agent: str
    to_agent: str
    cc_agents: List[str] = Field(default_factory=list)
    subject: str = ""
    body: str = ""
    thread_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    bead_id: Optional[str] = None
    convoy_id: Optional[str] = None
    rig_id: Optional[str] = None
    status: MailStatus = MailStatus.DRAFT
    priority: MailPriority = MailPriority.NORMAL
    created_at: datetime = Field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    delivery_attempts: int = 0
    last_error: Optional[str] = None


class Escalation(BaseModel):
    """An escalation in the Gastown system."""
    id: str
    issue_id: str
    severity: EscalationSeverity
    message: str
    from_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None


class CommandResult(BaseModel):
    """Result from executing a gt CLI command."""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    parsed_output: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None


# ============================================================================
# Exceptions
# ============================================================================

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


# ============================================================================
# Gastown Client
# ============================================================================

@dataclass
class GastownConfig:
    """Configuration for Gastown client."""
    gt_path: str = "gt"
    town_dir: Optional[Path] = None
    default_timeout: float = 30.0
    json_output: bool = True


class GastownClient:
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
        args: List[str],
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
        
        # Build command
        cmd = [gt_path]
        if capture_json and self.config.json_output:
            cmd.append("--json")
        cmd.extend(args)
        
        cmd_str = " ".join(cmd)
        logger.debug(f"Running: {cmd_str}")
        
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
            
            # Parse JSON output if requested
            parsed_output = None
            if capture_json and stdout.strip():
                try:
                    parsed_output = json.loads(stdout)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON output: {e}")
            
            result = CommandResult(
                command=cmd_str,
                exit_code=proc.returncode or 0,
                stdout=stdout,
                stderr=stderr,
                parsed_output=parsed_output,
                success=proc.returncode == 0,
            )
            
            if proc.returncode != 0:
                error_msg = stderr.strip() or f"Command failed with exit code {proc.returncode}"
                result.error_message = error_msg
                raise GastownCommandError(
                    message=error_msg,
                    command=cmd_str,
                    exit_code=proc.returncode or -1,
                    stderr=stderr,
                )
            
            return result
            
        except asyncio.TimeoutError:
            error_msg = f"Command timed out after {timeout or self.config.default_timeout}s"
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
    
    # ========================================================================
    # Convoy Management
    # ========================================================================
    
    async def convoy_create(
        self,
        name: str,
        priority: Union[ConvoyPriority, str] = ConvoyPriority.NORMAL,
        bead_ids: Optional[List[str]] = None,
        rig_id: Optional[str] = None,
        notify_human: bool = False,
        require_human_review: bool = False,
        is_mountain: bool = False,
        **options,
    ) -> Convoy:
        """Create a new convoy.
        
        Args:
            name: Convoy name.
            priority: Priority level.
            bead_ids: List of bead/issue IDs to include.
            rig_id: Associated rig ID.
            notify_human: Whether to notify human on completion.
            require_human_review: Whether to require human review.
            is_mountain: Enable mountain mode for autonomous execution.
            **options: Additional options.
            
        Returns:
            Created Convoy instance.
        """
        if isinstance(priority, str):
            try:
                priority = ConvoyPriority(priority.lower())
            except ValueError:
                raise GastownError(f"Invalid priority: {priority}")

        args = ["convoy", "create", name]
        args.extend(["--priority", priority.value])
        
        if bead_ids:
            for bead_id in bead_ids:
                args.extend(["--bead", bead_id])
        
        if rig_id:
            args.extend(["--rig", rig_id])
        
        if notify_human:
            args.append("--notify-human")
        
        if require_human_review:
            args.append("--require-review")
        
        if is_mountain:
            args.append("--mountain")
        
        # Add any additional options
        for key, value in options.items():
            if value is True:
                args.append(f"--{key.replace('_', '-')}")
            elif value is not None:
                args.extend([f"--{key.replace('_', '-')}", str(value)])
        
        result = await self._run_command(args)
        
        if result.parsed_output:
            return Convoy.model_validate(result.parsed_output)
        
        # Fallback: return basic convoy info
        return Convoy(
            id="",
            name=name,
            state=ConvoyState.FORMING,
            priority=priority,
            bead_ids=bead_ids or [],
            rig_id=rig_id,
            notify_human=notify_human,
            require_human_review=require_human_review,
            is_mountain=is_mountain,
        )
    
    async def convoy_list(
        self,
        state: Optional[Union[ConvoyState, str]] = None,
        rig_id: Optional[str] = None,
    ) -> List[Convoy]:
        """List all convoys.
        
        Args:
            state: Filter by state.
            rig_id: Filter by rig.
            
        Returns:
            List of Convoy instances.
        """
        args = ["convoy", "list"]
        
        if state:
            if isinstance(state, ConvoyState):
                state = state.value
            args.extend(["--state", state])
        
        if rig_id:
            args.extend(["--rig", rig_id])
        
        result = await self._run_command(args)
        
        if result.parsed_output:
            if isinstance(result.parsed_output, list):
                return [Convoy.model_validate(item) for item in result.parsed_output]
            elif "convoys" in result.parsed_output:
                return [Convoy.model_validate(item) for item in result.parsed_output["convoys"]]
        
        return []
    
    async def convoy_status(self, name_or_id: str) -> Convoy:
        """Get convoy status.
        
        Args:
            name_or_id: Convoy name or ID.
            
        Returns:
            Convoy instance with current status.
        """
        result = await self._run_command(["convoy", "status", name_or_id])
        
        if result.parsed_output:
            return Convoy.model_validate(result.parsed_output)
        
        raise GastownParseError(f"Failed to parse convoy status for {name_or_id}")
    
    async def convoy_archive(self, name_or_id: str) -> Convoy:
        """Archive a convoy.
        
        Args:
            name_or_id: Convoy name or ID to archive.
            
        Returns:
            Updated Convoy instance.
        """
        result = await self._run_command(["convoy", "archive", name_or_id])
        
        if result.parsed_output:
            return Convoy.model_validate(result.parsed_output)
        
        # Return minimal info if parsing fails
        return Convoy(
            id=name_or_id,
            name=name_or_id,
            state=ConvoyState.ARCHIVED,
        )
    
    async def convoy_add_bead(self, convoy_id: str, bead_id: str) -> Convoy:
        """Add a bead to a convoy.
        
        Args:
            convoy_id: Convoy ID.
            bead_id: Bead ID to add.
            
        Returns:
            Updated Convoy instance.
        """
        result = await self._run_command(
            ["convoy", "add", convoy_id, bead_id]
        )
        
        if result.parsed_output:
            return Convoy.model_validate(result.parsed_output)
        
        raise GastownParseError(f"Failed to add bead {bead_id} to convoy {convoy_id}")
    
    async def convoy_dispatch(self, convoy_id: str) -> Convoy:
        """Dispatch a convoy (start execution).
        
        Args:
            convoy_id: Convoy ID to dispatch.
            
        Returns:
            Updated Convoy instance.
        """
        result = await self._run_command(["convoy", "dispatch", convoy_id])
        
        if result.parsed_output:
            return Convoy.model_validate(result.parsed_output)
        
        raise GastownParseError(f"Failed to dispatch convoy {convoy_id}")
    
    # ========================================================================
    # Polecat (Agent) Operations
    # ========================================================================
    
    async def polecat_spawn(
        self,
        name: str,
        role: Union[PolecatRole, str] = PolecatRole.POLECAT,
        rig_id: Optional[str] = None,
        specialty: Optional[str] = None,
        runtime: str = "claude",
        convoy_id: Optional[str] = None,
        bead_id: Optional[str] = None,
        **options,
    ) -> Polecat:
        """Spawn a new polecat (agent).
        
        Args:
            name: Polecat name.
            role: Agent role.
            rig_id: Associated rig ID.
            specialty: Agent specialty (e.g., "rust", "frontend").
            runtime: Runtime provider (claude, codex, cursor).
            convoy_id: Convoy to assign to.
            bead_id: Bead to work on.
            **options: Additional options.
            
        Returns:
            Created Polecat instance.
        """
        if isinstance(role, str):
            try:
                role = PolecatRole(role.lower())
            except ValueError:
                raise GastownError(f"Invalid role: {role}")

        args = ["polecat", "spawn", name]
        args.extend(["--role", role.value])
        
        if rig_id:
            args.extend(["--rig", rig_id])
        
        if specialty:
            args.extend(["--specialty", specialty])
        
        if runtime:
            args.extend(["--runtime", runtime])
        
        if convoy_id:
            args.extend(["--convoy", convoy_id])
        
        if bead_id:
            args.extend(["--bead", bead_id])
        
        # Add additional options
        for key, value in options.items():
            if value is True:
                args.append(f"--{key.replace('_', '-')}")
            elif value is not None:
                args.extend([f"--{key.replace('_', '-')}", str(value)])
        
        result = await self._run_command(args)
        
        if result.parsed_output:
            return Polecat.model_validate(result.parsed_output)
        
        # Fallback
        return Polecat(
            id="",
            name=name,
            role=role,
            state=PolecatState.SPAWNING,
            rig_id=rig_id,
            specialty=specialty,
            runtime=runtime,
            bead_id=bead_id,
            convoy_id=convoy_id,
        )
    
    async def polecat_status(self, name_or_id: str) -> Polecat:
        """Get polecat status.
        
        Args:
            name_or_id: Polecat name or ID.
            
        Returns:
            Polecat instance with current status.
        """
        result = await self._run_command(["polecat", "status", name_or_id])
        
        if result.parsed_output:
            return Polecat.model_validate(result.parsed_output)
        
        raise GastownParseError(f"Failed to parse polecat status for {name_or_id}")
    
    async def polecat_list(
        self,
        state: Optional[Union[PolecatState, str]] = None,
        rig_id: Optional[str] = None,
    ) -> List[Polecat]:
        """List all polecats.
        
        Args:
            state: Filter by state.
            rig_id: Filter by rig.
            
        Returns:
            List of Polecat instances.
        """
        args = ["polecat", "list"]
        
        if state:
            if isinstance(state, PolecatState):
                state = state.value
            args.extend(["--state", state])
        
        if rig_id:
            args.extend(["--rig", rig_id])
        
        result = await self._run_command(args)
        
        if result.parsed_output:
            if isinstance(result.parsed_output, list):
                return [Polecat.model_validate(item) for item in result.parsed_output]
            elif "polecats" in result.parsed_output:
                return [Polecat.model_validate(item) for item in result.parsed_output["polecats"]]
        
        return []
    
    async def polecat_archive(self, name_or_id: str) -> Polecat:
        """Archive a polecat.
        
        Args:
            name_or_id: Polecat name or ID to archive.
            
        Returns:
            Updated Polecat instance.
        """
        result = await self._run_command(["polecat", "archive", name_or_id])
        
        if result.parsed_output:
            return Polecat.model_validate(result.parsed_output)
        
        return Polecat(
            id=name_or_id,
            name=name_or_id,
            state=PolecatState.ARCHIVED,
        )
    
    async def polecat_pause(self, name_or_id: str) -> Polecat:
        """Pause a polecat.
        
        Args:
            name_or_id: Polecat name or ID.
            
        Returns:
            Updated Polecat instance.
        """
        result = await self._run_command(["polecat", "pause", name_or_id])
        
        if result.parsed_output:
            return Polecat.model_validate(result.parsed_output)
        
        raise GastownParseError(f"Failed to pause polecat {name_or_id}")
    
    async def polecat_resume(self, name_or_id: str) -> Polecat:
        """Resume a paused polecat.
        
        Args:
            name_or_id: Polecat name or ID.
            
        Returns:
            Updated Polecat instance.
        """
        result = await self._run_command(["polecat", "resume", name_or_id])
        
        if result.parsed_output:
            return Polecat.model_validate(result.parsed_output)
        
        raise GastownParseError(f"Failed to resume polecat {name_or_id}")
    
    # ========================================================================
    # Rig Management
    # ========================================================================
    
    async def rig_list(self) -> List[Rig]:
        """List all rigs.
        
        Returns:
            List of Rig instances.
        """
        result = await self._run_command(["rig", "list"])
        
        if result.parsed_output:
            if isinstance(result.parsed_output, list):
                return [Rig.model_validate(item) for item in result.parsed_output]
            elif "rigs" in result.parsed_output:
                return [Rig.model_validate(item) for item in result.parsed_output["rigs"]]
        
        return []
    
    async def rig_status(self, name_or_id: str) -> Rig:
        """Get rig status.
        
        Args:
            name_or_id: Rig name or ID.
            
        Returns:
            Rig instance with current status.
        """
        result = await self._run_command(["rig", "status", name_or_id])
        
        if result.parsed_output:
            return Rig.model_validate(result.parsed_output)
        
        raise GastownParseError(f"Failed to parse rig status for {name_or_id}")
    
    async def rig_create(
        self,
        name: str,
        repo_url: Optional[str] = None,
        local_path: Optional[str] = None,
        runtime_provider: str = "claude",
        **options,
    ) -> Rig:
        """Create a new rig.
        
        Args:
            name: Rig name.
            repo_url: Repository URL.
            local_path: Local path to repository.
            runtime_provider: Default runtime provider.
            **options: Additional options.
            
        Returns:
            Created Rig instance.
        """
        args = ["rig", "create", name]
        
        if repo_url:
            args.extend(["--repo", repo_url])
        
        if local_path:
            args.extend(["--path", local_path])
        
        if runtime_provider:
            args.extend(["--runtime", runtime_provider])
        
        # Add additional options
        for key, value in options.items():
            if value is True:
                args.append(f"--{key.replace('_', '-')}")
            elif value is not None:
                args.extend([f"--{key.replace('_', '-')}", str(value)])
        
        result = await self._run_command(args)
        
        if result.parsed_output:
            return Rig.model_validate(result.parsed_output)
        
        return Rig(
            id="",
            name=name,
            repo_url=repo_url,
            local_path=local_path,
            runtime_provider=runtime_provider,
        )
    
    async def rig_archive(self, name_or_id: str) -> Rig:
        """Archive a rig.
        
        Args:
            name_or_id: Rig name or ID to archive.
            
        Returns:
            Updated Rig instance.
        """
        result = await self._run_command(["rig", "archive", name_or_id])
        
        if result.parsed_output:
            return Rig.model_validate(result.parsed_output)
        
        return Rig(
            id=name_or_id,
            name=name_or_id,
            state=RigState.ARCHIVED,
        )
    
    # ========================================================================
    # Hook Management
    # ========================================================================
    
    async def hook_list(
        self,
        rig_id: Optional[str] = None,
        state: Optional[Union[HookState, str]] = None,
    ) -> List[Hook]:
        """List all hooks.
        
        Args:
            rig_id: Filter by rig.
            state: Filter by state.
            
        Returns:
            List of Hook instances.
        """
        args = ["hook", "list"]
        
        if rig_id:
            args.extend(["--rig", rig_id])
        
        if state:
            if isinstance(state, HookState):
                state = state.value
            args.extend(["--state", state])
        
        result = await self._run_command(args)
        
        if result.parsed_output:
            if isinstance(result.parsed_output, list):
                return [Hook.model_validate(item) for item in result.parsed_output]
            elif "hooks" in result.parsed_output:
                return [Hook.model_validate(item) for item in result.parsed_output["hooks"]]
        
        return []
    
    async def hook_create(
        self,
        name: str,
        rig_id: str,
        base_branch: str = "main",
        agent_id: Optional[str] = None,
        **options,
    ) -> Hook:
        """Create a new hook.
        
        Args:
            name: Hook name.
            rig_id: Associated rig ID.
            base_branch: Base branch for the worktree.
            agent_id: Agent to assign to this hook.
            **options: Additional options.
            
        Returns:
            Created Hook instance.
        """
        args = ["hook", "create", name]
        args.extend(["--rig", rig_id])
        args.extend(["--branch", base_branch])
        
        if agent_id:
            args.extend(["--agent", agent_id])
        
        # Add additional options
        for key, value in options.items():
            if value is True:
                args.append(f"--{key.replace('_', '-')}")
            elif value is not None:
                args.extend([f"--{key.replace('_', '-')}", str(value)])
        
        result = await self._run_command(args)
        
        if result.parsed_output:
            return Hook.model_validate(result.parsed_output)
        
        return Hook(
            id="",
            name=name,
            rig_id=rig_id,
            base_branch=base_branch,
            agent_id=agent_id,
        )
    
    async def hook_status(self, name_or_id: str) -> Hook:
        """Get hook status.
        
        Args:
            name_or_id: Hook name or ID.
            
        Returns:
            Hook instance with current status.
        """
        result = await self._run_command(["hook", "status", name_or_id])
        
        if result.parsed_output:
            return Hook.model_validate(result.parsed_output)
        
        raise GastownParseError(f"Failed to parse hook status for {name_or_id}")
    
    async def hook_archive(self, name_or_id: str) -> Hook:
        """Archive a hook.
        
        Args:
            name_or_id: Hook name or ID to archive.
            
        Returns:
            Updated Hook instance.
        """
        result = await self._run_command(["hook", "archive", name_or_id])
        
        if result.parsed_output:
            return Hook.model_validate(result.parsed_output)
        
        return Hook(
            id=name_or_id,
            name=name_or_id,
            state=HookState.ARCHIVED,
        )
    
    # ========================================================================
    # Mail Operations
    # ========================================================================
    
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
                return [Mail.model_validate(item) for item in result.parsed_output["mail"]]
        
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
    
    # ========================================================================
    # Escalation Handling
    # ========================================================================
    
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
        
        # Fallback if parsing fails
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
                return [Escalation.model_validate(item) for item in result.parsed_output]
            elif "escalations" in result.parsed_output:
                return [Escalation.model_validate(item) for item in result.parsed_output["escalations"]]
        
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
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
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
