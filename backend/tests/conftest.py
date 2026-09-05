import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure testing uses an in-memory SQLite database to prevent dropping the real dev database.
# This MUST happen before any app modules are imported.
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

# Import models BEFORE create_all so ALL tables are registered in Base.metadata.
# The import order matters — models must be loaded before db.Base.metadata.create_all.
from app import models  # noqa: F401
from app.db import Base

# Create a single shared in-memory engine with StaticPool.
# StaticPool ensures ALL connections (including those from webhook_handler's
# internal SessionLocal()) share the same in-memory SQLite database.
TEST_ENGINE = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


def _patch_app_db():
    """Override the app's engine and SessionLocal to use our test engine."""
    import app.db as app_db

    app_db.engine = TEST_ENGINE
    app_db.SessionLocal = TestSessionLocal


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create all tables once per test session using the shared in-memory engine."""
    _patch_app_db()
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture(autouse=True)
def patch_db():
    """Ensure the app's db module always points to the test engine (for all tests)."""
    _patch_app_db()


@pytest.fixture
def db_session(setup_db, patch_db):
    """
    Provide a fresh DB session per test.
    The session is closed (not rolled back) after each test.
    Tests share the same in-memory DB — isolation is by test data conventions,
    not by transaction rollback, since the webhook handler opens its own sessions.
    """
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
