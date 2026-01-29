"""Tests for Router Hooks module.

AUDIT-1.1 Part I test coverage.
"""

import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from code_puppy.tools.router_hooks import (
    # Enums
    TaskClass,
    ModelCapability,
    # Data classes
    ModelConfig,
    ModelPool,
    RoutingHint,
    # Constants
    DEFAULT_MODEL_POOL,
    # Functions
    load_model_pool,
    save_model_pool,
    get_model_pool,
    create_routing_hint,
    get_model_for_task,
    get_fast_model,
    get_long_context_model,
    format_pool_summary,
)


class TestTaskClass:
    """Test TaskClass enum."""
    
    def test_code_tasks(self):
        """Code-related task classes exist."""
        assert TaskClass.CODE_GENERATION.value == "code_generation"
        assert TaskClass.CODE_REFACTOR.value == "code_refactor"
        assert TaskClass.BUG_FIX.value == "bug_fix"
    
    def test_analysis_tasks(self):
        """Analysis task classes exist."""
        assert TaskClass.CODE_ANALYSIS.value == "code_analysis"
        assert TaskClass.ARCHITECTURE_REVIEW.value == "architecture_review"
        assert TaskClass.SECURITY_AUDIT.value == "security_audit"
    
    def test_quick_tasks(self):
        """Quick task classes exist."""
        assert TaskClass.SIMPLE_QUERY.value == "simple_query"
        assert TaskClass.FORMAT_FIX.value == "format_fix"
    
    def test_complex_tasks(self):
        """Complex task classes exist."""
        assert TaskClass.COMPLEX_REASONING.value == "complex_reasoning"
        assert TaskClass.LARGE_REFACTOR.value == "large_refactor"


class TestModelCapability:
    """Test ModelCapability enum."""
    
    def test_capabilities(self):
        """All capabilities are defined."""
        assert ModelCapability.CODE_COMPLETION.value == "code_completion"
        assert ModelCapability.CHAT.value == "chat"
        assert ModelCapability.FUNCTION_CALLING.value == "function_calling"
        assert ModelCapability.VISION.value == "vision"
        assert ModelCapability.LONG_CONTEXT.value == "long_context"
        assert ModelCapability.FAST_INFERENCE.value == "fast_inference"
        assert ModelCapability.STREAMING.value == "streaming"


class TestModelConfig:
    """Test ModelConfig data class."""
    
    def test_create_config(self):
        """Create model config."""
        config = ModelConfig(
            name="test-model",
            provider="test-provider",
            model_id="test-id",
            max_input_tokens=50000,
            max_output_tokens=8192,
        )
        
        assert config.name == "test-model"
        assert config.max_input_tokens == 50000
    
    def test_config_with_capabilities(self):
        """Config with capabilities."""
        config = ModelConfig(
            name="test-model",
            provider="test",
            model_id="test",
            capabilities={
                ModelCapability.CODE_COMPLETION,
                ModelCapability.FAST_INFERENCE,
            },
        )
        
        assert ModelCapability.CODE_COMPLETION in config.capabilities
        assert ModelCapability.VISION not in config.capabilities
    
    def test_config_with_task_scores(self):
        """Config with task scores."""
        config = ModelConfig(
            name="test-model",
            provider="test",
            model_id="test",
            task_scores={
                TaskClass.CODE_GENERATION: 0.9,
                TaskClass.BUG_FIX: 0.85,
            },
        )
        
        assert config.task_scores[TaskClass.CODE_GENERATION] == 0.9
    
    def test_config_to_dict(self):
        """Config serializes to dict."""
        config = ModelConfig(
            name="test-model",
            provider="test-provider",
            model_id="test-id",
            max_input_tokens=50000,
            capabilities={ModelCapability.CHAT},
            task_scores={TaskClass.CODE_GENERATION: 0.9},
        )
        data = config.to_dict()
        
        assert data["name"] == "test-model"
        assert "chat" in data["capabilities"]
        assert data["task_scores"]["code_generation"] == 0.9
    
    def test_config_from_dict(self):
        """Config deserializes from dict."""
        data = {
            "name": "test-model",
            "provider": "test",
            "model_id": "test-id",
            "max_input_tokens": 100000,
            "capabilities": ["chat", "streaming"],
            "task_scores": {"bug_fix": 0.8},
        }
        config = ModelConfig.from_dict(data)
        
        assert config.name == "test-model"
        assert config.max_input_tokens == 100000
        assert ModelCapability.CHAT in config.capabilities
        assert TaskClass.BUG_FIX in config.task_scores


class TestModelPool:
    """Test ModelPool data class."""
    
    def test_create_pool(self):
        """Create model pool."""
        pool = ModelPool(
            models=[
                ModelConfig(name="m1", provider="p1", model_id="id1"),
                ModelConfig(name="m2", provider="p2", model_id="id2"),
            ],
            default_model="m1",
            fallback_model="m2",
        )
        
        assert len(pool.models) == 2
        assert pool.default_model == "m1"
    
    def test_get_model(self):
        """Get model by name."""
        pool = ModelPool(
            models=[
                ModelConfig(name="m1", provider="p1", model_id="id1"),
            ],
        )
        
        model = pool.get_model("m1")
        assert model is not None
        assert model.name == "m1"
        
        assert pool.get_model("nonexistent") is None
    
    def test_get_enabled_models(self):
        """Get only enabled models."""
        pool = ModelPool(
            models=[
                ModelConfig(name="m1", provider="p1", model_id="id1", enabled=True),
                ModelConfig(name="m2", provider="p2", model_id="id2", enabled=False),
                ModelConfig(name="m3", provider="p3", model_id="id3", enabled=True),
            ],
        )
        
        enabled = pool.get_enabled_models()
        assert len(enabled) == 2
        assert all(m.enabled for m in enabled)
    
    def test_get_models_for_capability(self):
        """Get models with specific capability."""
        pool = ModelPool(
            models=[
                ModelConfig(
                    name="m1", provider="p1", model_id="id1",
                    capabilities={ModelCapability.FAST_INFERENCE},
                ),
                ModelConfig(
                    name="m2", provider="p2", model_id="id2",
                    capabilities={ModelCapability.LONG_CONTEXT},
                ),
            ],
        )
        
        fast_models = pool.get_models_for_capability(ModelCapability.FAST_INFERENCE)
        assert len(fast_models) == 1
        assert fast_models[0].name == "m1"
    
    def test_pool_to_dict(self):
        """Pool serializes to dict."""
        pool = ModelPool(
            models=[ModelConfig(name="m1", provider="p1", model_id="id1")],
            default_model="m1",
        )
        data = pool.to_dict()
        
        assert len(data["models"]) == 1
        assert data["default_model"] == "m1"
    
    def test_pool_from_dict(self):
        """Pool deserializes from dict."""
        data = {
            "models": [
                {"name": "m1", "provider": "p1", "model_id": "id1"},
            ],
            "default_model": "m1",
            "fallback_model": "m2",
            "enable_auto_routing": False,
        }
        pool = ModelPool.from_dict(data)
        
        assert len(pool.models) == 1
        assert pool.default_model == "m1"


class TestDefaultModelPool:
    """Test default model pool configuration."""
    
    def test_cerebras_in_pool(self):
        """Cerebras is in default pool."""
        model = DEFAULT_MODEL_POOL.get_model("cerebras-code-pro")
        assert model is not None
        assert model.provider == "cerebras"
    
    def test_default_model_set(self):
        """Default model is set."""
        assert DEFAULT_MODEL_POOL.default_model == "cerebras-code-pro"
    
    def test_fallback_model_set(self):
        """Fallback model is set."""
        assert DEFAULT_MODEL_POOL.fallback_model == "gpt-4o"
    
    def test_auto_routing_disabled(self):
        """Auto-routing is disabled by default."""
        assert not DEFAULT_MODEL_POOL.enable_auto_routing


class TestPoolPersistence:
    """Test model pool persistence."""
    
    def test_save_and_load_pool(self):
        """Save and load pool from disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, ".codepuppy", "model_pool.json")
            
            pool = ModelPool(
                models=[
                    ModelConfig(name="test", provider="test", model_id="test-id"),
                ],
                default_model="test",
            )
            
            save_model_pool(pool, config_path)
            assert os.path.exists(config_path)
            
            loaded = load_model_pool(config_path)
            assert loaded.default_model == "test"
            assert len(loaded.models) == 1
    
    def test_load_missing_pool(self):
        """Loading missing pool returns default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "nonexistent.json")
            
            pool = load_model_pool(config_path)
            assert pool == DEFAULT_MODEL_POOL


class TestRoutingHint:
    """Test RoutingHint class."""
    
    def test_create_hint(self):
        """Create routing hint."""
        hint = RoutingHint(
            task_class=TaskClass.CODE_GENERATION,
            estimated_input_tokens=5000,
            estimated_output_tokens=2000,
        )
        
        assert hint.task_class == TaskClass.CODE_GENERATION
        assert hint.estimated_input_tokens == 5000
    
    def test_hint_with_requirements(self):
        """Hint with capability requirements."""
        hint = RoutingHint(
            task_class=TaskClass.COMPLEX_REASONING,
            requires_capabilities={ModelCapability.LONG_CONTEXT},
        )
        
        assert ModelCapability.LONG_CONTEXT in hint.requires_capabilities
    
    def test_hint_preferences(self):
        """Hint with preferences."""
        hint = RoutingHint(
            task_class=TaskClass.SIMPLE_QUERY,
            prefer_fast=True,
            prefer_cheap=True,
        )
        
        assert hint.prefer_fast
        assert hint.prefer_cheap
    
    def test_get_recommended_models(self):
        """Get model recommendations from hint."""
        hint = RoutingHint(
            task_class=TaskClass.CODE_GENERATION,
            prefer_fast=True,
        )
        
        recommendations = hint.get_recommended_models()
        assert len(recommendations) > 0
        # Cerebras should be recommended for fast code gen
        assert "cerebras-code-pro" in recommendations
    
    def test_recommendations_filter_by_tokens(self):
        """Recommendations filter by token requirements."""
        hint = RoutingHint(
            task_class=TaskClass.LARGE_REFACTOR,
            estimated_input_tokens=100000,  # Needs large context
        )
        
        recommendations = hint.get_recommended_models()
        # Only models with >= 100k context should be included
        # Cerebras has 50k so shouldn't be first
        if recommendations:
            pool = get_model_pool()
            first_model = pool.get_model(recommendations[0])
            if first_model:
                assert first_model.max_input_tokens >= 100000


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_create_routing_hint(self):
        """Create hint with helper function."""
        hint = create_routing_hint(
            TaskClass.BUG_FIX,
            input_tokens=3000,
            prefer_fast=True,
        )
        
        assert hint.task_class == TaskClass.BUG_FIX
        assert hint.estimated_input_tokens == 3000
        assert hint.prefer_fast
    
    def test_get_model_for_task(self):
        """Get best model for task class."""
        model = get_model_for_task(TaskClass.CODE_GENERATION)
        assert model is not None
        assert isinstance(model, str)
    
    def test_get_fast_model(self):
        """Get fastest model."""
        model = get_fast_model()
        assert model is not None
        # Should be Cerebras (has FAST_INFERENCE)
        assert "cerebras" in model.lower()
    
    def test_get_long_context_model(self):
        """Get long context model."""
        model = get_long_context_model()
        assert model is not None
        # Should have long context capability
        pool = get_model_pool()
        config = pool.get_model(model)
        if config:
            assert ModelCapability.LONG_CONTEXT in config.capabilities


class TestFormatPoolSummary:
    """Test pool summary formatting."""
    
    def test_format_default_pool(self):
        """Format default pool summary."""
        summary = format_pool_summary()
        
        assert "Model Pool Summary" in summary
        assert "cerebras-code-pro" in summary
        assert "Default:" in summary
        assert "Fallback:" in summary
    
    def test_format_custom_pool(self):
        """Format custom pool summary."""
        pool = ModelPool(
            models=[
                ModelConfig(
                    name="custom-model",
                    provider="custom",
                    model_id="custom-id",
                    max_input_tokens=10000,
                    capabilities={ModelCapability.CHAT},
                ),
            ],
            default_model="custom-model",
        )
        
        summary = format_pool_summary(pool)
        
        assert "custom-model" in summary
        assert "custom" in summary
        assert "10,000" in summary
