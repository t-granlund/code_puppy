"""Agent Orchestration - Coordinates agent invocation with workload-aware model selection.

This module provides the bridge between:
1. AGENT_WORKLOAD_REGISTRY (which agent uses which workload type)
2. WORKLOAD_CHAINS (which models to use for each workload)
3. PackGovernor (concurrency limits and slot management)

Orchestration Hierarchy:
  Epistemic Architect → Planning → Pack Leader → Sub-agents
                     ↘ Helios (creates new tools/agents) ↗

Usage:
    from code_puppy.core.agent_orchestration import AgentOrchestrator
    
    orchestrator = AgentOrchestrator()
    
    # Get model for an agent
    model = orchestrator.get_model_for_agent("husky")
    
    # Invoke an agent with automatic model selection
    result = await orchestrator.invoke_agent("pack-leader", task="...")
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from .pack_governor import AgentRole, PackGovernor
from .rate_limit_failover import RateLimitFailover, WorkloadType

logger = logging.getLogger(__name__)


# Orchestration hierarchy - who can invoke whom
ORCHESTRATION_HIERARCHY: Dict[str, List[str]] = {
    # Epistemic Architect can invoke anyone
    "epistemic-architect": [
        "planning",
        "pack-leader", 
        "helios",
        "qa-expert",
        "security-auditor",
    ],
    # Planning can invoke implementation agents
    "planning": [
        "pack-leader",
        "helios",
        "code-puppy",
    ],
    # Pack Leader coordinates the pack
    "pack-leader": [
        "bloodhound",
        "terrier",
        "husky",
        "shepherd",
        "retriever",
        "watchdog",
    ],
    # Helios can invoke any agent (as a universal constructor)
    "helios": [
        "pack-leader",
        "code-puppy",
        "python-programmer",
    ],
}


class AgentOrchestrator:
    """Orchestrates agent invocation with workload-aware model selection.
    
    Provides a unified interface for:
    1. Getting the right model for an agent
    2. Managing agent invocation with rate limit awareness
    3. Handling failover when models are exhausted
    """
    
    _instance: Optional["AgentOrchestrator"] = None
    
    def __new__(cls) -> "AgentOrchestrator":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._failover_manager = RateLimitFailover()
        self._governor = PackGovernor()
        self._initialized = True
    
    def get_workload_for_agent(self, agent_name: str) -> WorkloadType:
        """Get the workload type for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            WorkloadType for the agent
        """
        return self._failover_manager.get_workload_for_agent(agent_name)
    
    def get_model_for_agent(self, agent_name: str) -> str:
        """Get the primary model for an agent based on workload.
        
        Accounts for rate-limited models and returns the best available option.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Primary model name for this agent's workload
        """
        return self._failover_manager.get_primary_model_for_agent(agent_name)
    
    def get_failover_chain(self, agent_name: str) -> List[str]:
        """Get the full failover chain for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            List of models in failover priority order
        """
        return self._failover_manager.get_failover_chain_for_agent(agent_name)
    
    def get_allowed_invocations(self, agent_name: str) -> List[str]:
        """Get list of agents that can be invoked by this agent.
        
        Args:
            agent_name: The invoking agent's name
            
        Returns:
            List of agent names that can be invoked
        """
        return ORCHESTRATION_HIERARCHY.get(agent_name, [])
    
    def can_invoke(self, invoker: str, target: str) -> bool:
        """Check if one agent can invoke another.
        
        Args:
            invoker: Agent attempting to invoke
            target: Agent to be invoked
            
        Returns:
            True if invocation is allowed
        """
        allowed = self.get_allowed_invocations(invoker)
        if not allowed:
            # Agent not in hierarchy can invoke any other agent
            return True
        return target in allowed
    
    def get_agent_summary(self, agent_name: str) -> Dict[str, Any]:
        """Get a summary of an agent's configuration.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dict with workload, role, model, and failover info
        """
        workload = self.get_workload_for_agent(agent_name)
        role = self._governor._get_role(agent_name)
        model = self.get_model_for_agent(agent_name)
        chain = self.get_failover_chain(agent_name)
        
        return {
            "agent": agent_name,
            "workload": workload.name,
            "role": role.value,
            "primary_model": model,
            "failover_chain": chain[:3],  # First 3 for brevity
            "can_invoke": self.get_allowed_invocations(agent_name),
        }
    
    def get_all_agent_summaries(self) -> List[Dict[str, Any]]:
        """Get summaries for all registered agents.
        
        Returns:
            List of agent summary dicts
        """
        registry = self._failover_manager.AGENT_WORKLOAD_REGISTRY
        return [self.get_agent_summary(name) for name in registry.keys()]
    
    async def prepare_agent_invocation(
        self,
        agent_name: str,
        estimated_tokens: int = 10_000,
    ) -> Tuple[bool, str, Optional[str]]:
        """Prepare to invoke an agent (acquire slot, get model).
        
        Args:
            agent_name: Name of the agent to invoke
            estimated_tokens: Estimated tokens for the task
            
        Returns:
            Tuple of (can_proceed, model_to_use, slot_id)
        """
        result = await self._governor.acquire_slot(agent_name, estimated_tokens)
        
        if not result.granted:
            return False, "", None
        
        # Use assigned model from governor (may be forced summary mode)
        if result.forced_summary_mode:
            return True, result.assigned_model, result.slot_id
        
        # Get workload-appropriate model
        model = self.get_model_for_agent(agent_name)
        return True, model, result.slot_id
    
    async def release_agent_slot(self, slot_id: str) -> None:
        """Release an agent slot after completion.
        
        Args:
            slot_id: Slot ID from prepare_agent_invocation
        """
        await self._governor.release_slot(slot_id)
    
    def record_rate_limit(self, model_name: str, agent_name: str) -> str:
        """Record that a model hit rate limit during agent execution.
        
        Args:
            model_name: Model that hit rate limit
            agent_name: Agent that was using the model
            
        Returns:
            Suggested failover model
        """
        workload = self.get_workload_for_agent(agent_name)
        return self._failover_manager.get_workload_failover(model_name, workload) or ""


# Singleton accessor
def get_orchestrator() -> AgentOrchestrator:
    """Get the singleton AgentOrchestrator instance."""
    return AgentOrchestrator()


# Convenience functions for direct imports
def get_model_for_agent(agent_name: str) -> str:
    """Get the primary model for an agent."""
    return get_orchestrator().get_model_for_agent(agent_name)


def get_failover_chain_for_agent(agent_name: str) -> List[str]:
    """Get the failover chain for an agent."""
    return get_orchestrator().get_failover_chain(agent_name)


def get_workload_for_agent(agent_name: str) -> WorkloadType:
    """Get the workload type for an agent."""
    return get_orchestrator().get_workload_for_agent(agent_name)


def create_failover_model_for_agent(
    agent_name: str,
    primary_model=None,
    model_factory_func=None,
):
    """Create a FailoverModel for an agent with automatic workload-based failover.
    
    This wraps the primary model with automatic rate limit detection and failover
    to workload-appropriate backup models.
    
    Args:
        agent_name: Name of the agent (e.g., "bloodhound", "husky")
        primary_model: The primary Model instance. If None, created from workload chain.
        model_factory_func: Function to create Model from name: (str) -> Model
        
    Returns:
        FailoverModel wrapping the primary with failover chain,
        or the primary model if failover creation fails.
    
    Example:
        model = create_failover_model_for_agent("bloodhound")
        agent = Agent(model=model, ...)
    """
    from code_puppy.failover_model import FailoverModel, create_failover_model_for_agent as _create
    
    return _create(agent_name, primary_model, model_factory_func)
