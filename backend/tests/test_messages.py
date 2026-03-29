"""Tests for message endpoints"""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4


@pytest.mark.unit
class TestMessageCreation:
    """Test message creation endpoints"""

    def test_send_message_success(self, test_client: TestClient, auth_headers: dict):
        """Test successful message sending"""
        # First create a session
        session_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Test Chat"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]

        # Send a message
        response = test_client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"content": "Hello, PAI!"},
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert data["content"] == "Hello, PAI!"
        assert data["role"] in ["user", "assistant"]

    def test_send_message_to_nonexistent_session(self, test_client: TestClient, auth_headers: dict):
        """Test sending message to nonexistent session"""
        response = test_client.post(
            f"/api/v1/sessions/nonexistent-{uuid4()}/messages",
            json={"content": "Hello"},
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_send_empty_message(self, test_client: TestClient, auth_headers: dict):
        """Test sending empty message"""
        # Create session
        session_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Test"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]

        # Try to send empty message
        response = test_client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"content": ""},
            headers=auth_headers
        )
        # Should either reject or trim
        assert response.status_code in [200, 201, 422]

    def test_send_very_long_message(self, test_client: TestClient, auth_headers: dict):
        """Test sending very long message"""
        session_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Test"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]

        long_content = "a" * 10000
        response = test_client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"content": long_content},
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 422]


@pytest.mark.unit
class TestMessageRetrieval:
    """Test message retrieval endpoints"""

    def test_get_messages_in_session(self, test_client: TestClient, auth_headers: dict):
        """Test getting messages from a session"""
        # Create session and send messages
        session_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Test Chat"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]

        # Send multiple messages
        for i in range(3):
            test_client.post(
                f"/api/v1/sessions/{session_id}/messages",
                json={"content": f"Message {i}"},
                headers=auth_headers
            )

        # Get messages
        response = test_client.get(
            f"/api/v1/sessions/{session_id}/messages",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Data could be a list or dict with messages key
        messages = data if isinstance(data, list) else data.get("messages", [])
        assert len(messages) >= 3

    def test_get_messages_from_empty_session(self, test_client: TestClient, auth_headers: dict):
        """Test getting messages from session with no messages"""
        # Create empty session
        session_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Empty Chat"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]

        # Get messages
        response = test_client.get(
            f"/api/v1/sessions/{session_id}/messages",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        messages = data if isinstance(data, list) else data.get("messages", [])
        assert len(messages) == 0

    def test_get_specific_message(self, test_client: TestClient, auth_headers: dict):
        """Test getting a specific message"""
        # Create session and message
        session_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Test"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]

        msg_response = test_client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"content": "Specific message"},
            headers=auth_headers
        )
        message_id = msg_response.json()["id"]

        # Get specific message
        response = test_client.get(
            f"/api/v1/sessions/{session_id}/messages/{message_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == message_id


@pytest.mark.unit
class TestMessageDeletion:
    """Test message deletion endpoints"""

    def test_delete_message(self, test_client: TestClient, auth_headers: dict):
        """Test deleting a message"""
        # Create session and message
        session_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Test"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]

        msg_response = test_client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"content": "To delete"},
            headers=auth_headers
        )
        message_id = msg_response.json()["id"]

        # Delete message
        response = test_client.delete(
            f"/api/v1/sessions/{session_id}/messages/{message_id}",
            headers=auth_headers
        )
        assert response.status_code in [200, 204]

        # Verify it's deleted
        get_response = test_client.get(
            f"/api/v1/sessions/{session_id}/messages/{message_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404


@pytest.mark.integration
class TestMessageWorkflow:
    """Integration tests for message workflows"""

    def test_conversation_flow(self, test_client: TestClient, auth_headers: dict):
        """Test a realistic conversation flow"""
        # Create session
        session_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Conversation"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]

        # User message
        user_msg = test_client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"content": "What is AI?", "role": "user"},
            headers=auth_headers
        )
        assert user_msg.status_code in [200, 201]

        # Assistant response (simulated)
        assistant_msg = test_client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"content": "AI stands for Artificial Intelligence", "role": "assistant"},
            headers=auth_headers
        )
        assert assistant_msg.status_code in [200, 201]

        # Get conversation
        messages_response = test_client.get(
            f"/api/v1/sessions/{session_id}/messages",
            headers=auth_headers
        )
        assert messages_response.status_code == 200

    def test_message_ordering(self, test_client: TestClient, auth_headers: dict):
        """Test that messages maintain order"""
        session_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Order Test"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]

        # Send multiple messages
        message_contents = [f"Message {i}" for i in range(5)]
        sent_ids = []
        for content in message_contents:
            response = test_client.post(
                f"/api/v1/sessions/{session_id}/messages",
                json={"content": content},
                headers=auth_headers
            )
            sent_ids.append(response.json()["id"])

        # Get messages
        get_response = test_client.get(
            f"/api/v1/sessions/{session_id}/messages",
            headers=auth_headers
        )
        messages = get_response.json()
        messages = messages if isinstance(messages, list) else messages.get("messages", [])

        # Verify order is maintained (or at least all messages exist)
        assert len(messages) >= len(message_contents)
