"""Pytest configuration and fixtures for PAI API tests"""
import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from backend.db.models import Base
from backend.api.main import app, get_container
from backend.core.container import ServiceContainer
from fastapi.testclient import TestClient


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """Create a test database session"""
    # Create engine with in-memory SQLite
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()

    yield db

    db.close()

    # Drop all tables
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_container(test_db: Session) -> ServiceContainer:
    """Create a test service container with test database"""
    container = ServiceContainer(db_session=test_db)
    return container


@pytest.fixture(scope="function")
def test_client(test_db: Session) -> TestClient:
    """Create a test client with test database"""

    # Override the get_container dependency
    def override_get_container():
        return ServiceContainer(db_session=test_db)

    app.dependency_overrides[get_container] = override_get_container

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def valid_user_id() -> str:
    """Fixture for valid user ID"""
    return "test-user-123"


@pytest.fixture
def valid_jwt_token(test_client: TestClient, valid_user_id: str) -> str:
    """Fixture for valid JWT token"""
    response = test_client.post(
        "/api/v1/auth/token",
        json={"user_id": valid_user_id}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(valid_jwt_token: str) -> dict:
    """Fixture for authorization headers"""
    return {"Authorization": f"Bearer {valid_jwt_token}"}


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
