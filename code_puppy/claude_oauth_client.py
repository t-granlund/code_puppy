"""
Claude Code OAuth Client for Custom Tools

This module provides OAuth-authenticated API access to Claude models using
tokens from Claude Code. It handles token refresh, proper header formatting,
and error handling.

Example Usage:
    ```python
    from code_puppy.claude_oauth_client import ClaudeOAuthClient
    
    client = ClaudeOAuthClient()
    
    # Send a message
    response = await client.send_message(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": "Hello!"}],
        max_tokens=1024
    )
    
    print(response["content"][0]["text"])
    ```

Token File Format (~/.code_puppy/claude_code_oauth.json):
    ```json
    {
        "access_token": "eyJ...",
        "refresh_token": "eyJ...",
        "expires_at": 1735689600.0,
        "token_type": "Bearer"
    }
    ```
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class ClaudeOAuthError(Exception):
    """Base exception for Claude OAuth client errors."""
    pass


class TokenExpiredError(ClaudeOAuthError):
    """Raised when token is expired and refresh failed."""
    pass


class CloudflareBlockError(ClaudeOAuthError):
    """Raised when Cloudflare blocks the request."""
    pass


class ClaudeOAuthClient:
    """
    OAuth-authenticated client for Claude Code API.
    
    Automatically handles token refresh and provides the correct
    header format to avoid Cloudflare 400 errors.
    """
    
    API_BASE_URL = "https://api.anthropic.com"
    OAUTH_BASE_URL = "https://auth.anthropic.com"
    DEFAULT_REFRESH_BUFFER_SECONDS = 300  # 5 minutes
    MIN_REFRESH_BUFFER_PERCENT = 0.10  # 10% of token lifetime
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 2
    
    def __init__(
        self,
        token_file: Optional[Path] = None,
        refresh_buffer_seconds: Optional[int] = None,
    ):
        """
        Initialize the Claude OAuth client.
        
        Args:
            token_file: Path to token storage file. Defaults to
                ~/.code_puppy/claude_code_oauth.json
            refresh_buffer_seconds: How many seconds before expiry to refresh.
                Defaults to 300 seconds (5 min) or 10% of token lifetime,
                whichever is greater.
        """
        if token_file is None:
            # Use the same path as the claude_code_oauth plugin
            from code_puppy.plugins.claude_code_oauth.config import get_token_storage_path
            token_file = get_token_storage_path()
        
        self.token_file = token_file
        self.refresh_buffer_seconds = (
            refresh_buffer_seconds or self.DEFAULT_REFRESH_BUFFER_SECONDS
        )
        
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._expires_at: Optional[float] = None
        self._token_type: str = "Bearer"
        
        # Load tokens if available
        self._load_tokens()
    
    def _load_tokens(self) -> None:
        """Load tokens from disk."""
        if not self.token_file.exists():
            logger.debug(f"Token file not found: {self.token_file}")
            return
        
        try:
            with open(self.token_file, "r") as f:
                data = json.load(f)
            
            self._access_token = data.get("access_token")
            self._refresh_token = data.get("refresh_token")
            self._expires_at = data.get("expires_at")
            self._token_type = data.get("token_type", "Bearer")
            
            logger.debug(f"Loaded tokens from {self.token_file}")
        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
    
    def _save_tokens(self) -> None:
        """Save tokens to disk."""
        try:
            data = {
                "access_token": self._access_token,
                "refresh_token": self._refresh_token,
                "expires_at": self._expires_at,
                "token_type": self._token_type,
            }
            
            # Atomic write with temp file
            temp_file = self.token_file.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)
            
            temp_file.replace(self.token_file)
            logger.debug(f"Saved tokens to {self.token_file}")
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")
    
    def is_token_valid(self) -> bool:
        """
        Check if the current access token is valid and not expired.
        
        Returns:
            True if token exists and is not expired (with buffer), False otherwise.
        """
        if not self._access_token or not self._expires_at:
            return False
        
        now = time.time()
        
        # Calculate adaptive buffer
        # Use 10% of token lifetime or default buffer, whichever is greater
        if self._expires_at > now:
            token_lifetime = self._expires_at - now
            adaptive_buffer = max(
                self.refresh_buffer_seconds,
                token_lifetime * self.MIN_REFRESH_BUFFER_PERCENT,
            )
        else:
            adaptive_buffer = self.refresh_buffer_seconds
        
        expires_with_buffer = self._expires_at - adaptive_buffer
        
        if now >= expires_with_buffer:
            logger.debug(
                f"Token expires at {self._expires_at}, "
                f"buffer {adaptive_buffer}s, now {now} - needs refresh"
            )
            return False
        
        return True
    
    async def refresh_token_if_needed(self) -> None:
        """
        Refresh the access token if it's expired or close to expiring.
        
        Raises:
            TokenExpiredError: If token refresh fails.
        """
        if self.is_token_valid():
            return
        
        if not self._refresh_token:
            raise TokenExpiredError(
                "Access token expired and no refresh token available. "
                "Please re-authenticate with /claude_oauth command."
            )
        
        logger.info("Refreshing Claude Code OAuth token...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.OAUTH_BASE_URL}/oauth/token",
                    json={
                        "grant_type": "refresh_token",
                        "refresh_token": self._refresh_token,
                    },
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "claude-cli/2.0.61 (external, cli)",
                    },
                    timeout=30.0,
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    raise TokenExpiredError(
                        f"Token refresh failed (HTTP {response.status_code}): {error_text}"
                    )
                
                data = response.json()
                
                # Update tokens
                self._access_token = data["access_token"]
                self._refresh_token = data.get("refresh_token", self._refresh_token)
                
                # Calculate expires_at from expires_in
                expires_in = data.get("expires_in", 3600)
                self._expires_at = time.time() + expires_in
                self._token_type = data.get("token_type", "Bearer")
                
                # Save to disk
                self._save_tokens()
                
                logger.info(f"Token refreshed successfully (expires in {expires_in}s)")
        
        except httpx.RequestError as e:
            raise TokenExpiredError(f"Network error during token refresh: {e}")
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get the correct headers for Claude API requests.
        
        This is the CRITICAL part - wrong headers cause Cloudflare 400 errors.
        Do NOT use x-api-key with OAuth tokens!
        
        Returns:
            Dict of headers with proper Authorization format.
        """
        if not self._access_token:
            raise ClaudeOAuthError("No access token available")
        
        return {
            "Authorization": f"{self._token_type} {self._access_token}",
            "Content-Type": "application/json",
            "anthropic-beta": "oauth-2025-04-20,interleaved-thinking-2025-05-14",
            "anthropic-version": "2023-06-01",
            "x-app": "cli",
            "User-Agent": "claude-cli/2.0.61 (external, cli)",
        }
    
    async def send_message(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 4096,
        system: Optional[str] = None,
        temperature: float = 1.0,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Send a message to Claude using OAuth authentication.
        
        Args:
            model: Model name (e.g., "claude-sonnet-4-6", "claude-opus-4-6")
            messages: List of message dicts with "role" and "content"
            max_tokens: Maximum tokens to generate
            system: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            stream: Whether to stream the response (not implemented yet)
            **kwargs: Additional API parameters
        
        Returns:
            API response dict with "id", "content", "model", etc.
        
        Raises:
            TokenExpiredError: If token refresh fails
            CloudflareBlockError: If Cloudflare blocks the request
            ClaudeOAuthError: For other API errors
        """
        # Ensure token is fresh
        await self.refresh_token_if_needed()
        
        # Build request payload
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs,
        }
        
        if system:
            payload["system"] = system
        
        if stream:
            payload["stream"] = True
        
        # Make request with retries
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        f"{self.API_BASE_URL}/v1/messages",
                        headers=self._get_headers(),
                        json=payload,
                    )
                    
                    # Handle different error types
                    if response.status_code == 200:
                        return response.json()
                    
                    # Cloudflare HTML errors (400)
                    if response.status_code == 400 and "text/html" in response.headers.get("content-type", ""):
                        raise CloudflareBlockError(
                            "Cloudflare blocked the request (400). This usually means "
                            "the headers are incorrect. Check that you're using "
                            "Authorization: Bearer, not x-api-key."
                        )
                    
                    # Anthropic API errors (JSON)
                    if response.headers.get("content-type", "").startswith("application/json"):
                        error_data = response.json()
                        error_message = error_data.get("error", {}).get("message", response.text)
                        error_type = error_data.get("error", {}).get("type", "unknown")
                        
                        if response.status_code == 401:
                            raise TokenExpiredError(f"Authentication failed: {error_message}")
                        
                        raise ClaudeOAuthError(
                            f"API error (HTTP {response.status_code}, {error_type}): {error_message}"
                        )
                    
                    # Retry on 5xx errors
                    if 500 <= response.status_code < 600:
                        logger.warning(
                            f"Server error (HTTP {response.status_code}), "
                            f"retrying in {self.RETRY_DELAY_SECONDS}s... "
                            f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                        )
                        await asyncio.sleep(self.RETRY_DELAY_SECONDS * (2 ** attempt))
                        continue
                    
                    # Unknown error
                    raise ClaudeOAuthError(
                        f"Unexpected response (HTTP {response.status_code}): {response.text[:200]}"
                    )
            
            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(
                        f"Network error: {e}, retrying in {self.RETRY_DELAY_SECONDS}s... "
                        f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    await asyncio.sleep(self.RETRY_DELAY_SECONDS * (2 ** attempt))
                    continue
        
        # All retries exhausted
        raise ClaudeOAuthError(f"All retry attempts failed. Last error: {last_error}")
    
    async def stream_message(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 4096,
        system: Optional[str] = None,
        temperature: float = 1.0,
        **kwargs: Any,
    ):
        """
        Stream a message response from Claude using OAuth authentication.
        
        Args:
            model: Model name (e.g., "claude-sonnet-4-6", "claude-opus-4-6")
            messages: List of message dicts with "role" and "content"
            max_tokens: Maximum tokens to generate
            system: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional API parameters
        
        Yields:
            Server-sent events as dicts
        
        Raises:
            TokenExpiredError: If token refresh fails
            CloudflareBlockError: If Cloudflare blocks the request
            ClaudeOAuthError: For other API errors
        """
        # Ensure token is fresh
        await self.refresh_token_if_needed()
        
        # Build request payload
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
            **kwargs,
        }
        
        if system:
            payload["system"] = system
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.API_BASE_URL}/v1/messages",
                headers=self._get_headers(),
                json=payload,
            ) as response:
                # Check for errors before streaming
                if response.status_code != 200:
                    error_text = await response.aread()
                    
                    # Cloudflare HTML errors
                    if response.status_code == 400 and "text/html" in response.headers.get("content-type", ""):
                        raise CloudflareBlockError(
                            "Cloudflare blocked the request (400). Check your headers."
                        )
                    
                    # JSON errors
                    if response.headers.get("content-type", "").startswith("application/json"):
                        error_data = json.loads(error_text)
                        error_message = error_data.get("error", {}).get("message", error_text.decode())
                        raise ClaudeOAuthError(
                            f"API error (HTTP {response.status_code}): {error_message}"
                        )
                    
                    raise ClaudeOAuthError(
                        f"Unexpected error (HTTP {response.status_code}): {error_text.decode()[:200]}"
                    )
                
                # Stream events
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        
                        if data == "[DONE]":
                            break
                        
                        try:
                            event = json.loads(data)
                            yield event
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse SSE data: {e}")
                            continue


# Convenience functions for quick usage

async def create_client() -> ClaudeOAuthClient:
    """
    Create and return a ClaudeOAuthClient instance.
    
    Returns:
        Configured ClaudeOAuthClient ready to use.
    """
    return ClaudeOAuthClient()


async def quick_message(
    prompt: str,
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 4096,
) -> str:
    """
    Send a quick message and return the text response.
    
    Args:
        prompt: User prompt text
        model: Model to use (default: claude-sonnet-4-6)
        max_tokens: Max tokens to generate
    
    Returns:
        Response text from Claude
    
    Example:
        ```python
        response = await quick_message("What is 2+2?")
        print(response)  # "2 + 2 = 4"
        ```
    """
    client = ClaudeOAuthClient()
    response = await client.send_message(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )
    
    # Extract text from response
    content_blocks = response.get("content", [])
    text_parts = [
        block["text"]
        for block in content_blocks
        if block.get("type") == "text"
    ]
    
    return "\n".join(text_parts)


if __name__ == "__main__":
    # Example usage
    import asyncio
    
    async def main():
        client = ClaudeOAuthClient()
        
        response = await client.send_message(
            model="claude-sonnet-4-6",
            messages=[
                {"role": "user", "content": "Say hello in 3 words!"}
            ],
            max_tokens=1024,
        )
        
        print(response)
    
    asyncio.run(main())
