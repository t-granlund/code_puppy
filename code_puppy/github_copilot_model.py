"""GitHub Copilot SDK Model for pydantic_ai.

This module provides a custom Model implementation that uses the GitHub Copilot SDK
to access premium models through GitHub Copilot subscriptions.

The SDK communicates with the Copilot CLI via JSON-RPC in server mode.
"""

from __future__ import annotations

import logging
import subprocess
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from pydantic_ai._run_context import RunContext
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ModelResponsePart,
    ModelResponseStreamEvent,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models import Model, ModelRequestParameters, StreamedResponse
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import RequestUsage

logger = logging.getLogger(__name__)

# Premium request multipliers for different models
PREMIUM_REQUEST_MULTIPLIERS = {
    # Anthropic models
    "claude-opus-4.5": 3.0,
    "claude-opus-4.1": 3.0,
    "claude-opus-4": 3.0,
    "claude-sonnet-4.5": 1.0,
    "claude-sonnet-4": 1.0,
    "claude-haiku-4.5": 0.33,
    "claude-haiku-4": 0.33,
    # OpenAI models
    "gpt-5.2": 1.0,
    "gpt-5.2-codex": 1.0,
    "gpt-5.1": 1.0,
    "gpt-5.1-codex": 1.0,
    "gpt-5.1-codex-max": 1.0,
    "gpt-5.1-codex-mini": 0.33,
    "gpt-5": 1.0,
    "gpt-5-codex": 1.0,
    "gpt-5-mini": 0.0,  # Free
    "gpt-4.1": 0.0,  # Free
    # Google models
    "gemini-3-pro": 1.0,
    "gemini-3-flash": 0.33,
    # xAI models
    "grok-code-fast-1": 0.25,
    # Fine-tuned models
    "raptor-mini": 0.0,  # Free (fine-tuned GPT-5 mini)
}


def check_copilot_cli_installed() -> bool:
    """Check if GitHub Copilot CLI is installed."""
    try:
        result = subprocess.run(
            ["gh", "copilot", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_copilot_auth() -> bool:
    """Check if user is authenticated with GitHub Copilot."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0 and "Logged in" in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_premium_request_multiplier(model_name: str) -> float:
    """Get the premium request multiplier for a model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Multiplier value (e.g., 3.0 for Claude Opus, 0.33 for Haiku, 0 for free models)
    """
    model_lower = model_name.lower()
    for key, multiplier in PREMIUM_REQUEST_MULTIPLIERS.items():
        if key in model_lower:
            return multiplier
    return 1.0  # Default multiplier


@dataclass
class GitHubCopilotModel(Model):
    """GitHub Copilot SDK model implementation for pydantic_ai.
    
    This model uses the GitHub Copilot SDK to access premium models
    through GitHub Copilot subscriptions.
    """

    model_name: str
    _sdk_client: Any = field(default=None, init=False, repr=False)

    def __post_init__(self):
        """Initialize the GitHub Copilot SDK client."""
        # Check prerequisites
        if not check_copilot_cli_installed():
            raise RuntimeError(
                "GitHub Copilot CLI is not installed. "
                "Please install it with: gh extension install github/gh-copilot"
            )
        
        if not check_copilot_auth():
            raise RuntimeError(
                "Not authenticated with GitHub. "
                "Please run: gh auth login"
            )
        
        # Try to import the SDK
        try:
            from github_copilot_sdk import CopilotClient
            self._sdk_client = CopilotClient()
        except ImportError:
            raise RuntimeError(
                "GitHub Copilot SDK is not installed. "
                "Please install it with: pip install github-copilot-sdk"
            )

    def name(self) -> str:
        """Return the model name."""
        return self.model_name

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        """Make a non-streaming request to the Copilot model.
        
        Args:
            messages: List of messages in the conversation
            model_settings: Optional model settings
            model_request_parameters: Request parameters including tools
            
        Returns:
            ModelResponse
        """
        # Convert messages to Copilot SDK format
        sdk_messages = self._convert_messages(messages)
        
        # Build request parameters
        request_params = {
            "model": self.model_name,
            "messages": sdk_messages,
        }
        
        if model_settings:
            if hasattr(model_settings, "max_tokens") and model_settings.max_tokens:
                request_params["max_tokens"] = model_settings.max_tokens
            if hasattr(model_settings, "temperature") and model_settings.temperature:
                request_params["temperature"] = model_settings.temperature
            if hasattr(model_settings, "top_p") and model_settings.top_p:
                request_params["top_p"] = model_settings.top_p
        
        # Make the request
        try:
            response = await self._sdk_client.chat.completions.create(**request_params)
            
            # Convert response to pydantic_ai format
            content = response.choices[0].message.content
            
            # Build response
            parts: list[ModelResponsePart] = [TextPart(content=content)]
            model_response = ModelResponse(parts=parts)
            
            return model_response
            
        except Exception as e:
            logger.error(f"GitHub Copilot request failed: {e}")
            raise

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
        run_context: RunContext[Any] | None = None,
    ) -> AsyncIterator[StreamedResponse]:
        """Make a streaming request to the Copilot model.
        
        Args:
            messages: List of messages in the conversation
            model_settings: Optional model settings
            model_request_parameters: Request parameters including tools
            run_context: Optional run context
            
        Yields:
            StreamedResponse instance
        """
        # Convert messages to Copilot SDK format
        sdk_messages = self._convert_messages(messages)
        
        # Build request parameters
        request_params = {
            "model": self.model_name,
            "messages": sdk_messages,
            "stream": True,
        }
        
        if model_settings:
            if hasattr(model_settings, "max_tokens") and model_settings.max_tokens:
                request_params["max_tokens"] = model_settings.max_tokens
            if hasattr(model_settings, "temperature") and model_settings.temperature:
                request_params["temperature"] = model_settings.temperature
            if hasattr(model_settings, "top_p") and model_settings.top_p:
                request_params["top_p"] = model_settings.top_p
        
        # Make the streaming request
        try:
            stream = await self._sdk_client.chat.completions.create(**request_params)
            
            # Create and yield a streaming response
            yield GitHubCopilotStreamingResponse(
                model_request_parameters=model_request_parameters,
                _stream=stream,
                _model_name_str=self.model_name,
            )
                        
        except Exception as e:
            logger.error(f"GitHub Copilot streaming request failed: {e}")
            raise

    def _convert_messages(self, messages: list[ModelMessage]) -> list[dict[str, Any]]:
        """Convert pydantic_ai messages to Copilot SDK format.
        
        Args:
            messages: List of pydantic_ai ModelMessage objects
            
        Returns:
            List of message dictionaries for the SDK
        """
        sdk_messages = []
        
        for msg in messages:
            if isinstance(msg, ModelRequest):
                for part in msg.parts:
                    if isinstance(part, SystemPromptPart):
                        sdk_messages.append({
                            "role": "system",
                            "content": part.content,
                        })
                    elif isinstance(part, UserPromptPart):
                        sdk_messages.append({
                            "role": "user",
                            "content": part.content,
                        })
                    elif isinstance(part, ToolReturnPart):
                        # Tool results go as assistant message
                        sdk_messages.append({
                            "role": "assistant",
                            "content": str(part.content),
                        })
            elif isinstance(msg, ModelResponse):
                for part in msg.parts:
                    if isinstance(part, TextPart):
                        sdk_messages.append({
                            "role": "assistant",
                            "content": part.content,
                        })
                    elif isinstance(part, ToolCallPart):
                        # Tool calls go as assistant message
                        sdk_messages.append({
                            "role": "assistant",
                            "content": f"Tool call: {part.tool_name}",
                        })
        
        return sdk_messages


@dataclass
class GitHubCopilotStreamingResponse(StreamedResponse):
    """Streaming response handler for GitHub Copilot SDK."""

    _stream: Any
    _model_name_str: str
    _provider_name_str: str = "github-copilot"
    _timestamp_val: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    async def _get_event_iterator(self) -> AsyncIterator[ModelResponseStreamEvent]:
        """Process streaming chunks and yield events."""
        async for chunk in self._stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                
                # Handle text content
                if hasattr(delta, "content") and delta.content:
                    event = self._parts_manager.handle_text_delta(
                        vendor_part_id=None,
                        content=delta.content,
                    )
                    if event:
                        yield event
                
                # Update usage if available
                if hasattr(chunk, "usage") and chunk.usage:
                    self._usage = RequestUsage(
                        input_tokens=getattr(chunk.usage, "prompt_tokens", 0),
                        output_tokens=getattr(chunk.usage, "completion_tokens", 0),
                    )
