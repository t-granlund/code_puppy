"""Tests for RemoteProtocolError and connection error failover detection."""

import pytest
from code_puppy.failover_model import _is_failover_error


class TestRemoteProtocolErrorDetection:
    """Test that RemoteProtocolError and connection errors trigger failover."""

    def test_remote_protocol_error_by_type_name(self):
        """RemoteProtocolError should trigger failover by type name."""
        class RemoteProtocolError(Exception):
            pass
        
        exc = RemoteProtocolError("peer closed connection")
        assert _is_failover_error(exc) is True

    def test_httpx_remote_protocol_error_message(self):
        """httpx.RemoteProtocolError message should trigger failover."""
        exc = Exception(
            "httpx.RemoteProtocolError: peer closed connection without "
            "sending complete message body (incomplete chunked read)"
        )
        assert _is_failover_error(exc) is True

    def test_incomplete_chunked_read(self):
        """'incomplete chunked read' message should trigger failover."""
        exc = Exception("incomplete chunked read")
        assert _is_failover_error(exc) is True

    def test_peer_closed_connection(self):
        """'peer closed connection' message should trigger failover."""
        exc = Exception("peer closed connection without sending")
        assert _is_failover_error(exc) is True

    def test_connection_error_by_type_name(self):
        """ConnectionError should trigger failover by type name."""
        class ConnectionError(Exception):
            pass
        
        exc = ConnectionError("connection failed")
        assert _is_failover_error(exc) is True

    def test_connection_reset(self):
        """'connection reset' message should trigger failover."""
        exc = Exception("connection reset by peer")
        assert _is_failover_error(exc) is True

    def test_connection_refused(self):
        """'connection refused' message should trigger failover."""
        exc = Exception("connection refused")
        assert _is_failover_error(exc) is True

    def test_timeout_error_by_type_name(self):
        """TimeoutError should trigger failover by type name."""
        class TimeoutError(Exception):
            pass
        
        exc = TimeoutError("request timed out")
        assert _is_failover_error(exc) is True

    def test_unrelated_error_no_failover(self):
        """Unrelated errors should NOT trigger failover."""
        exc = Exception("some random error that's not retriable")
        assert _is_failover_error(exc) is False

    def test_value_error_no_failover(self):
        """ValueError should NOT trigger failover."""
        exc = ValueError("invalid argument")
        assert _is_failover_error(exc) is False


class TestExistingFailoverBehavior:
    """Ensure existing failover behavior still works."""

    def test_rate_limit_error(self):
        """RateLimitError should trigger failover."""
        class RateLimitError(Exception):
            pass
        
        exc = RateLimitError("rate limited")
        assert _is_failover_error(exc) is True

    def test_unexpected_model_behavior(self):
        """UnexpectedModelBehavior should trigger failover."""
        class UnexpectedModelBehavior(Exception):
            pass
        
        exc = UnexpectedModelBehavior("output validation failed")
        assert _is_failover_error(exc) is True

    def test_tool_retry_error(self):
        """ToolRetryError should trigger failover."""
        class ToolRetryError(Exception):
            pass
        
        exc = ToolRetryError("tool call failed")
        assert _is_failover_error(exc) is True

    def test_429_in_message(self):
        """'429' in message should trigger failover."""
        exc = Exception("HTTP 429 Too Many Requests")
        assert _is_failover_error(exc) is True

    def test_exceeded_maximum_retries(self):
        """'exceeded maximum retries' should trigger failover."""
        exc = Exception("Exceeded maximum retries (3) for output validation")
        assert _is_failover_error(exc) is True
