"""Convoy (work tracking) models.

Convoys bundle multiple beads (issues) that get assigned to agents.
Inspired by Gastown's convoy system.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Set
import uuid


class ConvoyState(Enum):
    """Lifecycle states for a convoy."""
    FORMING = "forming"       # Being created, beads being added
    MOUNTAIN = "mountain"     # Ready for dispatch, waiting for capacity
    DISPATCHING = "dispatching"  # Agents being assigned
    ACTIVE = "active"         # Work in progress
    STALLED = "stalled"       # Detected stuck
    COMPLETING = "completing"  # Work wrapping up
    ARCHIVED = "archived"     # All work done


class ConvoyPriority(Enum):
    """Priority levels for convoys."""
    CRITICAL = 0   # P0 - Drop everything
    HIGH = 1       # P1 - Urgent
    NORMAL = 2     # P2 - Standard
    LOW = 3        # P3 - Backlog


@dataclass
class Convoy:
    """A work convoy - bundles multiple beads for coordinated execution.
    
    Convoys are the primary unit of work orchestration in Orchestra.
    They track:
    - Which beads are included
    - Which agents are working on them
    - Overall progress and state
    - Notifications and handoffs
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "unnamed"
    
    state: ConvoyState = ConvoyState.FORMING
    priority: ConvoyPriority = ConvoyPriority.NORMAL
    
    # Work content
    bead_ids: List[str] = field(default_factory=list)  # Bead/issue IDs
    completed_beads: List[str] = field(default_factory=list)
    
    # Assignment
    rig_id: Optional[str] = None
    agent_ids: Set[str] = field(default_factory=set)
    
    # Configuration
    notify_human: bool = False  # Notify on completion
    require_human_review: bool = False
    auto_close: bool = True  # Auto-close when all beads done
    
    # Mountain mode (epic-scale execution)
    is_mountain: bool = False  # Enables autonomous stall detection
    max_stall_minutes: int = 30  # Stall detection threshold
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None  # Agent/person who created
    
    # Progress tracking
    progress_pct: float = 0.0
    last_update: Optional[datetime] = None
    notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "state": self.state.value,
            "priority": self.priority.value,
            "bead_ids": self.bead_ids,
            "completed_beads": self.completed_beads,
            "rig_id": self.rig_id,
            "agent_ids": list(self.agent_ids),
            "notify_human": self.notify_human,
            "require_human_review": self.require_human_review,
            "auto_close": self.auto_close,
            "is_mountain": self.is_mountain,
            "max_stall_minutes": self.max_stall_minutes,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_by": self.created_by,
            "progress_pct": self.progress_pct,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Convoy":
        return cls(
            id=data["id"],
            name=data["name"],
            state=ConvoyState(data.get("state", "forming")),
            priority=ConvoyPriority(data.get("priority", 2)),
            bead_ids=data.get("bead_ids", []),
            completed_beads=data.get("completed_beads", []),
            rig_id=data.get("rig_id"),
            agent_ids=set(data.get("agent_ids", [])),
            notify_human=data.get("notify_human", False),
            require_human_review=data.get("require_human_review", False),
            auto_close=data.get("auto_close", True),
            is_mountain=data.get("is_mountain", False),
            max_stall_minutes=data.get("max_stall_minutes", 30),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            created_by=data.get("created_by"),
            progress_pct=data.get("progress_pct", 0.0),
            last_update=datetime.fromisoformat(data["last_update"]) if data.get("last_update") else None,
            notes=data.get("notes", []),
        )
    
    def add_bead(self, bead_id: str) -> None:
        """Add a bead to this convoy."""
        if bead_id not in self.bead_ids:
            self.bead_ids.append(bead_id)
            self._update_progress()
    
    def mark_bead_complete(self, bead_id: str) -> None:
        """Mark a bead as completed."""
        if bead_id in self.bead_ids and bead_id not in self.completed_beads:
            self.completed_beads.append(bead_id)
            self._update_progress()
            
            # Check if convoy is complete
            if set(self.bead_ids) == set(self.completed_beads):
                self.state = ConvoyState.COMPLETING
    
    def _update_progress(self) -> None:
        """Recalculate progress percentage."""
        if not self.bead_ids:
            self.progress_pct = 0.0
        else:
            self.progress_pct = len(self.completed_beads) / len(self.bead_ids) * 100
        self.last_update = datetime.now()
    
    def assign_agent(self, agent_id: str) -> None:
        """Assign an agent to this convoy."""
        self.agent_ids.add(agent_id)
        if self.state == ConvoyState.FORMING:
            self.state = ConvoyState.DISPATCHING
        self.last_update = datetime.now()
