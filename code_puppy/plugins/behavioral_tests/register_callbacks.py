"""Register behavioral test framework callbacks (OPT-008).

Provides /behavioral command for running tests manually.
Integration with /agents validate --behavioral is in OPT-008-C.
"""

from code_puppy.callbacks import register_callback


def _handle_custom_command(command, name):
    """Handle /behavioral command."""
    if name != "behavioral":
        return None

    from code_puppy.messaging import emit_info, emit_warning

    try:
        from .test_cases import get_default_test_suite

        suite = get_default_test_suite()
        tests_by_cat = suite.get_tests_by_category()

        emit_info("🧪 Behavioral Test Suite (Phase 1: Descriptive Metrics)")
        emit_info(f"{'─' * 50}")
        emit_info(f"Total tests: {len(suite.tests)}")
        emit_info("")

        for category, tests in sorted(tests_by_cat.items()):
            emit_info(f"  Category: {category} ({len(tests)} tests)")
            for test in tests:
                emit_info(f"    • {test.name}: {test.description}")
            emit_info("")

        emit_info(
            "To run tests against a provider, use the behavioral test API:\n"
            "  from code_puppy.plugins.behavioral_tests.test_cases import get_default_test_suite\n"
            "  suite = get_default_test_suite()"
        )

    except Exception as e:
        emit_warning(f"Could not load behavioral test suite: {e}")

    return True


def _custom_help():
    """Register /behavioral in help menu."""
    return [
        ("behavioral", "Show available per-provider behavioral tests (Phase 1: metrics only)"),
    ]


register_callback("custom_command", _handle_custom_command)
register_callback("custom_command_help", _custom_help)
