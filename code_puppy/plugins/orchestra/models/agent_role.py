"""Agent role definitions for Orchestra.

Maps Gastown's role concepts to Code Puppy's plugin architecture.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import uuid


class AgentRole(Enum):
    """Orchestra agent roles (inspired by Gastown).
    
    Each role has specific responsibilities in the orchestration hierarchy:
    """
    MAYOR = "mayor"           # Primary AI coordinator, user interface
    POLECAT = "polecat"       # Ephemeral worker agent
    CREW = "crew"             # Human workspace
    WITNESS = "witness"       # Per-rig health monitor
    DEACON = "deacon"         # Cross-rig supervisor
    DOG = "dog"               # Infrastructure/maintenance task runner
    REFINERY = "refinery"     # Merge queue processor


class AgentState(Enum):
    """Lifecycle states for an agent."""
    IDLE = "idle"             # Waiting for assignment
    SPAWNING = "spawning"     # Starting up
    ACTIVE = "active"         # Working on task
    PAUSED = "paused"         # Temporarily stopped
    STUCK = "stuck"           # Detected as unresponsive
    COMPLETING = "completing" # Finishing work
    ARCHIVED = "archived"     # Work done, archived


@dataclass
class AgentIdentity:
    """Persistent identity for an agent.
    
    Unlike ephemeral sessions, identity persists across restarts
    and is stored in git-backed hooks.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "unnamed"
    role: AgentRole = AgentRole.POLECAT
    rig_id: Optional[str] = None
    hook_path: Optional[Path] = None
    
    # Agent characteristics
    specialty: Optional[str] = None  # e.g., "rust", "frontend", "tests"
    runtime: str = "claude"  # claude, codex, cursor, etc.
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "rig_id": self.rig_id,
            "hook_path": str(self.hook_path) if self.hook_path else None,
            "specialty": self.specialty,
            "runtime": self.runtime,
            "created_at": self.created_at.isoformat(),
            "version": self.version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentIdentity":
        return cls(
            id=data["id"],
            name=data["name"],
            role=AgentRole(data["role"]),
            rig_id=data.get("rig_id"),
            hook_path=Path(data["hook_path"]) if data.get("hook_path") else None,
            specialty=data.get("specialty"),
            runtime=data.get("runtime", "claude"),
            created_at=datetime.fromisoformat(data["created_at"]),
            version=data.get("version", 1),
        )


@dataclass 
class AgentSession:
    """An ephemeral session of an agent.
    
    Sessions are temporary - they start, do work, and end.
    The AgentIdentity persists across sessions.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    identity_id: str = ""
    state: AgentState = AgentState.IDLE
    
    # Work assignment
    bead_id: Optional[str] = None  # Current bead/issue being worked
    convoy_id: Optional[str] = None  # Convoy this session belongs to
    
    # Timestamps
    spawned_at: datetime = field(default_factory=datetime.now)
    activated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    
    # Context
    working_dir: Optional[Path] = None
    context_snapshot: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "state": self.state.value,
            "bead_id": self.bead_id,
            "convoy_id": self.convoy_id,
            "spawned_at": self.spawned_at.isoformat(),
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "working_dir": str(self.working_dir) if self.working_dir else None,
            "context_snapshot": self.context_snapshot,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentSession":
        return cls(
            id=data["id"],
            identity_id=data["identity_id"],
            state=AgentState(data["state"]),
            bead_id=data.get("bead_id"),
            convoy_id=data.get("convoy_id"),
            spawned_at=datetime.fromisoformat(data["spawned_at"]),
            activated_at=datetime.fromisoformat(data["activated_at"]) if data.get("activated_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            last_heartbeat=datetime.fromisoformat(data["last_heartbeat"]) if data.get("last_heartbeat") else None,
            working_dir=Path(data["working_dir"]) if data.get("working_dir") else None,
            context_snapshot=data.get("context_snapshot", {}),
        )
