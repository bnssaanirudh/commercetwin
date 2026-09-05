import os

import pytest

# Ensure testing uses an in-memory SQLite database to prevent dropping the real dev database.
# This MUST happen before any app modules are imported.
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from app.db import Base, SessionLocal, engine


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
