"""MCP Progressive Discovery — token tracking + configuration (OPT-010).

Tracks MCP tool schema token costs and provides per-server
configuration for progressive discovery.

Note: Actual two-phase tool loading (metadata → schema on demand)
requires pydantic-ai support for lazy schema loading, which is not
yet available. This module provides the tracking and configuration
infrastructure that will be ready when that capability exists.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Estimate: ~50 tokens per tool for full schema, ~10 for metadata-only
_TOKENS_PER_FULL_SCHEMA = 50
_TOKENS_PER_METADATA = 10

# Session-level tracking
_session_stats: Dict[str, "ServerToolStats"] = {}


@dataclass
class ServerToolStats:
    """Token tracking stats for a single MCP server's tools."""

    server_name: str
    total_tools: int = 0
    schemas_loaded: int = 0
    progressive_enabled: bool = True
    estimated_tokens_full: int = 0
    estimated_tokens_actual: int = 0
    first_seen: float = field(default_factory=time.time)

    @property
    def estimated_savings(self) -> int:
        """Estimated token savings vs full-load baseline."""
        if not self.progressive_enabled:
            return 0
        return max(0, self.estimated_tokens_full - self.estimated_tokens_actual)

    def to_dict(self) -> dict:
        return {
            "server_name": self.server_name,
            "total_tools": self.total_tools,
            "schemas_loaded": self.schemas_loaded,
            "progressive_enabled": self.progressive_enabled,
            "estimated_tokens_full": self.estimated_tokens_full,
            "estimated_tokens_actual": self.estimated_tokens_actual,
            "estimated_savings": self.estimated_savings,
        }


def _get_progressive_config_file() -> Path:
    """Get path to progressive discovery config file."""
    from code_puppy.config import CONFIG_DIR

    return Path(CONFIG_DIR) / "mcp_progressive.json"


def load_progressive_config() -> Dict[str, Any]:
    """Load per-server progressive discovery configuration.

    File format (~/.code_puppy/mcp_progressive.json):
    {
        "default_enabled": true,
        "servers": {
            "filesystem": {"progressive": false},
            "github": {"progressive": true}
        }
    }

    Returns:
        Config dict with default_enabled and per-server settings.
    """
    config_file = _get_progressive_config_file()

    if not config_file.exists():
        return {"default_enabled": True, "servers": {}}

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            logger.warning("mcp_progressive.json must be a JSON object")
            return {"default_enabled": True, "servers": {}}
        return data
    except (json.JSONDecodeError, Exception) as e:
        logger.warning("Failed to load mcp_progressive.json: %s", e)
        return {"default_enabled": True, "servers": {}}


def is_progressive_enabled(server_name: str) -> bool:
    """Check if progressive discovery is enabled for a server.

    Args:
        server_name: Name of the MCP server.

    Returns:
        True if progressive discovery is enabled.
    """
    config = load_progressive_config()
    servers = config.get("servers", {})

    if server_name in servers:
        return servers[server_name].get("progressive", True)

    return config.get("default_enabled", True)


def record_server_tools(
    server_name: str,
    tool_count: int,
    progressive_enabled: bool = True,
) -> ServerToolStats:
    """Record tool discovery for a server (called at server startup).

    Args:
        server_name: Name of the MCP server.
        tool_count: Number of tools discovered.
        progressive_enabled: Whether progressive mode is active.

    Returns:
        ServerToolStats with current tracking data.
    """
    full_tokens = tool_count * _TOKENS_PER_FULL_SCHEMA

    # If progressive is enabled, initial load is metadata-only
    # If disabled, all schemas load immediately
    if progressive_enabled:
        actual_tokens = tool_count * _TOKENS_PER_METADATA
    else:
        actual_tokens = full_tokens

    stats = ServerToolStats(
        server_name=server_name,
        total_tools=tool_count,
        schemas_loaded=0 if progressive_enabled else tool_count,
        progressive_enabled=progressive_enabled,
        estimated_tokens_full=full_tokens,
        estimated_tokens_actual=actual_tokens,
    )
    _session_stats[server_name] = stats

    logger.debug(
        "MCP tool tracking for '%s': %d tools, progressive=%s, "
        "full=%d tokens, actual=%d tokens",
        server_name,
        tool_count,
        progressive_enabled,
        full_tokens,
        actual_tokens,
    )
    return stats


def record_schema_loaded(server_name: str, tool_name: str) -> None:
    """Record that a tool's full schema was loaded on demand.

    Args:
        server_name: Name of the MCP server.
        tool_name: Name of the tool whose schema was loaded.
    """
    stats = _session_stats.get(server_name)
    if not stats:
        return

    stats.schemas_loaded += 1
    # Update actual tokens: replace one metadata entry with a full schema
    stats.estimated_tokens_actual += _TOKENS_PER_FULL_SCHEMA - _TOKENS_PER_METADATA

    logger.debug(
        "Schema loaded for '%s.%s': %d/%d schemas loaded, savings=%d tokens",
        server_name,
        tool_name,
        stats.schemas_loaded,
        stats.total_tools,
        stats.estimated_savings,
    )


def get_session_stats() -> Dict[str, ServerToolStats]:
    """Get token tracking stats for all servers in this session."""
    return dict(_session_stats)


def get_total_savings() -> int:
    """Get total estimated token savings across all servers."""
    return sum(s.estimated_savings for s in _session_stats.values())


def get_summary() -> str:
    """Get a formatted summary for /mcp output."""
    if not _session_stats:
        return "  No MCP tool tracking data available."

    lines = ["  📊 Progressive Discovery Stats:"]

    total_tools = 0
    total_loaded = 0
    total_full = 0
    total_actual = 0

    for name, stats in sorted(_session_stats.items()):
        mode = "progressive" if stats.progressive_enabled else "full-load"
        lines.append(
            f"    {name}: {stats.total_tools} tools ({mode}), "
            f"{stats.schemas_loaded} schemas loaded, "
            f"~{stats.estimated_savings} tokens saved"
        )
        total_tools += stats.total_tools
        total_loaded += stats.schemas_loaded
        total_full += stats.estimated_tokens_full
        total_actual += stats.estimated_tokens_actual

    total_savings = total_full - total_actual
    lines.append("  ─────────────────────────────")
    lines.append(
        f"  Total: {total_tools} tools, {total_loaded} schemas loaded, "
        f"~{total_savings} tokens saved vs full-load baseline"
    )

    return "\n".join(lines)


def clear_stats() -> None:
    """Clear session stats (for testing)."""
    _session_stats.clear()
