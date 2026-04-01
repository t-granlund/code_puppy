"""Pydantic models and enums for Gastown Client."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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
# Pydantic Models
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
