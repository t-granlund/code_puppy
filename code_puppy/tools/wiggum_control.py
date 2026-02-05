"""Wiggum loop control tools for agent-initiated loop management.

This module provides tools that allow agents to programmatically control
the /wiggum autonomous execution loop. This is essential for:

1. **Self-termination**: Agent can stop looping when work is complete
2. **Loop status**: Agent can check if it's running in wiggum mode
3. **Loop count**: Agent can track iteration progress

The key use case is the Epistemic Architect using wiggum to autonomously
execute through its OODA phases until all milestones are complete, then
self-terminating.

Usage:
    Agent calls complete_wiggum_loop() when:
    - All milestones in BUILD.md are complete
    - All quality gates have passed
    - Final verification is successful
    - Documentation is updated to new stable state
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from code_puppy.command_line.wiggum_state import (
    get_wiggum_count,
    is_wiggum_active,
    stop_wiggum,
)


class WiggumStatusOutput(BaseModel):
    """Output from checking wiggum loop status."""
    
    active: bool = Field(description="Whether wiggum loop is currently active")
    loop_count: int = Field(description="Current iteration number (0 if not active)")
    message: str = Field(description="Human-readable status message")


class WiggumStopOutput(BaseModel):
    """Output from stopping wiggum loop."""
    
    stopped: bool = Field(description="Whether the loop was successfully stopped")
    final_loop_count: int = Field(description="Total iterations completed")
    message: str = Field(description="Human-readable result message")


def check_wiggum_status() -> WiggumStatusOutput:
    """Check the current status of wiggum autonomous loop.
    
    Returns:
        WiggumStatusOutput with active status, loop count, and message.
    """
    active = is_wiggum_active()
    count = get_wiggum_count()
    
    if active:
        message = f"🍩 Wiggum loop is ACTIVE (iteration #{count})"
    else:
        message = "Wiggum loop is not active"
    
    return WiggumStatusOutput(
        active=active,
        loop_count=count,
        message=message,
    )


def complete_wiggum_loop(reason: str = "Work complete") -> WiggumStopOutput:
    """Stop the wiggum autonomous loop when work is complete.
    
    Call this tool when:
    - All milestones in BUILD.md are complete
    - All quality gates have passed
    - Final verification is successful
    - The epistemic state has been updated to reflect completion
    
    Args:
        reason: Explanation of why the loop is being stopped.
        
    Returns:
        WiggumStopOutput with stop status, final count, and message.
    """
    was_active = is_wiggum_active()
    final_count = get_wiggum_count()
    
    if was_active:
        stop_wiggum()
        message = f"🛑 Wiggum loop stopped after {final_count} iteration(s). Reason: {reason}"
        return WiggumStopOutput(
            stopped=True,
            final_loop_count=final_count,
            message=message,
        )
    else:
        return WiggumStopOutput(
            stopped=False,
            final_loop_count=0,
            message="Wiggum loop was not active. No action taken.",
        )


def register_check_wiggum_status(agent: Agent) -> None:
    """Register the check_wiggum_status tool with the given agent."""

    @agent.tool
    def check_wiggum_status_tool(
        context: RunContext,  # noqa: ARG001 - Required by framework
    ) -> WiggumStatusOutput:
        """Check if the agent is running in wiggum autonomous loop mode.
        
        Use this to:
        - Determine if you're in an autonomous execution loop
        - Get the current iteration count for logging/tracking
        - Decide whether to continue iterating or stop
        
        Returns:
            WiggumStatusOutput with:
                - active (bool): True if wiggum loop is running
                - loop_count (int): Current iteration number
                - message (str): Human-readable status
        """
        return check_wiggum_status()


def register_complete_wiggum_loop(agent: Agent) -> None:
    """Register the complete_wiggum_loop tool with the given agent."""

    @agent.tool
    def complete_wiggum_loop_tool(
        context: RunContext,  # noqa: ARG001 - Required by framework
        reason: str = "All milestones complete",
    ) -> WiggumStopOutput:
        """Stop the wiggum autonomous loop when all work is complete.
        
        IMPORTANT: Only call this when you have VERIFIED:
        1. All milestones in BUILD.md are marked complete
        2. All quality gates have passed
        3. Final E2E verification was successful
        4. epistemic/state.json has been updated to stable state
        5. CHECKPOINT.md shows "COMPLETE" status
        
        If any milestones remain or verification failed, do NOT call this.
        Instead, continue iterating to complete remaining work.
        
        Args:
            reason: Explanation of completion (e.g., "All 5 milestones complete, 
                   E2E tests passing, documentation updated")
        
        Returns:
            WiggumStopOutput with:
                - stopped (bool): True if loop was stopped
                - final_loop_count (int): Total iterations completed
                - message (str): Confirmation message
        
        Example:
            >>> complete_wiggum_loop(reason="All 5 milestones complete, "
            ...     "security audit passed, E2E tests green")
            WiggumStopOutput(stopped=True, final_loop_count=7, 
                message="🛑 Wiggum loop stopped after 7 iteration(s)...")
        """
        return complete_wiggum_loop(reason)


def register_wiggum_control_tools(agent: Agent) -> None:
    """Register all wiggum control tools with the given agent.
    
    This is a convenience function that registers both:
    - check_wiggum_status: Query loop status
    - complete_wiggum_loop: Stop the loop when done
    """
    register_check_wiggum_status(agent)
    register_complete_wiggum_loop(agent)
