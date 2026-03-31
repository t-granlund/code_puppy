"""Hook (persistent storage) models.

Hooks are git worktree-based persistent storage for agent work.
Inspired by Gastown's hook system.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import uuid


class HookState(Enum):
    """Lifecycle states for a hook."""
    CREATING = "creating"     # Git worktree being set up
    READY = "ready"           # Ready for use
    ACTIVE = "active"         # Agent working in hook
    STALE = "stale"           # No recent activity
    ARCHIVED = "archived"     # Work done, hook archived


@dataclass
class Hook:
    """A git worktree-based persistent storage for agent work.
    
    Hooks provide:
    - Persistent state that survives agent restarts
    - Version control through git
    - Rollback capability
    - Multi-agent coordination through shared git history
    
    Each hook is a git worktree with:
    - work/ - The working directory
    - .orchestra/ - Metadata and state
    - mail/ - Incoming/outgoing mail
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "unnamed"
    
    state: HookState = HookState.CREATING
    
    # Git info
    worktree_path: Optional[Path] = None
    base_branch: str = "main"  # Branch this hook is based on
    current_branch: Optional[str] = None  # Hook's branch name
    
    # Ownership
    agent_id: Optional[str] = None  # Current occupant
    rig_id: Optional[str] = None  # Which rig this belongs to
    
    # Content
    bead_ids: List[str] = field(default_factory=list)  # Beads being worked
    context_files: List[str] = field(default_factory=list)  # Files preserving context
    
    # Mail
    mail_inbox: List[str] = field(default_factory=list)  # Unread mail IDs
    mail_sent: List[str] = field(default_factory=list)  # Sent mail IDs
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_commit: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    commit_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "state": self.state.value,
            "worktree_path": str(self.worktree_path) if self.worktree_path else None,
            "base_branch": self.base_branch,
            "current_branch": self.current_branch,
            "agent_id": self.agent_id,
            "rig_id": self.rig_id,
            "bead_ids": self.bead_ids,
            "context_files": self.context_files,
            "mail_inbox": self.mail_inbox,
            "mail_sent": self.mail_sent,
            "created_at": self.created_at.isoformat(),
            "last_commit": self.last_commit.isoformat() if self.last_commit else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "commit_count": self.commit_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hook":
        return cls(
            id=data["id"],
            name=data["name"],
            state=HookState(data.get("state", "creating")),
            worktree_path=Path(data["worktree_path"]) if data.get("worktree_path") else None,
            base_branch=data.get("base_branch", "main"),
            current_branch=data.get("current_branch"),
            agent_id=data.get("agent_id"),
            rig_id=data.get("rig_id"),
            bead_ids=data.get("bead_ids", []),
            context_files=data.get("context_files", []),
            mail_inbox=data.get("mail_inbox", []),
            mail_sent=data.get("mail_sent", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_commit=datetime.fromisoformat(data["last_commit"]) if data.get("last_commit") else None,
            last_activity=datetime.fromisoformat(data["last_activity"]) if data.get("last_activity") else None,
            commit_count=data.get("commit_count", 0),
        )
    
    def get_work_path(self) -> Optional[Path]:
        """Get the working directory path."""
        if self.worktree_path:
            return self.worktree_path / "work"
        return None
    
    def get_mail_path(self) -> Optional[Path]:
        """Get the mail directory path."""
        if self.worktree_path:
            return self.worktree_path / ".orchestra" / "mail"
        return None
    
    def get_state_path(self) -> Optional[Path]:
        """Get the state directory path."""
        if self.worktree_path:
            return self.worktree_path / ".orchestra" / "state"
        return None
    
    def record_activity(self) -> None:
        """Record that activity occurred in this hook."""
        self.last_activity = datetime.now()
    
    def record_commit(self) -> None:
        """Record a commit in this hook."""
        self.last_commit = datetime.now()
        self.commit_count += 1
        self.record_activity()
