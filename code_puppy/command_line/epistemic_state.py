"""Epistemic state management for structured planning workflows.

This module tracks the state for epistemic planning sessions, including:
- Current pipeline stage (0-12)
- Assumptions, hypotheses, constraints
- Lens evaluations and gaps
- Goal candidates and gate results
- Build progress tracking

Integrates with the Epistemic Agent Runtime (EAR) methodology.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import json
import os


class GapSeverity(Enum):
    """Gap severity levels for prioritization."""
    CRITICAL = "critical"  # Must resolve before building
    HIGH = "high"          # Should resolve soon
    MEDIUM = "medium"      # Important but can iterate
    LOW = "low"            # Nice to have


class GateStatus(Enum):
    """Status of a quality gate check."""
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"


@dataclass
class Assumption:
    """An assumption in the epistemic state."""
    text: str
    confidence: float  # 0.0 to 1.0
    source: str = "user"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at,
        }


@dataclass
class Hypothesis:
    """A testable hypothesis."""
    text: str
    falsification_criteria: str
    confidence: float = 0.5
    status: str = "open"  # open, validated, invalidated
    evidence: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "falsification_criteria": self.falsification_criteria,
            "confidence": self.confidence,
            "status": self.status,
            "evidence": self.evidence,
        }


@dataclass
class Gap:
    """An identified gap in the epistemic state."""
    description: str
    severity: GapSeverity
    lens: str  # Which lens identified it
    resolution: Optional[str] = None
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "severity": self.severity.value,
            "lens": self.lens,
            "resolution": self.resolution,
            "resolved": self.resolved,
        }


@dataclass
class GateCheck:
    """Result of a quality gate check."""
    gate_name: str
    status: GateStatus
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_name": self.gate_name,
            "status": self.status.value,
            "notes": self.notes,
        }


@dataclass
class CandidateGoal:
    """A goal candidate that must pass gates."""
    description: str
    gate_checks: List[GateCheck] = field(default_factory=list)
    approved: bool = False
    lens_approvals: List[str] = field(default_factory=list)
    
    def passes_all_gates(self) -> bool:
        """Check if all 6 gates are passed."""
        if len(self.gate_checks) < 6:
            return False
        return all(gc.status == GateStatus.PASSED for gc in self.gate_checks)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "gate_checks": [gc.to_dict() for gc in self.gate_checks],
            "approved": self.approved,
            "lens_approvals": self.lens_approvals,
        }


@dataclass  
class Milestone:
    """A build milestone within a phase."""
    name: str
    checkpoint_question: str
    status: str = "pending"  # pending, in_progress, completed, blocked
    completed_at: Optional[str] = None
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "checkpoint_question": self.checkpoint_question,
            "status": self.status,
            "completed_at": self.completed_at,
            "notes": self.notes,
        }


@dataclass
class BuildPhase:
    """A phase in the build plan."""
    name: str
    goal: str
    milestones: List[Milestone] = field(default_factory=list)
    status: str = "pending"  # pending, in_progress, completed
    rollback_plan: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "goal": self.goal,
            "milestones": [m.to_dict() for m in self.milestones],
            "status": self.status,
            "rollback_plan": self.rollback_plan,
        }


@dataclass
class EpistemicSessionState:
    """Complete epistemic session state container."""
    
    # Metadata
    project_name: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Pipeline stage (0-12)
    current_stage: int = 0
    stage_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Stage 1: Epistemic State
    problem_statement: str = ""
    target_users: str = ""
    assumptions: List[Assumption] = field(default_factory=list)
    hypotheses: List[Hypothesis] = field(default_factory=list)
    hard_constraints: List[str] = field(default_factory=list)
    soft_constraints: List[str] = field(default_factory=list)
    evidence: List[Dict[str, str]] = field(default_factory=list)
    
    # Stage 2: Lens Outputs
    lens_outputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Stage 3: Gaps
    gaps: List[Gap] = field(default_factory=list)
    
    # Stage 4: Goals
    candidate_goals: List[CandidateGoal] = field(default_factory=list)
    approved_goals: List[str] = field(default_factory=list)
    
    # Stage 5-6: Build Plan
    build_phases: List[BuildPhase] = field(default_factory=list)
    specs_ready: bool = False
    readiness_approved: bool = False
    
    # Stage 7+: Execution tracking
    current_phase: int = 0
    current_milestone: int = 0
    checkpoints_completed: List[Dict[str, Any]] = field(default_factory=list)
    
    # Pause/Resume
    paused: bool = False
    pause_reason: Optional[str] = None
    
    def advance_stage(self, notes: str = "") -> int:
        """Advance to the next pipeline stage."""
        self.stage_history.append({
            "from_stage": self.current_stage,
            "to_stage": self.current_stage + 1,
            "timestamp": datetime.now().isoformat(),
            "notes": notes,
        })
        self.current_stage += 1
        self.updated_at = datetime.now().isoformat()
        return self.current_stage
    
    def add_assumption(self, text: str, confidence: float = 0.7) -> Assumption:
        """Add a new assumption."""
        assumption = Assumption(text=text, confidence=confidence)
        self.assumptions.append(assumption)
        self.updated_at = datetime.now().isoformat()
        return assumption
    
    def add_hypothesis(self, text: str, falsification: str) -> Hypothesis:
        """Add a new hypothesis."""
        hypothesis = Hypothesis(text=text, falsification_criteria=falsification)
        self.hypotheses.append(hypothesis)
        self.updated_at = datetime.now().isoformat()
        return hypothesis
    
    def add_gap(self, description: str, severity: GapSeverity, lens: str) -> Gap:
        """Add a new identified gap."""
        gap = Gap(description=description, severity=severity, lens=lens)
        self.gaps.append(gap)
        self.updated_at = datetime.now().isoformat()
        return gap
    
    def get_critical_gaps(self) -> List[Gap]:
        """Get all unresolved critical gaps."""
        return [g for g in self.gaps if g.severity == GapSeverity.CRITICAL and not g.resolved]
    
    def get_high_priority_gaps(self) -> List[Gap]:
        """Get all unresolved critical and high gaps."""
        return [g for g in self.gaps 
                if g.severity in (GapSeverity.CRITICAL, GapSeverity.HIGH) and not g.resolved]
    
    def pause(self, reason: str) -> None:
        """Pause the session with a reason."""
        self.paused = True
        self.pause_reason = reason
        self.updated_at = datetime.now().isoformat()
    
    def resume(self) -> None:
        """Resume a paused session."""
        self.paused = False
        self.pause_reason = None
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "project_name": self.project_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_stage": self.current_stage,
            "stage_history": self.stage_history,
            "problem_statement": self.problem_statement,
            "target_users": self.target_users,
            "assumptions": [a.to_dict() for a in self.assumptions],
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "hard_constraints": self.hard_constraints,
            "soft_constraints": self.soft_constraints,
            "evidence": self.evidence,
            "lens_outputs": self.lens_outputs,
            "gaps": [g.to_dict() for g in self.gaps],
            "candidate_goals": [g.to_dict() for g in self.candidate_goals],
            "approved_goals": self.approved_goals,
            "build_phases": [p.to_dict() for p in self.build_phases],
            "specs_ready": self.specs_ready,
            "readiness_approved": self.readiness_approved,
            "current_phase": self.current_phase,
            "current_milestone": self.current_milestone,
            "checkpoints_completed": self.checkpoints_completed,
            "paused": self.paused,
            "pause_reason": self.pause_reason,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EpistemicSessionState":
        """Create from dictionary."""
        state = cls()
        state.project_name = data.get("project_name", "")
        state.created_at = data.get("created_at", state.created_at)
        state.updated_at = data.get("updated_at", state.updated_at)
        state.current_stage = data.get("current_stage", 0)
        state.stage_history = data.get("stage_history", [])
        state.problem_statement = data.get("problem_statement", "")
        state.target_users = data.get("target_users", "")
        state.hard_constraints = data.get("hard_constraints", [])
        state.soft_constraints = data.get("soft_constraints", [])
        state.evidence = data.get("evidence", [])
        state.lens_outputs = data.get("lens_outputs", {})
        state.approved_goals = data.get("approved_goals", [])
        state.specs_ready = data.get("specs_ready", False)
        state.readiness_approved = data.get("readiness_approved", False)
        state.current_phase = data.get("current_phase", 0)
        state.current_milestone = data.get("current_milestone", 0)
        state.checkpoints_completed = data.get("checkpoints_completed", [])
        state.paused = data.get("paused", False)
        state.pause_reason = data.get("pause_reason")
        
        # Reconstruct complex objects
        for a_data in data.get("assumptions", []):
            state.assumptions.append(Assumption(**a_data))
        for h_data in data.get("hypotheses", []):
            state.hypotheses.append(Hypothesis(**h_data))
        for g_data in data.get("gaps", []):
            g_data["severity"] = GapSeverity(g_data["severity"])
            state.gaps.append(Gap(**g_data))
        
        return state
    
    @classmethod
    def from_json(cls, json_str: str) -> "EpistemicSessionState":
        """Load from JSON string."""
        return cls.from_dict(json.loads(json_str))


# Pipeline stage names for display
STAGE_NAMES = [
    "Philosophical Foundation",
    "Epistemic State Creation", 
    "Lens Evaluation",
    "Gap Analysis",
    "Goal Emergence + Gates",
    "MVP Planning",
    "Spec Generation",
    "Build Execution",
    "Improvement Audit",
    "Gap Re-Inspection",
    "Question Tracking",
    "Verification Audit",
    "Documentation Sync",
]


def get_stage_name(stage: int) -> str:
    """Get human-readable name for a pipeline stage."""
    if 0 <= stage < len(STAGE_NAMES):
        return STAGE_NAMES[stage]
    return f"Stage {stage}"


# Global singleton for epistemic session state
_epistemic_state: Optional[EpistemicSessionState] = None


def get_epistemic_state() -> Optional[EpistemicSessionState]:
    """Get the current epistemic session state."""
    return _epistemic_state


def start_epistemic_session(project_name: str = "") -> EpistemicSessionState:
    """Start a new epistemic session."""
    global _epistemic_state
    _epistemic_state = EpistemicSessionState(project_name=project_name)
    return _epistemic_state


def end_epistemic_session() -> None:
    """End the current epistemic session."""
    global _epistemic_state
    _epistemic_state = None


def is_epistemic_active() -> bool:
    """Check if an epistemic session is active."""
    return _epistemic_state is not None


def save_epistemic_state(filepath: str) -> bool:
    """Save the current epistemic state to a file."""
    if _epistemic_state is None:
        return False
    try:
        with open(filepath, "w") as f:
            f.write(_epistemic_state.to_json())
        return True
    except Exception:
        return False


def load_epistemic_state(filepath: str) -> Optional[EpistemicSessionState]:
    """Load epistemic state from a file."""
    global _epistemic_state
    try:
        with open(filepath, "r") as f:
            _epistemic_state = EpistemicSessionState.from_json(f.read())
        return _epistemic_state
    except Exception:
        return None
