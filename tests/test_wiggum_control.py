"""Tests for wiggum control tools."""

import pytest

from code_puppy.command_line.wiggum_state import (
    get_wiggum_count,
    is_wiggum_active,
    start_wiggum,
    stop_wiggum,
)
from code_puppy.tools.wiggum_control import (
    WiggumStatusOutput,
    WiggumStopOutput,
    check_wiggum_status,
    complete_wiggum_loop,
)


class TestWiggumControlTools:
    """Tests for wiggum control tool functions."""

    def setup_method(self):
        """Ensure wiggum is stopped before each test."""
        stop_wiggum()

    def teardown_method(self):
        """Ensure wiggum is stopped after each test."""
        stop_wiggum()

    def test_check_status_when_inactive(self):
        """Check status returns correct values when wiggum is inactive."""
        result = check_wiggum_status()
        
        assert isinstance(result, WiggumStatusOutput)
        assert result.active is False
        assert result.loop_count == 0
        assert "not active" in result.message.lower()

    def test_check_status_when_active(self):
        """Check status returns correct values when wiggum is active."""
        start_wiggum("test prompt")
        
        result = check_wiggum_status()
        
        assert isinstance(result, WiggumStatusOutput)
        assert result.active is True
        assert result.loop_count == 0  # Not incremented yet
        assert "ACTIVE" in result.message

    def test_complete_wiggum_when_inactive(self):
        """Completing wiggum when not active returns appropriate response."""
        result = complete_wiggum_loop("Test reason")
        
        assert isinstance(result, WiggumStopOutput)
        assert result.stopped is False
        assert result.final_loop_count == 0
        assert "was not active" in result.message.lower()

    def test_complete_wiggum_when_active(self):
        """Completing wiggum when active stops the loop."""
        start_wiggum("test prompt")
        
        # Verify active before
        assert is_wiggum_active() is True
        
        result = complete_wiggum_loop("All milestones done")
        
        assert isinstance(result, WiggumStopOutput)
        assert result.stopped is True
        assert "stopped" in result.message.lower()
        assert "All milestones done" in result.message
        
        # Verify stopped after
        assert is_wiggum_active() is False

    def test_complete_wiggum_preserves_loop_count(self):
        """Completing wiggum returns the correct final loop count."""
        from code_puppy.command_line.wiggum_state import increment_wiggum_count
        
        start_wiggum("test prompt")
        increment_wiggum_count()
        increment_wiggum_count()
        increment_wiggum_count()
        
        result = complete_wiggum_loop("Done after 3 loops")
        
        assert result.stopped is True
        assert result.final_loop_count == 3

    def test_check_status_shows_loop_count(self):
        """Check status shows current iteration number."""
        from code_puppy.command_line.wiggum_state import increment_wiggum_count
        
        start_wiggum("test prompt")
        increment_wiggum_count()
        increment_wiggum_count()
        
        result = check_wiggum_status()
        
        assert result.loop_count == 2
        assert "#2" in result.message or "2" in result.message


class TestToolRegistration:
    """Tests for tool registration functions."""

    def test_tools_in_registry(self):
        """Verify wiggum control tools are in the global registry."""
        from code_puppy.tools import TOOL_REGISTRY
        
        assert "check_wiggum_status" in TOOL_REGISTRY
        assert "complete_wiggum_loop" in TOOL_REGISTRY

    def test_epistemic_architect_has_tools(self):
        """Verify Epistemic Architect agent has wiggum tools."""
        from code_puppy.agents.agent_epistemic_architect import EpistemicArchitectAgent
        
        agent = EpistemicArchitectAgent()
        tools = agent.get_available_tools()
        
        assert "check_wiggum_status" in tools
        assert "complete_wiggum_loop" in tools
        assert "ask_user_question" in tools
