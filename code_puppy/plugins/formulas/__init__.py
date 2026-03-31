"""Formulas Plugin - Workflow system for Code Puppy.

Provides TOML-based workflow definitions for repeatable processes.
Inspired by Gastown's formula system and Beads' molecule system.

Formulas define multi-step processes that can be executed directly
(`cook`) or instantiated as trackable molecules (`pour`).
"""

from pathlib import Path

# Default directories for formulas
DEFAULT_FORMULA_DIR = Path.home() / ".config" / "code-puppy" / "formulas"
BUILTIN_FORMULA_DIR = Path(__file__).parent / "templates"

__version__ = "0.1.0"
