"""Tests for epistemic state management and commands."""

import json
import os
import tempfile
from datetime import datetime

import pytest

from code_puppy.command_line.epistemic_state import (
    Assumption,
    BuildPhase,
    CandidateGoal,
    EpistemicSessionState,
    Gap,
    GapSeverity,
    GateCheck,
    GateStatus,
    Hypothesis,
    Milestone,
    STAGE_NAMES,
    end_epistemic_session,
    get_epistemic_state,
    get_stage_name,
    is_epistemic_active,
    load_epistemic_state,
    save_epistemic_state,
    start_epistemic_session,
)


class TestAssumption:
    """Tests for the Assumption dataclass."""

    def test_create_assumption(self):
        """Test basic assumption creation."""
        assumption = Assumption(text="Users want fast responses", confidence=0.8)
        assert assumption.text == "Users want fast responses"
        assert assumption.confidence == 0.8
        assert assumption.source == "user"
        assert assumption.created_at is not None

    def test_assumption_to_dict(self):
        """Test assumption serialization."""
        assumption = Assumption(text="Test", confidence=0.5, source="interview")
        d = assumption.to_dict()
        assert d["text"] == "Test"
        assert d["confidence"] == 0.5
        assert d["source"] == "interview"
        assert "created_at" in d


class TestHypothesis:
    """Tests for the Hypothesis dataclass."""

    def test_create_hypothesis(self):
        """Test basic hypothesis creation."""
        hyp = Hypothesis(
            text="Users will adopt feature X",
            falsification_criteria="Less than 10% adoption in 30 days",
        )
        assert hyp.text == "Users will adopt feature X"
        assert hyp.falsification_criteria == "Less than 10% adoption in 30 days"
        assert hyp.confidence == 0.5
        assert hyp.status == "open"

    def test_hypothesis_to_dict(self):
        """Test hypothesis serialization."""
        hyp = Hypothesis(
            text="Test",
            falsification_criteria="Fails when X",
            confidence=0.7,
            evidence=["Evidence 1"],
        )
        d = hyp.to_dict()
        assert d["text"] == "Test"
        assert d["falsification_criteria"] == "Fails when X"
        assert d["confidence"] == 0.7
        assert d["evidence"] == ["Evidence 1"]


class TestGap:
    """Tests for the Gap dataclass."""

    def test_create_gap(self):
        """Test basic gap creation."""
        gap = Gap(
            description="No user authentication",
            severity=GapSeverity.CRITICAL,
            lens="Safety/Risk",
        )
        assert gap.description == "No user authentication"
        assert gap.severity == GapSeverity.CRITICAL
        assert gap.lens == "Safety/Risk"
        assert gap.resolved is False

    def test_gap_to_dict(self):
        """Test gap serialization."""
        gap = Gap(
            description="Test gap",
            severity=GapSeverity.HIGH,
            lens="Product",
            resolution="Fixed it",
            resolved=True,
        )
        d = gap.to_dict()
        assert d["severity"] == "high"
        assert d["resolved"] is True
        assert d["resolution"] == "Fixed it"


class TestGateCheck:
    """Tests for quality gate checks."""

    def test_create_gate_check(self):
        """Test gate check creation."""
        check = GateCheck(
            gate_name="Observables",
            status=GateStatus.PASSED,
            notes="Has clear metrics",
        )
        assert check.gate_name == "Observables"
        assert check.status == GateStatus.PASSED

    def test_gate_check_to_dict(self):
        """Test gate check serialization."""
        check = GateCheck(gate_name="Testability", status=GateStatus.FAILED)
        d = check.to_dict()
        assert d["gate_name"] == "Testability"
        assert d["status"] == "failed"


class TestCandidateGoal:
    """Tests for candidate goals."""

    def test_passes_all_gates_empty(self):
        """Test that empty gates means not passing."""
        goal = CandidateGoal(description="Build feature X")
        assert goal.passes_all_gates() is False

    def test_passes_all_gates_insufficient(self):
        """Test that fewer than 6 gates means not passing."""
        goal = CandidateGoal(
            description="Build feature X",
            gate_checks=[
                GateCheck(gate_name="Observables", status=GateStatus.PASSED),
                GateCheck(gate_name="Testability", status=GateStatus.PASSED),
            ],
        )
        assert goal.passes_all_gates() is False

    def test_passes_all_gates_all_passed(self):
        """Test that 6 passed gates means passing."""
        gates = [
            GateCheck(gate_name="Observables", status=GateStatus.PASSED),
            GateCheck(gate_name="Testability", status=GateStatus.PASSED),
            GateCheck(gate_name="Reversibility", status=GateStatus.PASSED),
            GateCheck(gate_name="Confidence", status=GateStatus.PASSED),
            GateCheck(gate_name="LensAgreement", status=GateStatus.PASSED),
            GateCheck(gate_name="EvidenceGrounding", status=GateStatus.PASSED),
        ]
        goal = CandidateGoal(description="Build feature X", gate_checks=gates)
        assert goal.passes_all_gates() is True

    def test_passes_all_gates_one_failed(self):
        """Test that one failed gate means not passing."""
        gates = [
            GateCheck(gate_name="Observables", status=GateStatus.PASSED),
            GateCheck(gate_name="Testability", status=GateStatus.PASSED),
            GateCheck(gate_name="Reversibility", status=GateStatus.FAILED),  # Failed!
            GateCheck(gate_name="Confidence", status=GateStatus.PASSED),
            GateCheck(gate_name="LensAgreement", status=GateStatus.PASSED),
            GateCheck(gate_name="EvidenceGrounding", status=GateStatus.PASSED),
        ]
        goal = CandidateGoal(description="Build feature X", gate_checks=gates)
        assert goal.passes_all_gates() is False


class TestEpistemicSessionState:
    """Tests for the main session state container."""

    def test_create_empty_state(self):
        """Test creating an empty state."""
        state = EpistemicSessionState()
        assert state.current_stage == 0
        assert state.project_name == ""
        assert len(state.assumptions) == 0

    def test_create_named_state(self):
        """Test creating a named state."""
        state = EpistemicSessionState(project_name="my-api")
        assert state.project_name == "my-api"

    def test_advance_stage(self):
        """Test advancing through stages."""
        state = EpistemicSessionState()
        assert state.current_stage == 0
        new_stage = state.advance_stage("Completed foundation")
        assert new_stage == 1
        assert len(state.stage_history) == 1
        assert state.stage_history[0]["notes"] == "Completed foundation"

    def test_add_assumption(self):
        """Test adding assumptions."""
        state = EpistemicSessionState()
        assumption = state.add_assumption("Users want speed", confidence=0.9)
        assert len(state.assumptions) == 1
        assert state.assumptions[0].text == "Users want speed"
        assert state.assumptions[0].confidence == 0.9

    def test_add_hypothesis(self):
        """Test adding hypotheses."""
        state = EpistemicSessionState()
        hyp = state.add_hypothesis(
            "Feature X increases retention",
            "Less than 5% retention increase after 30 days",
        )
        assert len(state.hypotheses) == 1
        assert state.hypotheses[0].text == "Feature X increases retention"

    def test_add_gap(self):
        """Test adding gaps."""
        state = EpistemicSessionState()
        gap = state.add_gap("No error handling", GapSeverity.HIGH, "Systems")
        assert len(state.gaps) == 1
        assert state.gaps[0].severity == GapSeverity.HIGH

    def test_get_critical_gaps(self):
        """Test filtering critical gaps."""
        state = EpistemicSessionState()
        state.add_gap("Critical 1", GapSeverity.CRITICAL, "Safety")
        state.add_gap("High 1", GapSeverity.HIGH, "Product")
        state.add_gap("Critical 2", GapSeverity.CRITICAL, "Systems")
        
        critical = state.get_critical_gaps()
        assert len(critical) == 2
        
        # Resolve one
        state.gaps[0].resolved = True
        critical = state.get_critical_gaps()
        assert len(critical) == 1

    def test_pause_resume(self):
        """Test pausing and resuming."""
        state = EpistemicSessionState()
        assert state.paused is False
        
        state.pause("Need user input on requirements")
        assert state.paused is True
        assert state.pause_reason == "Need user input on requirements"
        
        state.resume()
        assert state.paused is False
        assert state.pause_reason is None

    def test_to_dict(self):
        """Test serialization to dict."""
        state = EpistemicSessionState(project_name="test")
        state.add_assumption("Test assumption", 0.8)
        state.add_gap("Test gap", GapSeverity.MEDIUM, "Philosophy")
        
        d = state.to_dict()
        assert d["project_name"] == "test"
        assert len(d["assumptions"]) == 1
        assert len(d["gaps"]) == 1

    def test_to_json(self):
        """Test JSON serialization."""
        state = EpistemicSessionState(project_name="json-test")
        state.add_assumption("Assumption", 0.7)
        
        json_str = state.to_json()
        parsed = json.loads(json_str)
        assert parsed["project_name"] == "json-test"

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "project_name": "restored",
            "current_stage": 3,
            "assumptions": [
                {"text": "Test", "confidence": 0.6, "source": "user", "created_at": "2026-01-28T12:00:00"}
            ],
            "gaps": [
                {"description": "Gap", "severity": "high", "lens": "Product", "resolution": None, "resolved": False}
            ],
            "hypotheses": [],
            "hard_constraints": ["Must be fast"],
            "soft_constraints": [],
            "evidence": [],
            "lens_outputs": {},
            "candidate_goals": [],
            "approved_goals": [],
            "build_phases": [],
            "checkpoints_completed": [],
            "stage_history": [],
        }
        
        state = EpistemicSessionState.from_dict(data)
        assert state.project_name == "restored"
        assert state.current_stage == 3
        assert len(state.assumptions) == 1
        assert len(state.gaps) == 1
        assert state.gaps[0].severity == GapSeverity.HIGH

    def test_from_json(self):
        """Test deserialization from JSON string."""
        original = EpistemicSessionState(project_name="round-trip")
        original.add_assumption("Round trip test", 0.75)
        original.advance_stage("Testing")
        
        json_str = original.to_json()
        restored = EpistemicSessionState.from_json(json_str)
        
        assert restored.project_name == "round-trip"
        assert restored.current_stage == 1
        assert len(restored.assumptions) == 1
        assert restored.assumptions[0].confidence == 0.75


class TestGlobalStateFunctions:
    """Tests for the global state singleton functions."""

    def test_initial_state(self):
        """Test that there's no initial active session."""
        end_epistemic_session()  # Clean up any existing
        assert is_epistemic_active() is False
        assert get_epistemic_state() is None

    def test_start_and_end_session(self):
        """Test starting and ending sessions."""
        end_epistemic_session()
        
        state = start_epistemic_session("test-project")
        assert is_epistemic_active() is True
        assert state.project_name == "test-project"
        assert get_epistemic_state() is state
        
        end_epistemic_session()
        assert is_epistemic_active() is False
        assert get_epistemic_state() is None

    def test_save_and_load(self):
        """Test saving and loading state to file."""
        end_epistemic_session()
        
        # Create and populate a session
        state = start_epistemic_session("save-test")
        state.add_assumption("Saved assumption", 0.85)
        state.add_gap("Saved gap", GapSeverity.LOW, "Data Science")
        state.advance_stage("Saving")
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name
        
        try:
            assert save_epistemic_state(filepath) is True
            
            # End current session
            end_epistemic_session()
            assert is_epistemic_active() is False
            
            # Load from file
            loaded = load_epistemic_state(filepath)
            assert loaded is not None
            assert is_epistemic_active() is True
            assert loaded.project_name == "save-test"
            assert loaded.current_stage == 1
            assert len(loaded.assumptions) == 1
            assert len(loaded.gaps) == 1
        finally:
            end_epistemic_session()
            os.unlink(filepath)

    def test_save_no_session(self):
        """Test that save fails when no session active."""
        end_epistemic_session()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name
        try:
            assert save_epistemic_state(filepath) is False
        finally:
            os.unlink(filepath)

    def test_load_nonexistent(self):
        """Test that loading nonexistent file returns None."""
        end_epistemic_session()
        result = load_epistemic_state("/nonexistent/path/to/file.json")
        assert result is None
        assert is_epistemic_active() is False


class TestStageNames:
    """Tests for stage name utilities."""

    def test_stage_names_count(self):
        """Test that we have 13 stage names (0-12)."""
        assert len(STAGE_NAMES) == 13

    def test_get_stage_name_valid(self):
        """Test getting valid stage names."""
        assert get_stage_name(0) == "Philosophical Foundation"
        assert get_stage_name(1) == "Epistemic State Creation"
        assert get_stage_name(7) == "Build Execution"
        assert get_stage_name(12) == "Documentation Sync"

    def test_get_stage_name_invalid(self):
        """Test getting invalid stage names."""
        assert get_stage_name(-1) == "Stage -1"
        assert get_stage_name(13) == "Stage 13"
        assert get_stage_name(100) == "Stage 100"


class TestMilestoneAndPhase:
    """Tests for build phase tracking."""

    def test_create_milestone(self):
        """Test milestone creation."""
        milestone = Milestone(
            name="Setup database schema",
            checkpoint_question="Can a user create an account?",
        )
        assert milestone.status == "pending"
        assert milestone.completed_at is None

    def test_create_phase(self):
        """Test phase creation with milestones."""
        milestones = [
            Milestone(name="M1", checkpoint_question="Q1"),
            Milestone(name="M2", checkpoint_question="Q2"),
        ]
        phase = BuildPhase(
            name="Foundation",
            goal="Set up core infrastructure",
            milestones=milestones,
            rollback_plan="Revert to previous commit",
        )
        assert len(phase.milestones) == 2
        assert phase.rollback_plan == "Revert to previous commit"

    def test_phase_to_dict(self):
        """Test phase serialization."""
        phase = BuildPhase(
            name="Core",
            goal="Build main features",
            milestones=[Milestone(name="M1", checkpoint_question="Q1")],
        )
        d = phase.to_dict()
        assert d["name"] == "Core"
        assert len(d["milestones"]) == 1
