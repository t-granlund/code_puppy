# agent_tools.py
import asyncio
import hashlib
import itertools
import json
import logging
import pickle
import re
import traceback
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import List, Optional, Set

from dbos import DBOS, SetWorkflowID
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Pack Governor for concurrent agent limits
from code_puppy.core import PackGovernor, AgentRole, acquire_agent_slot, release_agent_slot

# Import Agent from pydantic_ai to create temporary agents for invocation
from pydantic_ai import Agent, RunContext, UsageLimits
from pydantic_ai.messages import ModelMessage

from code_puppy.config import (
    DATA_DIR,
    get_message_limit,
    get_use_dbos,
    get_value,
)
from code_puppy.messaging import (
    SubAgentInvocationMessage,
    SubAgentResponseMessage,
    emit_error,
    emit_info,
    emit_success,
    emit_warning,
    get_message_bus,
    get_session_context,
    set_session_context,
)
from code_puppy.tools.common import generate_group_id
from code_puppy.tools.subagent_context import subagent_context

# Set to track active subagent invocation tasks
_active_subagent_tasks: Set[asyncio.Task] = set()

# Atomic counter for DBOS workflow IDs - ensures uniqueness even in rapid back-to-back calls
# itertools.count() is thread-safe for next() calls
_dbos_workflow_counter = itertools.count()


def _generate_dbos_workflow_id(base_id: str) -> str:
    """Generate a unique DBOS workflow ID by appending an atomic counter.

    DBOS requires workflow IDs to be unique across all executions.
    This function ensures uniqueness by combining the base_id with
    an atomically incrementing counter.

    Args:
        base_id: The base identifier (e.g., group_id from generate_group_id)

    Returns:
        A unique workflow ID in format: {base_id}-wf-{counter}
    """
    counter = next(_dbos_workflow_counter)
    return f"{base_id}-wf-{counter}"


def _generate_session_hash_suffix() -> str:
    """Generate a short SHA1 hash suffix based on current timestamp for uniqueness.

    Returns:
        A 6-character hex string, e.g., "a3f2b1"
    """
    timestamp = str(datetime.now().timestamp())
    return hashlib.sha1(timestamp.encode()).hexdigest()[:6]


# Regex pattern for kebab-case session IDs
SESSION_ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SESSION_ID_MAX_LENGTH = 128


def _validate_session_id(session_id: str) -> None:
    """Validate that a session ID follows kebab-case naming conventions.

    Args:
        session_id: The session identifier to validate

    Raises:
        ValueError: If the session_id is invalid

    Valid format:
        - Lowercase letters (a-z)
        - Numbers (0-9)
        - Hyphens (-) to separate words
        - No uppercase, no underscores, no special characters
        - Length between 1 and 128 characters

    Examples:
        Valid: "my-session", "agent-session-1", "discussion-about-code"
        Invalid: "MySession", "my_session", "my session", "my--session"
    """
    if not session_id:
        raise ValueError("session_id cannot be empty")

    if len(session_id) > SESSION_ID_MAX_LENGTH:
        raise ValueError(
            f"Invalid session_id '{session_id}': must be {SESSION_ID_MAX_LENGTH} characters or less"
        )

    if not SESSION_ID_PATTERN.match(session_id):
        raise ValueError(
            f"Invalid session_id '{session_id}': must be kebab-case "
            "(lowercase letters, numbers, and hyphens only). "
            "Examples: 'my-session', 'agent-session-1', 'discussion-about-code'"
        )


def _get_subagent_sessions_dir() -> Path:
    """Get the directory for storing subagent session data.

    Returns:
        Path to XDG data directory/subagent_sessions/
    """
    sessions_dir = Path(DATA_DIR) / "subagent_sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    return sessions_dir


def _save_session_history(
    session_id: str,
    message_history: List[ModelMessage],
    agent_name: str,
    initial_prompt: str | None = None,
) -> None:
    """Save session history to filesystem.

    Args:
        session_id: The session identifier (must be kebab-case)
        message_history: List of messages to save
        agent_name: Name of the agent being invoked
        initial_prompt: The first prompt that started this session (for .txt metadata)

    Raises:
        ValueError: If session_id is not valid kebab-case format
    """
    # Validate session_id format before saving
    _validate_session_id(session_id)

    sessions_dir = _get_subagent_sessions_dir()

    # Save pickle file with message history
    pkl_path = sessions_dir / f"{session_id}.pkl"
    with open(pkl_path, "wb") as f:
        pickle.dump(message_history, f)

    # Save or update txt file with metadata
    txt_path = sessions_dir / f"{session_id}.txt"
    if not txt_path.exists() and initial_prompt:
        # Only write initial metadata on first save
        metadata = {
            "session_id": session_id,
            "agent_name": agent_name,
            "initial_prompt": initial_prompt,
            "created_at": datetime.now().isoformat(),
            "message_count": len(message_history),
        }
        with open(txt_path, "w") as f:
            json.dump(metadata, f, indent=2)
    elif txt_path.exists():
        # Update message count on subsequent saves
        try:
            with open(txt_path, "r") as f:
                metadata = json.load(f)
            metadata["message_count"] = len(message_history)
            metadata["last_updated"] = datetime.now().isoformat()
            with open(txt_path, "w") as f:
                json.dump(metadata, f, indent=2)
        except Exception:
            pass  # If we can't update metadata, no big deal


def _load_session_history(session_id: str) -> List[ModelMessage]:
    """Load session history from filesystem.

    Args:
        session_id: The session identifier (must be kebab-case)

    Returns:
        List of ModelMessage objects, or empty list if session doesn't exist

    Raises:
        ValueError: If session_id is not valid kebab-case format
    """
    # Validate session_id format before loading
    _validate_session_id(session_id)

    sessions_dir = _get_subagent_sessions_dir()
    pkl_path = sessions_dir / f"{session_id}.pkl"

    if not pkl_path.exists():
        return []

    try:
        with open(pkl_path, "rb") as f:
            return pickle.load(f)
    except Exception:
        # If pickle is corrupted or incompatible, return empty history
        return []


class AgentInfo(BaseModel):
    """Information about an available agent."""

    name: str
    display_name: str
    description: str


class ListAgentsOutput(BaseModel):
    """Output for the list_agents tool."""

    agents: List[AgentInfo]
    error: str | None = None


class AgentInvokeOutput(BaseModel):
    """Output for the invoke_agent tool."""

    response: str | None
    agent_name: str
    session_id: str | None = None
    error: str | None = None
    is_retriable: bool = False  # Hint that retry may succeed (transient network error)


def register_list_agents(agent):
    """Register the list_agents tool with the provided agent.

    Args:
        agent: The agent to register the tool with
    """

    @agent.tool
    def list_agents(context: RunContext) -> ListAgentsOutput:
        """List all available sub-agents that can be invoked.

        Returns:
            ListAgentsOutput: A list of available agents with their names and display names.
        """
        # Generate a group ID for this tool execution
        group_id = generate_group_id("list_agents")

        from rich.text import Text

        from code_puppy.config import get_banner_color

        list_agents_color = get_banner_color("list_agents")
        emit_info(
            Text.from_markup(
                f"\n[bold white on {list_agents_color}] LIST AGENTS [/bold white on {list_agents_color}]"
            ),
            message_group=group_id,
        )

        try:
            from code_puppy.agents import get_agent_descriptions, get_available_agents

            # Get available agents and their descriptions from the agent manager
            agents_dict = get_available_agents()
            descriptions_dict = get_agent_descriptions()

            # Convert to list of AgentInfo objects
            agents = [
                AgentInfo(
                    name=name,
                    display_name=display_name,
                    description=descriptions_dict.get(name, "No description available"),
                )
                for name, display_name in agents_dict.items()
            ]

            # Accumulate output into a single string and emit once
            # Use Text.from_markup() to pass a Rich object that won't be escaped
            lines = []
            for agent_item in agents:
                lines.append(
                    f"- [bold]{agent_item.name}[/bold]: {agent_item.display_name}\n"
                    f"  [dim]{agent_item.description}[/dim]"
                )
            emit_info(Text.from_markup("\n".join(lines)), message_group=group_id)

            return ListAgentsOutput(agents=agents)

        except Exception as e:
            error_msg = f"Error listing agents: {str(e)}"
            emit_error(error_msg, message_group=group_id)
            return ListAgentsOutput(agents=[], error=error_msg)

    return list_agents


def register_invoke_agent(agent):
    """Register the invoke_agent tool with the provided agent.

    Args:
        agent: The agent to register the tool with
    """

    @agent.tool
    async def invoke_agent(
        context: RunContext, agent_name: str, prompt: str, session_id: str | None = None
    ) -> AgentInvokeOutput:
        """Invoke a specific sub-agent with a given prompt.

        Args:
            agent_name: The name of the agent to invoke
            prompt: The prompt to send to the agent
            session_id: Optional session ID for maintaining conversation memory across invocations.

                       **Session ID Format:**
                       - Must be kebab-case (lowercase letters, numbers, hyphens only)
                       - Should be human-readable: e.g., "implement-oauth", "review-auth"
                       - For NEW sessions, a SHA1 hash suffix is automatically appended for uniqueness
                       - To CONTINUE a session, use the full session_id (with hash) from the previous invocation
                       - If None (default), auto-generates like "agent-name-session-1"

                       **When to use session_id:**
                       - **NEW SESSION**: Provide a base name like "review-auth" - we'll append a unique hash
                       - **CONTINUE SESSION**: Use the full session_id from output (e.g., "review-auth-a3f2b1")
                       - **ONE-OFF TASKS**: Leave as None (auto-generate)

                       **Most common pattern:** Leave session_id as None (auto-generate) unless you
                       specifically need conversational memory.

        Returns:
            AgentInvokeOutput: Contains:
                - response (str | None): The agent's response to the prompt
                - agent_name (str): Name of the invoked agent
                - session_id (str | None): The full session ID (with hash suffix) - USE THIS to continue the conversation!
                - error (str | None): Error message if invocation failed

        Examples:
            # COMMON CASE: One-off invocation, no memory needed (auto-generate session)
            result = invoke_agent(
                "qa-expert",
                "Review this function: def add(a, b): return a + b"
            )
            # result.session_id will be something like "qa-expert-session-a3f2b1"

            # MULTI-TURN: Start a NEW conversation with a base session ID
            # A hash suffix is auto-appended: "review-add-function" -> "review-add-function-a3f2b1"
            result1 = invoke_agent(
                "qa-expert",
                "Review this function: def add(a, b): return a + b",
                session_id="review-add-function"
            )
            # result1.session_id contains the full ID like "review-add-function-a3f2b1"

            # Continue the SAME conversation using session_id from the previous result
            result2 = invoke_agent(
                "qa-expert",
                "Can you suggest edge cases for that function?",
                session_id=result1.session_id  # Use the session_id from previous output!
            )

            # Multiple INDEPENDENT reviews (each gets unique hash suffix)
            auth_review = invoke_agent(
                "code-reviewer",
                "Review my authentication code",
                session_id="auth-review"  # -> "auth-review-<hash1>"
            )
            # auth_review.session_id contains the full ID to continue this review

            payment_review = invoke_agent(
                "code-reviewer",
                "Review my payment processing code",
                session_id="payment-review"  # -> "payment-review-<hash2>"
            )
            # payment_review.session_id contains a different full ID
        """
        from code_puppy.agents.agent_manager import load_agent

        # Validate user-provided session_id if given
        if session_id is not None:
            try:
                _validate_session_id(session_id)
            except ValueError as e:
                # Return error immediately if session_id is invalid
                group_id = generate_group_id("invoke_agent", agent_name)
                emit_error(str(e), message_group=group_id)
                return AgentInvokeOutput(
                    response=None, agent_name=agent_name, error=str(e)
                )

        # Generate a group ID for this tool execution
        group_id = generate_group_id("invoke_agent", agent_name)

        # Check if this is an existing session or a new one
        # For user-provided session_id, check if it exists
        # For None, we'll generate a new one below
        if session_id is not None:
            message_history = _load_session_history(session_id)
            is_new_session = len(message_history) == 0
        else:
            message_history = []
            is_new_session = True

        # Generate or finalize session_id
        if session_id is None:
            # Auto-generate a session ID with hash suffix for uniqueness
            # Example: "qa-expert-session-a3f2b1"
            hash_suffix = _generate_session_hash_suffix()
            session_id = f"{agent_name}-session-{hash_suffix}"
        elif is_new_session:
            # User provided a base name for a NEW session - append hash suffix
            # Example: "review-auth" -> "review-auth-a3f2b1"
            hash_suffix = _generate_session_hash_suffix()
            session_id = f"{session_id}-{hash_suffix}"
        # else: continuing existing session, use session_id as-is

        # === LOGFIRE OODA DELEGATION OBSERVABILITY ===
        # Log delegation event with OODA phase context for observability
        try:
            from code_puppy.core import get_workload_for_agent
            
            # Determine invoking agent name from context
            invoker_name = getattr(agent, 'name', 'unknown')
            target_workload = get_workload_for_agent(agent_name)
            
            # Map workload to OODA phase for observability
            workload_to_ooda = {
                "ORCHESTRATOR": "DECIDE",  # Decision-makers (helios, pack-leader)
                "REASONING": "ORIENT",     # Analyzers (qa-expert, security-auditor)
                "CODING": "ACT",           # Implementers (python-programmer, terminal-qa)
                "LIBRARIAN": "OBSERVE",    # Info gatherers (bloodhound, doc-writer)
            }
            ooda_phase = workload_to_ooda.get(target_workload.name, "ACT")
            
            # Use centralized observability logging
            try:
                from code_puppy.core.observability import log_agent_delegation
                log_agent_delegation(
                    invoker=invoker_name,
                    target=agent_name,
                    ooda_phase=ooda_phase,
                    workload=target_workload.name,
                    session_id=session_id,
                    is_new_session=is_new_session,
                )
            except ImportError:
                # Fall back to direct logfire if observability not available
                import logfire
                logfire.info(
                    "OODA Delegation: {invoker} → {target} ({phase} phase, {workload})",
                    invoker=invoker_name,
                    target=agent_name,
                    phase=ooda_phase,
                    workload=target_workload.name,
                    session_id=session_id,
                    is_new_session=is_new_session,
                )
        except Exception:
            pass  # Don't let logging break delegation

        # Lazy imports to avoid circular dependency
        from code_puppy.agents.subagent_stream_handler import subagent_stream_handler

        # Emit structured invocation message via MessageBus
        bus = get_message_bus()
        bus.emit(
            SubAgentInvocationMessage(
                agent_name=agent_name,
                session_id=session_id,
                prompt=prompt,
                is_new_session=is_new_session,
                message_count=len(message_history),
            )
        )

        # Save current session context and set the new one for this sub-agent
        previous_session_id = get_session_context()
        set_session_context(session_id)

        # Set terminal session for browser-based terminal tools
        # This uses contextvars which properly propagate through async tasks
        from code_puppy.tools.browser.terminal_tools import (
            _terminal_session_var,
            set_terminal_session,
        )

        terminal_session_token = set_terminal_session(f"terminal-{session_id}")

        # Set browser session for browser tools (qa-kitten, etc.)
        # This allows parallel agent invocations to each have their own browser
        from code_puppy.tools.browser.browser_manager import (
            set_browser_session,
        )

        browser_session_token = set_browser_session(f"browser-{session_id}")

        # Track acquired slot for cleanup
        acquired_slot_id: Optional[str] = None

        try:
            # Lazy import to break circular dependency with messaging module
            from code_puppy.model_factory import ModelFactory, make_model_settings

            # Load the specified agent config
            agent_config = load_agent(agent_name)

            # === PACK GOVERNOR: Acquire slot before running agent ===
            slot_result = await acquire_agent_slot(
                agent_name=agent_name,
                estimated_tokens=10_000,  # Conservative estimate
            )
            
            if not slot_result.granted:
                # Slot not available - wait or fail
                if slot_result.wait_seconds > 0:
                    emit_info(
                        f"⏳ Waiting {slot_result.wait_seconds:.1f}s for {agent_name} slot: {slot_result.reason}",
                        message_group=group_id,
                    )
                    await asyncio.sleep(slot_result.wait_seconds)
                    # Retry once after waiting
                    slot_result = await acquire_agent_slot(
                        agent_name=agent_name,
                        estimated_tokens=10_000,
                    )
                    if not slot_result.granted:
                        error_msg = f"Failed to acquire slot for {agent_name}: {slot_result.reason}"
                        emit_error(error_msg, message_group=group_id)
                        return AgentInvokeOutput(
                            response=None, agent_name=agent_name, session_id=session_id, error=error_msg
                        )
                else:
                    error_msg = f"Cannot start {agent_name}: {slot_result.reason}"
                    emit_error(error_msg, message_group=group_id)
                    return AgentInvokeOutput(
                        response=None, agent_name=agent_name, session_id=session_id, error=error_msg
                    )
            
            acquired_slot_id = slot_result.slot_id
            
            # If forced to summary mode, log it and use summary model
            if slot_result.forced_summary_mode:
                emit_info(
                    f"📝 {agent_name} running in summary mode (token threshold exceeded)",
                    message_group=group_id,
                )
                model_name = slot_result.assigned_model
            else:
                # === WORKLOAD-BASED MODEL SELECTION ===
                # Use the AGENT_WORKLOAD_REGISTRY to get the right model for this agent
                from code_puppy.core.agent_orchestration import get_model_for_agent
                model_name = get_model_for_agent(agent_name)
                
                # Log the workload-aware model selection
                from code_puppy.core import WorkloadType, get_workload_for_agent
                workload = get_workload_for_agent(agent_name)
                emit_info(
                    f"🎯 {agent_name} using {model_name} ({workload.name} workload)",
                    message_group=group_id,
                )

            models_config = ModelFactory.load_config()

            # Case-insensitive model lookup helper
            def find_model_key(name: str, config: dict) -> str | None:
                """Find model key with case-insensitive matching."""
                if name in config:
                    return name
                name_lower = name.lower()
                for key in config:
                    if key.lower() == name_lower:
                        return key
                return None

            # Try case-insensitive lookup first
            matched_key = find_model_key(model_name, models_config)
            if matched_key:
                model_name = matched_key
            elif model_name not in models_config:
                # Fallback to agent's configured model if workload model not available
                fallback_model = agent_config.get_model_name()
                emit_warning(
                    f"Model '{model_name}' not found, falling back to {fallback_model}",
                    message_group=group_id,
                )
                model_name = fallback_model
                matched_key = find_model_key(model_name, models_config)
                if matched_key:
                    model_name = matched_key
                elif model_name not in models_config:
                    raise ValueError(f"Model '{model_name}' not found in configuration")

            # Get the raw model first
            raw_model = ModelFactory.get_model(model_name, models_config)
            
            # Wrap in FailoverModel for automatic rate limit and error failover
            # This ensures sub-agents (husky, etc.) get the same failover behavior as main agents
            from code_puppy.failover_model import create_failover_model_for_agent as create_failover
            
            model = create_failover(
                agent_name,
                primary_model=raw_model,
                model_factory_func=lambda name: ModelFactory.get_model(name, models_config),
            )

            # Create a temporary agent instance to avoid interfering with current agent state
            instructions = agent_config.get_full_system_prompt()

            # Add AGENTS.md content to subagents
            puppy_rules = agent_config.load_puppy_rules()
            if puppy_rules:
                instructions += f"\n\n{puppy_rules}"

            # Apply prompt additions (like file permission handling) to temporary agents
            from code_puppy import callbacks
            from code_puppy.model_utils import prepare_prompt_for_model

            prompt_additions = callbacks.on_load_prompt()
            if len(prompt_additions):
                instructions += "\n" + "\n".join(prompt_additions)

            # Handle claude-code models: swap instructions, and prepend system prompt only on first message
            prepared = prepare_prompt_for_model(
                model_name,
                instructions,
                prompt,
                prepend_system_to_user=is_new_session,  # Only prepend on first message
            )
            instructions = prepared.instructions
            prompt = prepared.user_prompt

            subagent_name = f"temp-invoke-agent-{session_id}"
            model_settings = make_model_settings(model_name)

            # Get MCP servers for sub-agents (same as main agent)
            from code_puppy.mcp_ import get_mcp_manager

            mcp_servers = []
            mcp_disabled = get_value("disable_mcp_servers")
            if not (
                mcp_disabled and str(mcp_disabled).lower() in ("1", "true", "yes", "on")
            ):
                manager = get_mcp_manager()
                mcp_servers = manager.get_servers_for_agent()

            if get_use_dbos():
                from pydantic_ai.durable_exec.dbos import DBOSAgent

                # For DBOS, create agent without MCP servers (to avoid serialization issues)
                # and add them at runtime
                temp_agent = Agent(
                    model=model,
                    instructions=instructions,
                    output_type=str,
                    retries=3,
                    toolsets=[],  # MCP servers added separately for DBOS
                    history_processors=[agent_config.message_history_accumulator],
                    model_settings=model_settings,
                )

                # Register the tools that the agent needs
                from code_puppy.tools import register_tools_for_agent

                agent_tools = agent_config.get_available_tools()
                register_tools_for_agent(temp_agent, agent_tools)

                # Wrap with DBOS - no streaming for sub-agents
                dbos_agent = DBOSAgent(
                    temp_agent,
                    name=subagent_name,
                )
                temp_agent = dbos_agent

                # Store MCP servers to add at runtime
                subagent_mcp_servers = mcp_servers
            else:
                # Non-DBOS path - include MCP servers directly in the agent
                temp_agent = Agent(
                    model=model,
                    instructions=instructions,
                    output_type=str,
                    retries=3,
                    toolsets=mcp_servers,
                    history_processors=[agent_config.message_history_accumulator],
                    model_settings=model_settings,
                )

                # Register the tools that the agent needs
                from code_puppy.tools import register_tools_for_agent

                agent_tools = agent_config.get_available_tools()
                register_tools_for_agent(temp_agent, agent_tools)

                subagent_mcp_servers = None

            # Run the temporary agent with the provided prompt as an asyncio task
            # Pass the message_history from the session to continue the conversation
            workflow_id = None  # Track for potential cancellation

            # Always use subagent_stream_handler to silence output and update console manager
            # This ensures all sub-agent output goes through the aggregated dashboard
            stream_handler = partial(subagent_stream_handler, session_id=session_id)

            # Wrap the agent run in subagent context for tracking
            with subagent_context(agent_name):
                if get_use_dbos():
                    # Generate a unique workflow ID for DBOS - ensures no collisions in back-to-back calls
                    workflow_id = _generate_dbos_workflow_id(group_id)

                    # Add MCP servers to the DBOS agent's toolsets
                    # (temp_agent is discarded after this invocation, so no need to restore)
                    if subagent_mcp_servers:
                        temp_agent._toolsets = (
                            temp_agent._toolsets + subagent_mcp_servers
                        )

                    with SetWorkflowID(workflow_id):
                        task = asyncio.create_task(
                            temp_agent.run(
                                prompt,
                                message_history=message_history,
                                usage_limits=UsageLimits(
                                    request_limit=get_message_limit()
                                ),
                                event_stream_handler=stream_handler,
                            )
                        )
                        _active_subagent_tasks.add(task)
                else:
                    task = asyncio.create_task(
                        temp_agent.run(
                            prompt,
                            message_history=message_history,
                            usage_limits=UsageLimits(request_limit=get_message_limit()),
                            event_stream_handler=stream_handler,
                        )
                    )
                    _active_subagent_tasks.add(task)

                try:
                    result = await task
                finally:
                    _active_subagent_tasks.discard(task)
                    if task.cancelled():
                        if get_use_dbos() and workflow_id:
                            DBOS.cancel_workflow(workflow_id)

            # Extract the response from the result
            response = result.output

            # Update the session history with the new messages from this interaction
            # The result contains all_messages which includes the full conversation
            updated_history = result.all_messages()

            # Save to filesystem (include initial prompt only for new sessions)
            _save_session_history(
                session_id=session_id,
                message_history=updated_history,
                agent_name=agent_name,
                initial_prompt=prompt if is_new_session else None,
            )

            # Emit structured response message via MessageBus
            bus.emit(
                SubAgentResponseMessage(
                    agent_name=agent_name,
                    session_id=session_id,
                    response=response,
                    message_count=len(updated_history),
                )
            )

            # === LOGFIRE OODA DELEGATION COMPLETION ===
            try:
                import logfire
                invoker_name = getattr(agent, 'name', 'unknown')
                logfire.info(
                    "OODA Delegation Complete: {invoker} ← {target} (success)",
                    invoker=invoker_name,
                    target=agent_name,
                    session_id=session_id,
                    message_count=len(updated_history),
                    response_length=len(response) if response else 0,
                )
            except Exception:
                pass

            # Emit clean completion summary
            emit_success(
                f"✓ {agent_name} completed successfully", message_group=group_id
            )

            return AgentInvokeOutput(
                response=response, agent_name=agent_name, session_id=session_id
            )

        except Exception as e:
            # Check if this is a retriable error
            err_str = str(e).lower()
            err_type = type(e).__name__.lower()
            
            # Enhanced error detection
            is_retriable = any(indicator in err_str or indicator in err_type for indicator in [
                "remoteprotocolerror", "incomplete chunked", "peer closed",
                "connection reset", "connection refused", "timeout",
                "generator didn't stop",  # asynccontextmanager issue
                "unexpectedmodelbehavior",  # pydantic-ai validation failures
                "toolretryerror",  # Tool execution failures
                "rate limit", "429",  # Rate limiting
            ])
            
            # Extract detailed error context for validation failures
            error_context = str(e)
            if "unexpectedmodelbehavior" in err_type or "validation" in err_str:
                # Log validation failure details to help debug
                logger.error(
                    f"Agent {agent_name} validation failed. "
                    f"Error type: {type(e).__name__}, Details: {error_context}"
                )
                emit_error(
                    f"✗ {agent_name} validation failed: {error_context[:200]}",
                    message_group=group_id
                )
            else:
                # Log the failure with standard formatting
                emit_error(f"✗ {agent_name} failed: {str(e)}", message_group=group_id)

            # Full traceback for debugging
            error_msg = f"Error invoking agent '{agent_name}': {traceback.format_exc()}"
            emit_error(error_msg, message_group=group_id)

            return AgentInvokeOutput(
                response=None,
                agent_name=agent_name,
                session_id=session_id,
                error=error_msg,
                is_retriable=is_retriable,  # Hint to caller that retry may succeed
            )

        finally:
            # === PACK GOVERNOR: Release slot ===
            if acquired_slot_id:
                await release_agent_slot(acquired_slot_id)
            
            # Restore the previous session context
            set_session_context(previous_session_id)
            # Reset terminal session context
            _terminal_session_var.reset(terminal_session_token)
            # Reset browser session context
            from code_puppy.tools.browser.browser_manager import (
                _browser_session_var,
            )

            _browser_session_var.reset(browser_session_token)

    return invoke_agent
