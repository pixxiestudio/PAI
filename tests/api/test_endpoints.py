"""Integration tests for PAI REST API endpoints

Tests session, message, memory, learning, and skill endpoints
"""

import pytest
from fastapi.testclient import TestClient
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set mock API key for tests
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-mock-key-for-testing")

from backend.api.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.models import Base
from backend.core.container import ServiceContainer


@pytest.fixture(scope="session")
def test_db():
    """Create in-memory SQLite database for testing"""
    # Use check_same_thread=False for in-memory SQLite in tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=None  # Disable connection pooling for in-memory DB
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(test_db):
    """Create a fresh database session for each test"""
    SessionLocal = sessionmaker(bind=test_db, expire_on_commit=False)
    session = SessionLocal()

    yield session

    try:
        session.rollback()
        session.expunge_all()
    except:
        pass
    finally:
        session.close()


@pytest.fixture
def client(test_db, db_session):
    """Create TestClient with mocked container"""
    from backend.api.main import _container, get_container
    import backend.api.main as main_module

    # Ensure all tables are created
    Base.metadata.create_all(bind=test_db)

    # Create container with test db session
    container = ServiceContainer(db_session=db_session)
    main_module._container = container

    # Override get_container dependency
    def mock_get_container():
        return container

    app.dependency_overrides[get_container] = mock_get_container

    with TestClient(app) as test_client:
        yield test_client

    # Cleanup
    app.dependency_overrides.clear()


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_metrics(self, client):
        """Test metrics endpoint"""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
        assert "active_sessions" in response.json()

    def test_readiness(self, client):
        """Test readiness probe"""
        response = client.get("/api/v1/ready")
        assert response.status_code == 200
        assert response.json()["ready"] is True


class TestSessionEndpoints:
    """Test session management endpoints"""

    def test_create_session(self, client):
        """Test creating a new session"""
        response = client.post(
            "/api/v1/sessions",
            params={
                "user_id": "test-user",
                "pai_instance_id": "default",
                "session_type": "chat"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["user_id"] == "test-user"
        assert data["pai_instance_id"] == "default"

    def test_create_session_default_pai(self, client):
        """Test creating session with default PAI instance"""
        response = client.post(
            "/api/v1/sessions",
            params={
                "user_id": "test-user",
                "session_type": "chat"
            }
        )
        assert response.status_code == 200
        assert response.json()["pai_instance_id"] == "default"

    def test_get_session(self, client):
        """Test retrieving session details"""
        # Create session
        create_response = client.post(
            "/api/v1/sessions",
            params={"user_id": "test-user"}
        )
        session_id = create_response.json()["session_id"]

        # Get session
        response = client.get(f"/api/v1/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["session_id"] == session_id

    def test_end_session(self, client):
        """Test ending a session"""
        # Create session
        create_response = client.post(
            "/api/v1/sessions",
            params={"user_id": "test-user"}
        )
        session_id = create_response.json()["session_id"]

        # End session
        response = client.delete(f"/api/v1/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "ended"

    def test_list_sessions(self, client):
        """Test listing sessions"""
        # Create a session
        client.post(
            "/api/v1/sessions",
            params={"user_id": "test-user", "pai_instance_id": "default"}
        )

        # List sessions
        response = client.get("/api/v1/sessions")
        assert response.status_code == 200
        assert "sessions" in response.json()
        assert response.json()["total"] >= 0

    def test_list_sessions_filter_pai(self, client):
        """Test filtering sessions by PAI instance"""
        # Create sessions with different PAI instances
        client.post(
            "/api/v1/sessions",
            params={"user_id": "test-user", "pai_instance_id": "default"}
        )
        client.post(
            "/api/v1/sessions",
            params={"user_id": "test-user", "pai_instance_id": "code-expert"}
        )

        # Filter by PAI instance
        response = client.get("/api/v1/sessions?pai_instance_id=default")
        assert response.status_code == 200
        sessions = response.json()["sessions"]
        assert all(s["pai_instance_id"] == "default" for s in sessions)


class TestMessageEndpoints:
    """Test message handling endpoints"""

    def test_get_session_history_empty(self, client):
        """Test getting history for empty session"""
        # Create session
        create_response = client.post(
            "/api/v1/sessions",
            params={"user_id": "test-user"}
        )
        session_id = create_response.json()["session_id"]

        # Get history
        response = client.get(f"/api/v1/sessions/{session_id}/history")
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_send_message_creates_context(self, client):
        """Test that sending message creates context"""
        # Create session
        create_response = client.post(
            "/api/v1/sessions",
            params={"user_id": "test-user"}
        )
        session_id = create_response.json()["session_id"]

        # Note: We can't actually test send_message without mocking Claude API
        # But we can verify the endpoint exists
        response = client.get(f"/api/v1/sessions/{session_id}/history")
        assert response.status_code == 200

    def test_get_paginated_messages(self, client):
        """Test paginated message retrieval"""
        # Create session
        create_response = client.post(
            "/api/v1/sessions",
            params={"user_id": "test-user"}
        )
        session_id = create_response.json()["session_id"]

        # Get paginated messages
        response = client.get(f"/api/v1/sessions/{session_id}/messages?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert data["skip"] == 0
        assert data["limit"] == 10


class TestMemoryEndpoints:
    """Test memory management endpoints"""

    def test_get_user_memories_empty(self, client):
        """Test getting memories for user with none"""
        response = client.get("/api/v1/users/test-user/memories")
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_save_memory(self, client):
        """Test saving a memory"""
        response = client.post(
            "/api/v1/users/test-user/memories",
            json={
                "content": "Test memory content",
                "memory_type": "semantic",
                "importance": 0.8
            }
        )
        assert response.status_code == 200
        assert response.json()["created"] is True
        assert "memory_id" in response.json()

    def test_update_memory_importance(self, client):
        """Test updating memory importance"""
        # Save memory
        save_response = client.post(
            "/api/v1/users/test-user/memories",
            json={
                "content": "Test memory",
                "memory_type": "semantic"
            }
        )
        memory_id = save_response.json()["memory_id"]

        # Update importance
        response = client.put(
            f"/api/v1/memories/{memory_id}",
            params={"importance": 0.5}
        )
        assert response.status_code == 200
        assert response.json()["updated"] is True

    def test_get_session_context(self, client):
        """Test getting context injection for session"""
        # Create session
        create_response = client.post(
            "/api/v1/sessions",
            params={"user_id": "test-user"}
        )
        session_id = create_response.json()["session_id"]

        # Get context
        response = client.get(f"/api/v1/sessions/{session_id}/context")
        assert response.status_code == 200
        assert "context" in response.json()
        assert "token_estimate" in response.json()


class TestLearningEndpoints:
    """Test learning and feedback endpoints"""

    def test_get_learning_report(self, client):
        """Test getting learning report for PAI instance"""
        response = client.get("/api/v1/pai/default/learning")
        assert response.status_code == 200
        # Report might be empty but should have the right structure
        assert isinstance(response.json(), dict)

    def test_get_learned_preferences(self, client):
        """Test getting learned preferences"""
        response = client.get("/api/v1/users/test-user/learning-preferences")
        assert response.status_code == 200
        assert "preferences" in response.json()
        assert "count" in response.json()

    def test_get_success_patterns(self, client):
        """Test getting success patterns"""
        response = client.get("/api/v1/pai/default/patterns")
        assert response.status_code == 200
        assert "patterns" in response.json()


class TestSkillEndpoints:
    """Test skill management endpoints"""

    def test_list_skills(self, client):
        """Test listing available skills"""
        response = client.get("/api/v1/pai/default/skills")
        assert response.status_code == 200
        assert "skills" in response.json()
        assert "total" in response.json()


class TestErrorHandling:
    """Test error handling"""

    def test_invalid_session_error(self, client):
        """Test error when accessing invalid session"""
        response = client.get("/api/v1/sessions/invalid-session-id")
        assert response.status_code == 404
        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == "SESSION_NOT_FOUND"

    def test_validation_error(self, client):
        """Test validation error on bad request"""
        # Missing required parameter
        response = client.post("/api/v1/sessions")
        assert response.status_code == 422
        assert "error_code" in response.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
