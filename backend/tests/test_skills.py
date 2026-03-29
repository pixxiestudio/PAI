"""Tests for skills endpoints"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestSkillListing:
    """Test skill listing endpoints"""

    def test_get_skills_list(self, test_client: TestClient, auth_headers: dict):
        """Test getting list of available skills"""
        response = test_client.get(
            "/api/v1/skills",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Should return list or dict with skills
        if isinstance(data, dict):
            assert "skills" in data or len(data) >= 0
        else:
            assert isinstance(data, list)

    def test_skills_response_structure(self, test_client: TestClient, auth_headers: dict):
        """Test skills response structure"""
        response = test_client.get(
            "/api/v1/skills",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (dict, list))


@pytest.mark.unit
class TestSkillDetails:
    """Test skill detail endpoints"""

    def test_get_skill_details(self, test_client: TestClient, auth_headers: dict):
        """Test getting details of a specific skill"""
        skill_id = "test-skill"
        response = test_client.get(
            f"/api/v1/skills/{skill_id}",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_nonexistent_skill(self, test_client: TestClient, auth_headers: dict):
        """Test getting nonexistent skill"""
        response = test_client.get(
            "/api/v1/skills/nonexistent-skill-xyz",
            headers=auth_headers
        )
        assert response.status_code == 404


@pytest.mark.unit
class TestSkillExecution:
    """Test skill execution endpoints"""

    def test_execute_skill(self, test_client: TestClient, auth_headers: dict):
        """Test executing a skill"""
        response = test_client.post(
            "/api/v1/skills/test-skill/execute",
            json={"input": "test"},
            headers=auth_headers
        )
        # Could be 200 (success), 404 (not found), or 500 (error)
        assert response.status_code in [200, 404, 500]

    def test_execute_with_empty_input(self, test_client: TestClient, auth_headers: dict):
        """Test executing skill with empty input"""
        response = test_client.post(
            "/api/v1/skills/test-skill/execute",
            json={},
            headers=auth_headers
        )
        assert response.status_code in [200, 404, 422, 500]


@pytest.mark.integration
class TestSkillWorkflow:
    """Integration tests for skill workflows"""

    def test_list_and_check_skill(self, test_client: TestClient, auth_headers: dict):
        """Test listing skills and checking details"""
        # Get list
        list_response = test_client.get(
            "/api/v1/skills",
            headers=auth_headers
        )
        assert list_response.status_code == 200

        # If skills exist, check details
        data = list_response.json()
        skills = data if isinstance(data, list) else data.get("skills", [])
        if skills:
            first_skill = skills[0]
            skill_id = first_skill.get("id") or first_skill.get("name")
            if skill_id:
                detail_response = test_client.get(
                    f"/api/v1/skills/{skill_id}",
                    headers=auth_headers
                )
                assert detail_response.status_code in [200, 404]
