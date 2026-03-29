"""Tests for session endpoints"""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4


@pytest.mark.unit
class TestSessionCreation:
    """Test session creation endpoints"""

    def test_create_session_success(self, test_client: TestClient, auth_headers: dict):
        """Test successful session creation"""
        response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Test Chat"},
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert data["title"] == "Test Chat"

    def test_create_session_without_title(self, test_client: TestClient, auth_headers: dict):
        """Test creating session without title"""
        response = test_client.post(
            "/api/v1/sessions",
            json={},
            headers=auth_headers
        )
        # Should either use default or require title
        assert response.status_code in [200, 201, 422]

    def test_create_multiple_sessions(self, test_client: TestClient, auth_headers: dict):
        """Test creating multiple sessions"""
        session_ids = []
        for i in range(3):
            response = test_client.post(
                "/api/v1/sessions",
                json={"title": f"Chat {i}"},
                headers=auth_headers
            )
            assert response.status_code in [200, 201]
            session_ids.append(response.json()["id"])

        # All IDs should be unique
        assert len(set(session_ids)) == 3


@pytest.mark.unit
class TestSessionRetrieval:
    """Test session retrieval endpoints"""

    def test_get_sessions_list(self, test_client: TestClient, auth_headers: dict):
        """Test getting list of sessions"""
        # Create a session first
        create_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Test Chat"},
            headers=auth_headers
        )
        assert create_response.status_code in [200, 201]

        # Get sessions list
        response = test_client.get(
            "/api/v1/sessions",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "sessions" in data

    def test_get_session_details(self, test_client: TestClient, auth_headers: dict):
        """Test getting session details"""
        # Create session
        create_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Test Chat"},
            headers=auth_headers
        )
        session_id = create_response.json()["id"]

        # Get session details
        response = test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["title"] == "Test Chat"

    def test_get_nonexistent_session(self, test_client: TestClient, auth_headers: dict):
        """Test getting nonexistent session"""
        response = test_client.get(
            f"/api/v1/sessions/nonexistent-id-{uuid4()}",
            headers=auth_headers
        )
        assert response.status_code == 404


@pytest.mark.unit
class TestSessionUpdates:
    """Test session update endpoints"""

    def test_update_session_title(self, test_client: TestClient, auth_headers: dict):
        """Test updating session title"""
        # Create session
        create_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Original Title"},
            headers=auth_headers
        )
        session_id = create_response.json()["id"]

        # Update session
        response = test_client.put(
            f"/api/v1/sessions/{session_id}",
            json={"title": "Updated Title"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    def test_update_nonexistent_session(self, test_client: TestClient, auth_headers: dict):
        """Test updating nonexistent session"""
        response = test_client.put(
            f"/api/v1/sessions/nonexistent-{uuid4()}",
            json={"title": "New Title"},
            headers=auth_headers
        )
        assert response.status_code == 404


@pytest.mark.unit
class TestSessionDeletion:
    """Test session deletion endpoints"""

    def test_delete_session(self, test_client: TestClient, auth_headers: dict):
        """Test deleting a session"""
        # Create session
        create_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "To Delete"},
            headers=auth_headers
        )
        session_id = create_response.json()["id"]

        # Delete session
        response = test_client.delete(
            f"/api/v1/sessions/{session_id}",
            headers=auth_headers
        )
        assert response.status_code == 200 or response.status_code == 204

        # Verify it's deleted
        get_response = test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_delete_nonexistent_session(self, test_client: TestClient, auth_headers: dict):
        """Test deleting nonexistent session"""
        response = test_client.delete(
            f"/api/v1/sessions/nonexistent-{uuid4()}",
            headers=auth_headers
        )
        assert response.status_code == 404


@pytest.mark.integration
class TestSessionWorkflow:
    """Integration tests for session workflows"""

    def test_complete_session_lifecycle(self, test_client: TestClient, auth_headers: dict):
        """Test complete session lifecycle"""
        # Create
        create_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Lifecycle Test"},
            headers=auth_headers
        )
        assert create_response.status_code in [200, 201]
        session_id = create_response.json()["id"]

        # Read
        get_response = test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200

        # Update
        update_response = test_client.put(
            f"/api/v1/sessions/{session_id}",
            json={"title": "Updated Lifecycle Test"},
            headers=auth_headers
        )
        assert update_response.status_code == 200

        # Delete
        delete_response = test_client.delete(
            f"/api/v1/sessions/{session_id}",
            headers=auth_headers
        )
        assert delete_response.status_code in [200, 204]

    def test_session_isolation(self, test_client: TestClient, valid_user_id: str):
        """Test that sessions are isolated by user"""
        # Create sessions for two users (if multi-user support exists)
        # For now, just test that sessions can be created independently
        response1 = test_client.post(
            "/api/v1/auth/token",
            json={"user_id": valid_user_id}
        )
        headers1 = {"Authorization": f"Bearer {response1.json()['access_token']}"}

        response2 = test_client.post(
            "/api/v1/auth/token",
            json={"user_id": "different-user"}
        )
        headers2 = {"Authorization": f"Bearer {response2.json()['access_token']}"}

        # Create sessions for each user
        session1 = test_client.post(
            "/api/v1/sessions",
            json={"title": "User 1 Chat"},
            headers=headers1
        )
        session2 = test_client.post(
            "/api/v1/sessions",
            json={"title": "User 2 Chat"},
            headers=headers2
        )

        assert session1.status_code in [200, 201]
        assert session2.status_code in [200, 201]
        assert session1.json()["id"] != session2.json()["id"]
