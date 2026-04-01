"""Pydantic models for Gastown (gt) CLI responses.

This module provides type-safe representations of all Go binary responses
from the gt (gastown) command-line tool for agent orchestration.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field


class AgentRole(str, Enum):
    """Role definition for agents in Gastown."""
    MAYOR = "mayor"           # Primary AI coordinator, user interface
    POLECAT = "polecat"       # Ephemeral worker agent
    CREW = "crew"             # Human workspace
    WITNESS = "witness"       # Per-rig health monitor
    DEACON = "deacon"         # Cross-rig supervisor
    DOG = "dog"               # Infrastructure/maintenance task runner
    REFINERY = "refinery"     # Merge queue processor


class AgentState(str, Enum):
    """Lifecycle states for an agent."""
    IDLE = "idle"             # Waiting for assignment
    SPAWNING = "spawning"     # Starting up
    ACTIVE = "active"         # Working on task
    PAUSED = "paused"         # Temporarily stopped
    STUCK = "stuck"           # Detected as unresponsive
    COMPLETING = "completing" # Finishing work
    ARCHIVED = "archived"     # Work done, archived


class ConvoyState(str, Enum):
    """Lifecycle states for a convoy."""
    FORMING = "forming"         # Being created, beads being added
    MOUNTAIN = "mountain"       # Ready for dispatch, waiting for capacity
    DISPATCHING = "dispatching" # Agents being assigned
    ACTIVE = "active"           # Work in progress
    STALLED = "stalled"         # Detected stuck
    COMPLETING = "completing"   # Work wrapping up
    ARCHIVED = "archived"       # All work done


class Polecat(BaseModel):
    """Agent/agent identity from Gastown CLI.
    
    Represents a persistent agent identity in the Gastown system.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    
    id: str = Field(description="Unique agent identifier")
    name: str = Field(description="Agent name")
    
    # Role and characteristics
    role: AgentRole = Field(default=AgentRole.POLECAT, description="Agent role")
    specialty: Optional[str] = Field(default=None, description="Agent specialty (e.g., 'rust', 'frontend')")
    runtime: str = Field(default="claude", description="AI runtime (claude, codex, cursor, etc.)")
    
    # Assignment
    rig_id: Optional[str] = Field(default=None, description="Assigned rig ID")
    convoy_id: Optional[str] = Field(default=None, description="Active convoy ID")
    
    # State
    state: AgentState = Field(default=AgentState.IDLE, description="Current state")
    
    # Identity persistence
    hook_path: Optional[str] = Field(default=None, description="Path to git-backed hook")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    version: int = Field(default=1, description="Identity version")
    
    # Session tracking
    current_session_id: Optional[str] = Field(default=None, description="Current session ID if active")
    session_count: int = Field(default=0, description="Total sessions completed")


class Convoy(BaseModel):
    """Work bundle/coordination unit from Gastown CLI.
    
    Represents a convoy - a bundle of work items coordinated together.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    
    id: str = Field(description="Unique convoy identifier")
    name: str = Field(description="Convoy name")
    
    # State
    state: ConvoyState = Field(default=ConvoyState.FORMING, description="Current state")
    priority: int = Field(default=2, description="Priority (0=critical, 3=low)")
    
    # Work content
    bead_ids: List[str] = Field(default_factory=list, description="Bead/issue IDs in convoy")
    completed_beads: List[str] = Field(default_factory=list, description="Completed bead IDs")
    
    # Assignment
    rig_id: Optional[str] = Field(default=None, description="Assigned rig ID")
    agent_ids: Set[str] = Field(default_factory=set, description="Assigned agent IDs")
    
    # Configuration
    notify_human: bool = Field(default=False, description="Notify on completion")
    require_human_review: bool = Field(default=False, description="Require human review")
    auto_close: bool = Field(default=True, description="Auto-close when done")
    
    # Mountain mode (epic-scale execution)
    is_mountain: bool = Field(default=False, description="Mountain mode enabled")
    max_stall_minutes: int = Field(default=30, description="Stall detection threshold")
    
    # Progress
    progress_pct: float = Field(default=0.0, description="Completion percentage")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator ID")
    
    # Updates
    last_update: Optional[datetime] = Field(default=None, description="Last update timestamp")
    notes: List[str] = Field(default_factory=list, description="Convoy notes")


class Rig(BaseModel):
    """Project/workspace context from Gastown CLI.
    
    Represents a rig - a project workspace in Gastown.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    
    id: str = Field(description="Unique rig identifier")
    name: str = Field(description="Rig name")
    
    # Location
    path: str = Field(description="Filesystem path")
    remote_url: Optional[str] = Field(default=None, description="Git remote URL")
    
    # State
    is_active: bool = Field(default=True, description="Whether rig is active")
    is_mountain_capable: bool = Field(default=False, description="Can run mountain mode")
    
    # Configuration
    default_runtime: str = Field(default="claude", description="Default AI runtime")
    max_agents: int = Field(default=5, description="Maximum concurrent agents")
    
    # Agents
    agent_ids: List[str] = Field(default_factory=list, description="Registered agent IDs")
    polecat_count: int = Field(default=0, description="Number of polecats")
    
    # Convoys
    active_convoy_ids: List[str] = Field(default_factory=list, description="Active convoy IDs")
    archived_convoy_ids: List[str] = Field(default_factory=list, description="Archived convoy IDs")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    last_activity: Optional[datetime] = Field(default=None, description="Last activity timestamp")


class Hook(BaseModel):
    """Trigger/hook definition from Gastown CLI.
    
    Represents a git hook or trigger in the Gastown system.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    
    id: str = Field(description="Unique hook identifier")
    name: str = Field(description="Hook name")
    path: str = Field(description="Hook file path")
    
    # Hook type
    hook_type: str = Field(description="Type (pre-commit, post-merge, etc.)")
    event: str = Field(description="Triggering event")
    
    # Content
    script: str = Field(description="Hook script content")
    is_executable: bool = Field(default=True, description="Whether hook is executable")
    
    # Association
    rig_id: str = Field(description="Associated rig ID")
    agent_id: Optional[str] = Field(default=None, description="Associated agent ID")
    
    # State
    is_enabled: bool = Field(default=True, description="Whether hook is enabled")
    last_triggered: Optional[datetime] = Field(default=None, description="Last trigger timestamp")
    trigger_count: int = Field(default=0, description="Total triggers")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    created_by: str = Field(description="Creator ID")


class Mail(BaseModel):
    """Message between agents from Gastown CLI.
    
    Represents a message passed between agents.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    
    id: str = Field(description="Unique message identifier")
    
    # Sender/recipient
    from_agent: str = Field(description="Sender agent ID")
    to_agent: str = Field(description="Recipient agent ID")
    
    # Content
    subject: str = Field(description="Message subject")
    body: str = Field(description="Message body")
    
    # Priority
    priority: str = Field(default="normal", description="Message priority")
    
    # Threading
    thread_id: Optional[str] = Field(default=None, description="Thread ID")
    in_reply_to: Optional[str] = Field(default=None, description="Parent message ID")
    
    # State
    is_read: bool = Field(default=False, description="Whether message has been read")
    is_urgent: bool = Field(default=False, description="Urgent flag")
    
    # Timestamps
    sent_at: datetime = Field(default_factory=datetime.now, description="Send timestamp")
    read_at: Optional[datetime] = Field(default=None, description="Read timestamp")
    
    # Context
    convoy_id: Optional[str] = Field(default=None, description="Associated convoy ID")
    bead_id: Optional[str] = Field(default=None, description="Associated bead ID")
    
    # Attachments
    attachments: List[Dict[str, Any]] = Field(default_factory=list, description="Message attachments")


class Escalation(BaseModel):
    """Escalation record from Gastown CLI.
    
    Represents an escalation event in the system.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    
    id: str = Field(description="Unique escalation identifier")
    
    # Escalation type
    escalation_type: str = Field(description="Type of escalation (stuck_agent, failed_task, etc.)")
    severity: str = Field(default="medium", description="Escalation severity")
    
    # Source
    source_agent_id: Optional[str] = Field(default=None, description="Agent that triggered escalation")
    source_convoy_id: Optional[str] = Field(default=None, description="Convoy that triggered escalation")
    
    # Description
    description: str = Field(description="Escalation description")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    
    # Assignment
    assigned_to: Optional[str] = Field(default=None, description="Assigned handler")
    
    # State
    status: str = Field(default="open", description="Escalation status")
    resolution: Optional[str] = Field(default=None, description="Resolution notes")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    resolved_at: Optional[datetime] = Field(default=None, description="Resolution timestamp")
    
    # Notifications
    notifications_sent: List[str] = Field(default_factory=list, description="Notification recipients")
