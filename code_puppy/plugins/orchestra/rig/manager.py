"""Rig (project) manager for Orchestra.

Manages rigs - project containers that wrap git repositories.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..models import Rig, RigState, RigConfig
from .. import DEFAULT_TOWN_DIR, CONFIG_SUBDIR

logger = logging.getLogger(__name__)


class RigManager:
    """Manages rigs (projects) in the Orchestra system."""
    
    _instance = None
    
    def __new__(cls, town_path: Optional[Path] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, town_path: Optional[Path] = None):
        if self._initialized:
            return
            
        self.town_path = town_path or DEFAULT_TOWN_DIR
        self.rigs: Dict[str, Rig] = {}
        self._config_path = self.town_path / CONFIG_SUBDIR / "rigs.json"
        
        self._load_rigs()
        self._initialized = True
        logger.debug(f"RigManager initialized with town path: {self.town_path}")
    
    def _load_rigs(self) -> None:
        """Load rigs from persistent storage."""
        if self._config_path.exists():
            try:
                with open(self._config_path, 'r') as f:
                    data = json.load(f)
                    for rig_data in data.get("rigs", []):
                        rig = Rig.from_dict(rig_data)
                        self.rigs[rig.id] = rig
                        self.rigs[rig.name] = rig  # Also index by name
                logger.debug(f"Loaded {len(self.rigs) // 2} rigs")
            except Exception as e:
                logger.error(f"Failed to load rigs: {e}")
    
    def _save_rigs(self) -> None:
        """Save rigs to persistent storage."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Deduplicate by ID
        seen_ids = set()
        unique_rigs = []
        for rig in self.rigs.values():
            if rig.id not in seen_ids:
                seen_ids.add(rig.id)
                unique_rigs.append(rig.to_dict())
        
        try:
            with open(self._config_path, 'w') as f:
                json.dump({"rigs": unique_rigs}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save rigs: {e}")
    
    def create_rig(
        self,
        name: str,
        repo_url: Optional[str] = None,
        local_path: Optional[Path] = None,
        config: Optional[RigConfig] = None,
    ) -> Rig:
        """Create a new rig.
        
        Args:
            name: Unique name for the rig
            repo_url: Git repository URL (optional)
            local_path: Local path to existing repo (optional)
            config: Rig configuration
            
        Returns:
            The created Rig
        """
        if name in self.rigs:
            raise ValueError(f"Rig '{name}' already exists")
        
        rig = Rig(
            name=name,
            repo_url=repo_url,
            local_path=local_path,
            config=config or RigConfig(),
        )
        
        # Create rig directory structure
        rig_path = self._ensure_rig_structure(rig)
        rig.local_path = rig_path
        
        self.rigs[rig.id] = rig
        self.rigs[rig.name] = rig
        self._save_rigs()
        
        logger.info(f"Created rig '{name}' (id: {rig.id})")
        return rig
    
    def _ensure_rig_structure(self, rig: Rig) -> Path:
        """Ensure rig directory structure exists."""
        if rig.local_path and rig.local_path.exists():
            return rig.local_path
            
        rig_path = self.town_path / rig.name
        rig_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (rig_path / "crew").mkdir(exist_ok=True)
        (rig_path / ".orchestra" / "hooks").mkdir(parents=True, exist_ok=True)
        (rig_path / ".orchestra" / "state").mkdir(parents=True, exist_ok=True)
        
        # Create README
        readme = rig_path / "README.md"
        if not readme.exists():
            readme.write_text(f"""# {rig.name} Rig

This is an Orchestra rig for project '{rig.name}'.

## Structure
- `crew/` - Crew workspaces
- `.orchestra/hooks/` - Agent persistent storage
- `.orchestra/state/` - Rig state

## Quick Commands
- List agents: `orchestra agents list --rig {rig.name}`
- Spawn polecat: `orchestra spawn --rig {rig.name} <task>`
- Create convoy: `orchestra convoy create --rig {rig.name} <name>`
""")
        
        return rig_path
    
    def get_rig(self, name_or_id: str) -> Optional[Rig]:
        """Get a rig by name or ID."""
        return self.rigs.get(name_or_id)
    
    def list_rigs(self) -> List[Rig]:
        """List all rigs (deduplicated)."""
        seen = set()
        result = []
        for rig in self.rigs.values():
            if rig.id not in seen:
                seen.add(rig.id)
                result.append(rig)
        return result
    
    def remove_rig(self, name_or_id: str) -> bool:
        """Remove a rig."""
        rig = self.rigs.get(name_or_id)
        if not rig:
            return False
        
        # Remove from both indexes
        keys_to_remove = [k for k, v in self.rigs.items() if v.id == rig.id]
        for key in keys_to_remove:
            del self.rigs[key]
        
        self._save_rigs()
        logger.info(f"Removed rig '{rig.name}'")
        return True
    
    def get_rig_path(self, rig: Rig) -> Path:
        """Get the base path for a rig."""
        if rig.local_path:
            return rig.local_path
        return self.town_path / rig.name
    
    def sync_rig(self, rig: Rig) -> bool:
        """Sync a rig with its remote repository."""
        if not rig.repo_url or not rig.local_path:
            return False
        
        try:
            result = subprocess.run(
                ["git", "pull", "--ff-only"],
                cwd=rig.local_path,
                capture_output=True,
                text=True,
                timeout=60,
            )
            success = result.returncode == 0
            if success:
                rig.last_active = datetime.now()
                self._save_rigs()
            return success
        except Exception as e:
            logger.error(f"Failed to sync rig {rig.name}: {e}")
            return False
    
    def get_active_rigs(self) -> List[Rig]:
        """Get all active rigs."""
        return [r for r in self.list_rigs() if r.state == RigState.ACTIVE]
    
    def get_rig_for_path(self, path: Path) -> Optional[Rig]:
        """Find which rig contains the given path."""
        path = path.resolve()
        for rig in self.list_rigs():
            if rig.local_path:
                rig_path = rig.local_path.resolve()
                try:
                    path.relative_to(rig_path)
                    return rig
                except ValueError:
                    continue
        return None
