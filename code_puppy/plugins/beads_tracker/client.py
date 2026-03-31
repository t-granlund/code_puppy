"""Beads CLI client wrapper.

Provides a Python interface to the `bd` command-line tool.
"""

import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger(__name__)


@dataclass
class Bead:
    """Represents a bead (issue) from Beads."""
    id: str
    title: str
    description: str = ""
    status: str = "open"
    priority: int = 2  # 0=P0, 1=P1, 2=P2, 3=P3
    assignee: Optional[str] = None
    creator: Optional[str] = None
    parent: Optional[str] = None
    labels: List[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []
        if self.metadata is None:
            self.metadata = {}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Bead":
        """Create a Bead from a dictionary (bd JSON output)."""
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            status=data.get("status", "open"),
            priority=data.get("priority", 2),
            assignee=data.get("assignee"),
            creator=data.get("creator"),
            parent=data.get("parent"),
            labels=data.get("labels", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            closed_at=datetime.fromisoformat(data["closed_at"]) if data.get("closed_at") else None,
            metadata=data.get("metadata", {}),
        )


class BeadsError(Exception):
    """Error from beads CLI."""
    pass


class BeadsClient:
    """Client for the beads CLI (`bd`)."""
    
    def __init__(self, cwd: Optional[Path] = None, beads_dir: Optional[Path] = None):
        """Initialize the beads client.
        
        Args:
            cwd: Working directory for beads commands
            beads_dir: Override BEADS_DIR environment variable
        """
        self.cwd = cwd or Path.cwd()
        self.beads_dir = beads_dir
        self._check_beads()
    
    def _check_beads(self) -> None:
        """Verify beads CLI is available."""
        try:
            result = subprocess.run(
                ["bd", "version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise BeadsError("beads CLI not properly installed")
        except FileNotFoundError:
            raise BeadsError("beads CLI (bd) not found. Install: https://github.com/steveyegge/beads")
    
    def _run(self, args: List[str], json_output: bool = True) -> Union[Dict, str]:
        """Run a beads command.
        
        Args:
            args: Command arguments
            json_output: Expect JSON output
            
        Returns:
            Parsed JSON or raw string output
        """
        cmd = ["bd"] + args
        if json_output and "--json" not in args:
            cmd.append("--json")
        
        env = {}
        if self.beads_dir:
            env["BEADS_DIR"] = str(self.beads_dir)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                raise BeadsError(f"beads command failed: {error_msg}")
            
            if json_output:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Some commands don't output valid JSON
                    return {"raw": result.stdout}
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            raise BeadsError("beads command timed out")
    
    # Core bead operations
    
    def init(self, stealth: bool = False) -> Dict:
        """Initialize beads in the current directory."""
        args = ["init"]
        if stealth:
            args.append("--stealth")
        return self._run(args)
    
    def create(
        self,
        title: str,
        description: str = "",
        priority: int = 2,
        assignee: Optional[str] = None,
        parent: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> Bead:
        """Create a new bead."""
        args = ["create", title]
        
        if description:
            args.extend(["-d", description])
        if priority != 2:
            args.extend(["-p", str(priority)])
        if assignee:
            args.extend(["-a", assignee])
        if parent:
            args.extend(["--parent", parent])
        if labels:
            for label in labels:
                args.extend(["-l", label])
        
        result = self._run(args)
        return Bead.from_dict(result)
    
    def show(self, bead_id: str) -> Bead:
        """Show details of a bead."""
        result = self._run(["show", bead_id])
        return Bead.from_dict(result)
    
    def list(
        self,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        limit: int = 100,
    ) -> List[Bead]:
        """List beads."""
        args = ["list"]
        
        if status:
            args.extend(["-s", status])
        if assignee:
            args.extend(["-a", assignee])
        if limit != 100:
            args.extend(["-n", str(limit)])
        
        result = self._run(args)
        beads_data = result if isinstance(result, list) else result.get("beads", [])
        return [Bead.from_dict(b) for b in beads_data]
    
    def ready(self, assignee: Optional[str] = None) -> List[Bead]:
        """List beads that are ready to work (no blockers)."""
        args = ["ready"]
        if assignee:
            args.extend(["-a", assignee])
        
        result = self._run(args)
        beads_data = result if isinstance(result, list) else result.get("beads", [])
        return [Bead.from_dict(b) for b in beads_data]
    
    def update(
        self,
        bead_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        assignee: Optional[str] = None,
        claim: bool = False,
    ) -> Bead:
        """Update a bead."""
        args = ["update", bead_id]
        
        if title:
            args.extend(["-t", title])
        if description:
            args.extend(["-d", description])
        if status:
            args.extend(["-s", status])
        if priority is not None:
            args.extend(["-p", str(priority)])
        if assignee:
            args.extend(["-a", assignee])
        if claim:
            args.append("--claim")
        
        result = self._run(args)
        return Bead.from_dict(result)
    
    def close(self, bead_id: str, message: str = "") -> Bead:
        """Close a bead."""
        args = ["close", bead_id]
        if message:
            args.extend(["-m", message])
        
        result = self._run(args)
        return Bead.from_dict(result)
    
    # Dependency management
    
    def dep_add(
        self,
        child: str,
        parent: str,
        dep_type: str = "blocks",
    ) -> Dict:
        """Add a dependency between beads.
        
        Args:
            child: The blocked bead
            parent: The blocking bead  
            dep_type: Type of dependency (blocks, relates_to, duplicates, supersedes)
        """
        return self._run(["dep", "add", child, parent, "-t", dep_type])
    
    def dep_remove(self, child: str, parent: str) -> Dict:
        """Remove a dependency between beads."""
        return self._run(["dep", "remove", child, parent])
    
    def dep_list(self, bead_id: str) -> Dict:
        """List dependencies for a bead."""
        return self._run(["dep", "list", bead_id])
    
    # Formula/Molecule operations
    
    def formula_list(self) -> List[Dict]:
        """List available formulas."""
        result = self._run(["formula", "list"])
        return result if isinstance(result, list) else result.get("formulas", [])
    
    def cook(self, formula: str, variables: Optional[Dict[str, str]] = None) -> Dict:
        """Execute a formula."""
        args = ["cook", formula]
        if variables:
            for key, value in variables.items():
                args.extend(["--var", f"{key}={value}"])
        return self._run(args)
    
    def mol_pour(self, formula: str, variables: Optional[Dict[str, str]] = None) -> Dict:
        """Create a trackable molecule instance from a formula."""
        args = ["mol", "pour", formula]
        if variables:
            for key, value in variables.items():
                args.extend(["--var", f"{key}={value}"])
        return self._run(args)
    
    # Utility
    
    def prime(self, bead_id: Optional[str] = None) -> str:
        """Get context priming for beads (ready tasks summary)."""
        args = ["prime"]
        if bead_id:
            args.append(bead_id)
        return self._run(args, json_output=False)
    
    def compact(self, dry_run: bool = False) -> Dict:
        """Compact closed beads to save context."""
        args = ["compact"]
        if dry_run:
            args.append("--dry-run")
        return self._run(args)
    
    def status(self) -> Dict:
        """Get beads status."""
        return self._run(["status"])
