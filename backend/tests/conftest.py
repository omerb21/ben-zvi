"""
Pytest configuration and fixtures for backend tests.
"""
import os
import pytest
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Use in-memory SQLite for tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.database import Base, get_db
from app.main import app


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh shared in-memory database for each test function."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
async def client(test_db):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = httpx.ASGITransport(app=app)
    test_client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    try:
        yield test_client
    finally:
        await test_client.aclose()
        app.dependency_overrides.clear()
