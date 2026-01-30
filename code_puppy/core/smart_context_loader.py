"""Smart Context Loader - The Artifact Manager.

Prevents Pack Agents from reading the same file multiple times (5x cost).
Uses a singleton ContextManager with artifact IDs for efficient sharing.

Features:
- Content caching with hash-based invalidation
- Artifact IDs for lightweight references in prompts
- Automatic compression for large files
- Version tracking for modified files
"""

import hashlib
import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .context_compressor import ContextCompressor

logger = logging.getLogger(__name__)


@dataclass
class Artifact:
    """Cached file or context artifact."""
    
    id: str  # e.g., "artifact:file_main_v2"
    path: str  # Original file path
    content_hash: str  # MD5 of content
    content: str  # Full or compressed content
    compressed_content: Optional[str]  # Compressed version
    token_estimate: int  # Estimated tokens
    version: int  # Increment on modification
    created_at: float
    last_accessed: float
    access_count: int = 0
    is_compressed: bool = False
    
    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at
    
    @property
    def idle_seconds(self) -> float:
        return time.time() - self.last_accessed


@dataclass
class ArtifactReference:
    """Lightweight reference to an artifact for prompts."""
    
    artifact_id: str
    path: str
    summary: str  # Brief description for prompt
    token_estimate: int
    
    def to_prompt_text(self) -> str:
        """Format for inclusion in prompts."""
        return f"[{self.artifact_id}] {self.path}: {self.summary} (~{self.token_estimate} tokens)"


class ContextManager:
    """Singleton manager for shared context across agents.
    
    Prevents duplicate file reads by caching and providing artifact IDs.
    Agents can request files by path and receive either:
    - Artifact ID (for prompts): lightweight reference
    - Full content (when explicitly needed)
    - Compressed content (for reference files)
    """
    
    _instance: Optional["ContextManager"] = None
    _lock = threading.Lock()
    
    # Cache settings
    MAX_CACHE_SIZE_MB = 50
    MAX_ARTIFACTS = 100
    ARTIFACT_TTL_SECONDS = 300  # 5 minutes
    COMPRESSION_THRESHOLD_TOKENS = 500
    
    def __new__(cls) -> "ContextManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._artifacts: Dict[str, Artifact] = {}
        self._path_to_id: Dict[str, str] = {}
        self._compressor = ContextCompressor()
        self._version_counter = 0
        self._initialized = True
    
    def _generate_artifact_id(self, path: str) -> str:
        """Generate unique artifact ID for a path."""
        # Normalize path
        name = Path(path).name.replace(".", "_")
        self._version_counter += 1
        return f"artifact:{name}_v{self._version_counter}"
    
    def _compute_hash(self, content: str) -> str:
        """Compute content hash for cache invalidation."""
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _estimate_tokens(self, content: str) -> int:
        """Estimate token count."""
        return len(content) // 4
    
    def _evict_stale(self) -> None:
        """Evict stale artifacts based on TTL and access patterns."""
        now = time.time()
        to_remove = []
        
        for aid, artifact in self._artifacts.items():
            if artifact.idle_seconds > self.ARTIFACT_TTL_SECONDS:
                to_remove.append(aid)
        
        # Also evict if over size limit (remove least recently accessed)
        if len(self._artifacts) > self.MAX_ARTIFACTS:
            sorted_by_access = sorted(
                self._artifacts.items(),
                key=lambda x: x[1].last_accessed
            )
            to_remove.extend(aid for aid, _ in sorted_by_access[:len(to_remove) + 10])
        
        for aid in set(to_remove):
            if aid in self._artifacts:
                artifact = self._artifacts[aid]
                if artifact.path in self._path_to_id:
                    del self._path_to_id[artifact.path]
                del self._artifacts[aid]
        
        if to_remove:
            logger.debug(f"Evicted {len(to_remove)} stale artifacts")
    
    def load_file(
        self,
        path: str,
        force_reload: bool = False,
        compress: bool = True,
    ) -> Artifact:
        """Load a file into the context cache.
        
        Args:
            path: File path to load
            force_reload: Force reload even if cached
            compress: Whether to generate compressed version
            
        Returns:
            Artifact with content and ID
        """
        self._evict_stale()
        
        # Normalize path
        path = str(Path(path).resolve())
        
        # Check cache
        if not force_reload and path in self._path_to_id:
            artifact_id = self._path_to_id[path]
            if artifact_id in self._artifacts:
                artifact = self._artifacts[artifact_id]
                
                # Verify content hasn't changed
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        current_content = f.read()
                    current_hash = self._compute_hash(current_content)
                    
                    if current_hash == artifact.content_hash:
                        # Cache hit - update access stats
                        artifact.last_accessed = time.time()
                        artifact.access_count += 1
                        logger.debug(f"Cache hit for {path} ({artifact.access_count} accesses)")
                        return artifact
                except Exception:
                    pass
        
        # Cache miss - load file
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to load {path}: {e}")
            raise
        
        content_hash = self._compute_hash(content)
        token_estimate = self._estimate_tokens(content)
        
        # Generate compressed version if needed
        compressed_content = None
        is_compressed = False
        if compress and token_estimate > self.COMPRESSION_THRESHOLD_TOKENS:
            compressed_content = self._compressor.compress_file_context(
                path, content, is_active=False
            )
            is_compressed = len(compressed_content) < len(content)
        
        # Create artifact
        artifact_id = self._generate_artifact_id(path)
        artifact = Artifact(
            id=artifact_id,
            path=path,
            content_hash=content_hash,
            content=content,
            compressed_content=compressed_content,
            token_estimate=token_estimate,
            version=1,
            created_at=time.time(),
            last_accessed=time.time(),
            access_count=1,
            is_compressed=is_compressed,
        )
        
        # Store in cache
        self._artifacts[artifact_id] = artifact
        self._path_to_id[path] = artifact_id
        
        logger.debug(f"Loaded {path} as {artifact_id} ({token_estimate} tokens)")
        return artifact
    
    def get_reference(self, path: str) -> ArtifactReference:
        """Get a lightweight reference to a file for prompts.
        
        This is the preferred method for including file context in prompts
        without duplicating content across agents.
        
        Args:
            path: File path
            
        Returns:
            ArtifactReference for inclusion in prompts
        """
        artifact = self.load_file(path, compress=True)
        
        # Generate brief summary
        lines = artifact.content.splitlines()
        if len(lines) > 5:
            summary = f"{len(lines)} lines, first: {lines[0][:50]}..."
        else:
            summary = f"{len(lines)} lines"
        
        return ArtifactReference(
            artifact_id=artifact.id,
            path=path,
            summary=summary,
            token_estimate=artifact.token_estimate,
        )
    
    def get_content(
        self,
        artifact_id: str,
        compressed: bool = False,
    ) -> Optional[str]:
        """Get content by artifact ID.
        
        Args:
            artifact_id: The artifact ID
            compressed: Whether to return compressed version
            
        Returns:
            Content string or None if not found
        """
        if artifact_id not in self._artifacts:
            return None
        
        artifact = self._artifacts[artifact_id]
        artifact.last_accessed = time.time()
        artifact.access_count += 1
        
        if compressed and artifact.compressed_content:
            return artifact.compressed_content
        return artifact.content
    
    def get_content_by_path(
        self,
        path: str,
        compressed: bool = False,
    ) -> Optional[str]:
        """Get content by file path.
        
        Args:
            path: File path
            compressed: Whether to return compressed version
            
        Returns:
            Content string or None if not found
        """
        path = str(Path(path).resolve())
        if path not in self._path_to_id:
            # Load it
            try:
                artifact = self.load_file(path)
                if compressed and artifact.compressed_content:
                    return artifact.compressed_content
                return artifact.content
            except Exception:
                return None
        
        artifact_id = self._path_to_id[path]
        return self.get_content(artifact_id, compressed)
    
    def mark_modified(self, path: str) -> None:
        """Mark a file as modified (invalidate cache).
        
        Call this after writing to a file to ensure next read gets fresh content.
        
        Args:
            path: File path that was modified
        """
        path = str(Path(path).resolve())
        if path in self._path_to_id:
            artifact_id = self._path_to_id[path]
            if artifact_id in self._artifacts:
                # Increment version and reload on next access
                del self._artifacts[artifact_id]
            del self._path_to_id[path]
            logger.debug(f"Invalidated cache for {path}")
    
    def get_all_references(self) -> List[ArtifactReference]:
        """Get references to all cached artifacts.
        
        Useful for building context summaries.
        
        Returns:
            List of all cached artifact references
        """
        refs = []
        for artifact in self._artifacts.values():
            lines = artifact.content.splitlines()
            summary = f"{len(lines)} lines"
            refs.append(ArtifactReference(
                artifact_id=artifact.id,
                path=artifact.path,
                summary=summary,
                token_estimate=artifact.token_estimate,
            ))
        return refs
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dict with cache stats
        """
        total_tokens = sum(a.token_estimate for a in self._artifacts.values())
        total_accesses = sum(a.access_count for a in self._artifacts.values())
        
        return {
            "artifact_count": len(self._artifacts),
            "total_tokens_cached": total_tokens,
            "total_accesses": total_accesses,
            "cache_hit_rate": "N/A",  # Would need to track misses
            "oldest_artifact_age": max(
                (a.age_seconds for a in self._artifacts.values()),
                default=0
            ),
        }
    
    def clear(self) -> None:
        """Clear all cached artifacts."""
        self._artifacts.clear()
        self._path_to_id.clear()
        self._compressor.clear_cache()
        logger.debug("Context cache cleared")


class SmartContextLoader:
    """High-level interface for smart context loading.
    
    Wraps ContextManager with additional logic for:
    - Batch loading multiple files
    - Automatic compression decisions
    - Token budget management
    """
    
    def __init__(self, target_tokens: int = 15_000):
        """Initialize loader.
        
        Args:
            target_tokens: Target total tokens for loaded context
        """
        self._manager = ContextManager()
        self.target_tokens = target_tokens
    
    def load_files(
        self,
        paths: List[str],
        active_file: Optional[str] = None,
    ) -> Dict[str, ArtifactReference]:
        """Load multiple files with smart compression.
        
        Args:
            paths: List of file paths to load
            active_file: Currently active file (gets full content)
            
        Returns:
            Dict of path -> ArtifactReference
        """
        refs = {}
        total_tokens = 0
        
        for path in paths:
            try:
                if path == active_file:
                    # Active file - load full
                    artifact = self._manager.load_file(path, compress=False)
                else:
                    # Reference file - load compressed
                    artifact = self._manager.load_file(path, compress=True)
                
                ref = ArtifactReference(
                    artifact_id=artifact.id,
                    path=path,
                    summary=f"{len(artifact.content.splitlines())} lines",
                    token_estimate=artifact.token_estimate if path == active_file 
                        else self._estimate_compressed_tokens(artifact),
                )
                refs[path] = ref
                total_tokens += ref.token_estimate
                
            except Exception as e:
                logger.warning(f"Failed to load {path}: {e}")
        
        logger.debug(f"Loaded {len(refs)} files, ~{total_tokens} tokens")
        return refs
    
    def _estimate_compressed_tokens(self, artifact: Artifact) -> int:
        """Estimate tokens for compressed content."""
        if artifact.compressed_content:
            return len(artifact.compressed_content) // 4
        return artifact.token_estimate
    
    def get_for_prompt(
        self,
        paths: List[str],
        active_file: Optional[str] = None,
        include_content: bool = False,
    ) -> str:
        """Get formatted context for prompt inclusion.
        
        Args:
            paths: Files to include
            active_file: Currently active file
            include_content: Whether to include actual content
            
        Returns:
            Formatted string for prompt
        """
        refs = self.load_files(paths, active_file)
        
        lines = ["## Context Files"]
        for path, ref in refs.items():
            if include_content and path == active_file:
                content = self._manager.get_content(ref.artifact_id, compressed=False)
                lines.append(f"\n### {path} (active)\n```\n{content}\n```")
            elif include_content:
                content = self._manager.get_content(ref.artifact_id, compressed=True)
                lines.append(f"\n### {path}\n```\n{content}\n```")
            else:
                lines.append(f"- {ref.to_prompt_text()}")
        
        return "\n".join(lines)
    
    def invalidate(self, path: str) -> None:
        """Invalidate a file in cache after modification."""
        self._manager.mark_modified(path)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get loader statistics."""
        return self._manager.get_stats()
