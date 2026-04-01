"""Bridges module for external binary integration.

This module provides interfaces to external Go binaries (bd, dolt, gt)
used by Code Puppy for issue tracking, database management, and git operations.
"""

from code_puppy.bridges.go_binary_manager import (
    GoBinaryManager,
    BinaryConfig,
    BinaryInfo,
)

__all__ = ["GoBinaryManager", "BinaryConfig", "BinaryInfo"]
