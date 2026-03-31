"""Rig (project container) models.

A Rig wraps a git repository and manages its associated agents.
Inspired by Gastown's rig concept.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Set
from pathlib import Path
import uuid


class RigState(Enum):
    """Lifecycle states for a rig."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


@dataclass
class RigConfig:
    """Per-rig configuration."""
    # Agent runtime settings
    runtime_provider: str = "claude"  # claude, codex, cursor, etc.
    runtime_command: Optional[str] = None
    runtime_args: List[str] = field(default_factory=list)
    
    # Auto-spawn settings
    max_polecats: int = 5
    auto_spawn_witness: bool = True
    
    # Hook settings
    hooks_enabled: bool = True
    hooks_base_dir: Optional[str] = None
    
    # Beads integration
    beads_project: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "runtime_provider": self.runtime_provider,
            "runtime_command": self.runtime_command,
            "runtime_args": self.runtime_args,
            "max_polecats": self.max_polecats,
            "auto_spawn_witness": self.auto_spawn_witness,
            "hooks_enabled": self.hooks_enabled,
            "hooks_base_dir": self.hooks_base_dir,
            "beads_project": self.beads_project,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RigConfig":
        return cls(
            runtime_provider=data.get("runtime_provider", "claude"),
            runtime_command=data.get("runtime_command"),
            runtime_args=data.get("runtime_args", []),
            max_polecats=data.get("max_polecats", 5),
            auto_spawn_witness=data.get("auto_spawn_witness", True),
            hooks_enabled=data.get("hooks_enabled", True),
            hooks_base_dir=data.get("hooks_base_dir"),
            beads_project=data.get("beads_project"),
        )


@dataclass
class Rig:
    """A project container (rig) in the Orchestra system.
    
    A rig wraps a git repository and provides:
    - Isolated workspace for agents
    - Hook-based persistent storage
    - Per-project configuration
    - Agent management
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "unnamed"
    repo_url: Optional[str] = None
    local_path: Optional[Path] = None
    
    state: RigState = RigState.INITIALIZING
    config: RigConfig = field(default_factory=RigConfig)
    
    # Agent tracking
    agent_ids: Set[str] = field(default_factory=set)
    crew_ids: Set[str] = field(default_factory=set)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_active: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "repo_url": self.repo_url,
            "local_path": str(self.local_path) if self.local_path else None,
            "state": self.state.value,
            "config": self.config.to_dict(),
            "agent_ids": list(self.agent_ids),
            "crew_ids": list(self.crew_ids),
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat() if self.last_active else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rig":
        return cls(
            id=data["id"],
            name=data["name"],
            repo_url=data.get("repo_url"),
            local_path=Path(data["local_path"]) if data.get("local_path") else None,
            state=RigState(data.get("state", "initializing")),
            config=RigConfig.from_dict(data.get("config", {})),
            agent_ids=set(data.get("agent_ids", [])),
            crew_ids=set(data.get("crew_ids", [])),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_active=datetime.fromisoformat(data["last_active"]) if data.get("last_active") else None,
        )
    
    def get_hooks_path(self, town_path: Path) -> Path:
        """Get the hooks directory for this rig."""
        base = self.config.hooks_base_dir or ".orchestra/hooks"
        if self.local_path:
            return self.local_path / base
        return town_path / self.name / base
    
    def get_crew_path(self, town_path: Path) -> Path:
        """Get the crew workspace directory for this rig."""
        if self.local_path:
            return self.local_path / "crew"
        return town_path / self.name / "crew"
