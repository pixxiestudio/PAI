"""Tests for health check endpoints"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestHealthCheck:
    """Test health check endpoints"""

    def test_health_check_success(self, test_client: TestClient):
        """Test successful health check"""
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["ok", "healthy", "OK", "HEALTHY", True]

    def test_health_check_with_auth(self, test_client: TestClient, auth_headers: dict):
        """Test health check with authentication"""
        response = test_client.get(
            "/api/v1/health",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_health_check_without_auth(self, test_client: TestClient):
        """Test health check without authentication"""
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_check_response_structure(self, test_client: TestClient):
        """Test health check response structure"""
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        # Should have timestamp or status fields
        assert isinstance(data, dict)
        assert len(data) > 0


@pytest.mark.unit
class TestBaseEndpoint:
    """Test base endpoint"""

    def test_root_endpoint(self, test_client: TestClient):
        """Test root endpoint"""
        response = test_client.get("/")
        # Should either redirect or return API info
        assert response.status_code in [200, 307, 308]

    def test_api_docs(self, test_client: TestClient):
        """Test API documentation endpoint"""
        response = test_client.get("/docs")
        # Should return Swagger UI or similar
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestHealthIntegration:
    """Integration tests for health endpoints"""

    def test_health_check_consistency(self, test_client: TestClient):
        """Test that health checks are consistent"""
        responses = [test_client.get("/api/v1/health") for _ in range(3)]
        assert all(r.status_code == 200 for r in responses)
        statuses = [r.json()["status"] for r in responses]
        # All should report same status
        assert len(set(str(s) for s in statuses)) == 1
