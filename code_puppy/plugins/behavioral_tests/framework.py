"""Behavioral test framework for per-provider agent validation (OPT-008-A).

Phase 1: Descriptive metrics only — no pass/fail thresholds.
Collects metrics like tool calling frequency, instruction adherence,
and output format compliance across different providers.

Usage:
    from code_puppy.plugins.behavioral_tests.framework import (
        BehavioralTest,
        BehavioralTestSuite,
        TestMetric,
        run_behavioral_tests,
    )
"""

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TestMetric:
    """A single metric measurement from a behavioral test."""

    name: str
    value: Any
    unit: str = ""
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "description": self.description,
        }


@dataclass
class TestResult:
    """Result of running a single behavioral test against one provider."""

    test_name: str
    provider: str
    model_name: str
    metrics: List[TestMetric] = field(default_factory=list)
    duration_ms: float = 0.0
    error: Optional[str] = None
    raw_response: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "test_name": self.test_name,
            "provider": self.provider,
            "model_name": self.model_name,
            "metrics": [m.to_dict() for m in self.metrics],
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


@dataclass
class BehavioralTest:
    """A single behavioral test case.

    Each test defines a prompt, expected behaviors, and metric extractors.
    """

    name: str
    category: str  # e.g., "tool_calling", "instruction_following", "output_format"
    description: str
    prompt: str
    system_prompt: str = "You are a helpful coding assistant."
    tools: List[str] = field(default_factory=list)
    metric_extractors: List[Callable] = field(default_factory=list)

    def extract_metrics(self, response: str, duration_ms: float) -> List[TestMetric]:
        """Run all metric extractors against a response."""
        metrics = [
            TestMetric(
                name="response_length_chars",
                value=len(response) if response else 0,
                unit="chars",
                description="Total response length in characters",
            ),
            TestMetric(
                name="response_latency",
                value=round(duration_ms, 1),
                unit="ms",
                description="Time to complete response",
            ),
        ]

        for extractor in self.metric_extractors:
            try:
                extracted = extractor(response)
                if isinstance(extracted, list):
                    metrics.extend(extracted)
                elif isinstance(extracted, TestMetric):
                    metrics.append(extracted)
            except Exception as e:
                logger.debug("Metric extractor failed for '%s': %s", self.name, e)

        return metrics


@dataclass
class CompatibilityMatrix:
    """Compatibility matrix showing metrics per provider (Phase 1: descriptive only)."""

    results: List[TestResult] = field(default_factory=list)

    def add_result(self, result: TestResult) -> None:
        self.results.append(result)

    def get_results_by_provider(self) -> Dict[str, List[TestResult]]:
        """Group results by provider."""
        by_provider: Dict[str, List[TestResult]] = {}
        for result in self.results:
            by_provider.setdefault(result.provider, []).append(result)
        return by_provider

    def get_results_by_test(self) -> Dict[str, List[TestResult]]:
        """Group results by test name."""
        by_test: Dict[str, List[TestResult]] = {}
        for result in self.results:
            by_test.setdefault(result.test_name, []).append(result)
        return by_test

    def format_summary(self) -> str:
        """Format a human-readable summary of the compatibility matrix."""
        if not self.results:
            return "No behavioral test results available."

        lines = ["📊 Behavioral Test Compatibility Matrix (Phase 1: Metrics Only)", ""]

        by_provider = self.get_results_by_provider()
        for provider, results in sorted(by_provider.items()):
            lines.append(f"  Provider: {provider}")
            lines.append(f"  {'─' * 40}")
            for result in results:
                status = "✅" if not result.error else "❌"
                lines.append(f"    {status} {result.test_name} ({result.duration_ms:.0f}ms)")
                for metric in result.metrics:
                    val = metric.value
                    unit = f" {metric.unit}" if metric.unit else ""
                    lines.append(f"       {metric.name}: {val}{unit}")
                if result.error:
                    lines.append(f"       ERROR: {result.error}")
            lines.append("")

        return "\n".join(lines)

    def to_json(self) -> str:
        """Export results as JSON."""
        return json.dumps(
            [r.to_dict() for r in self.results],
            indent=2,
        )


class BehavioralTestSuite:
    """Collection of behavioral tests that can be run against providers."""

    def __init__(self) -> None:
        self.tests: List[BehavioralTest] = []
        self.matrix = CompatibilityMatrix()

    def add_test(self, test: BehavioralTest) -> None:
        """Add a test case to the suite."""
        self.tests.append(test)

    def get_tests_by_category(self) -> Dict[str, List[BehavioralTest]]:
        """Group tests by category."""
        by_category: Dict[str, List[BehavioralTest]] = {}
        for test in self.tests:
            by_category.setdefault(test.category, []).append(test)
        return by_category

    def record_result(
        self,
        test: BehavioralTest,
        provider: str,
        model_name: str,
        response: str,
        duration_ms: float,
        error: Optional[str] = None,
    ) -> TestResult:
        """Record a test result with extracted metrics."""
        metrics = test.extract_metrics(response, duration_ms) if not error else []

        result = TestResult(
            test_name=test.name,
            provider=provider,
            model_name=model_name,
            metrics=metrics,
            duration_ms=duration_ms,
            error=error,
            raw_response=response,
        )
        self.matrix.add_result(result)
        return result

    def get_summary(self) -> str:
        """Get formatted summary of all results."""
        return self.matrix.format_summary()
