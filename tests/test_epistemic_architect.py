"""Tests for the Epistemic Architect agent."""

import pytest

from code_puppy.agents.agent_epistemic_architect import (
    EXPERT_LENSES,
    PIPELINE_STAGES,
    QUALITY_GATES,
    EpistemicArchitectAgent,
    format_gates_summary,
    format_lens_summary,
    format_pipeline_summary,
)


class TestEpistemicArchitectAgent:
    """Tests for the EpistemicArchitectAgent class."""

    def test_agent_name(self):
        """Test agent name is correct."""
        agent = EpistemicArchitectAgent()
        assert agent.name == "epistemic-architect"

    def test_agent_display_name(self):
        """Test display name includes emoji."""
        agent = EpistemicArchitectAgent()
        assert "🏛️" in agent.display_name
        assert "🔬" in agent.display_name
        assert "Epistemic Architect" in agent.display_name

    def test_agent_description(self):
        """Test description mentions key concepts."""
        agent = EpistemicArchitectAgent()
        desc = agent.description
        assert "evidence-based" in desc.lower() or "structured" in desc.lower()
        assert "7" in desc or "lenses" in desc.lower() or "gates" in desc.lower()

    def test_available_tools(self):
        """Test that agent has appropriate tools."""
        agent = EpistemicArchitectAgent()
        tools = agent.get_available_tools()
        
        # Should have file exploration tools
        assert "list_files" in tools
        assert "read_file" in tools
        
        # Should have editing tools for creating epistemic artifacts
        assert "edit_file" in tools or "create_file" in tools
        
        # Should have reasoning transparency
        assert "agent_share_your_reasoning" in tools
        
        # Should have agent coordination
        assert "invoke_agent" in tools

    def test_system_prompt_contains_lenses(self):
        """Test that system prompt mentions all 7 lenses."""
        agent = EpistemicArchitectAgent()
        prompt = agent.get_system_prompt()
        
        assert "Philosophy" in prompt
        assert "Data Science" in prompt
        assert "Safety" in prompt or "Risk" in prompt
        assert "Topology" in prompt
        assert "Math" in prompt or "Theoretical" in prompt
        assert "Systems" in prompt or "Engineering" in prompt
        assert "Product" in prompt or "UX" in prompt

    def test_system_prompt_contains_gates(self):
        """Test that system prompt mentions the 6 quality gates."""
        agent = EpistemicArchitectAgent()
        prompt = agent.get_system_prompt()
        
        assert "Observables" in prompt
        assert "Testability" in prompt
        assert "Reversibility" in prompt
        assert "Confidence" in prompt
        assert "Agreement" in prompt or "Lens" in prompt
        assert "Evidence" in prompt

    def test_system_prompt_contains_ralph_loop(self):
        """Test that system prompt mentions Ralph loops."""
        agent = EpistemicArchitectAgent()
        prompt = agent.get_system_prompt()
        
        assert "Ralph" in prompt
        assert "Observe" in prompt
        assert "Orient" in prompt
        assert "Decide" in prompt
        assert "Act" in prompt

    def test_system_prompt_contains_stages(self):
        """Test that system prompt mentions pipeline stages."""
        agent = EpistemicArchitectAgent()
        prompt = agent.get_system_prompt()
        
        assert "Stage" in prompt or "stage" in prompt
        assert "Epistemic State" in prompt
        assert "Gap" in prompt
        assert "MVP" in prompt or "Planning" in prompt

    def test_system_prompt_contains_pause_triggers(self):
        """Test that system prompt mentions when to pause."""
        agent = EpistemicArchitectAgent()
        prompt = agent.get_system_prompt()
        
        assert "PAUSE" in prompt or "pause" in prompt or "Pause" in prompt
        assert "CRITICAL" in prompt or "critical" in prompt

    def test_model_requirements(self):
        """Test model requirements are specified."""
        agent = EpistemicArchitectAgent()
        reqs = agent.get_model_requirements()
        
        # Should prefer reasoning models
        if reqs:
            assert "preferred_traits" in reqs or "minimum_context" in reqs


class TestExpertLenses:
    """Tests for the EXPERT_LENSES configuration."""

    def test_seven_lenses(self):
        """Test that there are exactly 7 lenses."""
        assert len(EXPERT_LENSES) == 7

    def test_lens_structure(self):
        """Test that each lens has required fields."""
        for lens in EXPERT_LENSES:
            assert "name" in lens
            assert "emoji" in lens
            assert "question" in lens
            assert "outputs" in lens
            assert isinstance(lens["outputs"], list)
            assert len(lens["outputs"]) >= 2

    def test_lens_names(self):
        """Test expected lens names are present."""
        names = {lens["name"] for lens in EXPERT_LENSES}
        assert "Philosophy" in names
        assert "Data Science" in names
        assert "Safety/Risk" in names
        assert "Topology" in names
        assert "Theoretical Math" in names
        assert "Systems Engineering" in names
        assert "Product/UX" in names


class TestQualityGates:
    """Tests for the QUALITY_GATES configuration."""

    def test_six_gates(self):
        """Test that there are exactly 6 gates."""
        assert len(QUALITY_GATES) == 6

    def test_gate_structure(self):
        """Test that each gate has required fields."""
        for gate in QUALITY_GATES:
            assert "name" in gate
            assert "check" in gate
            assert "emoji" in gate

    def test_gate_names(self):
        """Test expected gate names are present."""
        names = {gate["name"] for gate in QUALITY_GATES}
        assert "Observables" in names
        assert "Testability" in names
        assert "Reversibility" in names
        assert "Confidence" in names
        assert "Lens Agreement" in names
        assert "Evidence Grounding" in names


class TestPipelineStages:
    """Tests for the PIPELINE_STAGES configuration."""

    def test_thirteen_stages(self):
        """Test that there are 13 stages (0-12)."""
        assert len(PIPELINE_STAGES) == 13

    def test_stage_ids_sequential(self):
        """Test that stage IDs are sequential from 0."""
        ids = [stage["id"] for stage in PIPELINE_STAGES]
        assert ids == list(range(13))

    def test_stage_structure(self):
        """Test that each stage has required fields."""
        for stage in PIPELINE_STAGES:
            assert "id" in stage
            assert "name" in stage
            assert "desc" in stage

    def test_key_stages_present(self):
        """Test that key stages are present."""
        names = {stage["name"] for stage in PIPELINE_STAGES}
        assert "Philosophical Foundation" in names
        assert "Epistemic State Creation" in names
        assert "Lens Evaluation" in names
        assert "Gap Analysis" in names
        assert "Goal Emergence" in names
        assert "MVP Planning" in names
        assert "Build Execution" in names


class TestFormatFunctions:
    """Tests for the formatting helper functions."""

    def test_format_lens_summary(self):
        """Test lens summary formatting."""
        summary = format_lens_summary()
        
        # Should be markdown table
        assert "|" in summary
        assert "Lens" in summary
        assert "Question" in summary
        
        # Should mention all lenses
        assert "Philosophy" in summary
        assert "Data Science" in summary

    def test_format_gates_summary(self):
        """Test gates summary formatting."""
        summary = format_gates_summary()
        
        # Should be bullet list
        assert "- " in summary or "* " in summary
        
        # Should mention all gates
        assert "Observables" in summary
        assert "Testability" in summary

    def test_format_pipeline_summary(self):
        """Test pipeline summary formatting."""
        summary = format_pipeline_summary()
        
        # Should be numbered list
        assert "0." in summary
        assert "1." in summary
        
        # Should mention key stages
        assert "Philosophical Foundation" in summary
        assert "Build Execution" in summary


class TestAgentMetadata:
    """Tests for agent metadata export."""

    def test_metadata_import(self):
        """Test that AGENT_METADATA is importable."""
        from code_puppy.agents.agent_epistemic_architect import AGENT_METADATA
        
        assert "name" in AGENT_METADATA
        assert AGENT_METADATA["name"] == "epistemic-architect"
        assert "description" in AGENT_METADATA
        assert "tags" in AGENT_METADATA
        assert "epistemic" in AGENT_METADATA["tags"]
