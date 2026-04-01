"""Pydantic models for Beads (bd) CLI responses.

This module provides type-safe representations of all Go binary responses
from the bd (beads) command-line tool.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class BeadStatus(str, Enum):
    """Status enumeration for beads/issues."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    COMPLETE = "complete"
    CLOSED = "closed"
    ARCHIVED = "archived"


class Priority(str, Enum):
    """Priority levels for beads/issues."""
    P0 = "p0"  # Critical
    P1 = "p1"  # High
    P2 = "p2"  # Normal
    P3 = "p3"  # Low


class Issue(BaseModel):
    """Issue representation from bd CLI.
    
    Represents a tracked work item/issue in the beads system.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    
    id: str = Field(description="Unique issue identifier")
    title: str = Field(description="Issue title")
    description: Optional[str] = Field(default=None, description="Issue description")
    status: BeadStatus = Field(default=BeadStatus.OPEN, description="Current status")
    priority: Priority = Field(default=Priority.P2, description="Issue priority")
    
    # Relationships
    parent_id: Optional[str] = Field(default=None, description="Parent issue ID")
    bead_ids: List[str] = Field(default_factory=list, description="Associated bead IDs")
    
    # Assignment
    assignee: Optional[str] = Field(default=None, description="Assigned user/agent")
    creator: str = Field(description="Issue creator")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    closed_at: Optional[datetime] = Field(default=None, description="Close timestamp")
    
    # Metadata
    labels: List[str] = Field(default_factory=list, description="Issue labels/tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Molecule(BaseModel):
    """Workflow/molecule template from bd CLI.
    
    Molecules define reusable workflow patterns for executing tasks.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    
    id: str = Field(description="Unique molecule identifier")
    name: str = Field(description="Molecule name")
    description: Optional[str] = Field(default=None, description="Molecule description")
    
    # Template definition
    template: str = Field(description="Molecule template content")
    version: int = Field(default=1, description="Template version")
    
    # Configuration
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Template parameters")
    required_params: List[str] = Field(default_factory=list, description="Required parameter names")
    
    # Relationships
    parent_id: Optional[str] = Field(default=None, description="Parent molecule ID")
    tags: List[str] = Field(default_factory=list, description="Molecule tags")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    created_by: str = Field(description="Creator identifier")


class Gate(BaseModel):
    """Dependency gate from bd CLI.
    
    Gates control workflow progression based on conditions.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    
    id: str = Field(description="Unique gate identifier")
    name: str = Field(description="Gate name")
    description: Optional[str] = Field(default=None, description="Gate description")
    
    # Gate type and condition
    gate_type: str = Field(description="Type of gate (block, notify, etc.)")
    condition: str = Field(description="Gate condition expression")
    
    # State
    is_open: bool = Field(default=False, description="Whether gate is open")
    is_required: bool = Field(default=True, description="Whether gate must pass")
    
    # Dependencies
    depends_on: List[str] = Field(default_factory=list, description="Gate dependencies")
    blocking_issues: List[str] = Field(default_factory=list, description="Issues blocking this gate")
    
    # Relationships
    bead_id: Optional[str] = Field(default=None, description="Associated bead ID")
    molecule_id: Optional[str] = Field(default=None, description="Associated molecule ID")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    opened_at: Optional[datetime] = Field(default=None, description="When gate opened")
    created_by: str = Field(description="Creator identifier")


class Formula(BaseModel):
    """Formula/template definition from bd CLI.
    
    Formulas are executable task definitions.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    
    id: str = Field(description="Unique formula identifier")
    name: str = Field(description="Formula name")
    description: Optional[str] = Field(default=None, description="Formula description")
    
    # Formula definition
    command: str = Field(description="Command to execute")
    working_dir: Optional[str] = Field(default=None, description="Working directory")
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    
    # Execution config
    timeout_seconds: int = Field(default=300, description="Execution timeout")
    retry_count: int = Field(default=0, description="Number of retries")
    
    # Dependencies
    dependencies: List[str] = Field(default_factory=list, description="Formula dependencies")
    outputs: List[str] = Field(default_factory=list, description="Expected outputs")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    created_by: str = Field(description="Creator identifier")
    version: int = Field(default=1, description="Formula version")


class Wisp(BaseModel):
    """Molecule instance/execution from bd CLI.
    
    Wisps are running or completed instances of molecules.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    
    id: str = Field(description="Unique wisp identifier")
    molecule_id: str = Field(description="Parent molecule ID")
    
    # Execution state
    status: str = Field(default="pending", description="Execution status")
    exit_code: Optional[int] = Field(default=None, description="Process exit code")
    
    # Parameters
    params: Dict[str, Any] = Field(default_factory=dict, description="Instance parameters")
    
    # Output
    stdout: Optional[str] = Field(default=None, description="Standard output")
    stderr: Optional[str] = Field(default=None, description="Standard error")
    artifacts: List[str] = Field(default_factory=list, description="Output artifacts")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    
    # Metadata
    triggered_by: str = Field(description="Who/what triggered this wisp")
    bead_id: Optional[str] = Field(default=None, description="Associated bead ID")


class BeadListResult(BaseModel):
    """List response wrapper from bd CLI.
    
    Standard wrapper for paginated list responses.
    """
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    
    items: List[Dict[str, Any]] = Field(default_factory=list, description="List items")
    total: int = Field(default=0, description="Total item count")
    
    # Pagination
    page: int = Field(default=1, description="Current page")
    per_page: int = Field(default=20, description="Items per page")
    has_more: bool = Field(default=False, description="Whether more pages exist")
    
    # Metadata
    query_time_ms: Optional[int] = Field(default=None, description="Query execution time")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Applied filters")
