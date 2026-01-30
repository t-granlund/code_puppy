"""Connection Pooling & Streaming - Network Optimizations.

Implements efficient HTTP connection management and response streaming:
1. Connection pooling per provider
2. Response streaming for large outputs
3. Automatic connection lifecycle management
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, Optional, Tuple

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """Configuration for a connection pool."""
    
    max_connections: int = 100  # Max connections in pool
    max_keepalive_connections: int = 20  # Max idle connections
    keepalive_expiry: float = 30.0  # Seconds before idle connection expires
    connect_timeout: float = 10.0  # Connection timeout
    read_timeout: float = 60.0  # Read timeout
    write_timeout: float = 30.0  # Write timeout
    pool_timeout: float = 10.0  # Timeout waiting for pool slot


@dataclass
class PoolStats:
    """Statistics for a connection pool."""
    
    total_requests: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    total_connections_created: int = 0
    connection_reuses: int = 0
    connection_errors: int = 0
    avg_response_time_ms: float = 0.0
    _response_times: list = field(default_factory=list)
    
    def record_request(self, response_time_ms: float) -> None:
        """Record a request and update averages."""
        self.total_requests += 1
        self._response_times.append(response_time_ms)
        
        # Keep only last 1000 response times
        if len(self._response_times) > 1000:
            self._response_times = self._response_times[-500:]
        
        self.avg_response_time_ms = (
            sum(self._response_times) / len(self._response_times)
        )


class ConnectionPool:
    """Managed connection pool for a provider.
    
    Provides:
    - Connection reuse
    - Automatic lifecycle management
    - Statistics tracking
    """
    
    def __init__(
        self,
        base_url: str,
        config: Optional[PoolConfig] = None,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx is required for connection pooling")
        
        self.base_url = base_url
        self.config = config or PoolConfig()
        self.default_headers = default_headers or {}
        self.stats = PoolStats()
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()
    
    async def _get_client(self) -> "httpx.AsyncClient":
        """Get or create the HTTP client."""
        async with self._lock:
            if self._client is None or self._client.is_closed:
                limits = httpx.Limits(
                    max_connections=self.config.max_connections,
                    max_keepalive_connections=self.config.max_keepalive_connections,
                    keepalive_expiry=self.config.keepalive_expiry,
                )
                timeout = httpx.Timeout(
                    connect=self.config.connect_timeout,
                    read=self.config.read_timeout,
                    write=self.config.write_timeout,
                    pool=self.config.pool_timeout,
                )
                self._client = httpx.AsyncClient(
                    base_url=self.base_url,
                    limits=limits,
                    timeout=timeout,
                    headers=self.default_headers,
                    http2=True,  # Enable HTTP/2 for better performance
                )
                self.stats.total_connections_created += 1
                logger.debug(f"Created connection pool for {self.base_url}")
            else:
                self.stats.connection_reuses += 1
            
            return self._client
    
    async def request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> "httpx.Response":
        """Make a request using the connection pool."""
        client = await self._get_client()
        start_time = time.time()
        
        try:
            response = await client.request(method, path, **kwargs)
            response_time = (time.time() - start_time) * 1000
            self.stats.record_request(response_time)
            return response
        except Exception as e:
            self.stats.connection_errors += 1
            raise
    
    async def get(self, path: str, **kwargs: Any) -> "httpx.Response":
        """Make a GET request."""
        return await self.request("GET", path, **kwargs)
    
    async def post(self, path: str, **kwargs: Any) -> "httpx.Response":
        """Make a POST request."""
        return await self.request("POST", path, **kwargs)
    
    async def close(self) -> None:
        """Close the connection pool."""
        async with self._lock:
            if self._client and not self._client.is_closed:
                await self._client.aclose()
                self._client = None
                logger.debug(f"Closed connection pool for {self.base_url}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            "base_url": self.base_url,
            "total_requests": self.stats.total_requests,
            "connections_created": self.stats.total_connections_created,
            "connection_reuses": self.stats.connection_reuses,
            "connection_errors": self.stats.connection_errors,
            "avg_response_time_ms": f"{self.stats.avg_response_time_ms:.1f}",
            "reuse_ratio": (
                self.stats.connection_reuses / self.stats.total_requests
                if self.stats.total_requests > 0 else 0
            ),
        }


class ConnectionPoolManager:
    """Manages connection pools for multiple providers.
    
    Provides:
    - Pool per provider
    - Centralized lifecycle management
    - Aggregate statistics
    """
    
    _instance: Optional["ConnectionPoolManager"] = None
    
    # Provider base URLs
    PROVIDER_URLS: Dict[str, str] = {
        "cerebras": "https://api.cerebras.ai",
        "gemini": "https://generativelanguage.googleapis.com",
        "gemini_flash": "https://generativelanguage.googleapis.com",
        "claude_opus": "https://api.anthropic.com",
        "claude_sonnet": "https://api.anthropic.com",
        "codex": "https://api.openai.com",
        "openai": "https://api.openai.com",
    }
    
    def __init__(self, default_config: Optional[PoolConfig] = None):
        self._pools: Dict[str, ConnectionPool] = {}
        self._default_config = default_config or PoolConfig()
        self._lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> "ConnectionPoolManager":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def get_pool(
        self,
        provider: str,
        base_url: Optional[str] = None,
        config: Optional[PoolConfig] = None,
    ) -> ConnectionPool:
        """Get or create a connection pool for a provider."""
        async with self._lock:
            if provider not in self._pools:
                url = base_url or self.PROVIDER_URLS.get(provider, f"https://api.{provider}.com")
                self._pools[provider] = ConnectionPool(
                    base_url=url,
                    config=config or self._default_config,
                )
            return self._pools[provider]
    
    async def close_all(self) -> None:
        """Close all connection pools."""
        async with self._lock:
            for pool in self._pools.values():
                await pool.close()
            self._pools.clear()
            logger.info("Closed all connection pools")
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all pools."""
        return {name: pool.get_stats() for name, pool in self._pools.items()}


@dataclass
class StreamChunk:
    """A chunk of streamed response data."""
    
    content: str
    delta: str  # Just the new content in this chunk
    index: int
    finish_reason: Optional[str] = None
    tokens_so_far: int = 0


class StreamingResponse:
    """Handles streaming responses from LLM APIs.
    
    Provides:
    - Async iteration over response chunks
    - Progress tracking
    - Early termination support
    """
    
    def __init__(
        self,
        response: "httpx.Response",
        content_extractor: Optional[callable] = None,
    ):
        self._response = response
        self._content_extractor = content_extractor or self._default_extractor
        self._chunks: list = []
        self._full_content = ""
        self._chunk_index = 0
        self._finished = False
    
    @staticmethod
    def _default_extractor(line: str) -> Optional[str]:
        """Default content extractor for SSE streams."""
        if line.startswith("data: "):
            data = line[6:]
            if data.strip() == "[DONE]":
                return None
            try:
                import json
                parsed = json.loads(data)
                # Handle OpenAI-style responses
                if "choices" in parsed and parsed["choices"]:
                    choice = parsed["choices"][0]
                    if "delta" in choice and "content" in choice["delta"]:
                        return choice["delta"]["content"]
                    elif "text" in choice:
                        return choice["text"]
                # Handle Anthropic-style responses
                if "delta" in parsed and "text" in parsed["delta"]:
                    return parsed["delta"]["text"]
            except json.JSONDecodeError:
                pass
        return ""
    
    async def __aiter__(self) -> AsyncIterator[StreamChunk]:
        """Iterate over response chunks."""
        async for line in self._response.aiter_lines():
            if self._finished:
                break
            
            content = self._content_extractor(line)
            
            if content is None:
                self._finished = True
                yield StreamChunk(
                    content=self._full_content,
                    delta="",
                    index=self._chunk_index,
                    finish_reason="stop",
                    tokens_so_far=self._estimate_tokens(self._full_content),
                )
                break
            
            if content:
                self._full_content += content
                self._chunk_index += 1
                
                chunk = StreamChunk(
                    content=self._full_content,
                    delta=content,
                    index=self._chunk_index,
                    tokens_so_far=self._estimate_tokens(self._full_content),
                )
                self._chunks.append(chunk)
                yield chunk
    
    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimate token count from text."""
        return len(text) // 4
    
    def stop(self) -> None:
        """Stop streaming early."""
        self._finished = True
    
    @property
    def full_content(self) -> str:
        """Get the full content received so far."""
        return self._full_content
    
    @property
    def chunk_count(self) -> int:
        """Get the number of chunks received."""
        return self._chunk_index


class StreamingClient:
    """Client for making streaming requests.
    
    Provides:
    - Unified interface for streaming across providers
    - Automatic content type handling
    - Progress callbacks
    """
    
    def __init__(
        self,
        pool_manager: Optional[ConnectionPoolManager] = None,
    ):
        self._pool_manager = pool_manager or ConnectionPoolManager.get_instance()
    
    @asynccontextmanager
    async def stream_request(
        self,
        provider: str,
        path: str,
        method: str = "POST",
        **kwargs: Any,
    ) -> AsyncIterator[StreamingResponse]:
        """Make a streaming request.
        
        Usage:
            async with client.stream_request("openai", "/v1/chat/completions", json=payload) as stream:
                async for chunk in stream:
                    print(chunk.delta, end="", flush=True)
        """
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx is required for streaming")
        
        pool = await self._pool_manager.get_pool(provider)
        client = await pool._get_client()
        
        # Ensure we're requesting a stream
        headers = kwargs.pop("headers", {})
        headers["Accept"] = "text/event-stream"
        
        start_time = time.time()
        
        async with client.stream(method, path, headers=headers, **kwargs) as response:
            pool.stats.record_request((time.time() - start_time) * 1000)
            yield StreamingResponse(response)


# Convenience functions
def get_pool_manager() -> ConnectionPoolManager:
    """Get the global connection pool manager."""
    return ConnectionPoolManager.get_instance()


async def get_provider_pool(
    provider: str,
    config: Optional[PoolConfig] = None,
) -> ConnectionPool:
    """Get a connection pool for a provider."""
    manager = get_pool_manager()
    return await manager.get_pool(provider, config=config)


@asynccontextmanager
async def streaming_completion(
    provider: str,
    path: str,
    payload: Dict[str, Any],
) -> AsyncIterator[StreamingResponse]:
    """Stream a completion from a provider.
    
    Usage:
        async with streaming_completion("openai", "/v1/chat/completions", payload) as stream:
            async for chunk in stream:
                print(chunk.delta, end="")
    """
    client = StreamingClient()
    async with client.stream_request(provider, path, json=payload) as stream:
        yield stream


async def cleanup_connections() -> None:
    """Close all connection pools (call on shutdown)."""
    manager = get_pool_manager()
    await manager.close_all()
