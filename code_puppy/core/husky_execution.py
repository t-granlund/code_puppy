"""🦮 Husky Execution Layer - Cerebras GLM 4.7 Integration.

The 'Hands' of the Traycer-style orchestrator - executes code generation
tasks using Cerebras GLM 4.7 with all optimizations from the migration guide.

Implements the 10 Rules from Cerebras GLM-4.7 Migration Guide:
1. Front-load instructions
2. Use MUST/STRICTLY language
3. Always respond in English
4. Leverage role-play personas
5. Break up complex tasks
6. Disable reasoning when not needed
7. Enable enhanced reasoning for complex tasks
8. Use critic agents for validation
9. Pair with frontier models (Opus plans, GLM executes)
10. Use clear_thinking for memory control

Architecture:
    ┌─────────────────────────────────────────────────┐
    │           HuskyExecutionLayer                    │
    │                                                 │
    │  ┌──────────────┐    ┌──────────────────────┐  │
    │  │ CerebrasGLM  │    │  GLMPromptOptimizer  │  │
    │  │   Settings   │    │  (Front-load + MUST) │  │
    │  └──────────────┘    └──────────────────────┘  │
    │           │                    │               │
    │           ▼                    ▼               │
    │  ┌─────────────────────────────────────────┐   │
    │  │         TokenBudgetManager              │   │
    │  │         (50K input limit)               │   │
    │  └─────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────┘
"""

from __future__ import annotations

import json
import logging
import re
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generator, List, Optional, Tuple

# Logfire instrumentation for observability
try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    logfire = None
    LOGFIRE_AVAILABLE = False

logger = logging.getLogger(__name__)


# =============================================================================
# 🔍 LOGFIRE INSTRUMENTATION HELPERS
# =============================================================================


@contextmanager
def span(name: str, **attributes: Any) -> Generator[None, None, None]:
    """Create a Logfire span if available, otherwise no-op."""
    if LOGFIRE_AVAILABLE and logfire:
        with logfire.span(name, **attributes):
            yield
    else:
        yield


def log_info(message: str, **kwargs: Any) -> None:
    """Log info via Logfire if available, otherwise standard logging."""
    if LOGFIRE_AVAILABLE and logfire:
        logfire.info(message, **kwargs)
    else:
        logger.info(f"{message} | {kwargs}" if kwargs else message)


def log_warning(message: str, **kwargs: Any) -> None:
    """Log warning via Logfire if available, otherwise standard logging."""
    if LOGFIRE_AVAILABLE and logfire:
        logfire.warn(message, **kwargs)
    else:
        logger.warning(f"{message} | {kwargs}" if kwargs else message)


# =============================================================================
# 🎛️ GLM 4.7 OPTIMIZED SETTINGS
# =============================================================================


class ReasoningMode(str, Enum):
    """GLM 4.7 reasoning modes based on task complexity."""
    
    DISABLED = "disabled"  # For simple tasks - Rule #6
    ENABLED = "enabled"  # For complex tasks - Rule #7
    MINIMAL = "minimal"  # Reason only when necessary


class ThinkingMemory(str, Enum):
    """How GLM handles thinking state between turns - Rule #10."""
    
    PRESERVE = "preserve"  # clear_thinking: false - for agentic loops
    CLEAR = "clear"  # clear_thinking: true - for one-off calls


@dataclass
class CerebrasGLMSettings:
    """Optimized settings for Cerebras GLM 4.7.
    
    Based on the official migration guide recommendations.
    """
    
    # Model identification
    model_id: str = "zai-glm-4.7"
    
    # Sampling parameters (from migration guide)
    temperature: float = 1.0  # Recommended default
    top_p: float = 0.95  # Recommended default
    
    # Context limits
    max_context_tokens: int = 131_072  # 131K context window
    max_output_tokens: int = 40_000  # Max output on Cerebras
    target_input_tokens: int = 50_000  # Conservative for rate limits
    
    # Reasoning control - Rule #6, #7
    reasoning_mode: ReasoningMode = ReasoningMode.ENABLED
    
    # Memory control - Rule #10
    thinking_memory: ThinkingMemory = ThinkingMemory.PRESERVE
    
    # Extra body parameters for Cerebras API
    def to_api_params(self) -> Dict[str, Any]:
        """Generate API parameters for Cerebras."""
        params = {
            "model": self.model_id,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_completion_tokens": self.max_output_tokens,
        }
        
        # GLM-specific extra_body parameters
        extra_body = {
            "disable_reasoning": self.reasoning_mode == ReasoningMode.DISABLED,
            "clear_thinking": self.thinking_memory == ThinkingMemory.CLEAR,
        }
        
        params["extra_body"] = extra_body
        
        return params
    
    @classmethod
    def for_simple_task(cls) -> "CerebrasGLMSettings":
        """Settings for simple tasks (tool calls, syntax fixes)."""
        return cls(
            reasoning_mode=ReasoningMode.DISABLED,
            thinking_memory=ThinkingMemory.CLEAR,
            max_output_tokens=1_000,
        )
    
    @classmethod
    def for_code_generation(cls) -> "CerebrasGLMSettings":
        """Settings for standard code generation."""
        return cls(
            reasoning_mode=ReasoningMode.MINIMAL,
            thinking_memory=ThinkingMemory.PRESERVE,
            max_output_tokens=4_000,
        )
    
    @classmethod
    def for_complex_task(cls) -> "CerebrasGLMSettings":
        """Settings for complex reasoning tasks."""
        return cls(
            reasoning_mode=ReasoningMode.ENABLED,
            thinking_memory=ThinkingMemory.PRESERVE,
            max_output_tokens=8_000,
        )
    
    @classmethod
    def for_agentic_loop(cls) -> "CerebrasGLMSettings":
        """Settings for multi-turn agentic sessions."""
        return cls(
            reasoning_mode=ReasoningMode.ENABLED,
            thinking_memory=ThinkingMemory.PRESERVE,  # Preserve state between turns
            max_output_tokens=4_000,
        )


# =============================================================================
# 📝 GLM PROMPT OPTIMIZER - Rules #1-4
# =============================================================================


class GLMPromptOptimizer:
    """Optimizes prompts for GLM 4.7's unique characteristics.
    
    Implements Rules #1-4 from the migration guide:
    - Rule #1: Front-load instructions (beginning bias)
    - Rule #2: Use MUST/STRICTLY language
    - Rule #3: Always respond in English
    - Rule #4: Leverage role-play personas
    """
    
    # Critical directives that must be at the START of every prompt
    FRONT_LOADED_DIRECTIVES = """<critical_rules>
You MUST:
1. Always respond in English only
2. NEVER skip reading files before editing them  
3. STRICTLY use absolute paths for all file operations
4. Follow the specifications EXACTLY as provided
5. Reason step-by-step for complex tasks
</critical_rules>

"""
    
    # Language enforcement (Rule #3)
    LANGUAGE_DIRECTIVE = "\n\n[IMPORTANT: All responses MUST be in English. Do not switch languages.]\n"
    
    def __init__(self, persona: Optional[str] = None):
        """Initialize with optional persona.
        
        Args:
            persona: Role-play persona for the model (Rule #4)
        """
        self.persona = persona or "expert Python developer"
    
    def optimize_system_prompt(
        self,
        original_prompt: str,
        task_context: Optional[str] = None,
    ) -> str:
        """Optimize a system prompt for GLM 4.7.
        
        Applies:
        - Front-loading critical directives (Rule #1)
        - MUST/STRICTLY language (Rule #2)
        - English language enforcement (Rule #3)
        - Role-play persona (Rule #4)
        """
        # Start with front-loaded directives
        optimized = self.FRONT_LOADED_DIRECTIVES
        
        # Add persona (Rule #4)
        optimized += f"""<persona>
You are acting as a {self.persona}. You MUST:
- Maintain this persona throughout the conversation
- Provide professional, structured responses
- Focus on code quality and correctness
</persona>

"""
        
        # Add task context if provided
        if task_context:
            optimized += f"""<task_context>
{task_context}
</task_context>

"""
        
        # Add original prompt with language directive
        optimized += original_prompt
        optimized += self.LANGUAGE_DIRECTIVE
        
        return optimized
    
    def optimize_user_message(
        self,
        message: str,
        enforce_structure: bool = True,
    ) -> str:
        """Optimize a user message for GLM 4.7.
        
        Args:
            message: The user message
            enforce_structure: Whether to add structural hints
        """
        # Strengthen language for better instruction following (Rule #2)
        optimized = message
        
        # Replace weak language with strong directives
        replacements = [
            ("please", "You MUST"),
            ("try to", "STRICTLY"),
            ("you should", "You MUST"),
            ("consider", "You MUST consider"),
            ("maybe", "STRICTLY"),
            ("if possible", "REQUIRED:"),
        ]
        
        for weak, strong in replacements:
            # Only replace at the start of sentences
            optimized = re.sub(
                rf'(?i)^{weak}\b',
                strong,
                optimized,
                flags=re.MULTILINE
            )
        
        return optimized
    
    def create_step_by_step_prompt(
        self,
        task_description: str,
        steps: List[str],
    ) -> str:
        """Create a step-by-step task prompt (Rule #5).
        
        GLM 4.7 doesn't have interleaved thinking, so we break
        tasks into explicit sub-steps.
        """
        prompt = f"""## Task: {task_description}

You MUST complete this task by following these steps IN ORDER:

"""
        for i, step in enumerate(steps, 1):
            prompt += f"{i}. {step}\n"
        
        prompt += """
IMPORTANT: Complete each step before moving to the next.
Show your work for each step clearly.
"""
        
        return prompt


# =============================================================================
# 🦮 HUSKY EXECUTION LAYER
# =============================================================================


@dataclass
class ExecutionRequest:
    """Request for code execution."""
    
    task_description: str
    file_paths: List[str]
    spec_requirements: List[str]
    constraints: List[str]
    context_content: Optional[Dict[str, str]] = None  # file_path -> content
    complexity: str = "medium"  # low, medium, high
    
    def estimate_tokens(self) -> int:
        """Estimate input token count."""
        total_chars = len(self.task_description)
        total_chars += sum(len(s) for s in self.spec_requirements)
        total_chars += sum(len(c) for c in self.constraints)
        
        if self.context_content:
            total_chars += sum(len(c) for c in self.context_content.values())
        
        return total_chars // 4  # Rough estimate


@dataclass
class ExecutionResult:
    """Result from code execution."""
    
    success: bool
    generated_code: str
    file_path: str
    
    # Token usage
    input_tokens: int = 0
    output_tokens: int = 0
    
    # Timing
    execution_time_ms: int = 0
    
    # Debugging
    raw_response: Optional[str] = None
    error_message: Optional[str] = None
    
    # GLM-specific
    reasoning_included: bool = False
    thinking_preserved: bool = False


class HuskyExecutionLayer:
    """The execution layer using Cerebras GLM 4.7.
    
    Named 'Husky' after the Code Puppy pack member that handles
    heavy lifting tasks at high speed.
    
    Responsibilities:
    - Optimize prompts for GLM 4.7
    - Manage token budgets
    - Execute code generation requests
    - Track usage and performance
    """
    
    def __init__(
        self,
        default_settings: Optional[CerebrasGLMSettings] = None,
        prompt_optimizer: Optional[GLMPromptOptimizer] = None,
    ):
        self.default_settings = default_settings or CerebrasGLMSettings()
        self.prompt_optimizer = prompt_optimizer or GLMPromptOptimizer(
            persona="expert Python developer specializing in clean, tested code"
        )
        
        # Usage tracking
        self._total_requests = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
    
    def get_settings_for_request(
        self,
        request: ExecutionRequest,
    ) -> CerebrasGLMSettings:
        """Get optimized settings based on request complexity."""
        
        if request.complexity == "low":
            return CerebrasGLMSettings.for_simple_task()
        elif request.complexity == "high":
            return CerebrasGLMSettings.for_complex_task()
        else:
            return CerebrasGLMSettings.for_code_generation()
    
    def build_prompt(
        self,
        request: ExecutionRequest,
        previous_feedback: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Build optimized system and user prompts.
        
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Build task context
        task_context = f"""
### Current Task
{request.task_description}

### Files to Modify
{', '.join(request.file_paths)}

### Specifications
{chr(10).join('- ' + s for s in request.spec_requirements)}

### Constraints
{chr(10).join('- ' + c for c in request.constraints)}
"""
        
        # Optimize system prompt
        system_prompt = self.prompt_optimizer.optimize_system_prompt(
            original_prompt="""You are a code generation agent. Your task is to implement
the specified functionality following all constraints and specifications.

Output ONLY the code - no explanations unless specifically requested.""",
            task_context=task_context,
        )
        
        # Build user message
        user_parts = [f"Implement the following:\n\n{request.task_description}"]
        
        # Add file context if provided
        if request.context_content:
            user_parts.append("\n\n### Current File Contents:")
            for path, content in request.context_content.items():
                # Truncate large files
                if len(content) > 5000:
                    content = content[:5000] + "\n... [truncated]"
                user_parts.append(f"\n**{path}:**\n```\n{content}\n```")
        
        # Add feedback from previous attempt if any
        if previous_feedback:
            user_parts.append(f"\n\n### Previous Attempt Feedback:\n{previous_feedback}")
            user_parts.append("\nPlease fix the issues and try again.")
        
        user_prompt = self.prompt_optimizer.optimize_user_message(
            "\n".join(user_parts)
        )
        
        return system_prompt, user_prompt
    
    async def execute(
        self,
        request: ExecutionRequest,
        previous_feedback: Optional[str] = None,
    ) -> ExecutionResult:
        """Execute a code generation request.
        
        This is where we call Cerebras GLM 4.7 through the ModelRouter.
        
        TODO: Wire to actual ModelRouter + Cerebras API
        """
        import time
        start_time = time.time()
        
        self._total_requests += 1
        
        with span(
            "Husky Execute",
            complexity=request.complexity.value,
            file_count=len(request.file_paths) if request.file_paths else 0,
        ):
            # Get optimized settings
            settings = self.get_settings_for_request(request)
            
            # Check token budget
            estimated_tokens = request.estimate_tokens()
            if estimated_tokens > settings.target_input_tokens:
                log_warning(
                    "Request may exceed token budget",
                    estimated_tokens=estimated_tokens,
                    budget=settings.target_input_tokens,
                )
            
            # Build prompts
            with span("Build Prompt"):
                system_prompt, user_prompt = self.build_prompt(request, previous_feedback)
            
            # Log the request
            log_info(
                "Executing request",
                complexity=request.complexity.value,
                reasoning_mode=settings.reasoning_mode.value,
                estimated_tokens=estimated_tokens,
            )
            
            # TODO: Actual API call via ModelRouter
            # For now, return placeholder
            
            result = ExecutionResult(
                success=True,
                generated_code=f"# Generated for: {request.task_description}\n# TODO: Implement via Cerebras",
                file_path=request.file_paths[0] if request.file_paths else "unknown.py",
                input_tokens=estimated_tokens,
                output_tokens=100,
                execution_time_ms=int((time.time() - start_time) * 1000),
                reasoning_included=settings.reasoning_mode != ReasoningMode.DISABLED,
                thinking_preserved=settings.thinking_memory == ThinkingMemory.PRESERVE,
            )
            
            # Track usage
            self._total_input_tokens += result.input_tokens
            self._total_output_tokens += result.output_tokens
            
            log_info(
                "Execution complete",
                success=result.success,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                execution_time_ms=result.execution_time_ms,
            )
            
            return result
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "total_requests": self._total_requests,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "average_input_per_request": (
                self._total_input_tokens / self._total_requests 
                if self._total_requests > 0 else 0
            ),
            "average_output_per_request": (
                self._total_output_tokens / self._total_requests
                if self._total_requests > 0 else 0
            ),
        }


# =============================================================================
# 🔀 TASK DECOMPOSER - Rule #5
# =============================================================================


class TaskDecomposer:
    """Decomposes complex tasks into sub-steps for GLM 4.7.
    
    Implements Rule #5: Break up the task.
    
    GLM 4.7 performs a single reasoning pass per prompt and doesn't
    continuously re-evaluate mid-task. By breaking tasks into explicit
    sub-steps, we get better results.
    """
    
    # Common task patterns and their decomposition templates
    DECOMPOSITION_TEMPLATES = {
        "refactor": [
            "List all files and functions that need refactoring",
            "Identify dependencies between the components",
            "Propose the new structure",
            "Implement changes one file at a time",
            "Verify all imports and references are updated",
        ],
        "implement_feature": [
            "Analyze existing code structure",
            "List required changes and new files",
            "Implement core functionality",
            "Add error handling",
            "Write unit tests",
        ],
        "fix_bug": [
            "Reproduce and understand the bug",
            "Identify root cause",
            "Propose the fix",
            "Implement the fix",
            "Verify the fix doesn't break existing functionality",
        ],
        "add_tests": [
            "Analyze the code to test",
            "Identify test cases (happy path, edge cases, error cases)",
            "Set up test fixtures",
            "Implement tests",
            "Verify coverage",
        ],
    }
    
    def decompose(
        self,
        task_description: str,
        task_type: Optional[str] = None,
    ) -> List[str]:
        """Decompose a task into sub-steps.
        
        Args:
            task_description: The task to decompose
            task_type: Optional hint about task type
            
        Returns:
            List of sub-steps to execute
        """
        # Try to detect task type from description
        if not task_type:
            task_type = self._detect_task_type(task_description)
        
        # Get template or generate generic steps
        if task_type in self.DECOMPOSITION_TEMPLATES:
            base_steps = self.DECOMPOSITION_TEMPLATES[task_type]
        else:
            base_steps = [
                "Understand the requirement",
                "Analyze affected code",
                "Plan the implementation",
                "Implement the changes",
                "Verify correctness",
            ]
        
        # Customize steps based on task description
        customized = []
        for step in base_steps:
            # Add context from task description
            customized.append(f"{step} for: {task_description[:50]}...")
        
        return customized
    
    def _detect_task_type(self, description: str) -> str:
        """Detect task type from description."""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ["refactor", "restructure", "reorganize"]):
            return "refactor"
        elif any(word in desc_lower for word in ["fix", "bug", "error", "issue"]):
            return "fix_bug"
        elif any(word in desc_lower for word in ["test", "coverage", "spec"]):
            return "add_tests"
        elif any(word in desc_lower for word in ["implement", "add", "create", "build"]):
            return "implement_feature"
        
        return "generic"


# =============================================================================
# 📤 EXPORTS
# =============================================================================

__all__ = [
    # Settings
    "CerebrasGLMSettings",
    "ReasoningMode",
    "ThinkingMemory",
    
    # Prompt Optimization
    "GLMPromptOptimizer",
    
    # Execution
    "ExecutionRequest",
    "ExecutionResult",
    "HuskyExecutionLayer",
    
    # Task Decomposition
    "TaskDecomposer",
]
