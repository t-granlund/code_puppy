import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from pydantic_ai.messages import ModelRequest, ToolCallPart, UserPromptPart, TextPart
import httpx

from code_puppy.plugins.antigravity_oauth.antigravity_model import AntigravityModel, _sanitize_tool_format_in_parts
from pydantic_ai.models import ModelRequestParameters

class TestAntigravitySanitization:
    
    def test_sanitize_tool_format_converts_tool_use(self):
        """Test that _sanitize_tool_format_in_parts converts 'tool_use' to 'function_call'."""
        
        # Instantiate model with dummy client
        with patch('httpx.AsyncClient') as mock_client:
            model = AntigravityModel(
                model_name="gemini-experimental",
                api_key="dummy_key",
                http_client=mock_client.return_value
            )
            
            # Create a "leaked" part sent by Claude:
            # { "type": "tool_use", "id": "...", "name": "foo", "input": {...} }
            leaked_part = {
                "role": "model",
                "parts": [
                    {
                        "type": "tool_use",
                        "id": "toolu_123",
                        "name": "list_files",
                        "input": {"path": "."}
                    }
                ]
            }
            
            # Run sanitization
            sanitized_parts = _sanitize_tool_format_in_parts(leaked_part["parts"])
            
            # Check results
            assert len(sanitized_parts) == 1
            part = sanitized_parts[0]
            
            # Should NOT have "type": "tool_use"
            assert part.get("type") != "tool_use"
            
            # Should HAVE "function_call" (snake_case as expected by internal API)
            assert "function_call" in part
            fc = part["function_call"]
            assert fc["name"] == "list_files"
            assert fc["args"] == {"path": "."}
            
            # Should NOT have "input" or "id"
            assert "input" not in part
            assert "id" not in part

    def test_sanitize_leaves_valid_text_parts_alone(self):
        """Test that regular text parts are unchanged."""
        with patch('httpx.AsyncClient') as mock_client:
            text_part = {
                "text": "Hello world"
            }
            parts = [text_part]
            
            sanitized = _sanitize_tool_format_in_parts(parts)
            
            assert len(sanitized) == 1
            assert sanitized[0]["text"] == "Hello world"
            
    def test_sanitize_recursively_handles_nested_format(self):
        """Test implicit recursive behavior if needed, or just list handling."""
        parts = [
            {"text": "foo"},
            {
                "type": "tool_use",
                "id": "123",
                "name": "bar",
                "input": {}
            }
        ]
        
        sanitized = _sanitize_tool_format_in_parts(parts)
        
        assert len(sanitized) == 2
        assert sanitized[0]["text"] == "foo"
        assert "function_call" in sanitized[1]

    @pytest.mark.asyncio
    async def test_request_calls_sanitization(self):
        """Integration-ish test: Mock client.post and verifies that payload is sanitized even if internal mapping was weird."""
        
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "response"}]
                    }
                }
            ]
        }
        mock_client.post.return_value = mock_response
        
        model = AntigravityModel(
            model_name="gemini-experimental",
            api_key="dummy_key",
            http_client=mock_client
        )
        
        # We need to simulate the condition where contents passed to `request` eventually contain the bad format.
        # Since we cannot easily force `_map_messages` to produce bad output without mocking it,
        # we will mock `_map_messages` to return leaked content!
        
        # This simulates "What if the history conversion leaked tool_use?"
        bad_content = [
            {
                "role": "model",
                "parts": [
                    {
                        "type": "tool_use",
                        "id": "123",
                        "name": "dangerous_tool",
                        "input": {}
                    }
                ]
            }
        ]
        
        with patch.object(model, '_map_messages', return_value=(None, bad_content)):
            # Call request
            await model.request(
                messages=[], # Content ignored due to mock
                model_settings=None,
                model_request_parameters=ModelRequestParameters(function_tools=[])
            )
            
        # Verify client.post was called
        mock_client.post.assert_called_once()
        
        # Inspect the JSON body sent
        _, kwargs = mock_client.post.call_args
        json_body = kwargs['json']
        
        # The key check: The body sent to the network should NOT have "tool_use"
        # It should have been converted to "function_call"
        contents = json_body['contents']
        part = contents[0]['parts'][0]
        
        assert "function_call" in part
        assert part.get("type") != "tool_use"

