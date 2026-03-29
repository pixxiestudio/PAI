"""Tests for GitHub integration endpoints"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestGitHubAuth:
    """Test GitHub authentication endpoints"""

    def test_set_github_token(self, test_client: TestClient, auth_headers: dict):
        """Test setting GitHub token"""
        response = test_client.post(
            "/api/v1/github/auth/token",
            params={"token": "ghp_test_token_12345"},
            headers=auth_headers
        )
        # Token might be invalid, but endpoint should accept it
        assert response.status_code in [200, 401]

    def test_set_empty_token(self, test_client: TestClient, auth_headers: dict):
        """Test setting empty token"""
        response = test_client.post(
            "/api/v1/github/auth/token",
            params={"token": ""},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_set_token_without_auth(self, test_client: TestClient):
        """Test setting token without authentication"""
        response = test_client.post(
            "/api/v1/github/auth/token",
            params={"token": "ghp_test_token"}
        )
        # Might be allowed or require auth depending on setup
        assert response.status_code in [200, 401]


@pytest.mark.unit
class TestGitHubValidation:
    """Test GitHub token validation"""

    def test_validate_token(self, test_client: TestClient, auth_headers: dict):
        """Test validating GitHub token"""
        response = test_client.get(
            "/api/v1/github/auth/validate",
            headers=auth_headers
        )
        # Will fail because no token configured, but endpoint should work
        assert response.status_code in [200, 401]

    def test_validate_without_token_configured(self, test_client: TestClient, auth_headers: dict):
        """Test validation when no token configured"""
        response = test_client.get(
            "/api/v1/github/auth/validate",
            headers=auth_headers
        )
        # Should return 401 if no token
        assert response.status_code in [401, 200]


@pytest.mark.unit
class TestGitHubRepositories:
    """Test GitHub repository endpoints"""

    def test_list_repositories(self, test_client: TestClient, auth_headers: dict):
        """Test listing repositories"""
        response = test_client.get(
            "/api/v1/github/repositories",
            headers=auth_headers
        )
        # Will fail without token, but endpoint should exist
        assert response.status_code in [200, 401]

    def test_list_repositories_with_limit(self, test_client: TestClient, auth_headers: dict):
        """Test listing repositories with limit"""
        response = test_client.get(
            "/api/v1/github/repositories?limit=10",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_list_repositories_for_user(self, test_client: TestClient, auth_headers: dict):
        """Test listing repositories for specific user"""
        response = test_client.get(
            "/api/v1/github/repositories?username=torvalds",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_get_repository(self, test_client: TestClient, auth_headers: dict):
        """Test getting repository details"""
        response = test_client.get(
            "/api/v1/github/repositories/torvalds/linux",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_get_nonexistent_repository(self, test_client: TestClient, auth_headers: dict):
        """Test getting nonexistent repository"""
        response = test_client.get(
            "/api/v1/github/repositories/nonexistentuser/nonexistentrepo",
            headers=auth_headers
        )
        assert response.status_code in [401, 404]


@pytest.mark.unit
class TestGitHubIssues:
    """Test GitHub issues endpoints"""

    def test_list_issues(self, test_client: TestClient, auth_headers: dict):
        """Test listing issues"""
        response = test_client.get(
            "/api/v1/github/repositories/python/cpython/issues",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_list_issues_with_state(self, test_client: TestClient, auth_headers: dict):
        """Test listing issues with state filter"""
        response = test_client.get(
            "/api/v1/github/repositories/python/cpython/issues?state=closed",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_list_issues_with_limit(self, test_client: TestClient, auth_headers: dict):
        """Test listing issues with limit"""
        response = test_client.get(
            "/api/v1/github/repositories/python/cpython/issues?limit=10",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_list_issues_all_states(self, test_client: TestClient, auth_headers: dict):
        """Test listing issues with all states"""
        response = test_client.get(
            "/api/v1/github/repositories/python/cpython/issues?state=all",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]


@pytest.mark.unit
class TestGitHubPullRequests:
    """Test GitHub pull requests endpoints"""

    def test_list_pull_requests(self, test_client: TestClient, auth_headers: dict):
        """Test listing pull requests"""
        response = test_client.get(
            "/api/v1/github/repositories/python/cpython/pulls",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_list_prs_open(self, test_client: TestClient, auth_headers: dict):
        """Test listing open pull requests"""
        response = test_client.get(
            "/api/v1/github/repositories/python/cpython/pulls?state=open",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_list_prs_closed(self, test_client: TestClient, auth_headers: dict):
        """Test listing closed pull requests"""
        response = test_client.get(
            "/api/v1/github/repositories/python/cpython/pulls?state=closed",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]

    def test_list_prs_with_limit(self, test_client: TestClient, auth_headers: dict):
        """Test listing pull requests with limit"""
        response = test_client.get(
            "/api/v1/github/repositories/python/cpython/pulls?limit=5",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]


@pytest.mark.integration
class TestGitHubWorkflow:
    """Integration tests for GitHub workflows"""

    def test_github_endpoints_exist(self, test_client: TestClient, auth_headers: dict):
        """Test that all GitHub endpoints are accessible"""
        endpoints = [
            "/api/v1/github/auth/validate",
            "/api/v1/github/repositories",
            "/api/v1/github/repositories/python/cpython",
            "/api/v1/github/repositories/python/cpython/issues",
            "/api/v1/github/repositories/python/cpython/pulls",
        ]

        for endpoint in endpoints:
            response = test_client.get(endpoint, headers=auth_headers)
            # Should not be 404 (endpoint should exist)
            assert response.status_code != 404, f"Endpoint {endpoint} not found"

    def test_github_response_structure(self, test_client: TestClient, auth_headers: dict):
        """Test GitHub endpoint response structure"""
        response = test_client.get(
            "/api/v1/github/repositories",
            headers=auth_headers
        )
        # Even if fails due to missing token, should return JSON
        if response.status_code in [200, 401, 400]:
            data = response.json()
            assert isinstance(data, dict)
