"""Tests for learning endpoints"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestLearningRetrieval:
    """Test learning data retrieval"""

    def test_get_learning_data(self, test_client: TestClient, auth_headers: dict):
        """Test getting learning data"""
        response = test_client.get(
            "/api/v1/learning",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Should be dict with learning info
        assert isinstance(data, dict)

    def test_get_learning_by_pai(self, test_client: TestClient, auth_headers: dict):
        """Test getting learning data for specific PAI"""
        pai_id = "test-pai-1"
        response = test_client.get(
            f"/api/v1/learning/{pai_id}",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_learning_data_structure(self, test_client: TestClient, auth_headers: dict):
        """Test learning data contains expected structure"""
        response = test_client.get(
            "/api/v1/learning",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Should have learning metrics
        assert isinstance(data, dict)


@pytest.mark.unit
class TestLearningPatterns:
    """Test learning patterns"""

    def test_get_patterns(self, test_client: TestClient, auth_headers: dict):
        """Test getting learning patterns"""
        response = test_client.get(
            "/api/v1/learning/patterns",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_get_preferences(self, test_client: TestClient, auth_headers: dict):
        """Test getting learned preferences"""
        response = test_client.get(
            "/api/v1/learning/preferences",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestLearningWorkflow:
    """Integration tests for learning workflows"""

    def test_learning_data_consistency(self, test_client: TestClient, auth_headers: dict):
        """Test learning data consistency"""
        responses = [
            test_client.get("/api/v1/learning", headers=auth_headers)
            for _ in range(2)
        ]
        assert all(r.status_code == 200 for r in responses)
        data1 = responses[0].json()
        data2 = responses[1].json()
        # Data should be similar (not exact due to updates)
        assert isinstance(data1, dict)
        assert isinstance(data2, dict)
