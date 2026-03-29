#!/usr/bin/env python3
"""Initialize PAI database"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from backend.db.models import Base
from backend.utils.config import settings


def init_db():
    """Create all database tables"""
    print(f"Initializing database at: {settings.database_url}")

    # Create engine
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("✓ Database initialized successfully!")
    print("✓ Created tables:")
    for table in Base.metadata.tables.keys():
        print(f"  - {table}")

    engine.dispose()


if __name__ == "__main__":
    init_db()
