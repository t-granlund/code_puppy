"""Tests for core/pack_governor.py - Pack Governor."""

import asyncio

import pytest

from code_puppy.core.pack_governor import (
    AcquireResult,
    AgentRole,
    AgentSlot,
    GovernorConfig,
    PackGovernor,
    acquire_agent_slot,
    get_governor_status,
    release_agent_slot,
)
from code_puppy.core.token_budget import TokenBudgetManager


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset all singletons before and after each test."""
    # Reset before test
    PackGovernor._instance = None
    TokenBudgetManager._instance = None
    yield
    # Reset after test
    PackGovernor._instance = None
    TokenBudgetManager._instance = None


@pytest.fixture
def fresh_governor():
    """Create a fresh governor instance for each test."""
    governor = PackGovernor()
    governor.config = GovernorConfig(
        max_coding_agents=2,
        max_reviewer_agents=1,
        cooldown_seconds=0.01,  # Fast for tests
    )
    governor.clear()
    yield governor
    governor.clear()


class TestAgentRole:
    """Tests for agent role detection."""
    
    def test_husky_is_coder(self, fresh_governor):
        """Husky should be classified as coder."""
        role = fresh_governor._get_role("husky")
        assert role == AgentRole.CODER
    
    def test_shepherd_is_reviewer(self, fresh_governor):
        """Shepherd should be classified as reviewer."""
        role = fresh_governor._get_role("shepherd")
        assert role == AgentRole.REVIEWER
    
    def test_bloodhound_is_searcher(self, fresh_governor):
        """Bloodhound should be classified as searcher."""
        role = fresh_governor._get_role("bloodhound")
        assert role == AgentRole.SEARCHER
    
    def test_unknown_defaults_to_coder(self, fresh_governor):
        """Unknown agents should default to coder."""
        role = fresh_governor._get_role("unknown-agent")
        assert role == AgentRole.CODER


class TestSlotAcquisition:
    """Tests for slot acquisition."""
    
    @pytest.mark.asyncio
    async def test_acquire_slot_success(self, fresh_governor):
        """Should grant slot when under limits."""
        result = await fresh_governor.acquire_slot("husky", estimated_tokens=5000)
        
        assert result.granted
        assert result.slot_id is not None
        assert result.assigned_model is not None
    
    @pytest.mark.asyncio
    async def test_acquire_respects_coder_limit(self, fresh_governor):
        """Should enforce coder limit."""
        # Acquire 2 slots (max)
        r1 = await fresh_governor.acquire_slot("husky", 5000)
        r2 = await fresh_governor.acquire_slot("terrier", 5000)
        
        assert r1.granted
        assert r2.granted
        
        # Third should be forced to summary mode
        r3 = await fresh_governor.acquire_slot("retriever", 5000)
        
        assert r3.granted
        assert r3.forced_summary_mode or r3.assigned_model == "gemini-3-flash"
    
    @pytest.mark.asyncio
    async def test_acquire_respects_reviewer_limit(self, fresh_governor):
        """Should enforce reviewer limit."""
        # Acquire 1 reviewer slot (max)
        r1 = await fresh_governor.acquire_slot("shepherd", 5000)
        
        assert r1.granted
        
        # Second reviewer should be forced to summary mode
        r2 = await fresh_governor.acquire_slot("watchdog", 5000)
        
        assert r2.granted
        assert r2.forced_summary_mode


class TestSlotRelease:
    """Tests for slot release."""
    
    @pytest.mark.asyncio
    async def test_release_slot(self, fresh_governor):
        """Should release slot and free capacity."""
        result = await fresh_governor.acquire_slot("husky", 5000)
        assert result.slot_id is not None
        
        await fresh_governor.release_slot(result.slot_id, tokens_used=4000)
        
        # Slot should be freed
        assert result.slot_id not in fresh_governor._active_slots
    
    @pytest.mark.asyncio
    async def test_release_allows_new_acquisition(self, fresh_governor):
        """Releasing slot should allow new acquisitions."""
        # Fill up slots
        r1 = await fresh_governor.acquire_slot("husky", 5000)
        r2 = await fresh_governor.acquire_slot("terrier", 5000)
        
        # Release one
        await fresh_governor.release_slot(r1.slot_id, tokens_used=4000)
        
        # Should now be able to acquire without summary mode
        r3 = await fresh_governor.acquire_slot("retriever", 5000)
        assert r3.granted
        assert not r3.forced_summary_mode


class TestGovernorStatus:
    """Tests for governor status."""
    
    @pytest.mark.asyncio
    async def test_status_reflects_active_slots(self, fresh_governor):
        """Status should show active slots."""
        await fresh_governor.acquire_slot("husky", 5000)
        await fresh_governor.acquire_slot("shepherd", 3000)
        
        status = fresh_governor.get_status()
        
        assert status["active_slots"] == 2
        assert "coder" in status["by_role"]
        assert "reviewer" in status["by_role"]
    
    def test_status_shows_token_totals(self, fresh_governor):
        """Status should show total estimated tokens."""
        # Initially no tokens
        status = fresh_governor.get_status()
        assert status["total_estimated_tokens"] == 0


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    @pytest.mark.asyncio
    async def test_acquire_agent_slot_function(self, fresh_governor):
        """Convenience function should work."""
        result = await acquire_agent_slot("husky", 5000)
        assert result.granted
    
    @pytest.mark.asyncio
    async def test_release_agent_slot_function(self, fresh_governor):
        """Convenience function should work."""
        result = await acquire_agent_slot("husky", 5000)
        await release_agent_slot(result.slot_id, 4000)
        
        # Should be released
        assert result.slot_id not in fresh_governor._active_slots
    
    def test_get_governor_status_function(self, fresh_governor):
        """Convenience function should work."""
        status = get_governor_status()
        assert "active_slots" in status


class TestGovernorConfig:
    """Tests for governor configuration."""
    
    def test_custom_config(self):
        """Should use custom configuration."""
        PackGovernor._instance = None
        
        governor = PackGovernor()
        governor.config = GovernorConfig(
            max_coding_agents=5,
            max_reviewer_agents=3,
            force_summary_threshold_tokens=100_000,
        )
        
        assert governor.config.max_coding_agents == 5
        assert governor.config.max_reviewer_agents == 3
        
        governor.clear()
        PackGovernor._instance = None


class TestAgentSlot:
    """Tests for AgentSlot dataclass."""
    
    def test_runtime_calculation(self):
        """Should calculate runtime correctly."""
        import time
        
        slot = AgentSlot(
            agent_id="test",
            agent_name="husky",
            role=AgentRole.CODER,
            model="cerebras-glm-4.7",
            started_at=time.time() - 5,  # 5 seconds ago
            estimated_tokens=5000,
        )
        
        assert slot.runtime_seconds >= 5.0
        assert slot.runtime_seconds < 6.0
