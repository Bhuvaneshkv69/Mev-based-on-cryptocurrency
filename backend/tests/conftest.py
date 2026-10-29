"""Pytest Configuration and Test Fixtures.

Configures an isolated test database, manages schema creation and cleanup,
and sets up FastAPI dependency overrides so tests never touch or wipe
a developer's active database.
"""

import os
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

# ------------------------------------------------------------------------------
# Test Database Engine Setup
# ------------------------------------------------------------------------------
# If TEST_DATABASE_URL is provided in environment, run against that database
# (e.g., a dedicated PostgreSQL test instance: postgresql+psycopg://.../mevshield_test).
# Otherwise, default to SQLite in-memory with StaticPool for instantaneous,
# completely isolated test execution without external service dependencies.
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

if TEST_DATABASE_URL.startswith("sqlite"):
    test_engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database() -> Generator[None, None, None]:
    """Create all database tables once for the test session, and drop on teardown."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide an isolated database session per test with automatic rollback/clean."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        # Clean up records created during the test
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with get_db dependency overridden to use the test session."""
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
