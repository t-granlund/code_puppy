"""Pack Governor - Manages concurrent Pack Agent execution.

Enforces constraints to prevent rate limit exhaustion:
- Max 2 active "Coding" agents (Cerebras) at once
- Max 1 active "Reviewer" agent (Claude)
- Force summary mode (Gemini Flash) when over threshold
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from .model_router import ModelRouter, ModelTier, TaskType
from .token_budget import TokenBudgetManager

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Roles for pack agents with different concurrency limits."""
    
    CODER = "coder"  # Uses Cerebras (Sprinter)
    REVIEWER = "reviewer"  # Uses Claude (Architect/Builder)
    SEARCHER = "searcher"  # Uses Gemini (Librarian)
    SUMMARIZER = "summarizer"  # Uses Gemini Flash (Librarian)


@dataclass
class AgentSlot:
    """Represents an active agent slot."""
    
    agent_id: str
    agent_name: str
    role: AgentRole
    model: str
    started_at: float
    estimated_tokens: int
    
    @property
    def runtime_seconds(self) -> float:
        return time.time() - self.started_at


@dataclass
class GovernorConfig:
    """Configuration for pack governor."""
    
    max_coding_agents: int = 2
    max_reviewer_agents: int = 1
    max_searcher_agents: int = 3
    force_summary_threshold_tokens: int = 50_000
    summary_model: str = "gemini-3-flash"
    cooldown_seconds: float = 1.0  # Min time between agent starts
    deadlock_timeout_seconds: float = 60.0  # Max wait before forcing release
    stale_slot_timeout_seconds: float = 300.0  # 5 min max runtime per slot


@dataclass
class AcquireResult:
    """Result of trying to acquire an agent slot."""
    
    granted: bool
    slot_id: Optional[str] = None
    assigned_model: Optional[str] = None
    wait_seconds: float = 0.0
    reason: str = ""
    forced_summary_mode: bool = False


class PackGovernor:
    """Governs concurrent Pack Agent execution.
    
    Ensures we don't exceed rate limits by:
    1. Limiting concurrent agents by role
    2. Tracking token usage across agents
    3. Forcing summary mode when approaching limits
    4. Providing cooldown between agent starts
    """
    
    _instance: Optional["PackGovernor"] = None
    
    # Agent name to role mapping
    AGENT_ROLES: Dict[str, AgentRole] = {
        # Pack agents
        "husky": AgentRole.CODER,
        "terrier": AgentRole.CODER,
        "bloodhound": AgentRole.SEARCHER,
        "retriever": AgentRole.CODER,
        "shepherd": AgentRole.REVIEWER,
        "watchdog": AgentRole.REVIEWER,
        # Main agents
        "code-puppy": AgentRole.CODER,
        "python-programmer": AgentRole.CODER,
        "qa-expert": AgentRole.REVIEWER,
        "security-auditor": AgentRole.REVIEWER,
    }
    
    # Role to default tier mapping
    ROLE_TIERS: Dict[AgentRole, ModelTier] = {
        AgentRole.CODER: ModelTier.SPRINTER,
        AgentRole.REVIEWER: ModelTier.ARCHITECT,
        AgentRole.SEARCHER: ModelTier.LIBRARIAN,
        AgentRole.SUMMARIZER: ModelTier.LIBRARIAN,
    }
    
    def __new__(cls) -> "PackGovernor":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[GovernorConfig] = None):
        if self._initialized:
            return
        
        self.config = config or GovernorConfig()
        self._active_slots: Dict[str, AgentSlot] = {}
        self._lock = asyncio.Lock()
        self._last_start_time: float = 0.0
        self._router = ModelRouter()
        self._budget_mgr = TokenBudgetManager()
        self._slot_counter = 0
        self._initialized = True
    
    def _get_role(self, agent_name: str) -> AgentRole:
        """Get role for an agent."""
        return self.AGENT_ROLES.get(agent_name, AgentRole.CODER)
    
    def _count_active_by_role(self, role: AgentRole) -> int:
        """Count active agents by role."""
        return sum(1 for s in self._active_slots.values() if s.role == role)
    
    def _get_max_for_role(self, role: AgentRole) -> int:
        """Get max concurrent agents for role."""
        limits = {
            AgentRole.CODER: self.config.max_coding_agents,
            AgentRole.REVIEWER: self.config.max_reviewer_agents,
            AgentRole.SEARCHER: self.config.max_searcher_agents,
            AgentRole.SUMMARIZER: 5,  # Summary agents are cheap
        }
        return limits.get(role, 2)
    
    async def acquire_slot(
        self,
        agent_name: str,
        estimated_tokens: int = 10_000,
        timeout: float = 30.0,
    ) -> AcquireResult:
        """Acquire a slot to run an agent.
        
        This is the main entry point for Pack Leader to get permission
        to run a sub-agent.
        
        DEADLOCK PREVENTION:
        - Stale slots (>5 min runtime) are auto-released
        - If waiting >60s for a role, force summary mode
        - release_slot() is always called in finally blocks
        
        Args:
            agent_name: Name of the agent to run
            estimated_tokens: Estimated tokens for the task
            timeout: Max seconds to wait for a slot
            
        Returns:
            AcquireResult with slot info or denial reason
        """
        start_time = time.time()
        role = self._get_role(agent_name)
        max_for_role = self._get_max_for_role(role)
        
        async with self._lock:
            # DEADLOCK PREVENTION: Clean up stale slots
            await self._cleanup_stale_slots()
            # Check if we need cooldown
            time_since_last = time.time() - self._last_start_time
            if time_since_last < self.config.cooldown_seconds:
                wait_time = self.config.cooldown_seconds - time_since_last
                await asyncio.sleep(wait_time)
            
            # Check role limits
            active_count = self._count_active_by_role(role)
            if active_count >= max_for_role:
                # Check if we should wait or force summary mode
                if role in (AgentRole.CODER, AgentRole.REVIEWER):
                    # Try forcing to summary mode
                    logger.info(
                        f"{agent_name} ({role.value}) at limit {active_count}/{max_for_role}, "
                        f"forcing summary mode"
                    )
                    return AcquireResult(
                        granted=True,
                        assigned_model=self.config.summary_model,
                        reason=f"Role limit reached, using summary mode",
                        forced_summary_mode=True,
                    )
                else:
                    return AcquireResult(
                        granted=False,
                        reason=f"Max {role.value} agents ({max_for_role}) already active",
                    )
            
            # Check budget
            tier = self.ROLE_TIERS.get(role, ModelTier.BUILDER_MID)
            model = self._router.get_model_for_tier(tier)
            if not model:
                model = self._router.get_model_for_tier(ModelTier.LIBRARIAN)
            
            if model:
                budget_check = self._budget_mgr.check_budget(
                    model.provider, estimated_tokens
                )
                
                if not budget_check.can_proceed:
                    if budget_check.failover_to:
                        # Use failover model
                        logger.info(
                            f"Budget exceeded for {model.name}, "
                            f"failing over to {budget_check.failover_to}"
                        )
                        return AcquireResult(
                            granted=True,
                            assigned_model=budget_check.failover_to,
                            reason=f"Budget failover: {budget_check.reason}",
                        )
                    elif budget_check.wait_seconds < timeout - (time.time() - start_time):
                        # Wait for budget reset
                        await asyncio.sleep(budget_check.wait_seconds)
                    else:
                        # Force summary mode
                        return AcquireResult(
                            granted=True,
                            assigned_model=self.config.summary_model,
                            reason="Budget exceeded, using summary mode",
                            forced_summary_mode=True,
                        )
            
            # Check if total active tokens approaching threshold
            total_active_tokens = sum(
                s.estimated_tokens for s in self._active_slots.values()
            )
            if total_active_tokens + estimated_tokens > self.config.force_summary_threshold_tokens:
                logger.info(
                    f"Total active tokens ({total_active_tokens}) approaching threshold, "
                    f"forcing {agent_name} to summary mode"
                )
                return AcquireResult(
                    granted=True,
                    assigned_model=self.config.summary_model,
                    reason="Token threshold reached, using summary mode",
                    forced_summary_mode=True,
                )
            
            # Grant the slot
            self._slot_counter += 1
            slot_id = f"slot_{self._slot_counter}"
            
            slot = AgentSlot(
                agent_id=slot_id,
                agent_name=agent_name,
                role=role,
                model=model.name if model else self.config.summary_model,
                started_at=time.time(),
                estimated_tokens=estimated_tokens,
            )
            
            self._active_slots[slot_id] = slot
            self._last_start_time = time.time()
            
            logger.debug(
                f"Granted slot {slot_id} for {agent_name} ({role.value}) "
                f"with model {slot.model}"
            )
            
            return AcquireResult(
                granted=True,
                slot_id=slot_id,
                assigned_model=slot.model,
                reason="Slot granted",
            )
    
    async def release_slot(self, slot_id: str, tokens_used: int = 0) -> None:
        """Release an agent slot after completion.
        
        Args:
            slot_id: The slot ID returned from acquire_slot
            tokens_used: Actual tokens used (for budget tracking)
        """
        async with self._lock:
            if slot_id in self._active_slots:
                slot = self._active_slots[slot_id]
                
                # Record usage
                if tokens_used > 0:
                    # Infer provider from model
                    model_config = self._router._models.get(slot.model)
                    if model_config:
                        self._budget_mgr.record_usage(model_config.provider, tokens_used)
                
                del self._active_slots[slot_id]
                logger.debug(
                    f"Released slot {slot_id} for {slot.agent_name}, "
                    f"runtime: {slot.runtime_seconds:.2f}s, tokens: {tokens_used}"
                )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current governor status.
        
        Returns:
            Dict with slot status by role
        """
        status = {
            "active_slots": len(self._active_slots),
            "by_role": {},
            "total_estimated_tokens": sum(
                s.estimated_tokens for s in self._active_slots.values()
            ),
            "budget_status": self._budget_mgr.get_status(),
        }
        
        for role in AgentRole:
            count = self._count_active_by_role(role)
            max_count = self._get_max_for_role(role)
            status["by_role"][role.value] = f"{count}/{max_count}"
        
        return status
    
    def clear(self) -> None:
        """Clear all active slots (for testing)."""
        self._active_slots.clear()
        self._slot_counter = 0

    async def _cleanup_stale_slots(self) -> int:
        """Clean up slots that have exceeded the stale timeout.
        
        DEADLOCK PREVENTION: This ensures that if an agent crashes
        without calling release_slot(), the slot is eventually freed.
        
        Returns:
            Number of stale slots cleaned up
        """
        now = time.time()
        stale_slots = []
        
        for slot_id, slot in self._active_slots.items():
            runtime = now - slot.started_at
            if runtime > self.config.stale_slot_timeout_seconds:
                stale_slots.append(slot_id)
                logger.warning(
                    f"Cleaning up stale slot {slot_id} for {slot.agent_name} "
                    f"(runtime: {runtime:.1f}s > {self.config.stale_slot_timeout_seconds}s)"
                )
        
        for slot_id in stale_slots:
            del self._active_slots[slot_id]
        
        return len(stale_slots)

    def get_deadlock_risk(self) -> Dict[str, Any]:
        """Assess current deadlock risk.
        
        A deadlock can occur if:
        - All coders are waiting on reviewers
        - The reviewer needs a coder to fix something
        
        Returns:
            Dict with deadlock risk assessment
        """
        coder_count = self._count_active_by_role(AgentRole.CODER)
        reviewer_count = self._count_active_by_role(AgentRole.REVIEWER)
        
        risk_level = "LOW"
        
        if (coder_count >= self.config.max_coding_agents and 
            reviewer_count >= self.config.max_reviewer_agents):
            risk_level = "HIGH"
        elif (coder_count >= self.config.max_coding_agents or
              reviewer_count >= self.config.max_reviewer_agents):
            risk_level = "MEDIUM"
        
        return {
            "risk_level": risk_level,
            "coders_active": f"{coder_count}/{self.config.max_coding_agents}",
            "reviewers_active": f"{reviewer_count}/{self.config.max_reviewer_agents}",
            "recommendation": (
                "Force summary mode for new agents" if risk_level == "HIGH"
                else "Normal operation" if risk_level == "LOW"
                else "Monitor closely"
            ),
        }


# Convenience functions for integration

async def acquire_agent_slot(
    agent_name: str,
    estimated_tokens: int = 10_000,
) -> AcquireResult:
    """Convenience function to acquire an agent slot."""
    governor = PackGovernor()
    return await governor.acquire_slot(agent_name, estimated_tokens)


async def release_agent_slot(slot_id: str, tokens_used: int = 0) -> None:
    """Convenience function to release an agent slot."""
    governor = PackGovernor()
    await governor.release_slot(slot_id, tokens_used)


def get_governor_status() -> Dict[str, Any]:
    """Get current governor status."""
    governor = PackGovernor()
    return governor.get_status()
