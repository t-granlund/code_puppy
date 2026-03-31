"""Orchestra Plugin - Multi-agent orchestration for Code Puppy.

This plugin brings Gastown-style multi-agent orchestration to Code Puppy,
including:
- Roles: Mayor, Polecats, Crew, Witness, Deacon, Dogs
- Rigs: Project containers
- Hooks: Git worktree-based persistent storage
- Convoys: Work tracking units
- Mail: Inter-agent messaging

Based on concepts from https://github.com/steveyegge/gastown
"""

from pathlib import Path

# Default town directory (~/gt like Gastown)
DEFAULT_TOWN_DIR = Path.home() / "gt"

# Hook subdirectory for persistent agent storage
HOOKS_SUBDIR = ".orchestra/hooks"

# Config subdirectory
CONFIG_SUBDIR = ".orchestra"

__version__ = "0.1.0"
