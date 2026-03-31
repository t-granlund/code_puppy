"""Beads Tracker Plugin - Enhanced Beads integration for Code Puppy.

This plugin provides full integration with the `bd` CLI for issue/bead tracking:
- Create and track beads (issues)
- Dependency management
- Ready task detection
- Claiming and assignment
- Hierarchy support (epics → tasks → subtasks)

Beads provides distributed graph issue tracking powered by Dolt.
See: https://github.com/steveyegge/beads
"""

import logging

logger = logging.getLogger(__name__)

__version__ = "0.1.0"

# Default beads config
DEFAULT_CONFIG = {
    "auto_init": True,
    "sync_mode": "embedded",  # embedded or server
    "compact_threshold": 1000,
}
