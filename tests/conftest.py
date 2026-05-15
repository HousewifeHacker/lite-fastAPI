import os
from collections.abc import Generator


import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from fastapi.testclient import TestClient

from app.main import (
    Base,
    DATABASE_URLS,
    app,
    get_db
)

TEST_DB_URL = DATABASE_URLS["test"]
engine = create_engine(
    TEST_DB_URL,
    echo=True,  # log SQL queries to the console for debugging
    connect_args={"check_same_thread": False} # needed for SQLite to allow multiple threads to access the database. Not needed for other databases like PostgreSQL or MySQL.
)
TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@pytest.fixture(scope="function")
def db_session(setup_database) -> Generator[Session]:
    """
    Include as dependency for db tests.

    Creates a new database session for each test,
    and rolls back any changes after the test is complete. 
    """
    # provide session
    with TestSessionLocal() as session:
        yield session


@pytest.fixture
def client(setup_database) -> Generator[TestClient]:
    """
    Include as dependency for API tests.
    Provides a TestClient instance for making API requests to the FastAPI app.
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def setup_database():
    Base.metadata.create_all(engine)

    yield

    Base.metadata.drop_all(engine)

@pytest.fixture(scope="session", autouse=True)
def cleanup_database():
    yield

    if os.path.exists(TEST_DB_URL.replace("sqlite:///", "")):
        os.remove(TEST_DB_URL.replace("sqlite:///", ""))

    engine.dispose()