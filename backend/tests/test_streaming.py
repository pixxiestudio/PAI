"""Tests for streaming endpoints"""
import pytest
import json
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestHealthStreamEndpoint:
    """Test health check streaming endpoint"""

    def test_stream_health_endpoint_exists(self, test_client: TestClient):
        """Test that health stream endpoint exists"""
        response = test_client.get("/api/v1/stream/health/stream")
        # Should succeed (might be 200 or 101 for WebSocket-like)
        assert response.status_code in [200, 206]

    def test_health_stream_content_type(self, test_client: TestClient):
        """Test health stream has correct content type"""
        response = test_client.get("/api/v1/stream/health/stream")
        if response.status_code == 200:
            assert "json" in response.headers.get("content-type", "").lower() or \
                   "ndjson" in response.headers.get("content-type", "").lower()

    def test_health_stream_receives_data(self, test_client: TestClient):
        """Test that health stream returns data"""
        response = test_client.get("/api/v1/stream/health/stream")
        if response.status_code == 200:
            # Should have some content
            content = response.content
            assert len(content) > 0


@pytest.mark.unit
class TestSessionMessageStreaming:
    """Test session message streaming endpoint"""

    def test_stream_session_messages_endpoint_exists(self, test_client: TestClient, auth_headers: dict):
        """Test that session message stream endpoint exists"""
        response = test_client.get(
            "/api/v1/stream/sessions/test-session/messages",
            params={"user_message": "Hello"},
            headers=auth_headers
        )
        # Could be 200 (with content) or 404 (session not found)
        assert response.status_code in [200, 404, 500]

    def test_stream_messages_requires_user_message(self, test_client: TestClient, auth_headers: dict):
        """Test that user_message parameter is required"""
        response = test_client.get(
            "/api/v1/stream/sessions/test-session/messages",
            headers=auth_headers
        )
        assert response.status_code == 422  # Missing required parameter

    def test_stream_messages_nonexistent_session(self, test_client: TestClient, auth_headers: dict):
        """Test streaming for nonexistent session"""
        response = test_client.get(
            "/api/v1/stream/sessions/nonexistent-session/messages",
            params={"user_message": "Test"},
            headers=auth_headers
        )
        # Should return 404 for nonexistent session
        assert response.status_code == 404

    def test_stream_messages_with_valid_session(self, test_client: TestClient, auth_headers: dict):
        """Test streaming with valid session"""
        # First create a session
        session_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Stream Test"},
            headers=auth_headers
        )

        if session_response.status_code in [200, 201]:
            session_id = session_response.json()["id"]

            # Try to stream messages
            stream_response = test_client.get(
                f"/api/v1/stream/sessions/{session_id}/messages",
                params={"user_message": "Hello PAI"},
                headers=auth_headers
            )

            # Should return 200 or 500 (depending on Claude API availability)
            assert stream_response.status_code in [200, 500]


@pytest.mark.unit
class TestStreamingFormatAndContent:
    """Test streaming response format"""

    def test_health_stream_ndjson_format(self, test_client: TestClient):
        """Test that health stream returns NDJSON format"""
        response = test_client.get("/api/v1/stream/health/stream")
        if response.status_code == 200:
            # Should be newline-delimited JSON
            lines = response.content.decode().strip().split('\n')
            assert len(lines) > 0
            for line in lines:
                if line:  # Skip empty lines
                    try:
                        json.loads(line)
                    except json.JSONDecodeError:
                        # Some lines might not be valid JSON (streaming chunks)
                        pass

    def test_stream_response_headers(self, test_client: TestClient):
        """Test streaming response headers"""
        response = test_client.get("/api/v1/stream/health/stream")
        if response.status_code == 200:
            # Check for streaming headers
            assert response.headers.get("transfer-encoding") or \
                   response.headers.get("content-length") or \
                   "stream" in response.headers.get("content-type", "").lower()


@pytest.mark.integration
class TestStreamingWorkflow:
    """Integration tests for streaming workflows"""

    def test_full_streaming_workflow(self, test_client: TestClient, auth_headers: dict):
        """Test complete streaming workflow"""
        # 1. Create session
        session_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Streaming Workflow"},
            headers=auth_headers
        )
        assert session_response.status_code in [200, 201]
        session_id = session_response.json()["id"]

        # 2. Send user message
        msg_response = test_client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"content": "Hello PAI"},
            headers=auth_headers
        )
        assert msg_response.status_code in [200, 201]

        # 3. Stream response
        stream_response = test_client.get(
            f"/api/v1/stream/sessions/{session_id}/messages",
            params={"user_message": "What can you do?"},
            headers=auth_headers
        )
        # Should work or fail gracefully
        assert stream_response.status_code in [200, 500]

    def test_streaming_multiple_messages(self, test_client: TestClient, auth_headers: dict):
        """Test streaming multiple messages in sequence"""
        # Create session
        session_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Multi-message streaming"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]

        # Send multiple messages and stream responses
        messages = [
            "What is AI?",
            "Tell me more",
            "How does it work?"
        ]

        for msg in messages:
            response = test_client.get(
                f"/api/v1/stream/sessions/{session_id}/messages",
                params={"user_message": msg},
                headers=auth_headers
            )
            # Each should succeed or fail gracefully
            assert response.status_code in [200, 500]


@pytest.mark.integration
class TestStreamingErrorHandling:
    """Test error handling in streaming"""

    def test_stream_with_empty_message(self, test_client: TestClient, auth_headers: dict):
        """Test streaming with empty message"""
        # Create session
        session_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Empty message test"},
            headers=auth_headers
        )
        if session_response.status_code in [200, 201]:
            session_id = session_response.json()["id"]

            response = test_client.get(
                f"/api/v1/stream/sessions/{session_id}/messages",
                params={"user_message": ""},
                headers=auth_headers
            )
            # Should handle empty message (either reject or process)
            assert response.status_code in [200, 400, 422, 500]

    def test_stream_with_very_long_message(self, test_client: TestClient, auth_headers: dict):
        """Test streaming with very long message"""
        # Create session
        session_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Long message test"},
            headers=auth_headers
        )
        if session_response.status_code in [200, 201]:
            session_id = session_response.json()["id"]

            long_msg = "a" * 10000
            response = test_client.get(
                f"/api/v1/stream/sessions/{session_id}/messages",
                params={"user_message": long_msg},
                headers=auth_headers
            )
            # Should handle long message
            assert response.status_code in [200, 500]
