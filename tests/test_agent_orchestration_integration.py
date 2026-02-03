"""Integration tests for agent orchestration - validates agent invocation chains.

Tests that:
1. Planning agent can invoke all agents in the orchestration hierarchy
2. Pack Leader can invoke all pack sub-agents
3. Helios (Universal Constructor) is accessible
4. All QA agents (qa-kitten, qa-expert) are invokable
5. Workload-aware model selection works for each agent
"""

import pytest

from code_puppy.agents.agent_manager import get_available_agents, load_agent
from code_puppy.agents.base_agent import BaseAgent
from code_puppy.core.agent_orchestration import (
    ORCHESTRATION_HIERARCHY,
    AgentOrchestrator,
)
from code_puppy.core.failover_config import (
    AGENT_WORKLOAD_REGISTRY,
    WORKLOAD_CHAINS,
    WorkloadType,
    get_chain_for_workload,
)


# =============================================================================
# Test Agent Discovery and Loading
# =============================================================================


class TestAgentDiscovery:
    """Test that all expected agents are discoverable."""

    def test_planning_agent_exists(self):
        """Test Planning Agent is registered."""
        agents = get_available_agents()
        assert "planning-agent" in agents

    def test_pack_leader_exists(self):
        """Test Pack Leader is registered."""
        agents = get_available_agents()
        assert "pack-leader" in agents

    def test_helios_exists(self):
        """Test Helios (Universal Constructor) is registered."""
        agents = get_available_agents()
        assert "helios" in agents

    def test_qa_agents_exist(self):
        """Test QA agents are registered."""
        agents = get_available_agents()
        assert "qa-kitten" in agents
        assert "qa-expert" in agents

    def test_pack_sub_agents_exist(self):
        """Test all pack sub-agents are registered."""
        agents = get_available_agents()
        assert "bloodhound" in agents
        assert "terrier" in agents
        assert "husky" in agents
        assert "shepherd" in agents
        assert "retriever" in agents
        assert "watchdog" in agents

    def test_reviewer_agents_exist(self):
        """Test code reviewer agents are registered."""
        agents = get_available_agents()
        assert "python-reviewer" in agents
        assert "code-reviewer" in agents
        assert "security-auditor" in agents


# =============================================================================
# Test Orchestration Hierarchy
# =============================================================================


class TestOrchestrationHierarchy:
    """Test the orchestration hierarchy defines correct relationships."""

    def test_planning_can_invoke_pack_leader(self):
        """Planning agent can invoke Pack Leader."""
        assert "pack-leader" in ORCHESTRATION_HIERARCHY.get("planning", [])

    def test_planning_can_invoke_helios(self):
        """Planning agent can invoke Helios."""
        assert "helios" in ORCHESTRATION_HIERARCHY.get("planning", [])

    def test_planning_can_invoke_code_puppy(self):
        """Planning agent can invoke Code Puppy."""
        assert "code-puppy" in ORCHESTRATION_HIERARCHY.get("planning", [])

    def test_epistemic_architect_can_invoke_planning(self):
        """Epistemic Architect can invoke Planning."""
        assert "planning" in ORCHESTRATION_HIERARCHY.get("epistemic-architect", [])

    def test_epistemic_architect_can_invoke_qa_expert(self):
        """Epistemic Architect can invoke QA Expert."""
        assert "qa-expert" in ORCHESTRATION_HIERARCHY.get("epistemic-architect", [])

    def test_pack_leader_can_invoke_all_pack_members(self):
        """Pack Leader can invoke all pack sub-agents."""
        pack_members = ORCHESTRATION_HIERARCHY.get("pack-leader", [])
        assert "bloodhound" in pack_members
        assert "terrier" in pack_members
        assert "husky" in pack_members
        assert "shepherd" in pack_members
        assert "retriever" in pack_members
        assert "watchdog" in pack_members

    def test_helios_can_invoke_pack_leader(self):
        """Helios can invoke Pack Leader for complex tasks."""
        assert "pack-leader" in ORCHESTRATION_HIERARCHY.get("helios", [])


# =============================================================================
# Test Agent Tools and Capabilities
# =============================================================================


class TestAgentToolsForOrchestration:
    """Test agents have the tools needed for orchestration."""

    @pytest.fixture
    def planning_agent(self):
        """Load Planning Agent."""
        return load_agent("planning-agent")

    @pytest.fixture
    def pack_leader(self):
        """Load Pack Leader."""
        return load_agent("pack-leader")

    @pytest.fixture
    def helios(self):
        """Load Helios agent."""
        return load_agent("helios")

    def test_planning_has_invoke_agent(self, planning_agent):
        """Planning Agent has invoke_agent tool."""
        tools = planning_agent.get_available_tools()
        assert "invoke_agent" in tools

    def test_planning_has_list_agents(self, planning_agent):
        """Planning Agent has list_agents tool."""
        tools = planning_agent.get_available_tools()
        assert "list_agents" in tools

    def test_pack_leader_has_invoke_agent(self, pack_leader):
        """Pack Leader has invoke_agent tool."""
        tools = pack_leader.get_available_tools()
        assert "invoke_agent" in tools

    def test_pack_leader_has_list_agents(self, pack_leader):
        """Pack Leader has list_agents tool."""
        tools = pack_leader.get_available_tools()
        assert "list_agents" in tools

    def test_helios_has_universal_constructor(self, helios):
        """Helios has universal_constructor tool."""
        tools = helios.get_available_tools()
        assert "universal_constructor" in tools


# =============================================================================
# Test Agent Workload Mapping
# =============================================================================


class TestAgentWorkloadMapping:
    """Test agents are mapped to correct workloads for model selection."""

    @pytest.fixture
    def orchestrator(self):
        """Get agent orchestrator instance."""
        return AgentOrchestrator()

    def test_pack_leader_is_orchestrator_workload(self, orchestrator):
        """Pack Leader uses ORCHESTRATOR workload for complex planning."""
        workload = orchestrator.get_workload_for_agent("pack-leader")
        assert workload == WorkloadType.ORCHESTRATOR

    def test_husky_is_coding_workload(self, orchestrator):
        """Husky (task executor) uses CODING workload."""
        workload = orchestrator.get_workload_for_agent("husky")
        assert workload == WorkloadType.CODING

    def test_shepherd_is_reasoning_workload(self, orchestrator):
        """Shepherd (code reviewer) uses REASONING workload."""
        workload = orchestrator.get_workload_for_agent("shepherd")
        assert workload == WorkloadType.REASONING

    def test_retriever_is_coding_workload(self, orchestrator):
        """Retriever (task execution) uses CODING workload per registry."""
        workload = orchestrator.get_workload_for_agent("retriever")
        assert workload == WorkloadType.CODING


# =============================================================================
# Test Workload Chains Have Valid Models
# =============================================================================


class TestWorkloadChainsForAgents:
    """Test workload chains have valid models for agent invocation."""

    def test_orchestrator_chain_not_empty(self):
        """ORCHESTRATOR chain has models for Pack Leader."""
        chain = get_chain_for_workload(WorkloadType.ORCHESTRATOR)
        assert len(chain) >= 5, "ORCHESTRATOR chain should have 5+ models"

    def test_reasoning_chain_not_empty(self):
        """REASONING chain has models for Shepherd, critics."""
        chain = get_chain_for_workload(WorkloadType.REASONING)
        assert len(chain) >= 5, "REASONING chain should have 5+ models"

    def test_coding_chain_not_empty(self):
        """CODING chain has models for Husky task execution."""
        chain = get_chain_for_workload(WorkloadType.CODING)
        assert len(chain) >= 5, "CODING chain should have 5+ models"

    def test_librarian_chain_not_empty(self):
        """LIBRARIAN chain has models for Retriever, search agents."""
        chain = get_chain_for_workload(WorkloadType.LIBRARIAN)
        assert len(chain) >= 5, "LIBRARIAN chain should have 5+ models"


# =============================================================================
# Test Full Agent Invocation Path
# =============================================================================


class TestAgentInvocationPath:
    """Test full agent invocation path from Planning to sub-agents."""

    def test_planning_system_prompt_mentions_agents(self):
        """Planning Agent system prompt mentions available agents."""
        agent = load_agent("planning-agent")
        prompt = agent.get_system_prompt()
        # Should mention agent coordination
        assert "agent" in prompt.lower()
        assert "invoke" in prompt.lower() or "coordinate" in prompt.lower()

    def test_pack_leader_system_prompt_mentions_pack(self):
        """Pack Leader system prompt mentions the pack sub-agents."""
        agent = load_agent("pack-leader")
        prompt = agent.get_system_prompt()
        # Should mention all pack members
        assert "bloodhound" in prompt.lower()
        assert "terrier" in prompt.lower()
        assert "husky" in prompt.lower()
        assert "shepherd" in prompt.lower()
        assert "retriever" in prompt.lower()
        assert "watchdog" in prompt.lower()

    def test_all_pack_agents_inherit_base_agent(self):
        """All pack agents inherit from BaseAgent."""
        pack_agents = [
            "pack-leader",
            "bloodhound",
            "terrier",
            "husky",
            "shepherd",
            "retriever",
            "watchdog",
        ]
        for agent_name in pack_agents:
            agent = load_agent(agent_name)
            assert isinstance(agent, BaseAgent), f"{agent_name} should inherit BaseAgent"

    def test_qa_agents_have_different_specialties(self):
        """QA agents have different specialties (kitten=web, expert=risk-based)."""
        qa_kitten = load_agent("qa-kitten")
        qa_expert = load_agent("qa-expert")

        kitten_desc = qa_kitten.description.lower()
        expert_desc = qa_expert.description.lower()

        # QA Kitten is for web browser automation
        assert "web" in kitten_desc or "browser" in kitten_desc or "playwright" in kitten_desc

        # QA Expert is for broader risk-based QA
        assert "qa" in expert_desc or "risk" in expert_desc or "coverage" in expert_desc


# =============================================================================
# Test Agent Model Selection Integration
# =============================================================================


class TestAgentModelSelection:
    """Test that agents get appropriate models for their workload."""

    @pytest.fixture
    def orchestrator(self):
        """Get fresh orchestrator."""
        orch = AgentOrchestrator()
        orch._instance = None  # Reset singleton
        return AgentOrchestrator()

    def test_all_registered_agents_have_workload(self, orchestrator):
        """All agents in AGENT_WORKLOAD_REGISTRY get valid workloads."""
        for agent_name in AGENT_WORKLOAD_REGISTRY.keys():
            workload = orchestrator.get_workload_for_agent(agent_name)
            assert workload is not None, f"{agent_name} should have a workload"
            assert isinstance(workload, WorkloadType)

    def test_workload_chains_all_have_models(self):
        """All workload types have model chains defined."""
        for workload_type in WorkloadType:
            assert workload_type in WORKLOAD_CHAINS, f"{workload_type} should have chain"
            chain = WORKLOAD_CHAINS[workload_type]
            assert len(chain) > 0, f"{workload_type} chain should not be empty"


# =============================================================================
# Test End-to-End Orchestration Scenario
# =============================================================================


class TestEndToEndOrchestration:
    """Test complete orchestration flow from planning to execution."""

    def test_planning_to_pack_leader_path(self):
        """Verify path from Planning Agent to Pack Leader."""
        # 1. Planning Agent exists and has invoke_agent
        planning = load_agent("planning-agent")
        assert "invoke_agent" in planning.get_available_tools()

        # 2. Pack Leader is in orchestration hierarchy
        assert "pack-leader" in ORCHESTRATION_HIERARCHY.get("planning", [])

        # 3. Pack Leader exists and can be loaded
        pack_leader = load_agent("pack-leader")
        assert pack_leader is not None

        # 4. Pack Leader has correct workload
        orchestrator = AgentOrchestrator()
        workload = orchestrator.get_workload_for_agent("pack-leader")
        assert workload == WorkloadType.ORCHESTRATOR

    def test_pack_leader_to_husky_path(self):
        """Verify path from Pack Leader to Husky (task execution)."""
        # 1. Pack Leader has invoke_agent
        pack_leader = load_agent("pack-leader")
        assert "invoke_agent" in pack_leader.get_available_tools()

        # 2. Husky is in pack hierarchy
        assert "husky" in ORCHESTRATION_HIERARCHY.get("pack-leader", [])

        # 3. Husky exists and uses CODING workload
        husky = load_agent("husky")
        assert husky is not None

        orchestrator = AgentOrchestrator()
        workload = orchestrator.get_workload_for_agent("husky")
        assert workload == WorkloadType.CODING

    def test_helios_can_create_tools(self):
        """Verify Helios has universal constructor capability."""
        helios = load_agent("helios")
        tools = helios.get_available_tools()
        assert "universal_constructor" in tools

        # Helios can also invoke other agents
        assert "helios" in ORCHESTRATION_HIERARCHY  # Helios is in hierarchy

    def test_qa_expert_for_quality_assurance(self):
        """Verify QA Expert path for quality assurance tasks."""
        # QA Expert is accessible from Epistemic Architect
        assert "qa-expert" in ORCHESTRATION_HIERARCHY.get("epistemic-architect", [])

        # QA Expert exists and has testing tools
        qa_expert = load_agent("qa-expert")
        assert qa_expert is not None

        # Has reasoning workload for analysis
        orchestrator = AgentOrchestrator()
        workload = orchestrator.get_workload_for_agent("qa-expert")
        assert workload in [WorkloadType.REASONING, WorkloadType.CODING]
