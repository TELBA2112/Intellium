"""
Pytest configuration and fixtures.

This module provides shared fixtures and configuration for all tests.
"""

import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.database import Base, get_db
from app.main import app
from app.models.user import User

# Test database URL (in-memory SQLite for speed)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.
    
    Yields:
        Database session
        
    Examples:
        >>> def test_create_user(db):
        ...     user = User(email="test@example.com")
        ...     db.add(user)
        ...     db.commit()
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop tables
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with a test database.
    
    Args:
        db: Test database session
        
    Yields:
        FastAPI test client
        
    Examples:
        >>> def test_endpoint(client):
        ...     response = client.get("/api/v1/users")
        ...     assert response.status_code == 200
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db: Session) -> User:
    """
    Create a test user in the database.
    
    Args:
        db: Database session
        
    Returns:
        Created test user
        
    Examples:
        >>> def test_with_user(test_user):
        ...     assert test_user.email == "test@example.com"
    """
    from app.core.security import get_password_hash
    
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def test_superuser(db: Session) -> User:
    """
    Create a test superuser in the database.
    
    Args:
        db: Database session
        
    Returns:
        Created test superuser
    """
    from app.core.security import get_password_hash
    
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def user_token(test_user: User) -> str:
    """
    Create an access token for test user.
    
    Args:
        test_user: Test user object
        
    Returns:
        JWT access token
        
    Examples:
        >>> def test_authenticated(client, user_token):
        ...     headers = {"Authorization": f"Bearer {user_token}"}
        ...     response = client.get("/api/v1/users/me", headers=headers)
        ...     assert response.status_code == 200
    """
    from app.core.security import create_access_token
    
    return create_access_token(data={"sub": test_user.email})


@pytest.fixture(scope="function")
def superuser_token(test_superuser: User) -> str:
    """
    Create an access token for test superuser.
    
    Args:
        test_superuser: Test superuser object
        
    Returns:
        JWT access token
    """
    from app.core.security import create_access_token
    
    return create_access_token(data={"sub": test_superuser.email})


@pytest.fixture(autouse=True)
def reset_db():
    """
    Reset database before each test.
    
    This fixture runs automatically before each test.
    """
    pass
