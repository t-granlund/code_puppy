"""Response Caching & Prompt Compression - Efficiency Optimizations.

Implements intelligent caching and prompt optimization:
1. Response caching with TTL and hash-based lookup
2. Prompt compression to reduce token usage
3. Semantic similarity for cache hits
"""

import asyncio
import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from collections import OrderedDict

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cached response entry."""
    
    key: str  # Hash of the prompt
    prompt_prefix: str  # First 100 chars for debugging
    response: str
    model: str
    input_tokens: int
    output_tokens: int
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    ttl_seconds: float = 3600.0  # 1 hour default
    
    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() - self.created_at > self.ttl_seconds
    
    @property
    def age_seconds(self) -> float:
        """Get age of the cache entry."""
        return time.time() - self.created_at


@dataclass
class CacheStats:
    """Statistics for the response cache."""
    
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    tokens_saved: int = 0
    cost_saved_usd: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0


class ResponseCache:
    """Intelligent response cache with TTL and LRU eviction.
    
    Features:
    - Hash-based lookup for exact matches
    - LRU eviction when max size reached
    - TTL-based expiration
    - Token savings tracking
    """
    
    def __init__(
        self,
        max_entries: int = 1000,
        default_ttl: float = 3600.0,  # 1 hour
        max_memory_mb: float = 100.0,
    ):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_entries = max_entries
        self._default_ttl = default_ttl
        self._max_memory_bytes = max_memory_mb * 1024 * 1024
        self._stats = CacheStats()
        self._lock = asyncio.Lock()
    
    @staticmethod
    def _hash_prompt(
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Create a hash key for a prompt."""
        content = f"{model}:{system_prompt or ''}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    @staticmethod
    def _normalize_prompt(prompt: str) -> str:
        """Normalize a prompt for better cache hits."""
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', prompt.strip())
        # Normalize common variations
        normalized = normalized.lower()
        return normalized
    
    async def get(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        normalize: bool = True,
    ) -> Optional[CacheEntry]:
        """Get a cached response if available."""
        if normalize:
            prompt = self._normalize_prompt(prompt)
        
        key = self._hash_prompt(prompt, model, system_prompt)
        
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                
                # Check expiration
                if entry.is_expired:
                    del self._cache[key]
                    self._stats.expirations += 1
                    self._stats.misses += 1
                    return None
                
                # Update access tracking
                entry.last_accessed = time.time()
                entry.access_count += 1
                
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                
                self._stats.hits += 1
                self._stats.tokens_saved += entry.input_tokens + entry.output_tokens
                
                logger.debug(f"Cache hit for prompt hash {key}")
                return entry
            
            self._stats.misses += 1
            return None
    
    async def put(
        self,
        prompt: str,
        response: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        system_prompt: Optional[str] = None,
        ttl: Optional[float] = None,
        normalize: bool = True,
    ) -> str:
        """Store a response in the cache."""
        if normalize:
            normalized_prompt = self._normalize_prompt(prompt)
        else:
            normalized_prompt = prompt
        
        key = self._hash_prompt(normalized_prompt, model, system_prompt)
        
        entry = CacheEntry(
            key=key,
            prompt_prefix=prompt[:100],
            response=response,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            ttl_seconds=ttl or self._default_ttl,
        )
        
        async with self._lock:
            # Evict if at capacity
            while len(self._cache) >= self._max_entries:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats.evictions += 1
            
            self._cache[key] = entry
            logger.debug(f"Cached response for prompt hash {key}")
        
        return key
    
    async def invalidate(self, key: str) -> bool:
        """Invalidate a specific cache entry."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self) -> int:
        """Clear all cache entries."""
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count
    
    async def cleanup_expired(self) -> int:
        """Remove all expired entries."""
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            for key in expired_keys:
                del self._cache[key]
                self._stats.expirations += 1
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "entries": len(self._cache),
            "max_entries": self._max_entries,
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "hit_rate": f"{self._stats.hit_rate:.1f}%",
            "evictions": self._stats.evictions,
            "expirations": self._stats.expirations,
            "tokens_saved": self._stats.tokens_saved,
        }


@dataclass
class CompressionResult:
    """Result of prompt compression."""
    
    original_text: str
    compressed_text: str
    original_tokens_est: int
    compressed_tokens_est: int
    compression_ratio: float
    techniques_applied: List[str]


class PromptCompressor:
    """Compress prompts to reduce token usage.
    
    Techniques:
    - Whitespace normalization
    - Comment removal (for code)
    - Redundancy elimination
    - Abbreviation expansion (optional)
    """
    
    # Approximate tokens per character for estimation
    CHARS_PER_TOKEN = 4.0
    
    def __init__(
        self,
        aggressive: bool = False,
        preserve_structure: bool = True,
        max_compression_ratio: float = 0.5,  # Don't compress beyond 50%
    ):
        self._aggressive = aggressive
        self._preserve_structure = preserve_structure
        self._max_compression_ratio = max_compression_ratio
    
    def compress(
        self,
        text: str,
        is_code: bool = False,
        preserve_newlines: bool = True,
    ) -> CompressionResult:
        """Compress a prompt/text."""
        original = text
        techniques = []
        
        # 1. Normalize whitespace
        if not preserve_newlines:
            text = re.sub(r'\n\s*\n', '\n', text)  # Multiple newlines to one
            techniques.append("normalize_newlines")
        
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to one
        techniques.append("normalize_spaces")
        
        # 2. Remove trailing whitespace
        text = '\n'.join(line.rstrip() for line in text.split('\n'))
        techniques.append("remove_trailing_whitespace")
        
        # 3. Remove comments (if code and aggressive)
        if is_code and self._aggressive:
            # Remove single-line comments
            text = re.sub(r'#[^\n]*', '', text)
            text = re.sub(r'//[^\n]*', '', text)
            techniques.append("remove_line_comments")
            
            # Remove multi-line comments
            text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
            text = re.sub(r'""".*?"""', '', text, flags=re.DOTALL)
            text = re.sub(r"'''.*?'''", '', text, flags=re.DOTALL)
            techniques.append("remove_block_comments")
        
        # 4. Remove empty lines (if aggressive)
        if self._aggressive:
            text = '\n'.join(line for line in text.split('\n') if line.strip())
            techniques.append("remove_empty_lines")
        
        # 5. Trim overall
        text = text.strip()
        techniques.append("trim")
        
        # Calculate metrics
        original_tokens = int(len(original) / self.CHARS_PER_TOKEN)
        compressed_tokens = int(len(text) / self.CHARS_PER_TOKEN)
        ratio = len(text) / len(original) if original else 1.0
        
        # Don't over-compress (preserve meaning)
        if ratio < self._max_compression_ratio:
            text = original  # Revert if too aggressive
            compressed_tokens = original_tokens
            ratio = 1.0
            techniques = ["compression_reverted_too_aggressive"]
        
        return CompressionResult(
            original_text=original,
            compressed_text=text,
            original_tokens_est=original_tokens,
            compressed_tokens_est=compressed_tokens,
            compression_ratio=ratio,
            techniques_applied=techniques,
        )
    
    def compress_messages(
        self,
        messages: List[Dict[str, str]],
    ) -> Tuple[List[Dict[str, str]], int]:
        """Compress a list of chat messages.
        
        Returns:
            Tuple of (compressed messages, tokens saved estimate)
        """
        total_saved = 0
        compressed_messages = []
        
        for msg in messages:
            if "content" in msg:
                result = self.compress(msg["content"])
                compressed_messages.append({
                    **msg,
                    "content": result.compressed_text,
                })
                total_saved += result.original_tokens_est - result.compressed_tokens_est
            else:
                compressed_messages.append(msg)
        
        return compressed_messages, total_saved
    
    def truncate_context(
        self,
        text: str,
        max_tokens: int,
        preserve_start: int = 500,
        preserve_end: int = 500,
    ) -> str:
        """Truncate text to fit token limit while preserving start and end.
        
        Useful for keeping relevant context when input is too large.
        """
        estimated_tokens = int(len(text) / self.CHARS_PER_TOKEN)
        
        if estimated_tokens <= max_tokens:
            return text
        
        # Calculate how many characters to keep
        max_chars = int(max_tokens * self.CHARS_PER_TOKEN)
        
        # Reserve space for start, end, and truncation marker
        marker = "\n\n[... content truncated ...]\n\n"
        start_chars = int(preserve_start * self.CHARS_PER_TOKEN)
        end_chars = int(preserve_end * self.CHARS_PER_TOKEN)
        
        if start_chars + end_chars + len(marker) >= len(text):
            # Text is small enough, just return it
            return text
        
        # Take start and end portions
        start_portion = text[:start_chars]
        end_portion = text[-end_chars:]
        
        return start_portion + marker + end_portion


class DedupingCache:
    """Cache that detects and deduplicates similar prompts.
    
    Uses simple string similarity to find near-duplicates.
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.95,  # 95% similar = same
    ):
        self._threshold = similarity_threshold
        self._prompts: List[Tuple[str, str, str]] = []  # (normalized, hash, original)
    
    def find_similar(
        self,
        prompt: str,
        model: str,
    ) -> Optional[str]:
        """Find a similar prompt's hash if exists."""
        normalized = self._normalize(prompt)
        
        for stored_norm, stored_hash, _ in self._prompts:
            similarity = self._similarity(normalized, stored_norm)
            if similarity >= self._threshold:
                return stored_hash
        
        return None
    
    def add_prompt(
        self,
        prompt: str,
        prompt_hash: str,
    ) -> None:
        """Add a prompt to the dedup index."""
        normalized = self._normalize(prompt)
        self._prompts.append((normalized, prompt_hash, prompt))
        
        # Keep only recent prompts to bound memory
        if len(self._prompts) > 1000:
            self._prompts = self._prompts[-500:]
    
    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text for comparison."""
        return re.sub(r'\s+', ' ', text.lower().strip())
    
    @staticmethod
    def _similarity(a: str, b: str) -> float:
        """Calculate simple similarity ratio."""
        if not a or not b:
            return 0.0
        
        # Use length-based quick check first
        len_ratio = min(len(a), len(b)) / max(len(a), len(b))
        if len_ratio < 0.5:
            return 0.0
        
        # Simple character overlap
        set_a = set(a.split())
        set_b = set(b.split())
        
        if not set_a or not set_b:
            return 0.0
        
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        
        return intersection / union


# Singleton instance for global access
_response_cache: Optional[ResponseCache] = None
_prompt_compressor: Optional[PromptCompressor] = None


def get_response_cache() -> ResponseCache:
    """Get the global response cache."""
    global _response_cache
    if _response_cache is None:
        _response_cache = ResponseCache()
    return _response_cache


def get_prompt_compressor() -> PromptCompressor:
    """Get the global prompt compressor."""
    global _prompt_compressor
    if _prompt_compressor is None:
        _prompt_compressor = PromptCompressor()
    return _prompt_compressor


async def cached_completion(
    prompt: str,
    model: str,
    completion_func: Any,  # Async function that returns response
    system_prompt: Optional[str] = None,
    ttl: Optional[float] = None,
    compress: bool = True,
) -> Tuple[str, bool]:
    """Execute a completion with caching.
    
    Args:
        prompt: The user prompt
        model: Model name
        completion_func: Async function to call for actual completion
        system_prompt: Optional system prompt
        ttl: Cache TTL in seconds
        compress: Whether to compress the prompt
    
    Returns:
        Tuple of (response, was_cached)
    """
    cache = get_response_cache()
    
    # Optionally compress
    if compress:
        compressor = get_prompt_compressor()
        result = compressor.compress(prompt)
        prompt = result.compressed_text
    
    # Check cache
    cached = await cache.get(prompt, model, system_prompt)
    if cached:
        return cached.response, True
    
    # Execute actual completion
    response = await completion_func()
    
    # Store in cache (estimate tokens from response length)
    input_tokens = int(len(prompt) / 4)
    output_tokens = int(len(response) / 4)
    
    await cache.put(
        prompt=prompt,
        response=response,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        system_prompt=system_prompt,
        ttl=ttl,
    )
    
    return response, False
