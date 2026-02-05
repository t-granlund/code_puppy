"""Project Bootstrap System for Epistemic Architect.

This module provides infrastructure for discovering existing project state
and resuming the Epistemic pipeline from where it left off.

The Bootstrap system:
1. Scans existing directory for project artifacts (BUILD.md, epistemic/, docs/, specs/)
2. Parses existing content to extract completed work
3. Identifies which pipeline stages are complete vs incomplete
4. Pre-populates epistemic state from discovered content
5. Generates focused questions only for missing information
6. Resumes authentication checklist verification

Key Components:
- DiscoveredProject: Container for all discovered artifacts
- ProjectCompletionStatus: Which stages are done
- bootstrap_from_existing(): Main entry point for discovery
- generate_followup_questions(): Only ask what's missing
- resume_auth_checklist(): Re-verify existing auth state

Usage:
    # When entering an existing project directory
    discovery = bootstrap_from_existing(Path.cwd())
    
    if discovery.has_existing_content:
        # Pre-populate agent context
        state = discovery.to_epistemic_state()
        
        # Only ask about gaps
        questions = generate_followup_questions(discovery)
        
        # Resume auth verification
        auth_result = resume_auth_checklist(discovery.auth_checklist_path)
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


# =============================================================================
# 🔥 LOGFIRE TELEMETRY SUPPORT
# =============================================================================

def _log_bootstrap_event(event_type: str, **kwargs) -> None:
    """Log a Bootstrap telemetry event to Logfire.
    
    Pattern follows auth_preflight.py for consistent observability.
    Fails silently if Logfire is not available.
    """
    try:
        import logfire
        logfire.info(f"Project bootstrap: {event_type}", **kwargs)
    except Exception:
        pass


# =============================================================================
# 📊 DISCOVERY STATUS DEFINITIONS
# =============================================================================

class StageStatus(str, Enum):
    """Status of a pipeline stage."""
    NOT_STARTED = "not_started"
    PARTIAL = "partial"
    COMPLETE = "complete"
    NEEDS_REVIEW = "needs_review"  # Has content but may be outdated


class DiscoverySource(str, Enum):
    """Where content was discovered from."""
    BUILD_MD = "BUILD.md"
    CLAUDE_MD = "CLAUDE.md"
    EPISTEMIC_STATE = "epistemic/state.json"
    AUTH_CHECKLIST = "epistemic/auth-checklist.json"
    LENS_EVALUATION = "docs/lens-evaluation.md"
    GAP_ANALYSIS = "docs/gap-analysis.md"
    GOALS_GATES = "docs/goals-and-gates.md"
    IMPROVEMENT_PLAN = "docs/improvement-plan.md"
    SPECS_FOLDER = "specs/"
    README = "README.md"
    PACKAGE_JSON = "package.json"
    PYPROJECT = "pyproject.toml"
    REQUIREMENTS_TXT = "requirements.txt"


# =============================================================================
# 📋 DISCOVERED CONTENT MODELS
# =============================================================================

@dataclass
class DiscoveredArtifact:
    """A discovered project artifact."""
    source: DiscoverySource
    path: Path
    exists: bool
    last_modified: Optional[datetime] = None
    content_summary: str = ""
    extracted_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiscoveredAssumption:
    """An assumption extracted from existing content."""
    text: str
    source: DiscoverySource
    confidence: float = 0.7
    needs_validation: bool = True


@dataclass
class DiscoveredHypothesis:
    """A hypothesis extracted from existing content."""
    text: str
    source: DiscoverySource
    testable: bool = True
    validated: bool = False


@dataclass
class DiscoveredConstraint:
    """A constraint extracted from existing content."""
    text: str
    source: DiscoverySource
    is_hard: bool = True  # Hard = cannot violate, Soft = prefer to avoid


@dataclass
class DiscoveredGoal:
    """A goal extracted from existing content."""
    text: str
    source: DiscoverySource
    priority: int = 1  # 1 = highest
    has_success_criteria: bool = False


class StageCompletionStatus(BaseModel):
    """Completion status for each pipeline stage."""
    stage_0_philosophy: StageStatus = StageStatus.NOT_STARTED
    stage_1_epistemic_state: StageStatus = StageStatus.NOT_STARTED
    stage_2_lens_evaluation: StageStatus = StageStatus.NOT_STARTED
    stage_3_gap_analysis: StageStatus = StageStatus.NOT_STARTED
    stage_4_goal_emergence: StageStatus = StageStatus.NOT_STARTED
    stage_5_mvp_planning: StageStatus = StageStatus.NOT_STARTED
    stage_6_spec_generation: StageStatus = StageStatus.NOT_STARTED
    stage_7_preflight_auth: StageStatus = StageStatus.NOT_STARTED
    stage_8_build_execution: StageStatus = StageStatus.NOT_STARTED
    stage_9_improvement_audit: StageStatus = StageStatus.NOT_STARTED
    stage_10_gap_reinspection: StageStatus = StageStatus.NOT_STARTED
    stage_11_question_tracking: StageStatus = StageStatus.NOT_STARTED
    stage_12_verification_audit: StageStatus = StageStatus.NOT_STARTED
    stage_13_documentation_sync: StageStatus = StageStatus.NOT_STARTED
    
    def get_resume_stage(self) -> int:
        """Get the stage number to resume from."""
        stages = [
            self.stage_0_philosophy,
            self.stage_1_epistemic_state,
            self.stage_2_lens_evaluation,
            self.stage_3_gap_analysis,
            self.stage_4_goal_emergence,
            self.stage_5_mvp_planning,
            self.stage_6_spec_generation,
            self.stage_7_preflight_auth,
            self.stage_8_build_execution,
            self.stage_9_improvement_audit,
            self.stage_10_gap_reinspection,
            self.stage_11_question_tracking,
            self.stage_12_verification_audit,
            self.stage_13_documentation_sync,
        ]
        
        for i, status in enumerate(stages):
            if status in (StageStatus.NOT_STARTED, StageStatus.PARTIAL):
                return i
        
        # All complete - go to audit loop
        return 9  # Stage 9: Improvement Audit
    
    def get_completed_stages(self) -> List[int]:
        """Get list of completed stage numbers."""
        stages = [
            self.stage_0_philosophy,
            self.stage_1_epistemic_state,
            self.stage_2_lens_evaluation,
            self.stage_3_gap_analysis,
            self.stage_4_goal_emergence,
            self.stage_5_mvp_planning,
            self.stage_6_spec_generation,
            self.stage_7_preflight_auth,
            self.stage_8_build_execution,
            self.stage_9_improvement_audit,
            self.stage_10_gap_reinspection,
            self.stage_11_question_tracking,
            self.stage_12_verification_audit,
            self.stage_13_documentation_sync,
        ]
        
        return [i for i, status in enumerate(stages) if status == StageStatus.COMPLETE]


class DiscoveredProject(BaseModel):
    """Complete discovery result for an existing project."""
    project_path: str
    project_name: str = ""
    has_existing_content: bool = False
    discovery_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Discovered artifacts
    artifacts: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Extracted epistemic content
    assumptions: List[Dict[str, Any]] = Field(default_factory=list)
    hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    constraints: List[Dict[str, Any]] = Field(default_factory=list)
    goals: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Technology stack detected
    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)
    
    # Stage completion
    stage_status: Dict[str, str] = Field(default_factory=dict)
    resume_from_stage: int = 0
    
    # Auth status
    has_auth_checklist: bool = False
    auth_requirements_count: int = 0
    auth_passed_count: int = 0
    auth_needs_attention: List[str] = Field(default_factory=list)
    
    # Missing information (questions to ask)
    missing_information: List[str] = Field(default_factory=list)
    suggested_questions: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


# =============================================================================
# 🔍 CONTENT EXTRACTION FUNCTIONS
# =============================================================================

def extract_assumptions_from_readme(content: str) -> List[Dict[str, Any]]:
    """Extract assumptions from README content."""
    assumptions = []
    
    # Look for common assumption patterns
    patterns = [
        r"(?:assumes?|assuming|assumption)[:\s]+([^\n.]+)",
        r"(?:requires?|requirement)[:\s]+([^\n.]+)",
        r"(?:depends? on|dependency)[:\s]+([^\n.]+)",
        r"(?:expects?|expected)[:\s]+([^\n.]+)",
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if len(match.strip()) > 10:  # Ignore very short matches
                assumptions.append({
                    "text": match.strip(),
                    "source": "README.md",
                    "confidence": 0.6,
                    "needs_validation": True,
                })
    
    return assumptions


def extract_goals_from_readme(content: str) -> List[Dict[str, Any]]:
    """Extract goals from README content."""
    goals = []
    
    # Look for goal-like sections
    patterns = [
        r"##\s*(?:goals?|objectives?|features?)\s*\n((?:[^\n#]+\n?)+)",
        r"(?:goal|objective|feature)[:\s]+([^\n.]+)",
        r"[-*]\s+(?:to\s+)?([A-Z][^.\n]+)",  # Bullet points starting with caps
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            text = match.strip()
            if 10 < len(text) < 200:
                goals.append({
                    "text": text,
                    "source": "README.md",
                    "priority": 2,
                    "has_success_criteria": False,
                })
    
    return goals[:10]  # Limit to top 10


def extract_constraints_from_content(content: str, source: str) -> List[Dict[str, Any]]:
    """Extract constraints from any content."""
    constraints = []
    
    patterns = [
        r"(?:must|shall|required to)[:\s]+([^\n.]+)",
        r"(?:cannot|must not|shall not)[:\s]+([^\n.]+)",
        r"(?:constraint|limitation|restriction)[:\s]+([^\n.]+)",
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if len(match.strip()) > 10:
                is_hard = "must" in match.lower() or "shall" in match.lower()
                constraints.append({
                    "text": match.strip(),
                    "source": source,
                    "is_hard": is_hard,
                })
    
    return constraints


def detect_tech_stack(project_path: Path) -> Tuple[List[str], List[str], List[str]]:
    """Detect languages, frameworks, and services from project files."""
    languages = []
    frameworks = []
    services = []
    
    # Check for Python
    if (project_path / "pyproject.toml").exists() or (project_path / "requirements.txt").exists():
        languages.append("Python")
        
        # Check pyproject.toml for frameworks
        pyproject = project_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            if "fastapi" in content.lower():
                frameworks.append("FastAPI")
            if "django" in content.lower():
                frameworks.append("Django")
            if "flask" in content.lower():
                frameworks.append("Flask")
            if "pydantic" in content.lower():
                frameworks.append("Pydantic")
    
    # Check for Node.js
    package_json = project_path / "package.json"
    if package_json.exists():
        languages.append("JavaScript/TypeScript")
        try:
            pkg = json.loads(package_json.read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            
            if "react" in deps:
                frameworks.append("React")
            if "next" in deps:
                frameworks.append("Next.js")
            if "vue" in deps:
                frameworks.append("Vue.js")
            if "express" in deps:
                frameworks.append("Express")
            if "typescript" in deps:
                languages.append("TypeScript")
        except Exception:
            pass
    
    # Check for Go
    if (project_path / "go.mod").exists():
        languages.append("Go")
    
    # Check for Rust
    if (project_path / "Cargo.toml").exists():
        languages.append("Rust")
    
    # Check for services via common config files
    if (project_path / ".env").exists() or (project_path / ".env.example").exists():
        env_file = project_path / ".env" if (project_path / ".env").exists() else project_path / ".env.example"
        try:
            env_content = env_file.read_text().lower()
            if "azure" in env_content:
                services.append("Azure")
            if "aws" in env_content or "s3" in env_content:
                services.append("AWS")
            if "google" in env_content or "gcp" in env_content:
                services.append("GCP")
            if "postgres" in env_content or "postgresql" in env_content:
                services.append("PostgreSQL")
            if "redis" in env_content:
                services.append("Redis")
            if "mongodb" in env_content or "mongo" in env_content:
                services.append("MongoDB")
        except Exception:
            pass
    
    # Check for Docker
    if (project_path / "Dockerfile").exists() or (project_path / "docker-compose.yml").exists():
        services.append("Docker")
    
    # Check for Kubernetes
    if (project_path / "k8s").is_dir() or (project_path / "kubernetes").is_dir():
        services.append("Kubernetes")
    
    return languages, frameworks, services


def parse_epistemic_state_json(state_path: Path) -> Dict[str, Any]:
    """Parse existing epistemic/state.json if it exists."""
    if not state_path.exists():
        return {}
    
    try:
        return json.loads(state_path.read_text())
    except Exception as e:
        logger.warning(f"Failed to parse epistemic state: {e}")
        return {}


def parse_build_md(build_path: Path) -> Dict[str, Any]:
    """Parse BUILD.md to extract milestones and completion status."""
    if not build_path.exists():
        return {}
    
    content = build_path.read_text()
    result = {
        "exists": True,
        "milestones": [],
        "completed_milestones": 0,
        "total_milestones": 0,
        "current_phase": None,
    }
    
    # Extract milestones
    milestone_pattern = r"##\s*(?:Milestone|Phase)\s*(\d+)[:\s]*([^\n]+)"
    matches = re.findall(milestone_pattern, content, re.IGNORECASE)
    
    for num, title in matches:
        # Check if completed (look for ✅ or [x])
        is_complete = "✅" in title or "[x]" in title.lower()
        result["milestones"].append({
            "number": int(num),
            "title": title.strip(),
            "complete": is_complete,
        })
        result["total_milestones"] += 1
        if is_complete:
            result["completed_milestones"] += 1
    
    # Try to find current phase
    current_pattern = r"(?:current|active|in progress)[:\s]*(?:phase|milestone)\s*(\d+)"
    current_match = re.search(current_pattern, content, re.IGNORECASE)
    if current_match:
        result["current_phase"] = int(current_match.group(1))
    
    return result


def parse_auth_checklist(checklist_path: Path) -> Dict[str, Any]:
    """Parse existing auth-checklist.json."""
    if not checklist_path.exists():
        return {}
    
    try:
        data = json.loads(checklist_path.read_text())
        requirements = data.get("requirements", [])
        
        passed = sum(1 for r in requirements if r.get("status") == "passed")
        failed = sum(1 for r in requirements if r.get("status") == "failed")
        missing = sum(1 for r in requirements if r.get("status") in ("missing", "not_checked"))
        
        needs_attention = [
            r.get("name", r.get("id", "unknown"))
            for r in requirements
            if r.get("status") in ("failed", "missing", "not_checked")
        ]
        
        return {
            "exists": True,
            "total": len(requirements),
            "passed": passed,
            "failed": failed,
            "missing": missing,
            "needs_attention": needs_attention,
            "ready_for_phase2": data.get("ready_for_phase2", False),
        }
    except Exception as e:
        logger.warning(f"Failed to parse auth checklist: {e}")
        return {}


# =============================================================================
# 🚀 MAIN BOOTSTRAP FUNCTIONS
# =============================================================================

def bootstrap_from_existing(project_path: Path) -> DiscoveredProject:
    """Discover and analyze an existing project directory.
    
    This is the main entry point for project bootstrapping.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        DiscoveredProject with all discovered content and gaps
    """
    _log_bootstrap_event("discovery_start", project_path=str(project_path))
    
    discovery = DiscoveredProject(
        project_path=str(project_path),
        project_name=project_path.name,
    )
    
    # Track what we find
    found_artifacts = []
    
    # ======================
    # Check for BUILD.md
    # ======================
    build_path = project_path / "BUILD.md"
    if build_path.exists():
        found_artifacts.append("BUILD.md")
        build_data = parse_build_md(build_path)
        discovery.artifacts["BUILD.md"] = build_data
        
        if build_data.get("total_milestones", 0) > 0:
            # Has milestones - at least Stage 5 was started
            if build_data.get("completed_milestones", 0) == build_data.get("total_milestones", 0):
                discovery.stage_status["stage_5_mvp_planning"] = StageStatus.COMPLETE.value
                discovery.stage_status["stage_8_build_execution"] = StageStatus.COMPLETE.value
            else:
                discovery.stage_status["stage_5_mvp_planning"] = StageStatus.COMPLETE.value
                discovery.stage_status["stage_8_build_execution"] = StageStatus.PARTIAL.value
    
    # ======================
    # Check for epistemic/state.json
    # ======================
    state_path = project_path / "epistemic" / "state.json"
    if state_path.exists():
        found_artifacts.append("epistemic/state.json")
        state_data = parse_epistemic_state_json(state_path)
        discovery.artifacts["epistemic/state.json"] = {"exists": True, "data": state_data}
        
        # Extract existing epistemic content
        if "assumptions" in state_data:
            discovery.assumptions = state_data["assumptions"]
        if "hypotheses" in state_data:
            discovery.hypotheses = state_data["hypotheses"]
        if "constraints" in state_data:
            discovery.constraints = state_data["constraints"]
        if "goals" in state_data:
            discovery.goals = state_data["goals"]
        if "evidence" in state_data:
            discovery.evidence = state_data["evidence"]
        
        discovery.stage_status["stage_1_epistemic_state"] = StageStatus.COMPLETE.value
    
    # ======================
    # Check for auth checklist
    # ======================
    auth_path = project_path / "epistemic" / "auth-checklist.json"
    auth_data = parse_auth_checklist(auth_path)
    if auth_data:
        found_artifacts.append("epistemic/auth-checklist.json")
        discovery.has_auth_checklist = True
        discovery.auth_requirements_count = auth_data.get("total", 0)
        discovery.auth_passed_count = auth_data.get("passed", 0)
        discovery.auth_needs_attention = auth_data.get("needs_attention", [])
        discovery.artifacts["epistemic/auth-checklist.json"] = auth_data
        
        if auth_data.get("ready_for_phase2"):
            discovery.stage_status["stage_7_preflight_auth"] = StageStatus.COMPLETE.value
        elif auth_data.get("passed", 0) > 0:
            discovery.stage_status["stage_7_preflight_auth"] = StageStatus.PARTIAL.value
    
    # ======================
    # Check for docs/
    # ======================
    docs_path = project_path / "docs"
    if docs_path.is_dir():
        # Lens evaluation
        lens_path = docs_path / "lens-evaluation.md"
        if lens_path.exists():
            found_artifacts.append("docs/lens-evaluation.md")
            discovery.stage_status["stage_2_lens_evaluation"] = StageStatus.COMPLETE.value
        
        # Gap analysis
        gap_path = docs_path / "gap-analysis.md"
        if gap_path.exists():
            found_artifacts.append("docs/gap-analysis.md")
            discovery.stage_status["stage_3_gap_analysis"] = StageStatus.COMPLETE.value
        
        # Goals and gates
        goals_path = docs_path / "goals-and-gates.md"
        if goals_path.exists():
            found_artifacts.append("docs/goals-and-gates.md")
            discovery.stage_status["stage_4_goal_emergence"] = StageStatus.COMPLETE.value
        
        # Improvement plan
        improvement_path = docs_path / "improvement-plan.md"
        if improvement_path.exists():
            found_artifacts.append("docs/improvement-plan.md")
            discovery.stage_status["stage_9_improvement_audit"] = StageStatus.NEEDS_REVIEW.value
    
    # ======================
    # Check for specs/
    # ======================
    specs_path = project_path / "specs"
    if specs_path.is_dir():
        spec_files = list(specs_path.glob("*.md"))
        if spec_files:
            found_artifacts.append(f"specs/ ({len(spec_files)} files)")
            discovery.stage_status["stage_6_spec_generation"] = StageStatus.COMPLETE.value
            discovery.artifacts["specs/"] = {
                "exists": True,
                "count": len(spec_files),
                "files": [f.name for f in spec_files[:10]],
            }
    
    # ======================
    # Check for README.md
    # ======================
    readme_path = project_path / "README.md"
    if readme_path.exists():
        found_artifacts.append("README.md")
        try:
            readme_content = readme_path.read_text()
            
            # Extract assumptions from README
            readme_assumptions = extract_assumptions_from_readme(readme_content)
            for assumption in readme_assumptions:
                if assumption not in discovery.assumptions:
                    discovery.assumptions.append(assumption)
            
            # Extract goals from README
            readme_goals = extract_goals_from_readme(readme_content)
            for goal in readme_goals:
                if goal not in discovery.goals:
                    discovery.goals.append(goal)
            
            # Extract constraints from README
            readme_constraints = extract_constraints_from_content(readme_content, "README.md")
            for constraint in readme_constraints:
                if constraint not in discovery.constraints:
                    discovery.constraints.append(constraint)
            
            discovery.artifacts["README.md"] = {
                "exists": True,
                "length": len(readme_content),
                "assumptions_found": len(readme_assumptions),
                "goals_found": len(readme_goals),
            }
        except Exception as e:
            logger.warning(f"Failed to parse README: {e}")
    
    # ======================
    # Detect tech stack
    # ======================
    languages, frameworks, services = detect_tech_stack(project_path)
    discovery.languages = languages
    discovery.frameworks = frameworks
    discovery.services = services
    
    # ======================
    # Determine has_existing_content
    # ======================
    discovery.has_existing_content = len(found_artifacts) > 0
    
    # ======================
    # Calculate resume stage
    # ======================
    status = StageCompletionStatus(**{
        k: StageStatus(v) for k, v in discovery.stage_status.items()
    })
    discovery.resume_from_stage = status.get_resume_stage()
    
    # ======================
    # Generate missing information list
    # ======================
    discovery.missing_information = _identify_missing_information(discovery)
    discovery.suggested_questions = _generate_followup_questions(discovery)
    
    _log_bootstrap_event(
        "discovery_complete",
        project_path=str(project_path),
        has_existing_content=discovery.has_existing_content,
        artifacts_found=len(found_artifacts),
        resume_stage=discovery.resume_from_stage,
        assumptions_count=len(discovery.assumptions),
        goals_count=len(discovery.goals),
        auth_needs_attention=len(discovery.auth_needs_attention),
    )
    
    return discovery


def _identify_missing_information(discovery: DiscoveredProject) -> List[str]:
    """Identify what information is still missing."""
    missing = []
    
    if not discovery.assumptions:
        missing.append("No assumptions documented - need to surface hidden assumptions")
    
    if not discovery.hypotheses:
        missing.append("No hypotheses documented - what are we testing?")
    
    if not discovery.constraints:
        missing.append("No constraints documented - what are the hard/soft limits?")
    
    if not discovery.goals:
        missing.append("No goals documented - what are we trying to achieve?")
    
    if not discovery.evidence:
        missing.append("No evidence documented - what do we already know?")
    
    if discovery.stage_status.get("stage_2_lens_evaluation") != StageStatus.COMPLETE.value:
        missing.append("Lens evaluation not complete - need 7 expert perspectives")
    
    if discovery.stage_status.get("stage_3_gap_analysis") != StageStatus.COMPLETE.value:
        missing.append("Gap analysis not complete - need to identify blind spots")
    
    if discovery.stage_status.get("stage_4_goal_emergence") != StageStatus.COMPLETE.value:
        missing.append("Goals not validated through 6 quality gates")
    
    if discovery.has_auth_checklist and discovery.auth_needs_attention:
        missing.append(f"Auth requirements need attention: {', '.join(discovery.auth_needs_attention[:3])}")
    
    return missing


def _generate_followup_questions(discovery: DiscoveredProject) -> List[str]:
    """Generate focused questions based on what's missing."""
    questions = []
    
    # If we have no epistemic state at all
    if not discovery.assumptions and not discovery.hypotheses:
        questions.append("What are you trying to build? (high-level description)")
        questions.append("Who is the target user/audience?")
        questions.append("What problem does this solve?")
    
    # If we have goals but no constraints
    if discovery.goals and not discovery.constraints:
        questions.append("What are the hard constraints? (must-haves, deadlines, budget)")
        questions.append("What are the soft constraints? (nice-to-haves, preferences)")
    
    # If we detected services but no auth checklist
    if discovery.services and not discovery.has_auth_checklist:
        services_str = ", ".join(discovery.services)
        questions.append(f"I see you're using {services_str} - are these already authenticated?")
    
    # If auth needs attention
    if discovery.auth_needs_attention:
        for auth_item in discovery.auth_needs_attention[:2]:
            questions.append(f"The {auth_item} authentication needs to be set up. Do you have the credentials?")
    
    # If we have specs but no goals
    if discovery.artifacts.get("specs/") and not discovery.goals:
        questions.append("I found specs but no documented goals - what's the overall objective?")
    
    # If we have a BUILD.md with incomplete milestones
    build_data = discovery.artifacts.get("BUILD.md", {})
    if build_data.get("total_milestones", 0) > build_data.get("completed_milestones", 0):
        remaining = build_data["total_milestones"] - build_data["completed_milestones"]
        questions.append(f"There are {remaining} incomplete milestones - should we continue from where you left off?")
    
    # If we detected tech stack but no architecture docs
    if discovery.languages and not discovery.artifacts.get("docs/architecture.md"):
        tech = ", ".join(discovery.languages + discovery.frameworks)
        questions.append(f"I see you're using {tech} - is there an architectural decision record or design doc?")
    
    return questions


def generate_bootstrap_summary(discovery: DiscoveredProject) -> str:
    """Generate a human-readable summary of what was discovered."""
    lines = [
        f"# 🔍 Project Discovery: {discovery.project_name}",
        "",
    ]
    
    if not discovery.has_existing_content:
        lines.append("**No existing Epistemic artifacts found.** Starting fresh from Stage 0.")
        return "\n".join(lines)
    
    lines.append("## 📦 Discovered Artifacts")
    for artifact_name, artifact_data in discovery.artifacts.items():
        if isinstance(artifact_data, dict) and artifact_data.get("exists"):
            lines.append(f"- ✅ `{artifact_name}`")
        else:
            lines.append(f"- ⬜ `{artifact_name}` (not found)")
    
    lines.append("")
    lines.append("## 🔧 Tech Stack Detected")
    if discovery.languages:
        lines.append(f"- **Languages:** {', '.join(discovery.languages)}")
    if discovery.frameworks:
        lines.append(f"- **Frameworks:** {', '.join(discovery.frameworks)}")
    if discovery.services:
        lines.append(f"- **Services:** {', '.join(discovery.services)}")
    
    lines.append("")
    lines.append("## 📊 Pipeline Progress")
    lines.append(f"**Resume from Stage {discovery.resume_from_stage}**")
    lines.append("")
    
    stage_names = [
        "0: Philosophy", "1: Epistemic State", "2: Lens Evaluation",
        "3: Gap Analysis", "4: Goal Emergence", "5: MVP Planning",
        "6: Spec Generation", "7: Pre-Flight Auth", "8: Build Execution",
        "9: Improvement Audit", "10: Gap Re-Inspection", "11: Question Tracking",
        "12: Verification Audit", "13: Documentation Sync"
    ]
    
    for i, name in enumerate(stage_names):
        stage_key = f"stage_{i}_" + name.split(":")[1].strip().lower().replace(" ", "_").replace("-", "_")
        status = discovery.stage_status.get(stage_key, StageStatus.NOT_STARTED.value)
        
        if status == StageStatus.COMPLETE.value:
            icon = "✅"
        elif status == StageStatus.PARTIAL.value:
            icon = "🔄"
        elif status == StageStatus.NEEDS_REVIEW.value:
            icon = "👀"
        else:
            icon = "⬜"
        
        lines.append(f"- {icon} Stage {name}")
    
    if discovery.auth_needs_attention:
        lines.append("")
        lines.append("## 🔐 Auth Status")
        lines.append(f"- ✅ Passed: {discovery.auth_passed_count}/{discovery.auth_requirements_count}")
        lines.append("- ⚠️ Needs attention:")
        for item in discovery.auth_needs_attention:
            lines.append(f"  - {item}")
    
    if discovery.missing_information:
        lines.append("")
        lines.append("## ❓ Missing Information")
        for item in discovery.missing_information:
            lines.append(f"- {item}")
    
    if discovery.suggested_questions:
        lines.append("")
        lines.append("## 💬 Suggested Questions")
        for q in discovery.suggested_questions:
            lines.append(f"- {q}")
    
    return "\n".join(lines)


def to_epistemic_state_json(discovery: DiscoveredProject) -> Dict[str, Any]:
    """Convert discovery to epistemic state.json format."""
    return {
        "project_name": discovery.project_name,
        "created_at": discovery.discovery_timestamp.isoformat(),
        "bootstrapped": True,
        "bootstrap_source": "project_discovery",
        "assumptions": discovery.assumptions,
        "hypotheses": discovery.hypotheses,
        "constraints": discovery.constraints,
        "goals": discovery.goals,
        "evidence": discovery.evidence,
        "tech_stack": {
            "languages": discovery.languages,
            "frameworks": discovery.frameworks,
            "services": discovery.services,
        },
        "resume_from_stage": discovery.resume_from_stage,
        "missing_information": discovery.missing_information,
    }


# =============================================================================
# 🔧 AGENT TOOL REGISTRATION
# =============================================================================

def register_discover_project(agent):
    """Register the discover_project tool."""
    
    @agent.tool
    async def discover_project(project_path: str = ".") -> str:
        """Discover existing project content and determine where to resume.
        
        Scans the project directory for:
        - BUILD.md (execution plan)
        - epistemic/state.json (epistemic state)
        - epistemic/auth-checklist.json (auth requirements)
        - docs/*.md (lens evaluation, gap analysis, goals)
        - specs/*.md (specifications)
        - README.md (project description)
        - Tech stack files (package.json, pyproject.toml, etc.)
        
        Returns a summary of:
        - What was found
        - Which pipeline stages are complete
        - Which stage to resume from
        - What information is still missing
        - Suggested questions to fill gaps
        
        Args:
            project_path: Path to scan. Defaults to current directory.
            
        Returns:
            Human-readable discovery summary with recommendations.
        """
        path = Path(project_path).resolve()
        if not path.exists():
            return f"Error: Path '{project_path}' does not exist."
        
        discovery = bootstrap_from_existing(path)
        return generate_bootstrap_summary(discovery)
    
    return discover_project


def register_get_discovery_state(agent):
    """Register the get_discovery_state tool."""
    
    @agent.tool
    async def get_discovery_state(project_path: str = ".") -> str:
        """Get the discovered project state as JSON for use in epistemic state.
        
        This tool returns structured JSON data that can be used to
        pre-populate the epistemic state when starting in an existing project.
        
        Args:
            project_path: Path to scan. Defaults to current directory.
            
        Returns:
            JSON string with discovered assumptions, goals, constraints, etc.
        """
        path = Path(project_path).resolve()
        if not path.exists():
            return json.dumps({"error": f"Path '{project_path}' does not exist."})
        
        discovery = bootstrap_from_existing(path)
        state = to_epistemic_state_json(discovery)
        return json.dumps(state, indent=2, default=str)
    
    return get_discovery_state


def register_get_resume_questions(agent):
    """Register the get_resume_questions tool."""
    
    @agent.tool
    async def get_resume_questions(project_path: str = ".") -> str:
        """Get focused questions to ask based on what's missing.
        
        After discovering existing content, this returns only the questions
        that need to be asked to fill gaps. Skip questions for information
        that was already found in existing artifacts.
        
        Args:
            project_path: Path to scan. Defaults to current directory.
            
        Returns:
            List of questions to ask the user.
        """
        path = Path(project_path).resolve()
        if not path.exists():
            return "Error: Path does not exist."
        
        discovery = bootstrap_from_existing(path)
        
        if not discovery.suggested_questions:
            if discovery.has_existing_content:
                return "✅ No additional questions needed. Project discovery found all required information."
            else:
                # Return standard interview questions for new project
                return """No existing project content found. Start with the standard interview:

1. What are you trying to build? (high-level description)
2. Who is the target user/audience?
3. What problem does this solve?
4. What constraints exist? (timeline, budget, tech requirements)
5. What assumptions are you making?
6. What evidence do you have that this is needed?"""
        
        questions = discovery.suggested_questions
        lines = ["## 💬 Questions (Based on Missing Information)", ""]
        for i, q in enumerate(questions, 1):
            lines.append(f"{i}. {q}")
        
        return "\n".join(lines)
    
    return get_resume_questions


def register_bootstrap_tools(agent):
    """Register all project bootstrap tools."""
    register_discover_project(agent)
    register_get_discovery_state(agent)
    register_get_resume_questions(agent)
    
    _log_bootstrap_event("tools_registered", tool_count=3)

