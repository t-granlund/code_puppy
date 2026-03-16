#!/usr/bin/env python3
"""Comprehensive test suite for Claude Code OAuth integration.

Tests cover:
1. Token loading from correct path
2. Token expiry logic with adaptive buffer (5min or 10%)
3. Header construction for API requests
4. Support for both claude-opus-4-6 and claude-sonnet-4-6
5. Error handling (Cloudflare HTML vs Anthropic JSON errors)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest
import requests

# Import the modules we're testing
from code_puppy.plugins.claude_code_oauth.config import (
    CLAUDE_CODE_OAUTH_CONFIG,
    get_claude_models_path,
    get_token_storage_path,
)
from code_puppy.plugins.claude_code_oauth.utils import (
    _calculate_refresh_buffer,
    _is_token_actually_expired,
    exchange_code_for_tokens,
    fetch_claude_code_models,
    filter_latest_claude_models,
    get_valid_access_token,
    is_token_expired,
    load_stored_tokens,
    refresh_access_token,
    save_tokens,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_token_data() -> Dict[str, Any]:
    """Valid token data with 1-hour expiry."""
    now = time.time()
    return {
        "access_token": "test_access_token_abc123",
        "refresh_token": "test_refresh_token_xyz789",
        "token_type": "Bearer",
        "expires_in": 3600,  # 1 hour
        "expires_at": now + 3600,
        "scope": "org:create_api_key user:profile user:inference",
    }


@pytest.fixture
def mock_expired_token_data() -> Dict[str, Any]:
    """Expired token data (expired 10 minutes ago)."""
    now = time.time()
    return {
        "access_token": "expired_token",
        "refresh_token": "refresh_for_expired",
        "token_type": "Bearer",
        "expires_in": 3600,
        "expires_at": now - 600,  # 10 minutes ago
        "scope": "org:create_api_key user:profile user:inference",
    }


@pytest.fixture
def mock_near_expiry_token_data() -> Dict[str, Any]:
    """Token data expiring in 4 minutes (should trigger refresh with 5min buffer)."""
    now = time.time()
    return {
        "access_token": "near_expiry_token",
        "refresh_token": "refresh_near_expiry",
        "token_type": "Bearer",
        "expires_in": 3600,
        "expires_at": now + 240,  # 4 minutes from now
        "scope": "org:create_api_key user:profile user:inference",
    }


@pytest.fixture
def mock_oauth_context():
    """Mock OAuth context for testing token exchange."""
    from code_puppy.plugins.claude_code_oauth.utils import OAuthContext

    return OAuthContext(
        state="test_state_123",
        code_verifier="test_verifier_456",
        code_challenge="test_challenge_789",
        created_at=time.time(),
        redirect_uri="http://localhost:8765/callback",
    )


# ============================================================================
# Test 1: Token Loading from Correct Path
# ============================================================================


def test_token_storage_path_location():
    """Verify tokens are loaded from the correct XDG data directory path."""
    token_path = get_token_storage_path()
    
    # Should be in XDG_DATA_HOME/.code_puppy/claude_code_oauth.json
    assert token_path.name == "claude_code_oauth.json"
    assert ".code_puppy" in str(token_path)
    

def test_load_stored_tokens_success(mock_token_data, tmp_path):
    """Test successful token loading from file."""
    token_file = tmp_path / "claude_code_oauth.json"
    token_file.write_text(json.dumps(mock_token_data))
    
    with patch("code_puppy.plugins.claude_code_oauth.utils.get_token_storage_path", return_value=token_file):
        tokens = load_stored_tokens()
        
        assert tokens is not None
        assert tokens["access_token"] == "test_access_token_abc123"
        assert tokens["refresh_token"] == "test_refresh_token_xyz789"
        assert "expires_at" in tokens


def test_load_stored_tokens_file_not_found(tmp_path):
    """Test loading when token file doesn't exist."""
    nonexistent_file = tmp_path / "nonexistent_tokens.json"
    
    with patch("code_puppy.plugins.claude_code_oauth.utils.get_token_storage_path", return_value=nonexistent_file):
        tokens = load_stored_tokens()
        assert tokens is None


def test_load_stored_tokens_invalid_json(tmp_path):
    """Test loading when token file contains invalid JSON."""
    token_file = tmp_path / "claude_code_oauth.json"
    token_file.write_text("not valid json {{{")
    
    with patch("code_puppy.plugins.claude_code_oauth.utils.get_token_storage_path", return_value=token_file):
        tokens = load_stored_tokens()
        assert tokens is None


# ============================================================================
# Test 2: Token Expiry Check with Adaptive Buffer
# ============================================================================


def test_calculate_refresh_buffer_default():
    """Test default refresh buffer is 5 minutes (300 seconds)."""
    buffer = _calculate_refresh_buffer(None)
    assert buffer == 300.0


def test_calculate_refresh_buffer_10_percent():
    """Test buffer is 10% of expires_in when that's less than 5 minutes."""
    # 20 minutes = 1200 seconds
    # 10% = 120 seconds (2 minutes)
    buffer = _calculate_refresh_buffer(1200)
    assert buffer == 120.0


def test_calculate_refresh_buffer_caps_at_5_minutes():
    """Test buffer caps at 5 minutes for long-lived tokens."""
    # 2 hours = 7200 seconds
    # 10% = 720 seconds (12 minutes), but should cap at 300
    buffer = _calculate_refresh_buffer(7200)
    assert buffer == 300.0


def test_calculate_refresh_buffer_minimum_30_seconds():
    """Test buffer has a minimum of 30 seconds."""
    # 100 seconds, 10% = 10 seconds, but minimum is 30
    buffer = _calculate_refresh_buffer(100)
    assert buffer == 30.0


def test_is_token_expired_with_buffer(mock_near_expiry_token_data):
    """Test that tokens expiring in <5 minutes are considered expired."""
    # Token expires in 4 minutes, should be considered expired with 5min buffer
    assert is_token_expired(mock_near_expiry_token_data) is True


def test_is_token_not_expired_fresh_token(mock_token_data):
    """Test that fresh tokens are not considered expired."""
    # Token expires in 1 hour, should not be expired
    assert is_token_expired(mock_token_data) is False


def test_is_token_actually_expired(mock_expired_token_data):
    """Test distinguishing between buffer-expired and truly expired."""
    # Should be truly expired (no buffer applied)
    assert _is_token_actually_expired(mock_expired_token_data) is True


def test_is_token_actually_expired_near_expiry(mock_near_expiry_token_data):
    """Test token near expiry is not actually expired yet."""
    # Expires in 4 minutes, not actually expired yet
    assert _is_token_actually_expired(mock_near_expiry_token_data) is False


def test_is_token_expired_no_expires_at():
    """Test handling tokens without expires_at field."""
    tokens = {"access_token": "test", "refresh_token": "test"}
    assert is_token_expired(tokens) is False


# ============================================================================
# Test 3: Header Construction
# ============================================================================


def test_fetch_models_header_construction():
    """Test correct headers are sent when fetching models."""
    access_token = "test_token_12345"
    
    with patch("code_puppy.plugins.claude_code_oauth.utils.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {
            "data": [
                {"id": "claude-opus-4-6"},
                {"id": "claude-sonnet-4-6"},
            ]
        }
        mock_get.return_value = mock_response
        
        models = fetch_claude_code_models(access_token)
        
        # Verify the request was made with correct headers
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        
        headers = call_args.kwargs.get("headers", {})
        assert headers["Authorization"] == f"Bearer {access_token}"
        assert headers["Content-Type"] == "application/json"
        assert headers["anthropic-beta"] == "oauth-2025-04-20"
        assert "anthropic-version" in headers
        
        # Verify models were parsed correctly
        assert models == ["claude-opus-4-6", "claude-sonnet-4-6"]


def test_token_refresh_header_construction():
    """Test correct headers are sent during token refresh."""
    with patch("code_puppy.plugins.claude_code_oauth.utils.load_stored_tokens") as mock_load:
        mock_load.return_value = {
            "access_token": "old_token",
            "refresh_token": "refresh_token_xyz",
            "expires_in": 3600,
            "expires_at": time.time() - 600,  # Expired
        }
        
        with patch("code_puppy.plugins.claude_code_oauth.utils.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "access_token": "new_token",
                "refresh_token": "new_refresh_token",
                "expires_in": 3600,
            }
            mock_post.return_value = mock_response
            
            with patch("code_puppy.plugins.claude_code_oauth.utils.save_tokens", return_value=True):
                with patch("code_puppy.plugins.claude_code_oauth.utils.update_claude_code_model_tokens"):
                    new_token = refresh_access_token(force=True)
            
            # Verify headers
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            headers = call_args.kwargs.get("headers", {})
            assert headers["Content-Type"] == "application/json"
            assert headers["Accept"] == "application/json"
            assert headers["anthropic-beta"] == "oauth-2025-04-20"
            
            # Verify payload structure
            payload = call_args.kwargs.get("json", {})
            assert payload["grant_type"] == "refresh_token"
            assert payload["client_id"] == CLAUDE_CODE_OAUTH_CONFIG["client_id"]
            assert payload["refresh_token"] == "refresh_token_xyz"
            
            assert new_token == "new_token"


def test_token_exchange_header_construction(mock_oauth_context):
    """Test correct headers during authorization code exchange."""
    with patch("code_puppy.plugins.claude_code_oauth.utils.requests.post") as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {
            "access_token": "exchanged_token",
            "refresh_token": "exchanged_refresh",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response
        
        tokens = exchange_code_for_tokens("auth_code_123", mock_oauth_context)
        
        # Verify headers
        call_args = mock_post.call_args
        headers = call_args.kwargs.get("headers", {})
        
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        assert headers["anthropic-beta"] == "oauth-2025-04-20"
        
        # Verify payload
        payload = call_args.kwargs.get("json", {})
        assert payload["grant_type"] == "authorization_code"
        assert payload["code"] == "auth_code_123"
        assert payload["state"] == mock_oauth_context.state
        assert payload["code_verifier"] == mock_oauth_context.code_verifier
        assert payload["redirect_uri"] == mock_oauth_context.redirect_uri
        
        assert tokens is not None
        assert "expires_at" in tokens


# ============================================================================
# Test 4: Model Support (opus-4-6 and sonnet-4-6)
# ============================================================================


@pytest.mark.parametrize("model_name,family", [
    ("claude-opus-4-6", "opus"),
    ("claude-sonnet-4-6", "sonnet"),
])
def test_model_family_parsing(model_name, family):
    """Test both opus and sonnet 4-6 models are correctly identified."""
    models = [model_name]
    filtered = filter_latest_claude_models(models)
    assert model_name in filtered


def test_filter_keeps_both_opus_and_sonnet():
    """Test filtering keeps both opus and sonnet when present."""
    models = [
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-haiku-3-5-20241022",
    ]
    
    filtered = filter_latest_claude_models(models, max_per_family={"default": 1, "opus": 3})
    
    # Should keep opus, sonnet, and latest haiku
    assert "claude-opus-4-6" in filtered
    assert "claude-sonnet-4-6" in filtered
    assert "claude-haiku-3-5-20241022" in filtered


def test_filter_opus_versions_with_max_3():
    """Test opus filtering with max_per_family=3 for opus."""
    models = [
        "claude-opus-4-6",
        "claude-opus-3-5-20240229",
        "claude-opus-3-0-20240229",
        "claude-opus-2-1-20230815",
    ]
    
    filtered = filter_latest_claude_models(models, max_per_family={"opus": 3, "default": 1})
    
    # Should keep only the top 3 opus models
    assert len([m for m in filtered if "opus" in m]) == 3
    assert "claude-opus-4-6" in filtered
    assert "claude-opus-3-5-20240229" in filtered
    assert "claude-opus-3-0-20240229" in filtered
    assert "claude-opus-2-1-20230815" not in filtered


def test_model_config_includes_effort_for_4_6():
    """Test that opus-4-6 and sonnet-4-6 configs include 'effort' in supported_settings."""
    from code_puppy.plugins.claude_code_oauth.utils import _build_model_entry
    
    opus_config = _build_model_entry("claude-opus-4-6", "test_token", 200000)
    sonnet_config = _build_model_entry("claude-sonnet-4-6", "test_token", 200000)
    
    assert "effort" in opus_config["supported_settings"]
    assert "effort" in sonnet_config["supported_settings"]
    
    # Verify other settings are also present
    for config in [opus_config, sonnet_config]:
        assert "temperature" in config["supported_settings"]
        assert "extended_thinking" in config["supported_settings"]
        assert "budget_tokens" in config["supported_settings"]


def test_model_config_no_effort_for_older_models():
    """Test that older models don't include 'effort' setting."""
    from code_puppy.plugins.claude_code_oauth.utils import _build_model_entry
    
    haiku_config = _build_model_entry("claude-haiku-3-5-20241022", "test_token", 200000)
    
    assert "effort" not in haiku_config["supported_settings"]
    assert "temperature" in haiku_config["supported_settings"]


# ============================================================================
# Test 5: Error Handling (Cloudflare HTML vs Anthropic JSON)
# ============================================================================


def test_cloudflare_html_error_handling():
    """Test handling of Cloudflare 400 HTML responses (not JSON)."""
    cloudflare_html = """
    <!DOCTYPE html>
    <html>
    <head><title>400 Bad Request</title></head>
    <body>
    <h1>Bad Request</h1>
    <p>Your browser sent a request that this server could not understand.</p>
    </body>
    </html>
    """
    
    with patch("code_puppy.plugins.claude_code_oauth.utils.load_stored_tokens") as mock_load:
        mock_load.return_value = {
            "access_token": "old_token",
            "refresh_token": "refresh_token",
            "expires_in": 3600,
            "expires_at": time.time() - 600,
        }
        
        with patch("code_puppy.plugins.claude_code_oauth.utils.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/html"}  # HTML, not JSON!
            mock_response.text = cloudflare_html
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_post.return_value = mock_response
            
            result = refresh_access_token(force=True)
            
            # Should return None and not crash
            assert result is None


def test_anthropic_json_error_handling():
    """Test handling of proper Anthropic JSON error responses."""
    anthropic_error = {
        "type": "error",
        "error": {
            "type": "invalid_request_error",
            "message": "Invalid refresh token",
        }
    }
    
    with patch("code_puppy.plugins.claude_code_oauth.utils.load_stored_tokens") as mock_load:
        mock_load.return_value = {
            "access_token": "old_token",
            "refresh_token": "invalid_refresh",
            "expires_in": 3600,
            "expires_at": time.time() - 600,
        }
        
        with patch("code_puppy.plugins.claude_code_oauth.utils.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.headers = {"content-type": "application/json"}
            mock_response.text = json.dumps(anthropic_error)
            mock_response.json.return_value = anthropic_error
            mock_post.return_value = mock_response
            
            result = refresh_access_token(force=True)
            
            # Should return None on error
            assert result is None


def test_network_error_handling():
    """Test handling of network errors during token refresh."""
    with patch("code_puppy.plugins.claude_code_oauth.utils.load_stored_tokens") as mock_load:
        mock_load.return_value = {
            "access_token": "old_token",
            "refresh_token": "refresh_token",
            "expires_in": 3600,
            "expires_at": time.time() - 600,
        }
        
        with patch("code_puppy.plugins.claude_code_oauth.utils.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("Network error")
            
            result = refresh_access_token(force=True)
            
            # Should return None and not crash
            assert result is None


def test_fetch_models_html_response_handling():
    """Test handling HTML responses when fetching models (Cloudflare errors)."""
    access_token = "test_token"
    cloudflare_html = "<html><body>Cloudflare error</body></html>"
    
    with patch("code_puppy.plugins.claude_code_oauth.utils.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = cloudflare_html
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response
        
        models = fetch_claude_code_models(access_token)
        
        # Should return None, not crash
        assert models is None


# ============================================================================
# Test 6: Token Refresh Workflow
# ============================================================================


def test_get_valid_access_token_fresh(mock_token_data):
    """Test getting valid token when current token is fresh."""
    with patch("code_puppy.plugins.claude_code_oauth.utils.load_stored_tokens", return_value=mock_token_data):
        token = get_valid_access_token()
        assert token == "test_access_token_abc123"


def test_get_valid_access_token_triggers_refresh(mock_near_expiry_token_data):
    """Test that near-expiry tokens trigger refresh."""
    refreshed_tokens = {
        "access_token": "refreshed_token",
        "refresh_token": "new_refresh",
        "expires_in": 3600,
        "expires_at": time.time() + 3600,
    }
    
    with patch("code_puppy.plugins.claude_code_oauth.utils.load_stored_tokens", return_value=mock_near_expiry_token_data):
        with patch("code_puppy.plugins.claude_code_oauth.utils.refresh_access_token", return_value="refreshed_token"):
            token = get_valid_access_token()
            assert token == "refreshed_token"


def test_get_valid_access_token_refresh_fails_but_not_expired():
    """Test fallback to current token when refresh fails but token not actually expired."""
    near_expiry = {
        "access_token": "current_token",
        "refresh_token": "refresh",
        "expires_in": 3600,
        "expires_at": time.time() + 240,  # 4 minutes (in buffer, but not expired)
    }
    
    with patch("code_puppy.plugins.claude_code_oauth.utils.load_stored_tokens", return_value=near_expiry):
        with patch("code_puppy.plugins.claude_code_oauth.utils.refresh_access_token", return_value=None):
            token = get_valid_access_token()
            # Should fall back to current token since it's not actually expired
            assert token == "current_token"


def test_get_valid_access_token_no_tokens():
    """Test handling when no tokens are stored."""
    with patch("code_puppy.plugins.claude_code_oauth.utils.load_stored_tokens", return_value=None):
        token = get_valid_access_token()
        assert token is None


# ============================================================================
# Test 7: Token Saving
# ============================================================================


def test_save_tokens_success(mock_token_data, tmp_path):
    """Test successful token saving with proper permissions."""
    token_file = tmp_path / "claude_code_oauth.json"
    
    with patch("code_puppy.plugins.claude_code_oauth.utils.get_token_storage_path", return_value=token_file):
        success = save_tokens(mock_token_data)
        
        assert success is True
        assert token_file.exists()
        
        # Verify file contents
        saved_data = json.loads(token_file.read_text())
        assert saved_data["access_token"] == mock_token_data["access_token"]
        
        # Verify file permissions (should be 0o600 - owner read/write only)
        import stat
        file_mode = token_file.stat().st_mode
        assert stat.S_IMODE(file_mode) == 0o600





# ============================================================================
# Manual Integration Test (commented out)
# ============================================================================

"""
# ===========================================================================
# MANUAL INTEGRATION TEST - Requires real credentials
# ===========================================================================
# 
# To run this test with real credentials:
# 1. Uncomment the test below
# 2. Set environment variable: CLAUDE_CODE_TEST_TOKEN=your_real_token
# 3. Run: pytest tests/test_claude_oauth_integration.py::test_real_api_integration -v
#
# This test will make actual API calls to Anthropic's servers.
# ===========================================================================

import os

@pytest.mark.skipif(
    not os.getenv("CLAUDE_CODE_TEST_TOKEN"),
    reason="CLAUDE_CODE_TEST_TOKEN not set - skipping real API test"
)
def test_real_api_integration():
    '''Manual integration test with real API credentials.
    
    This test validates:
    1. Token loading from disk
    2. Token refresh if needed
    3. Model fetching from API
    4. Header construction in real requests
    
    To run:
        export CLAUDE_CODE_TEST_TOKEN=your_actual_token
        pytest tests/test_claude_oauth_integration.py::test_real_api_integration -v
    '''
    import os
    from code_puppy.plugins.claude_code_oauth.utils import (
        fetch_claude_code_models,
        get_valid_access_token,
        save_tokens,
    )
    
    # Optionally save a test token first
    test_token = os.getenv("CLAUDE_CODE_TEST_TOKEN")
    if test_token and test_token != "mock_token":
        # Save token to disk (will use real storage path)
        token_data = {
            "access_token": test_token,
            "refresh_token": "test_refresh",  # Not needed for this test
            "expires_in": 3600,
            "expires_at": time.time() + 3600,
        }
        save_tokens(token_data)
    
    # Test 1: Load token from disk
    token = get_valid_access_token()
    assert token is not None, "Failed to load token"
    print(f"✅ Loaded token: {token[:20]}...")
    
    # Test 2: Fetch models from API
    models = fetch_claude_code_models(token)
    assert models is not None, "Failed to fetch models"
    assert len(models) > 0, "No models returned from API"
    print(f"✅ Fetched {len(models)} models: {models}")
    
    # Test 3: Verify expected models are present
    assert "claude-opus-4-6" in models, "claude-opus-4-6 not in model list"
    assert "claude-sonnet-4-6" in models, "claude-sonnet-4-6 not in model list"
    print("✅ Both opus-4-6 and sonnet-4-6 models are available")
    
    # Test 4: Verify model filtering
    from code_puppy.plugins.claude_code_oauth.utils import filter_latest_claude_models
    filtered = filter_latest_claude_models(models, max_per_family={"default": 1, "opus": 3})
    assert "claude-opus-4-6" in filtered
    assert "claude-sonnet-4-6" in filtered
    print(f"✅ Filtered to {len(filtered)} latest models")
    
    print("\\n🎉 All real API integration tests passed!")

"""


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

def test_save_tokens_uses_storage_path_with_mkdir(tmp_path):
    """Test that save_tokens works when get_token_storage_path provides a valid path."""
    # get_token_storage_path creates its parent dir, so simulate that behavior
    nested_path = tmp_path / "nested" / "dir" / "claude_code_oauth.json"
    nested_path.parent.mkdir(parents=True, exist_ok=True)  # Simulate what get_token_storage_path does
    
    with patch("code_puppy.plugins.claude_code_oauth.utils.get_token_storage_path", return_value=nested_path):
        success = save_tokens({"access_token": "test"})
        
        assert success is True
        assert nested_path.exists()
        
        # Verify content
        saved_data = json.loads(nested_path.read_text())
        assert saved_data["access_token"] == "test"
