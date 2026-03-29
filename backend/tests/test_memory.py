"""Tests for memory endpoints"""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4


@pytest.mark.unit
class TestMemoryCreation:
    """Test memory creation endpoints"""

    def test_save_memory_success(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test successful memory saving"""
        response = test_client.post(
            f"/api/v1/users/{valid_user_id}/memories",
            json={
                "content": "I prefer coffee in the morning",
                "category": "preferences",
                "importance": 0.8
            },
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert data["content"] == "I prefer coffee in the morning"
        assert data["category"] == "preferences"

    def test_save_memory_minimal(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test saving memory with minimal data"""
        response = test_client.post(
            f"/api/v1/users/{valid_user_id}/memories",
            json={"content": "Simple fact"},
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 422]

    def test_save_empty_memory(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test saving empty memory"""
        response = test_client.post(
            f"/api/v1/users/{valid_user_id}/memories",
            json={"content": ""},
            headers=auth_headers
        )
        assert response.status_code in [422]  # Should be rejected


@pytest.mark.unit
class TestMemoryRetrieval:
    """Test memory retrieval endpoints"""

    def test_get_memories(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test getting list of memories"""
        # Save a memory first
        test_client.post(
            f"/api/v1/users/{valid_user_id}/memories",
            json={
                "content": "Test memory",
                "category": "knowledge",
                "importance": 0.5
            },
            headers=auth_headers
        )

        # Get memories
        response = test_client.get(
            f"/api/v1/users/{valid_user_id}/memories",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        memories = data if isinstance(data, list) else data.get("memories", [])
        assert isinstance(memories, list)

    def test_get_memories_by_category(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test getting memories filtered by category"""
        # Save memories in different categories
        test_client.post(
            f"/api/v1/users/{valid_user_id}/memories",
            json={"content": "Preference", "category": "preferences"},
            headers=auth_headers
        )
        test_client.post(
            f"/api/v1/users/{valid_user_id}/memories",
            json={"content": "Knowledge", "category": "knowledge"},
            headers=auth_headers
        )

        # Get filtered memories
        response = test_client.get(
            f"/api/v1/users/{valid_user_id}/memories?category=preferences",
            headers=auth_headers
        )
        assert response.status_code == 200


@pytest.mark.unit
class TestMemoryUpdates:
    """Test memory update endpoints"""

    def test_update_memory_importance(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test updating memory importance"""
        # Save memory
        save_response = test_client.post(
            f"/api/v1/users/{valid_user_id}/memories",
            json={
                "content": "Important fact",
                "importance": 0.5
            },
            headers=auth_headers
        )
        memory_id = save_response.json()["id"]

        # Update importance
        response = test_client.put(
            f"/api/v1/users/{valid_user_id}/memories/{memory_id}",
            json={"importance": 0.9},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["importance"] == 0.9

    def test_update_memory_content(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test updating memory content"""
        save_response = test_client.post(
            f"/api/v1/users/{valid_user_id}/memories",
            json={"content": "Original content"},
            headers=auth_headers
        )
        memory_id = save_response.json()["id"]

        response = test_client.put(
            f"/api/v1/users/{valid_user_id}/memories/{memory_id}",
            json={"content": "Updated content"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["content"] == "Updated content"


@pytest.mark.unit
class TestMemoryDeletion:
    """Test memory deletion endpoints"""

    def test_delete_memory(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test deleting a memory"""
        save_response = test_client.post(
            f"/api/v1/users/{valid_user_id}/memories",
            json={"content": "To delete"},
            headers=auth_headers
        )
        memory_id = save_response.json()["id"]

        # Delete
        response = test_client.delete(
            f"/api/v1/users/{valid_user_id}/memories/{memory_id}",
            headers=auth_headers
        )
        assert response.status_code in [200, 204]

        # Verify deleted
        get_response = test_client.get(
            f"/api/v1/users/{valid_user_id}/memories/{memory_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404


@pytest.mark.integration
class TestMemoryWorkflow:
    """Integration tests for memory workflows"""

    def test_memory_lifecycle(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test complete memory lifecycle"""
        # Create
        create_response = test_client.post(
            f"/api/v1/users/{valid_user_id}/memories",
            json={"content": "Test", "importance": 0.5},
            headers=auth_headers
        )
        assert create_response.status_code in [200, 201]
        memory_id = create_response.json()["id"]

        # Read
        get_response = test_client.get(
            f"/api/v1/users/{valid_user_id}/memories/{memory_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200

        # Update
        update_response = test_client.put(
            f"/api/v1/users/{valid_user_id}/memories/{memory_id}",
            json={"importance": 0.9},
            headers=auth_headers
        )
        assert update_response.status_code == 200

        # Delete
        delete_response = test_client.delete(
            f"/api/v1/users/{valid_user_id}/memories/{memory_id}",
            headers=auth_headers
        )
        assert delete_response.status_code in [200, 204]

    def test_bulk_memory_operations(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test creating and managing multiple memories"""
        memory_ids = []

        # Create 5 memories
        for i in range(5):
            response = test_client.post(
                f"/api/v1/users/{valid_user_id}/memories",
                json={
                    "content": f"Memory {i}",
                    "category": "knowledge",
                    "importance": 0.5 + (i * 0.1)
                },
                headers=auth_headers
            )
            assert response.status_code in [200, 201]
            memory_ids.append(response.json()["id"])

        # Get all memories
        get_response = test_client.get(
            f"/api/v1/users/{valid_user_id}/memories",
            headers=auth_headers
        )
        assert get_response.status_code == 200

        # Update one
        update_response = test_client.put(
            f"/api/v1/users/{valid_user_id}/memories/{memory_ids[0]}",
            json={"importance": 1.0},
            headers=auth_headers
        )
        assert update_response.status_code == 200

        # Delete one
        delete_response = test_client.delete(
            f"/api/v1/users/{valid_user_id}/memories/{memory_ids[1]}",
            headers=auth_headers
        )
        assert delete_response.status_code in [200, 204]
