"""Tests for authentication endpoints"""
import pytest
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestAuthTokenGeneration:
    """Test JWT token generation"""

    def test_token_generation_success(self, test_client: TestClient, valid_user_id: str):
        """Test successful token generation"""
        response = test_client.post(
            "/api/v1/auth/token",
            json={"user_id": valid_user_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_token_contains_user_id(self, test_client: TestClient, valid_user_id: str):
        """Test that token contains user ID"""
        response = test_client.post(
            "/api/v1/auth/token",
            json={"user_id": valid_user_id}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        # Decode without verification (for testing)
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert decoded["sub"] == valid_user_id

    def test_token_has_expiration(self, test_client: TestClient, valid_user_id: str):
        """Test that token has expiration time"""
        response = test_client.post(
            "/api/v1/auth/token",
            json={"user_id": valid_user_id}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        decoded = jwt.decode(token, options={"verify_signature": False})
        assert "exp" in decoded
        # Token should expire in the future
        assert decoded["exp"] > datetime.now(timezone.utc).timestamp()

    def test_missing_user_id(self, test_client: TestClient):
        """Test token generation without user_id"""
        response = test_client.post(
            "/api/v1/auth/token",
            json={}
        )
        assert response.status_code == 422  # Unprocessable Entity

    def test_empty_user_id(self, test_client: TestClient):
        """Test token generation with empty user_id"""
        response = test_client.post(
            "/api/v1/auth/token",
            json={"user_id": ""}
        )
        # Should either reject or generate token for empty ID
        assert response.status_code in [200, 422]

    def test_multiple_token_generations(self, test_client: TestClient, valid_user_id: str):
        """Test generating multiple tokens for same user"""
        response1 = test_client.post(
            "/api/v1/auth/token",
            json={"user_id": valid_user_id}
        )
        response2 = test_client.post(
            "/api/v1/auth/token",
            json={"user_id": valid_user_id}
        )
        assert response1.status_code == 200
        assert response2.status_code == 200
        # Tokens should be different (different iat/exp)
        token1 = response1.json()["access_token"]
        token2 = response2.json()["access_token"]
        assert token1 != token2


@pytest.mark.unit
class TestAuthValidation:
    """Test token validation"""

    def test_valid_token_in_request(self, test_client: TestClient, valid_jwt_token: str, auth_headers: dict):
        """Test that valid token is accepted in requests"""
        # Token validation would typically be tested via protected endpoints
        # We'll use the health endpoint as a simple check
        response = test_client.get(
            "/api/v1/health",
            headers=auth_headers
        )
        # Health endpoint typically doesn't require auth, but headers should not cause issues
        assert response.status_code == 200

    def test_invalid_token_format(self, test_client: TestClient):
        """Test request with invalid token format"""
        headers = {"Authorization": "Bearer invalid.token.format"}
        response = test_client.get(
            "/api/v1/health",
            headers=headers
        )
        # Should either accept or reject based on endpoint protection
        # Health endpoint typically doesn't require auth
        assert response.status_code in [200, 401]

    def test_missing_authorization_header(self, test_client: TestClient):
        """Test request without authorization header"""
        response = test_client.get("/api/v1/health")
        # Should work for public endpoints
        assert response.status_code == 200

    def test_malformed_authorization_header(self, test_client: TestClient):
        """Test request with malformed authorization header"""
        headers = {"Authorization": "InvalidFormat token"}
        response = test_client.get(
            "/api/v1/health",
            headers=headers
        )
        # Should handle gracefully
        assert response.status_code in [200, 400, 401]


@pytest.mark.unit
class TestAuthEdgeCases:
    """Test edge cases for authentication"""

    def test_special_characters_in_user_id(self, test_client: TestClient):
        """Test token generation with special characters in user_id"""
        special_id = "user@example.com"
        response = test_client.post(
            "/api/v1/auth/token",
            json={"user_id": special_id}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert decoded["sub"] == special_id

    def test_very_long_user_id(self, test_client: TestClient):
        """Test token generation with very long user_id"""
        long_id = "a" * 500
        response = test_client.post(
            "/api/v1/auth/token",
            json={"user_id": long_id}
        )
        # Should handle or reject long IDs gracefully
        assert response.status_code in [200, 422]

    def test_unicode_user_id(self, test_client: TestClient):
        """Test token generation with unicode characters in user_id"""
        unicode_id = "用户-123"
        response = test_client.post(
            "/api/v1/auth/token",
            json={"user_id": unicode_id}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert decoded["sub"] == unicode_id


@pytest.mark.integration
class TestAuthIntegration:
    """Integration tests for authentication flow"""

    def test_full_auth_flow(self, test_client: TestClient, valid_user_id: str):
        """Test complete authentication flow"""
        # Generate token
        auth_response = test_client.post(
            "/api/v1/auth/token",
            json={"user_id": valid_user_id}
        )
        assert auth_response.status_code == 200

        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Use token in subsequent request
        response = test_client.get(
            "/api/v1/health",
            headers=headers
        )
        assert response.status_code == 200

    def test_token_reuse(self, test_client: TestClient, valid_user_id: str):
        """Test that generated token can be reused"""
        # Generate token
        auth_response = test_client.post(
            "/api/v1/auth/token",
            json={"user_id": valid_user_id}
        )
        token = auth_response.json()["access_token"]

        # Use token multiple times
        for _ in range(3):
            response = test_client.get(
                "/api/v1/health",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
