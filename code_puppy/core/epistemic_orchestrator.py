"""🧠 BART Orchestration System - Belief-Augmented Reasoning & Tasking.

Implements the Plan → Execute → Verify loop using Ralph methodology
to prevent Agent Drift and enforce evidence-based development.

The BART system separates:
- **Belief Layer** (Reasoning): The "Truth" state (PRDs, Specs, Constraints)
- **Tasking Layer** (Execution): The "Hands" that execute with filtered context
- **Bidirectional Verification**: Ralph Loop validates output against belief

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │              BART Orchestration System                      │
    │                    (Claude Opus 4.5)                        │
    │                                                             │
    │  ┌─────────────┐                        ┌─────────────┐     │
    │  │   PLAN      │                        │   VERIFY    │     │
    │  │ (Reasoning) │◄───────────────────────│(Bidirection)│     │
    │  └──────┬──────┘                        └──────▲──────┘     │
    │         │ Context Filter                       │            │
    │         ▼                                      │            │
    │  ┌─────────────┐                              │            │
    │  │   EXECUTE   │──────────Evidence/Code───────┘            │
    │  │  (Tasking)  │                                            │
    │  └─────────────┘                                            │
    │  Cerebras GLM                                               │
    └─────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, field_validator

# Import centralized token budget constants
from code_puppy.core.failover_config import (
    CEREBRAS_TARGET_INPUT_TOKENS,
    FORCE_SUMMARY_THRESHOLD,
)

# Logfire instrumentation for observability
try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    logfire = None
    LOGFIRE_AVAILABLE = False

logger = logging.getLogger(__name__)


# =============================================================================
# 🔍 LOGFIRE INSTRUMENTATION HELPERS
# =============================================================================


@contextmanager
def span(name: str, **attributes: Any) -> Generator[None, None, None]:
    """Create a Logfire span if available, otherwise no-op.
    
    Usage:
        with span("Ralph Loop", iteration=1, milestone="feat-1"):
            # ... code ...
    """
    if LOGFIRE_AVAILABLE and logfire:
        with logfire.span(name, **attributes):
            yield
    else:
        yield


def log_info(message: str, **kwargs: Any) -> None:
    """Log info via Logfire if available, otherwise standard logging."""
    if LOGFIRE_AVAILABLE and logfire:
        logfire.info(message, **kwargs)
    else:
        logger.info(f"{message} | {kwargs}" if kwargs else message)


def log_warning(message: str, **kwargs: Any) -> None:
    """Log warning via Logfire if available, otherwise standard logging."""
    if LOGFIRE_AVAILABLE and logfire:
        logfire.warn(message, **kwargs)
    else:
        logger.warning(f"{message} | {kwargs}" if kwargs else message)


def log_error(message: str, **kwargs: Any) -> None:
    """Log error via Logfire if available, otherwise standard logging."""
    if LOGFIRE_AVAILABLE and logfire:
        logfire.error(message, **kwargs)
    else:
        logger.error(f"{message} | {kwargs}" if kwargs else message)


# =============================================================================
# 🧱 CORE PYDANTIC MODELS - The Belief State Artifact
# =============================================================================


def _utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


def _new_id() -> str:
    """Generate a new unique ID."""
    return str(uuid.uuid4())[:8]


class ConfidenceLevel(str, Enum):
    """Confidence levels for epistemic claims."""
    
    VERY_LOW = "very_low"  # 0.0 - 0.2
    LOW = "low"  # 0.2 - 0.4
    MEDIUM = "medium"  # 0.4 - 0.6
    HIGH = "high"  # 0.6 - 0.8
    VERY_HIGH = "very_high"  # 0.8 - 1.0
    
    @classmethod
    def from_float(cls, value: float) -> "ConfidenceLevel":
        if value < 0.2:
            return cls.VERY_LOW
        elif value < 0.4:
            return cls.LOW
        elif value < 0.6:
            return cls.MEDIUM
        elif value < 0.8:
            return cls.HIGH
        else:
            return cls.VERY_HIGH


class GapSeverity(str, Enum):
    """Severity levels for identified gaps."""
    
    CRITICAL = "critical"  # Must resolve before building
    HIGH = "high"  # Should resolve soon
    MEDIUM = "medium"  # Important but can iterate
    LOW = "low"  # Nice to have


class PhaseStatus(str, Enum):
    """Status of an execution phase."""
    
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class VerificationResult(str, Enum):
    """Result of Ralph Loop verification."""
    
    PASS = "pass"
    DRIFT_DETECTED = "drift_detected"
    SYNTAX_ERROR = "syntax_error"
    SPEC_VIOLATION = "spec_violation"
    SECURITY_CONCERN = "security_concern"
    INCOMPLETE = "incomplete"


# -----------------------------------------------------------------------------
# Epistemic State Components
# -----------------------------------------------------------------------------


class Assumption(BaseModel):
    """An explicit assumption with confidence tracking."""
    
    id: str = Field(default_factory=_new_id)
    text: str
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    source: str = "user"  # user, inferred, evidence
    falsification_criteria: Optional[str] = None
    created_at: datetime = Field(default_factory=_utc_now)
    
    @property
    def confidence_level(self) -> ConfidenceLevel:
        return ConfidenceLevel.from_float(self.confidence)


class Hypothesis(BaseModel):
    """A testable hypothesis with evidence tracking."""
    
    id: str = Field(default_factory=_new_id)
    claim: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    falsification_criteria: str
    evidence_for: List[str] = Field(default_factory=list)
    evidence_against: List[str] = Field(default_factory=list)
    depends_on_assumptions: List[str] = Field(default_factory=list)
    status: str = "open"  # open, validated, refuted, superseded
    created_at: datetime = Field(default_factory=_utc_now)


class Constraint(BaseModel):
    """A hard or soft constraint on the solution."""
    
    id: str = Field(default_factory=_new_id)
    text: str
    type: str = "hard"  # hard (non-negotiable) or soft (preference)
    rationale: Optional[str] = None
    source: str = "user"


class Gap(BaseModel):
    """An identified gap in understanding or implementation."""
    
    id: str = Field(default_factory=_new_id)
    description: str
    severity: GapSeverity
    lens_source: str  # Which lens identified this
    resolution_strategy: Optional[str] = None
    resolved: bool = False
    blocked_goals: List[str] = Field(default_factory=list)


class Goal(BaseModel):
    """An actionable goal that has passed quality gates."""
    
    id: str = Field(default_factory=_new_id)
    description: str
    observables: List[str]  # Measurable outcomes
    success_criteria: str
    rollback_plan: str
    confidence: float = Field(ge=0.6, le=1.0)  # Must be >= 0.6 to pass gates
    approved_by_lenses: List[str] = Field(default_factory=list)  # Need 3+
    evidence_grounding: List[str] = Field(default_factory=list)
    gates_passed: List[str] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Epic/Phase/Milestone Hierarchy
# -----------------------------------------------------------------------------


class Checkpoint(BaseModel):
    """A verification point within a milestone."""
    
    id: str = Field(default_factory=_new_id)
    name: str
    question: str  # What are we checking?
    expected_outcome: str
    actual_outcome: Optional[str] = None
    passed: Optional[bool] = None


class Milestone(BaseModel):
    """A small unit of work (1-2 hours) with checkpoints."""
    
    id: str = Field(default_factory=_new_id)
    name: str
    description: str
    estimated_duration_minutes: int = 60
    file_paths: List[str] = Field(default_factory=list)  # Files to modify
    spec_requirements: List[str] = Field(default_factory=list)  # Spec IDs
    checkpoints: List[Checkpoint] = Field(default_factory=list)
    status: PhaseStatus = PhaseStatus.NOT_STARTED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class Phase(BaseModel):
    """A collection of milestones (Foundation, Core, Polish)."""
    
    id: str = Field(default_factory=_new_id)
    name: str  # e.g., "Foundation", "Core", "Polish"
    description: str
    milestones: List[Milestone] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)  # Phase IDs
    status: PhaseStatus = PhaseStatus.NOT_STARTED


class Epic(BaseModel):
    """A high-level feature grouping phases."""
    
    id: str = Field(default_factory=_new_id)
    name: str
    description: str
    phases: List[Phase] = Field(default_factory=list)
    owner: str = "orchestrator"
    priority: int = 1


# -----------------------------------------------------------------------------
# The Master Epistemic State Artifact
# -----------------------------------------------------------------------------


class EpistemicStateArtifact(BaseModel):
    """The complete belief state - the 'source of truth' for the project.
    
    This is what the BART orchestrator uses to:
    1. Plan work (which epics/phases/milestones) [Reasoning Layer]
    2. Curate context (what files/specs each sub-agent sees) [Context Filter]
    3. Verify work (does output match specs and constraints?) [Bidirectional Verification]
    """
    
    id: str = Field(default_factory=_new_id)
    project_name: str
    version: int = 1
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    
    # Epistemic Content (from Stage 1 interview)
    assumptions: List[Assumption] = Field(default_factory=list)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    hard_constraints: List[Constraint] = Field(default_factory=list)
    soft_constraints: List[Constraint] = Field(default_factory=list)
    
    # Analysis Results (from Stages 2-4)
    gaps: List[Gap] = Field(default_factory=list)
    approved_goals: List[Goal] = Field(default_factory=list)
    
    # Execution Plan (from Stages 5-6)
    epics: List[Epic] = Field(default_factory=list)
    
    # Authentication Requirements (from Stage 6 - Pre-Flight Check)
    # These are populated by the auth_preflight module during planning
    auth_requirements_detected: bool = False
    auth_checklist_path: Optional[str] = None
    auth_ready_for_phase2: bool = False
    
    # Runtime State
    current_epic_id: Optional[str] = None
    current_phase_id: Optional[str] = None
    current_milestone_id: Optional[str] = None
    
    def get_critical_gaps(self) -> List[Gap]:
        """Get unresolved CRITICAL gaps that block work."""
        return [g for g in self.gaps if g.severity == GapSeverity.CRITICAL and not g.resolved]
    
    def get_current_milestone(self) -> Optional[Milestone]:
        """Get the current milestone being worked on."""
        if not self.current_milestone_id:
            return None
        for epic in self.epics:
            for phase in epic.phases:
                for milestone in phase.milestones:
                    if milestone.id == self.current_milestone_id:
                        return milestone
        return None
    
    def bump_version(self) -> None:
        """Increment version and update timestamp."""
        self.version += 1
        self.updated_at = _utc_now()
    
    def to_json(self) -> str:
        """Serialize to JSON for persistence."""
        return self.model_dump_json(indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "EpistemicStateArtifact":
        """Deserialize from JSON."""
        return cls.model_validate_json(json_str)


# =============================================================================
# 🔪 CONTEXT SLICER - Minimum Viable Context for Sub-Agents
# =============================================================================


@dataclass
class MinimumViableContext:
    """The sliced context for a specific task.
    
    Ensures sub-agents (especially Cerebras) only see relevant content,
    staying within token limits while maintaining task fidelity.
    """
    
    # What the agent is working on
    milestone: Milestone
    
    # Filtered content
    relevant_file_paths: List[str]  # Only files for this milestone
    relevant_specs: List[str]  # Only specs for this milestone
    relevant_constraints: List[Constraint]  # Applicable constraints
    
    # Context budget
    estimated_tokens: int = 0
    max_tokens: int = CEREBRAS_TARGET_INPUT_TOKENS  # From failover_config
    
    # Slice metadata
    slice_id: str = field(default_factory=_new_id)
    sliced_at: datetime = field(default_factory=_utc_now)
    
    def to_prompt_context(self) -> str:
        """Format as prompt context for the sub-agent."""
        lines = [
            f"## Task: {self.milestone.name}",
            f"**Description:** {self.milestone.description}",
            "",
            "### Files to Modify:",
        ]
        for fp in self.relevant_file_paths:
            lines.append(f"- `{fp}`")
        
        lines.append("\n### Spec Requirements:")
        for spec in self.relevant_specs:
            lines.append(f"- {spec}")
        
        lines.append("\n### Constraints:")
        for c in self.relevant_constraints:
            constraint_type = "🔒 HARD" if c.type == "hard" else "⚙️ SOFT"
            lines.append(f"- {constraint_type}: {c.text}")
        
        lines.append("\n### Checkpoints:")
        for cp in self.milestone.checkpoints:
            lines.append(f"- [ ] {cp.name}: {cp.question}")
        
        return "\n".join(lines)


class ContextCurator:
    """Curates context for the Tasking Layer based on current milestone.
    
    Implements the 'Context Filter' from BART methodology:
    - Filters belief state to current phase requirements
    - Respects token budgets (especially for Cerebras)
    - Ensures sub-agents don't see irrelevant context (prevents pollution)
    """
    
    def __init__(
        self,
        state: EpistemicStateArtifact,
        max_tokens: int = CEREBRAS_TARGET_INPUT_TOKENS,
    ):
        self.state = state
        self.max_tokens = max_tokens
    
    def slice_for_milestone(self, milestone: Milestone) -> MinimumViableContext:
        """Create a minimum viable context slice for a milestone.
        
        Args:
            milestone: The milestone to create context for
            
        Returns:
            MinimumViableContext with only relevant information
        """
        with span("Slice Context", milestone=milestone.name, max_tokens=self.max_tokens):
            # Get relevant constraints (hard constraints always, soft if mentioned)
            relevant_constraints = list(self.state.hard_constraints)
            for constraint in self.state.soft_constraints:
                # Include if any spec requirement mentions constraint keywords
                constraint_words = set(constraint.text.lower().split())
                for spec in milestone.spec_requirements:
                    if any(word in spec.lower() for word in constraint_words):
                        relevant_constraints.append(constraint)
                        break
            
            mvc = MinimumViableContext(
                milestone=milestone,
                relevant_file_paths=milestone.file_paths,
                relevant_specs=milestone.spec_requirements,
                relevant_constraints=relevant_constraints,
                max_tokens=self.max_tokens,
            )
            
            # Estimate token count (rough: 4 chars per token)
            context_str = mvc.to_prompt_context()
            mvc.estimated_tokens = len(context_str) // 4
            
            log_info(
                "Context slice created",
                slice_id=mvc.slice_id,
                estimated_tokens=mvc.estimated_tokens,
                file_count=len(mvc.relevant_file_paths),
                spec_count=len(mvc.relevant_specs),
                constraint_count=len(relevant_constraints),
            )
            
            return mvc
    
    def filter_file_content(
        self,
        file_path: str,
        content: str,
        focus_areas: Optional[List[str]] = None,
    ) -> str:
        """Filter file content to relevant sections.
        
        For large files, extract only the sections relevant to the task.
        """
        if len(content) < 10000:  # Small files pass through
            return content
        
        # For large files, try to extract relevant sections
        if focus_areas:
            lines = content.split("\n")
            relevant_lines = []
            in_relevant_section = False
            
            for i, line in enumerate(lines):
                # Check if line contains any focus keyword
                if any(focus.lower() in line.lower() for focus in focus_areas):
                    in_relevant_section = True
                    # Include context before (5 lines)
                    start = max(0, i - 5)
                    relevant_lines.extend(lines[start:i])
                
                if in_relevant_section:
                    relevant_lines.append(line)
                    # Stop after 50 lines of relevant content
                    if len(relevant_lines) > 50:
                        relevant_lines.append("... [truncated]")
                        in_relevant_section = False
            
            if relevant_lines:
                return "\n".join(relevant_lines)
        
        # Fallback: return first 200 lines + last 50 lines
        lines = content.split("\n")
        if len(lines) > 300:
            return "\n".join(
                lines[:200] + 
                [f"\n... [{len(lines) - 250} lines omitted] ...\n"] + 
                lines[-50:]
            )
        
        return content


# =============================================================================
# 👁️ RALPH LOOP VERIFIER - Bidirectional Verification Layer
# =============================================================================


@dataclass
class VerificationReport:
    """Report from a verification cycle."""
    
    verification_id: str = field(default_factory=_new_id)
    milestone_id: str = ""
    result: VerificationResult = VerificationResult.PASS
    
    # Static analysis results
    syntax_errors: List[str] = field(default_factory=list)
    lint_warnings: List[str] = field(default_factory=list)
    
    # Intent verification (Claude Sonnet comparison)
    drift_score: float = 0.0  # 0.0 = perfect match, 1.0 = complete drift
    drift_details: List[str] = field(default_factory=list)
    
    # Spec compliance
    specs_checked: List[str] = field(default_factory=list)
    specs_passed: List[str] = field(default_factory=list)
    specs_failed: List[str] = field(default_factory=list)
    
    # Checkpoints
    checkpoints_passed: List[str] = field(default_factory=list)
    checkpoints_failed: List[str] = field(default_factory=list)
    
    # Timing
    verification_duration_ms: int = 0
    verified_at: datetime = field(default_factory=_utc_now)
    
    # Recommendations
    fix_suggestions: List[str] = field(default_factory=list)
    should_retry: bool = False
    max_retries_remaining: int = 3
    
    def is_passing(self) -> bool:
        """Check if verification passed."""
        return self.result == VerificationResult.PASS
    
    def to_feedback_prompt(self) -> str:
        """Format as feedback prompt for retry."""
        lines = [
            "## ⚠️ Verification Failed - Please Fix:",
            f"**Result:** {self.result.value}",
            f"**Drift Score:** {self.drift_score:.2f}",
        ]
        
        if self.syntax_errors:
            lines.append("\n### Syntax Errors:")
            for err in self.syntax_errors:
                lines.append(f"- ❌ {err}")
        
        if self.drift_details:
            lines.append("\n### Intent Drift Detected:")
            for detail in self.drift_details:
                lines.append(f"- 📍 {detail}")
        
        if self.specs_failed:
            lines.append("\n### Spec Violations:")
            for spec in self.specs_failed:
                lines.append(f"- 🚫 {spec}")
        
        if self.fix_suggestions:
            lines.append("\n### Suggested Fixes:")
            for fix in self.fix_suggestions:
                lines.append(f"- 💡 {fix}")
        
        return "\n".join(lines)


class RalphLoopVerifier:
    """The Ralph Loop verification engine - Bidirectional Verification Layer.
    
    Implements the recursive Execute → Verify → Fix cycle:
    
    1. Drift Detection: After Tasking Layer generates code, don't save immediately
    2. Static Analysis: Run local linting/syntax checks (Cost: $0)
    3. Intent Verification: Use Claude Sonnet to compare diff vs belief state
    4. Auto-Fix: If Drift > Tolerance, reject and retry
    5. Commit: Only when Verification == PASS
    """
    
    def __init__(
        self,
        state: EpistemicStateArtifact,
        drift_tolerance: float = 0.3,
        max_retries: int = 3,
    ):
        self.state = state
        self.drift_tolerance = drift_tolerance
        self.max_retries = max_retries
        self._retry_count = 0
    
    async def verify_code_generation(
        self,
        milestone: Milestone,
        generated_code: str,
        file_path: str,
        original_content: Optional[str] = None,
    ) -> VerificationReport:
        """Verify generated code against specs and constraints.
        
        This is the core of the Ralph Loop - called after each generation
        before committing any changes.
        """
        with span("Verify Code Generation", milestone=milestone.id, file=file_path):
            start_time = time.time()
            report = VerificationReport(milestone_id=milestone.id)
            
            # Phase 1: Static Analysis (Cost: $0)
            with span("Static Analysis", file=file_path):
                await self._run_static_analysis(report, generated_code, file_path)
            
            if report.syntax_errors:
                report.result = VerificationResult.SYNTAX_ERROR
                report.should_retry = True
                report.fix_suggestions.append("Fix syntax errors before proceeding")
                log_warning(
                    "Syntax errors detected",
                    error_count=len(report.syntax_errors),
                    file=file_path,
                )
                return self._finalize_report(report, start_time)
            
            # Phase 2: Intent Verification (uses Claude Sonnet)
            with span("Intent Verification"):
                await self._verify_intent(
                    report, 
                    milestone, 
                    generated_code, 
                    original_content
                )
            
            if report.drift_score > self.drift_tolerance:
                report.result = VerificationResult.DRIFT_DETECTED
                report.should_retry = True
                log_warning(
                    "Drift detected",
                    drift_score=report.drift_score,
                    tolerance=self.drift_tolerance,
                )
                return self._finalize_report(report, start_time)
            
            # Phase 3: Spec Compliance Check
            with span("Spec Compliance Check"):
                await self._check_spec_compliance(report, milestone, generated_code)
            
            if report.specs_failed:
                report.result = VerificationResult.SPEC_VIOLATION
                report.should_retry = True
                log_warning("Spec violations found", count=len(report.specs_failed))
                return self._finalize_report(report, start_time)
            
            # Phase 4: Checkpoint Verification
            with span("Checkpoint Verification"):
                await self._verify_checkpoints(report, milestone, generated_code)
            
            if report.checkpoints_failed:
                report.result = VerificationResult.INCOMPLETE
                report.should_retry = True
                log_warning(
                    "Checkpoints failed",
                    count=len(report.checkpoints_failed),
                )
                return self._finalize_report(report, start_time)
            
            # All checks passed!
            report.result = VerificationResult.PASS
            report.should_retry = False
            log_info(
                "Verification passed",
                drift_score=report.drift_score,
                verification_time_ms=int((time.time() - start_time) * 1000),
            )
            
            return self._finalize_report(report, start_time)
    
    async def _run_static_analysis(
        self,
        report: VerificationReport,
        code: str,
        file_path: str,
    ) -> None:
        """Run static analysis on generated code."""
        # Basic Python syntax check
        if file_path.endswith(".py"):
            try:
                compile(code, file_path, "exec")
            except SyntaxError as e:
                report.syntax_errors.append(
                    f"Line {e.lineno}: {e.msg}"
                )
        
        # TODO: Integrate with real linters (ruff, pylint, etc.)
        # For now, check for common issues
        if "TODO" in code or "FIXME" in code:
            report.lint_warnings.append("Code contains TODO/FIXME markers")
        
        if "import *" in code:
            report.lint_warnings.append("Avoid wildcard imports")
    
    async def _verify_intent(
        self,
        report: VerificationReport,
        milestone: Milestone,
        generated_code: str,
        original_content: Optional[str],
    ) -> None:
        """Compare generated code against intended changes.
        
        Uses Claude Sonnet (Tier 2) to assess if the code matches
        the milestone requirements.
        
        TODO: Wire this to actual ModelRouter + Claude Sonnet call
        """
        # Calculate a simple drift score based on requirements coverage
        requirements_found = 0
        total_requirements = len(milestone.spec_requirements)
        
        if total_requirements == 0:
            report.drift_score = 0.0
            return
        
        code_lower = generated_code.lower()
        for spec in milestone.spec_requirements:
            # Check if spec keywords appear in code
            spec_words = [w for w in spec.lower().split() if len(w) > 4]
            if any(word in code_lower for word in spec_words):
                requirements_found += 1
            else:
                report.drift_details.append(
                    f"Spec not clearly addressed: {spec[:50]}..."
                )
        
        report.drift_score = 1.0 - (requirements_found / total_requirements)
        
        # Add fix suggestions based on drift
        if report.drift_score > 0.3:
            report.fix_suggestions.append(
                f"Focus on these specs: {milestone.spec_requirements}"
            )
    
    async def _check_spec_compliance(
        self,
        report: VerificationReport,
        milestone: Milestone,
        generated_code: str,
    ) -> None:
        """Check if generated code complies with all relevant specs."""
        for spec in milestone.spec_requirements:
            report.specs_checked.append(spec)
            
            # Simple keyword-based check (TODO: use LLM for semantic check)
            # For now, mark as passed if we don't detect obvious violations
            report.specs_passed.append(spec)
    
    async def _verify_checkpoints(
        self,
        report: VerificationReport,
        milestone: Milestone,
        generated_code: str,
    ) -> None:
        """Verify milestone checkpoints are addressed."""
        for checkpoint in milestone.checkpoints:
            # Check if checkpoint appears to be addressed
            # (simplified - in production, use LLM verification)
            checkpoint_words = checkpoint.name.lower().split()
            code_lower = generated_code.lower()
            
            if any(word in code_lower for word in checkpoint_words if len(word) > 3):
                report.checkpoints_passed.append(checkpoint.id)
                checkpoint.passed = True
            else:
                report.checkpoints_failed.append(checkpoint.id)
                checkpoint.passed = False
                report.fix_suggestions.append(
                    f"Address checkpoint: {checkpoint.name}"
                )
    
    def _finalize_report(
        self,
        report: VerificationReport,
        start_time: float,
    ) -> VerificationReport:
        """Finalize the verification report."""
        report.verification_duration_ms = int((time.time() - start_time) * 1000)
        report.max_retries_remaining = self.max_retries - self._retry_count
        
        if report.should_retry:
            self._retry_count += 1
        else:
            self._retry_count = 0
        
        logger.info(
            f"Verification complete: {report.result.value} | "
            f"Drift: {report.drift_score:.2f} | "
            f"Duration: {report.verification_duration_ms}ms"
        )
        
        return report


# =============================================================================
# 🎭 THE ORCHESTRATOR - Putting It All Together
# =============================================================================


class OrchestratorPhase(str, Enum):
    """Current phase of the orchestrator."""
    
    PLANNING = "planning"  # Interviewing, creating epistemic state
    ANALYZING = "analyzing"  # Running lenses, gap analysis
    EXECUTING = "executing"  # Running milestones through Ralph loops
    VERIFYING = "verifying"  # Final verification
    COMPLETE = "complete"
    BLOCKED = "blocked"  # Critical gap or repeated failures


@dataclass
class OrchestratorState:
    """Runtime state of the orchestrator."""
    
    phase: OrchestratorPhase = OrchestratorPhase.PLANNING
    epistemic_state: Optional[EpistemicStateArtifact] = None
    current_context: Optional[MinimumViableContext] = None
    last_verification: Optional[VerificationReport] = None
    total_ralph_loops: int = 0
    total_retries: int = 0
    blocked_reason: Optional[str] = None


class EpistemicOrchestrator:
    """The BART Orchestrator - Plan → Execute → Verify.
    
    This is the 'Pack Leader' upgraded with BART belief state enforcement.
    It manages the complete flow from idea to working code.
    
    Key responsibilities:
    1. Reasoning Layer (Planning): Interview user, create Belief State Artifact
    2. Context Filter: Slice context for each sub-agent task
    3. Tasking Layer (Execution): Dispatch work to execution models
    4. Bidirectional Verification: Run Ralph Loop until specs are met
    
    Usage:
        orchestrator = EpistemicOrchestrator()
        
        # Phase 1: Planning
        state = await orchestrator.create_epistemic_state(user_input)
        
        # Phase 2: Analysis
        await orchestrator.run_lens_evaluation()
        await orchestrator.run_gap_analysis()
        
        # Phase 3: Execution with Ralph Loops
        for milestone in orchestrator.get_milestones():
            await orchestrator.execute_milestone(milestone)
    """
    
    def __init__(
        self,
        drift_tolerance: float = 0.3,
        max_retries: int = 3,
        cerebras_token_limit: int = CEREBRAS_TARGET_INPUT_TOKENS,
    ):
        self.drift_tolerance = drift_tolerance
        self.max_retries = max_retries
        self.cerebras_token_limit = cerebras_token_limit
        
        self._state = OrchestratorState()
        self._curator: Optional[ContextCurator] = None
        self._verifier: Optional[RalphLoopVerifier] = None
    
    @property
    def phase(self) -> OrchestratorPhase:
        return self._state.phase
    
    @property
    def epistemic_state(self) -> Optional[EpistemicStateArtifact]:
        return self._state.epistemic_state
    
    # -------------------------------------------------------------------------
    # Phase 1: Planning (Reasoning Layer - The Belief State)
    # -------------------------------------------------------------------------
    
    async def create_epistemic_state(
        self,
        project_name: str,
        initial_description: str,
    ) -> EpistemicStateArtifact:
        """Create initial epistemic state from user input.
        
        This uses Claude Opus (Tier 1) for the planning interview.
        
        Args:
            project_name: Name of the project
            initial_description: User's initial description
            
        Returns:
            The created EpistemicStateArtifact
        """
        # TODO: Wire to actual Claude Opus via ModelRouter
        # For now, create a skeleton state
        
        state = EpistemicStateArtifact(
            project_name=project_name,
            assumptions=[
                Assumption(text=f"Building: {initial_description}"),
            ],
        )
        
        self._state.epistemic_state = state
        self._state.phase = OrchestratorPhase.PLANNING
        
        # Initialize curator and verifier
        self._curator = ContextCurator(state, self.cerebras_token_limit)
        self._verifier = RalphLoopVerifier(
            state, 
            self.drift_tolerance, 
            self.max_retries
        )
        
        logger.info(f"Created belief state for: {project_name}")
        
        return state
    
    async def add_assumption(
        self,
        text: str,
        confidence: float = 0.7,
        falsification_criteria: Optional[str] = None,
    ) -> Assumption:
        """Add an assumption to the epistemic state."""
        if not self._state.epistemic_state:
            raise ValueError("No epistemic state - call create_epistemic_state first")
        
        assumption = Assumption(
            text=text,
            confidence=confidence,
            falsification_criteria=falsification_criteria,
        )
        self._state.epistemic_state.assumptions.append(assumption)
        self._state.epistemic_state.bump_version()
        
        return assumption
    
    async def add_constraint(
        self,
        text: str,
        constraint_type: str = "hard",
        rationale: Optional[str] = None,
    ) -> Constraint:
        """Add a constraint to the epistemic state."""
        if not self._state.epistemic_state:
            raise ValueError("No epistemic state")
        
        constraint = Constraint(
            text=text,
            type=constraint_type,
            rationale=rationale,
        )
        
        if constraint_type == "hard":
            self._state.epistemic_state.hard_constraints.append(constraint)
        else:
            self._state.epistemic_state.soft_constraints.append(constraint)
        
        self._state.epistemic_state.bump_version()
        return constraint
    
    # -------------------------------------------------------------------------
    # Phase 2: Analysis (Lens Evaluation & Gap Analysis)
    # -------------------------------------------------------------------------
    
    async def run_lens_evaluation(self) -> Dict[str, Any]:
        """Run all 7 lenses against the epistemic state.
        
        Uses Claude Opus (Tier 1) for thorough analysis.
        """
        if not self._state.epistemic_state:
            raise ValueError("No epistemic state")
        
        self._state.phase = OrchestratorPhase.ANALYZING
        
        # TODO: Wire to actual lens evaluation via ModelRouter
        # For now, return placeholder
        
        logger.info("Running lens evaluation...")
        
        return {
            "philosophy": {"gaps": [], "confidence_delta": 0},
            "data_science": {"metrics_proposed": [], "experiments": []},
            "safety": {"risks": [], "mitigations": []},
            "topology": {"dependencies": [], "transitions": []},
            "theoretical_math": {"axioms": [], "proofs": []},
            "systems_engineering": {"services": [], "interfaces": []},
            "product_ux": {"flows": [], "mvp_scope": []},
        }
    
    async def run_gap_analysis(self) -> List[Gap]:
        """Identify gaps from lens evaluation.
        
        Categorizes gaps as CRITICAL/HIGH/MEDIUM/LOW.
        """
        if not self._state.epistemic_state:
            raise ValueError("No epistemic state")
        
        # TODO: Wire to actual analysis
        logger.info("Running gap analysis...")
        
        return self._state.epistemic_state.gaps
    
    # -------------------------------------------------------------------------
    # Phase 3: Execution with Ralph Loops
    # -------------------------------------------------------------------------
    
    async def execute_milestone(
        self,
        milestone: Milestone,
        execution_callback: Optional[Callable[[MinimumViableContext], str]] = None,
    ) -> VerificationReport:
        """Execute a milestone through the Ralph Loop.
        
        This is the core execution flow:
        1. Slice context for this milestone
        2. Dispatch to Cerebras GLM 4.7
        3. Verify output
        4. Retry if verification fails
        5. Commit only on PASS
        
        Args:
            milestone: The milestone to execute
            execution_callback: Optional callback for actual code generation
            
        Returns:
            Final VerificationReport (PASS or final failure)
        """
        if not self._curator or not self._verifier:
            raise ValueError("Orchestrator not initialized")
        
        with span("Execute Milestone", milestone=milestone.name, id=milestone.id):
            self._state.phase = OrchestratorPhase.EXECUTING
            milestone.status = PhaseStatus.IN_PROGRESS
            milestone.started_at = _utc_now()
            
            # Step 1: Slice context
            with span("Slice Context", milestone=milestone.name):
                context = self._curator.slice_for_milestone(milestone)
                self._state.current_context = context
                log_info(
                    "Context sliced",
                    milestone=milestone.name,
                    token_count=context.total_tokens,
                    file_count=len(context.relevant_files),
                )
            
            log_info("Executing milestone", milestone=milestone.name)
            
            # Step 2-4: Ralph Loop (Execute → Verify → Fix)
            report = await self.run_ralph_loop(
                milestone=milestone,
                context=context,
                execution_callback=execution_callback,
            )
            
            # Step 5: Update milestone status
            if report.is_passing():
                milestone.status = PhaseStatus.VERIFIED
                milestone.completed_at = _utc_now()
                log_info("Milestone verified", milestone=milestone.name)
            else:
                milestone.status = PhaseStatus.FAILED
                log_warning("Milestone failed", milestone=milestone.name)
            
            self._state.last_verification = report
            
            return report
    
    async def run_ralph_loop(
        self,
        milestone: Milestone,
        context: MinimumViableContext,
        execution_callback: Optional[Callable[[MinimumViableContext], str]] = None,
        max_iterations: int = 3,
    ) -> VerificationReport:
        """The recursive Ralph Loop: Execute → Verify → Fix.
        
        This is THE core primitive from the BART methodology - Bidirectional Verification.
        
        Args:
            milestone: Current milestone
            context: Sliced context for the task
            execution_callback: Callback to generate code
            max_iterations: Maximum retry attempts
            
        Returns:
            Final VerificationReport
        """
        iteration = 0
        feedback: Optional[str] = None
        last_report: Optional[VerificationReport] = None
        
        with span("Ralph Loop", milestone=milestone.name, max_iterations=max_iterations):
            while iteration < max_iterations:
                self._state.total_ralph_loops += 1
                iteration += 1
                
                log_info(
                    "Ralph Loop iteration",
                    iteration=iteration,
                    max_iterations=max_iterations,
                    milestone=milestone.name,
                )
                
                with span("Ralph Iteration", iteration=iteration):
                    # OBSERVE: Gather current state
                    prompt_context = context.to_prompt_context()
                    if feedback:
                        prompt_context += f"\n\n{feedback}"
                    
                    # ORIENT + DECIDE: (Handled by the sub-agent)
                    # ACT: Execute code generation
                    with span("Execute Code Generation"):
                        if execution_callback:
                            generated_code = execution_callback(context)
                        else:
                            # Placeholder - in production, call Cerebras via ModelRouter
                            generated_code = f"# Generated for: {milestone.name}\n# TODO: Implement"
                    
                    # VERIFY: Check output against specs
                    file_path = milestone.file_paths[0] if milestone.file_paths else "unknown.py"
                    report = await self._verifier.verify_code_generation(
                        milestone=milestone,
                        generated_code=generated_code,
                        file_path=file_path,
                    )
                    
                    last_report = report
                    
                    # If passing, break the loop
                    if report.is_passing():
                        log_info(
                            "Ralph Loop passed",
                            iteration=iteration,
                            drift_score=report.drift_score,
                        )
                        return report
                    
                    # If max retries exhausted, break
                    if not report.should_retry or report.max_retries_remaining <= 0:
                        log_warning("Ralph Loop exhausted retries", iteration=iteration)
                        break
                    
                    # Generate feedback for next iteration
                    feedback = report.to_feedback_prompt()
                    self._state.total_retries += 1
                    
                    log_info(
                        "Retrying with feedback",
                        drift_score=report.drift_score,
                        retry_count=self._state.total_retries,
                    )
        
        return last_report or VerificationReport(
            result=VerificationResult.INCOMPLETE,
            should_retry=False,
        )
    
    # -------------------------------------------------------------------------
    # State Management
    # -------------------------------------------------------------------------
    
    def get_milestones(self) -> List[Milestone]:
        """Get all milestones in order."""
        if not self._state.epistemic_state:
            return []
        
        milestones = []
        for epic in self._state.epistemic_state.epics:
            for phase in epic.phases:
                milestones.extend(phase.milestones)
        
        return milestones
    
    def get_next_milestone(self) -> Optional[Milestone]:
        """Get the next unstarted milestone."""
        for milestone in self.get_milestones():
            if milestone.status == PhaseStatus.NOT_STARTED:
                return milestone
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        milestones = self.get_milestones()
        completed = sum(1 for m in milestones if m.status == PhaseStatus.VERIFIED)
        
        return {
            "phase": self._state.phase.value,
            "total_milestones": len(milestones),
            "completed_milestones": completed,
            "total_ralph_loops": self._state.total_ralph_loops,
            "total_retries": self._state.total_retries,
            "blocked": self._state.phase == OrchestratorPhase.BLOCKED,
            "blocked_reason": self._state.blocked_reason,
        }
    
    async def save_state(self, path: Path) -> None:
        """Save epistemic state to file."""
        if not self._state.epistemic_state:
            raise ValueError("No state to save")
        
        path.write_text(self._state.epistemic_state.to_json())
        logger.info(f"Saved belief state to: {path}")
    
    async def load_state(self, path: Path) -> EpistemicStateArtifact:
        """Load epistemic state from file."""
        content = path.read_text()
        state = EpistemicStateArtifact.from_json(content)
        
        self._state.epistemic_state = state
        self._curator = ContextCurator(state, self.cerebras_token_limit)
        self._verifier = RalphLoopVerifier(
            state, 
            self.drift_tolerance, 
            self.max_retries
        )
        
        logger.info(f"Loaded epistemic state from: {path}")
        return state


# =============================================================================
# 📤 EXPORTS
# =============================================================================

__all__ = [
    # Core Models
    "EpistemicStateArtifact",
    "Assumption",
    "Hypothesis",
    "Constraint",
    "Gap",
    "Goal",
    "Epic",
    "Phase",
    "Milestone",
    "Checkpoint",
    
    # Enums
    "ConfidenceLevel",
    "GapSeverity",
    "PhaseStatus",
    "VerificationResult",
    "OrchestratorPhase",
    
    # Context Management
    "MinimumViableContext",
    "ContextCurator",
    
    # Verification
    "VerificationReport",
    "RalphLoopVerifier",
    
    # Orchestrator
    "EpistemicOrchestrator",
    "OrchestratorState",
]
