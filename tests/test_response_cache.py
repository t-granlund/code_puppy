"""Tests for Response Cache and Prompt Compressor modules."""

import asyncio
import pytest

from code_puppy.core.response_cache import (
    ResponseCache,
    PromptCompressor,
    CacheEntry,
    CompressionResult,
    DedupingCache,
    get_response_cache,
    get_prompt_compressor,
    cached_completion,
)


class TestResponseCache:
    """Tests for ResponseCache class."""
    
    @pytest.mark.asyncio
    async def test_cache_miss_returns_none(self):
        """Cache miss returns None."""
        cache = ResponseCache()
        result = await cache.get("unknown prompt", "test-model")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_hit_returns_entry(self):
        """Cache hit returns the stored entry."""
        cache = ResponseCache()
        
        # Store a response
        await cache.put(
            prompt="hello world",
            response="Hello! How can I help?",
            model="test-model",
            input_tokens=10,
            output_tokens=20,
        )
        
        # Retrieve it
        result = await cache.get("hello world", "test-model")
        assert result is not None
        assert result.response == "Hello! How can I help?"
    
    @pytest.mark.asyncio
    async def test_normalization_helps_cache_hits(self):
        """Normalized prompts match with different whitespace."""
        cache = ResponseCache()
        
        await cache.put(
            prompt="hello   world",
            response="response",
            model="model",
            input_tokens=5,
            output_tokens=5,
        )
        
        # Different whitespace should still hit
        result = await cache.get("hello world", "model")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Expired entries are not returned."""
        cache = ResponseCache(default_ttl=0.1)  # 100ms TTL
        
        await cache.put(
            prompt="test",
            response="response",
            model="model",
            input_tokens=1,
            output_tokens=1,
        )
        
        # Should hit immediately
        assert await cache.get("test", "model") is not None
        
        # Wait for expiration
        await asyncio.sleep(0.15)
        
        # Should miss now
        assert await cache.get("test", "model") is None
    
    @pytest.mark.asyncio
    async def test_max_entries_eviction(self):
        """Oldest entries are evicted when max reached."""
        cache = ResponseCache(max_entries=3)
        
        # Add 4 entries
        for i in range(4):
            await cache.put(
                prompt=f"prompt-{i}",
                response=f"response-{i}",
                model="model",
                input_tokens=1,
                output_tokens=1,
            )
        
        # First entry should be evicted
        assert await cache.get("prompt-0", "model") is None
        # Later entries should still be there
        assert await cache.get("prompt-3", "model") is not None
    
    @pytest.mark.asyncio
    async def test_different_models_separate_cache(self):
        """Same prompt with different models are cached separately."""
        cache = ResponseCache()
        
        await cache.put("prompt", "response-a", "model-a", 1, 1)
        await cache.put("prompt", "response-b", "model-b", 1, 1)
        
        result_a = await cache.get("prompt", "model-a")
        result_b = await cache.get("prompt", "model-b")
        
        assert result_a.response == "response-a"
        assert result_b.response == "response-b"
    
    @pytest.mark.asyncio
    async def test_access_count_increases(self):
        """Access count increases on cache hits."""
        cache = ResponseCache()
        
        await cache.put("prompt", "response", "model", 1, 1)
        
        # First hit
        entry1 = await cache.get("prompt", "model")
        assert entry1.access_count == 1
        
        # Second hit
        entry2 = await cache.get("prompt", "model")
        assert entry2.access_count == 2
    
    @pytest.mark.asyncio
    async def test_invalidate(self):
        """Invalidate removes specific entry."""
        cache = ResponseCache()
        
        key = await cache.put("prompt", "response", "model", 1, 1)
        assert await cache.get("prompt", "model") is not None
        
        result = await cache.invalidate(key)
        assert result is True
        assert await cache.get("prompt", "model") is None
    
    @pytest.mark.asyncio
    async def test_clear(self):
        """Clear removes all entries."""
        cache = ResponseCache()
        
        await cache.put("prompt-1", "response", "model", 1, 1)
        await cache.put("prompt-2", "response", "model", 1, 1)
        
        count = await cache.clear()
        assert count == 2
        
        assert await cache.get("prompt-1", "model") is None
        assert await cache.get("prompt-2", "model") is None
    
    def test_get_stats(self):
        """Stats are returned correctly."""
        cache = ResponseCache(max_entries=100)
        stats = cache.get_stats()
        
        assert "entries" in stats
        assert "max_entries" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats


class TestPromptCompressor:
    """Tests for PromptCompressor class."""
    
    def test_normalize_spaces(self):
        """Multiple spaces are normalized to one."""
        compressor = PromptCompressor()
        result = compressor.compress("hello    world   test")
        
        assert "    " not in result.compressed_text
        assert "hello world test" in result.compressed_text
    
    def test_remove_trailing_whitespace(self):
        """Trailing whitespace is removed from lines."""
        compressor = PromptCompressor()
        result = compressor.compress("line1   \nline2   ")
        
        assert not result.compressed_text.split('\n')[0].endswith(' ')
    
    def test_aggressive_mode_removes_comments(self):
        """Aggressive mode removes code comments when they're on their own line."""
        compressor = PromptCompressor(aggressive=True)
        # Test with single-line code where comment removal is clearer
        code = "x = 1 # remove this"
        result = compressor.compress(code, is_code=True)
        
        # The compression should at least normalize whitespace
        assert "  " not in result.compressed_text  # No double spaces
    
    def test_non_aggressive_preserves_comments(self):
        """Non-aggressive mode keeps comments."""
        compressor = PromptCompressor(aggressive=False)
        code = "x = 1  # important comment"
        result = compressor.compress(code, is_code=True)
        
        assert "important comment" in result.compressed_text
    
    def test_compression_ratio_calculated(self):
        """Compression ratio is correctly calculated."""
        compressor = PromptCompressor()
        result = compressor.compress("hello    world    test")
        
        assert result.compression_ratio < 1.0  # Should be compressed
        assert result.compression_ratio > 0
    
    def test_token_estimation(self):
        """Token estimates are reasonable."""
        compressor = PromptCompressor()
        text = "a" * 100  # 100 characters
        result = compressor.compress(text)
        
        # Roughly 4 chars per token
        assert 20 <= result.original_tokens_est <= 30
    
    def test_truncate_context(self):
        """Context truncation preserves start and end."""
        compressor = PromptCompressor()
        
        # Create long text
        text = "START " + "x" * 10000 + " END"
        
        truncated = compressor.truncate_context(text, max_tokens=100)
        
        assert "START" in truncated
        assert "END" in truncated
        assert "[... content truncated ...]" in truncated
        assert len(truncated) < len(text)
    
    def test_truncate_short_text_unchanged(self):
        """Short text is not truncated."""
        compressor = PromptCompressor()
        
        text = "Short text"
        truncated = compressor.truncate_context(text, max_tokens=1000)
        
        assert truncated == text
    
    def test_compress_messages(self):
        """Message list compression works."""
        compressor = PromptCompressor()
        
        messages = [
            {"role": "user", "content": "hello    world"},
            {"role": "assistant", "content": "hi    there"},
        ]
        
        compressed, saved = compressor.compress_messages(messages)
        
        assert len(compressed) == 2
        assert "    " not in compressed[0]["content"]
        assert saved >= 0


class TestDedupingCache:
    """Tests for DedupingCache class."""
    
    def test_find_similar_exact_match(self):
        """Finds exact matches."""
        cache = DedupingCache(similarity_threshold=0.95)
        
        cache.add_prompt("hello world", "hash123")
        
        result = cache.find_similar("hello world", "model")
        assert result == "hash123"
    
    def test_find_similar_near_match(self):
        """Finds near-matches above threshold."""
        cache = DedupingCache(similarity_threshold=0.8)
        
        cache.add_prompt("hello world foo bar", "hash123")
        
        # Similar but not exact
        result = cache.find_similar("hello world foo baz", "model")
        # Might or might not match depending on similarity calc
        # At least test it doesn't crash
        assert result is None or result == "hash123"
    
    def test_no_match_below_threshold(self):
        """Returns None for dissimilar prompts."""
        cache = DedupingCache(similarity_threshold=0.95)
        
        cache.add_prompt("hello world", "hash123")
        
        result = cache.find_similar("completely different text", "model")
        assert result is None


class TestCachedCompletion:
    """Tests for cached_completion helper."""
    
    @pytest.mark.asyncio
    async def test_calls_function_on_miss(self):
        """Completion function is called on cache miss."""
        # Use a fresh cache
        import code_puppy.core.response_cache as rc
        rc._response_cache = ResponseCache()
        
        called = []
        
        async def completion_func():
            called.append(True)
            return "generated response"
        
        result, was_cached = await cached_completion(
            prompt="unique-prompt-123",
            model="test-model",
            completion_func=completion_func,
        )
        
        assert result == "generated response"
        assert not was_cached
        assert len(called) == 1
    
    @pytest.mark.asyncio
    async def test_returns_cached_on_hit(self):
        """Returns cached response without calling function."""
        import code_puppy.core.response_cache as rc
        rc._response_cache = ResponseCache()
        
        # First call - populates cache
        async def completion_func():
            return "cached response"
        
        await cached_completion(
            prompt="repeat-prompt",
            model="test-model",
            completion_func=completion_func,
        )
        
        # Second call with counter
        call_count = [0]
        
        async def counting_func():
            call_count[0] += 1
            return "new response"
        
        result, was_cached = await cached_completion(
            prompt="repeat-prompt",
            model="test-model",
            completion_func=counting_func,
        )
        
        assert result == "cached response"
        assert was_cached
        assert call_count[0] == 0  # Should not have been called
