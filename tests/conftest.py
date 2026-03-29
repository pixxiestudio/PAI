"""Pytest configuration and shared fixtures for PAI tests"""
import pytest
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Set mock API key for testing BEFORE importing backend modules
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-mock-key-for-testing-only")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.db.models import Base
from backend.core.engine import PAIEngine
from backend.core.memory import MemorySystem
from backend.core.context import ContextManager
from backend.core.learning import SelfLearningSystem
from backend.core.personality import PersonalityManager


# Test database setup
@pytest.fixture(scope="session")
def test_db():
    """Create in-memory SQLite database for testing"""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(test_db):
    """Create a fresh database session for each test"""
    Session = sessionmaker(bind=test_db)
    session = Session()

    yield session

    # Proper cleanup: rollback, expunge all objects, close
    session.rollback()
    session.expunge_all()
    session.close()


# Component fixtures
@pytest.fixture
def pai_engine(db_session):
    """Create PAIEngine instance for testing"""
    engine = PAIEngine(db_session=db_session)
    return engine


@pytest.fixture
def memory_system(db_session):
    """Create MemorySystem instance for testing"""
    return MemorySystem(db_session=db_session)


@pytest.fixture
def context_manager(memory_system, db_session):
    """Create ContextManager instance for testing"""
    return ContextManager(memory_system, db_session=db_session)


@pytest.fixture
def learning_system(db_session):
    """Create SelfLearningSystem instance for testing"""
    return SelfLearningSystem(db_session=db_session)


@pytest.fixture
def personality_manager(db_session):
    """Create PersonalityManager instance for testing"""
    return PersonalityManager(db_session=db_session)


# Test data fixtures
@pytest.fixture
def sample_session_id():
    """Generate a unique sample session ID for each test"""
    return str(uuid.uuid4())


@pytest.fixture
def sample_user_id():
    """Generate a unique sample user ID for each test"""
    return str(uuid.uuid4())


@pytest.fixture
def sample_pai_instance_id():
    """Generate a unique sample PAI instance ID for each test"""
    return str(uuid.uuid4())


@pytest.fixture
def sample_message():
    """Generate a sample message"""
    return "Hello, can you help me with this code?"


@pytest.fixture
def sample_context():
    """Generate sample context"""
    return "Previous discussion about Python functions and best practices"
