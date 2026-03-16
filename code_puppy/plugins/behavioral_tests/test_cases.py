"""Built-in behavioral test cases (OPT-008-B).

Phase 1: 5 test cases covering tool calling and instruction adherence.
These are descriptive — they collect metrics, not pass/fail verdicts.
"""

from .framework import BehavioralTest, TestMetric


def _extract_code_block_count(response: str) -> TestMetric:
    """Count code blocks in response."""
    count = response.count("```") // 2 if response else 0
    return TestMetric(
        name="code_block_count",
        value=count,
        unit="blocks",
        description="Number of fenced code blocks in response",
    )


def _extract_list_item_count(response: str) -> TestMetric:
    """Count markdown list items in response."""
    import re

    count = len(re.findall(r"^\s*[-*]\s", response, re.MULTILINE)) if response else 0
    return TestMetric(
        name="list_item_count",
        value=count,
        unit="items",
        description="Number of markdown list items in response",
    )


def _extract_has_required_sections(response: str) -> TestMetric:
    """Check if response has markdown headers (structured output)."""
    import re

    headers = re.findall(r"^#{1,4}\s", response, re.MULTILINE) if response else []
    return TestMetric(
        name="section_header_count",
        value=len(headers),
        unit="headers",
        description="Number of markdown section headers",
    )


def _extract_word_count(response: str) -> TestMetric:
    """Count words in response."""
    count = len(response.split()) if response else 0
    return TestMetric(
        name="word_count",
        value=count,
        unit="words",
        description="Total word count of response",
    )


# ---------------------------------------------------------------------------
# Test Case 1: Tool calling frequency
# ---------------------------------------------------------------------------
TEST_TOOL_CALLING_BASIC = BehavioralTest(
    name="tool_calling_basic",
    category="tool_calling",
    description="Tests whether the model calls tools proactively when given a file-related task",
    prompt="List all Python files in the current directory and tell me how many there are.",
    system_prompt="You are a coding assistant with access to file tools. Always use tools to answer questions about files.",
    tools=["list_files"],
    metric_extractors=[_extract_word_count],
)

# ---------------------------------------------------------------------------
# Test Case 2: Instruction following — output format
# ---------------------------------------------------------------------------
TEST_OUTPUT_FORMAT = BehavioralTest(
    name="output_format_compliance",
    category="instruction_following",
    description="Tests whether the model follows specific output format instructions",
    prompt="Explain the difference between a list and a tuple in Python. Format your response with exactly 3 sections: Definition, Key Differences, When to Use Each.",
    system_prompt="You are a Python tutor. Always structure your responses with clear markdown headers as requested.",
    metric_extractors=[_extract_has_required_sections, _extract_code_block_count],
)

# ---------------------------------------------------------------------------
# Test Case 3: Instruction following — constraint adherence
# ---------------------------------------------------------------------------
TEST_CONSTRAINT_ADHERENCE = BehavioralTest(
    name="constraint_adherence",
    category="instruction_following",
    description="Tests whether the model respects explicit constraints (e.g., word limits)",
    prompt="Explain what a Python decorator is in exactly 3 bullet points. No more, no less.",
    system_prompt="You are a concise coding assistant. Always follow formatting constraints exactly.",
    metric_extractors=[_extract_list_item_count, _extract_word_count],
)

# ---------------------------------------------------------------------------
# Test Case 4: Multi-turn consistency
# ---------------------------------------------------------------------------
TEST_MULTI_TURN = BehavioralTest(
    name="multi_turn_consistency",
    category="multi_turn",
    description="Tests consistency in a multi-turn context (single prompt simulating context)",
    prompt=(
        "In a previous message, I told you my project uses FastAPI and SQLAlchemy. "
        "Based on that context, suggest 3 testing strategies. "
        "Make sure your suggestions are specific to FastAPI and SQLAlchemy, not generic."
    ),
    system_prompt="You are a senior backend developer. The user's project uses FastAPI and SQLAlchemy. Reference these technologies specifically in your responses.",
    metric_extractors=[_extract_list_item_count, _extract_word_count],
)

# ---------------------------------------------------------------------------
# Test Case 5: Code generation quality
# ---------------------------------------------------------------------------
TEST_CODE_GENERATION = BehavioralTest(
    name="code_generation_quality",
    category="code_generation",
    description="Tests code generation with specific requirements",
    prompt="Write a Python function called `retry_with_backoff` that retries a callable up to 3 times with exponential backoff. Include type hints and a docstring.",
    system_prompt="You are an expert Python developer. Always include type hints, docstrings, and follow PEP 8.",
    metric_extractors=[_extract_code_block_count, _extract_word_count],
)


def get_default_test_suite():
    """Get the default behavioral test suite with all built-in tests."""
    from .framework import BehavioralTestSuite

    suite = BehavioralTestSuite()
    suite.add_test(TEST_TOOL_CALLING_BASIC)
    suite.add_test(TEST_OUTPUT_FORMAT)
    suite.add_test(TEST_CONSTRAINT_ADHERENCE)
    suite.add_test(TEST_MULTI_TURN)
    suite.add_test(TEST_CODE_GENERATION)
    return suite
