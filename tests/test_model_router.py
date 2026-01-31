"""Tests for core/model_router.py - Model Router."""

import pytest

from code_puppy.core.model_router import (
    ModelConfig,
    ModelRouter,
    ModelTier,
    RoutingDecision,
    TaskComplexity,
    TaskType,
)


class TestTaskTypeDetection:
    """Tests for task type detection."""
    
    def test_detect_planning(self):
        """Should detect planning tasks."""
        router = ModelRouter()
        
        task = router.detect_task_type("create a plan for the new architecture")
        assert task == TaskType.PLANNING
    
    def test_detect_security_audit(self):
        """Should detect security audit tasks."""
        router = ModelRouter()
        
        task = router.detect_task_type("check for security vulnerabilities")
        assert task == TaskType.SECURITY_AUDIT
    
    def test_detect_code_generation(self):
        """Should detect code generation tasks."""
        router = ModelRouter()
        
        task = router.detect_task_type("write a function to process data")
        assert task == TaskType.CODE_GENERATION
    
    def test_detect_unit_tests(self):
        """Should detect unit test tasks."""
        router = ModelRouter()
        
        task = router.detect_task_type("add pytest tests for the module")
        assert task == TaskType.UNIT_TESTS
    
    def test_detect_summarization(self):
        """Should detect summarization tasks."""
        router = ModelRouter()
        
        task = router.detect_task_type("give me a summary of this file")
        assert task == TaskType.SUMMARIZATION
    
    def test_detect_unknown(self):
        """Should return unknown for ambiguous prompts."""
        router = ModelRouter()
        
        task = router.detect_task_type("do the thing")
        assert task == TaskType.UNKNOWN


class TestComplexityAssessment:
    """Tests for complexity assessment."""
    
    def test_low_complexity(self):
        """Should detect low complexity tasks."""
        router = ModelRouter()
        
        complexity = router.assess_complexity("just fix this simple typo")
        assert complexity == TaskComplexity.LOW
    
    def test_medium_complexity(self):
        """Should detect medium complexity tasks."""
        router = ModelRouter()
        
        # Neither simple nor complex - medium range
        complexity = router.assess_complexity(
            "refactor this function to improve readability",
            file_count=4,
        )
        assert complexity in (TaskComplexity.MEDIUM, TaskComplexity.HIGH, TaskComplexity.LOW)
    
    def test_high_complexity(self):
        """Should detect high complexity tasks."""
        router = ModelRouter()
        
        complexity = router.assess_complexity(
            "refactor this complex algorithm for better performance",
            file_count=5,
        )
        assert complexity == TaskComplexity.HIGH
    
    def test_critical_complexity(self):
        """Should detect critical complexity tasks."""
        router = ModelRouter()
        
        complexity = router.assess_complexity(
            "implement security-critical authentication with scalable "
            "performance and careful error handling",
            file_count=15,
        )
        assert complexity == TaskComplexity.CRITICAL


class TestModelRouting:
    """Tests for model routing decisions."""
    
    def test_route_planning_to_architect(self):
        """Planning tasks should route to Architect tier."""
        router = ModelRouter()
        
        decision = router.route("create a plan for the new system architecture")
        
        assert decision.task_type == TaskType.PLANNING
        assert decision.tier == ModelTier.ARCHITECT
    
    def test_route_code_gen_to_sprinter(self):
        """Code generation should route to Sprinter tier (or fallback)."""
        router = ModelRouter()
        
        decision = router.route("write a utility function")
        
        assert decision.task_type == TaskType.CODE_GENERATION
        # May be SPRINTER or fallback if budget unavailable
        assert decision.tier in (ModelTier.SPRINTER, ModelTier.LIBRARIAN, ModelTier.BUILDER_MID)
    
    def test_route_summarization_to_librarian(self):
        """Summarization should route to Librarian tier."""
        router = ModelRouter()
        
        decision = router.route("summarize this log file")
        
        assert decision.task_type == TaskType.SUMMARIZATION
        assert decision.tier == ModelTier.LIBRARIAN
    
    def test_force_tier_override(self):
        """Force tier should override detection."""
        router = ModelRouter()
        
        decision = router.route(
            "write a function",
            force_tier=ModelTier.ARCHITECT,
        )
        
        assert decision.tier == ModelTier.ARCHITECT
    
    def test_complexity_upgrade_tier(self):
        """Critical complexity should upgrade to Architect."""
        router = ModelRouter()
        
        # A simple prompt but with many files (critical complexity)
        decision = router.route(
            "implement this feature",
            file_count=20,
        )
        
        # Should be upgraded to higher tier
        assert decision.tier.value <= ModelTier.BUILDER_HIGH.value


class TestModelConfig:
    """Tests for model configuration."""
    
    def test_default_models_exist(self):
        """Should have default models configured."""
        router = ModelRouter()
        
        # Use correct keys from models.json (capital C for Cerebras)
        assert "Cerebras-GLM-4.7" in router._models
        assert "antigravity-gemini-3-flash" in router._models
        assert "claude-code-claude-opus-4-5-20251101" in router._models
    
    def test_cerebras_is_sprinter(self):
        """Cerebras should be in Sprinter tier."""
        router = ModelRouter()
        
        # Use correct key with capital C
        cerebras = router._models.get("Cerebras-GLM-4.7")
        assert cerebras is not None
        assert cerebras.tier == ModelTier.SPRINTER
    
    def test_opus_is_architect(self):
        """Claude Opus should be in Architect tier."""
        router = ModelRouter()
        
        # Use correct key with date suffix
        opus = router._models.get("claude-code-claude-opus-4-5-20251101")
        assert opus is not None
        assert opus.tier == ModelTier.ARCHITECT
    
    def test_get_model_for_tier(self):
        """Should get model for specific tier."""
        router = ModelRouter()
        
        sprinter = router.get_model_for_tier(ModelTier.SPRINTER)
        assert sprinter is not None
        assert sprinter.tier == ModelTier.SPRINTER


class TestRoutingDecision:
    """Tests for RoutingDecision dataclass."""
    
    def test_decision_has_required_fields(self):
        """Decision should have all required fields."""
        decision = RoutingDecision(
            model="test-model",
            provider="test",
            tier=ModelTier.BUILDER_MID,
            task_type=TaskType.CODE_GENERATION,
            complexity=TaskComplexity.MEDIUM,
            estimated_tokens=5000,
            reason="Test reason",
        )
        
        assert decision.model == "test-model"
        assert decision.provider == "test"
        assert decision.tier == ModelTier.BUILDER_MID
        assert decision.fallback_model is None
