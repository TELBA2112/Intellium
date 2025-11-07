"""
Tests for authentication endpoints.

This module tests:
- User registration
- User login
- Token validation
- Current user retrieval
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


class TestUserRegistration:
    """Test cases for user registration endpoint."""
    
    def test_register_new_user(self, client: TestClient):
        """
        Test successful user registration.
        
        Given: A new user with valid email and password
        When: POST request to /auth/register
        Then: User is created and returned with 201 status
        """
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert data["is_superuser"] is False
        assert "id" in data
        assert "hashed_password" not in data
    
    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """
        Test registration with existing email.
        
        Given: A user already exists with an email
        When: POST request with the same email
        Then: 400 error is returned
        """
        response = client.post(
            "/auth/register",
            json={
                "email": test_user.email,
                "password": "password123",
                "full_name": "Duplicate User"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_invalid_email(self, client: TestClient):
        """
        Test registration with invalid email format.
        
        Given: Invalid email format
        When: POST request to /auth/register
        Then: 422 validation error is returned
        """
        response = client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
                "full_name": "Test User"
            }
        )
        
        assert response.status_code == 422
    
    def test_register_short_password(self, client: TestClient):
        """
        Test registration with password too short.
        
        Given: Password less than minimum length
        When: POST request to /auth/register
        Then: 422 validation error is returned
        """
        response = client.post(
            "/auth/register",
            json={
                "email": "user@example.com",
                "password": "123",
                "full_name": "Test User"
            }
        )
        
        assert response.status_code == 422
    
    def test_register_missing_fields(self, client: TestClient):
        """
        Test registration with missing required fields.
        
        Given: Missing email or password
        When: POST request to /auth/register
        Then: 422 validation error is returned
        """
        response = client.post(
            "/auth/register",
            json={
                "email": "user@example.com"
                # Missing password
            }
        )
        
        assert response.status_code == 422


class TestUserLogin:
    """Test cases for user login endpoint."""
    
    def test_login_success(self, client: TestClient, test_user: User):
        """
        Test successful user login.
        
        Given: Valid email and password
        When: POST request to /auth/login
        Then: Access token and user data are returned
        """
        response = client.post(
            "/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == test_user.email
    
    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """
        Test login with incorrect password.
        
        Given: Valid email but wrong password
        When: POST request to /auth/login
        Then: 401 unauthorized error is returned
        """
        response = client.post(
            "/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client: TestClient):
        """
        Test login with non-existent email.
        
        Given: Email that doesn't exist in database
        When: POST request to /auth/login
        Then: 401 unauthorized error is returned
        """
        response = client.post(
            "/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_login_inactive_user(self, client: TestClient, db: Session):
        """
        Test login with inactive user account.
        
        Given: User account that is not active
        When: POST request to /auth/login
        Then: 403 forbidden error is returned
        """
        from app.core.security import get_password_hash
        
        # Create inactive user
        inactive_user = User(
            email="inactive@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Inactive User",
            is_active=False,
            is_superuser=False,
        )
        db.add(inactive_user)
        db.commit()
        
        response = client.post(
            "/auth/login",
            data={
                "username": "inactive@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 403
        assert "inactive" in response.json()["detail"].lower()


class TestCurrentUser:
    """Test cases for current user endpoint."""
    
    def test_get_current_user_success(
        self,
        client: TestClient,
        test_user: User,
        user_token: str
    ):
        """
        Test retrieving current authenticated user.
        
        Given: Valid authentication token
        When: GET request to /auth/me
        Then: Current user data is returned
        """
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id
    
    def test_get_current_user_invalid_token(self, client: TestClient):
        """
        Test retrieving current user with invalid token.
        
        Given: Invalid authentication token
        When: GET request to /auth/me
        Then: 401 unauthorized error is returned
        """
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_get_current_user_no_token(self, client: TestClient):
        """
        Test retrieving current user without token.
        
        Given: No authentication token provided
        When: GET request to /auth/me
        Then: 401 unauthorized error is returned
        """
        response = client.get("/auth/me")
        
        assert response.status_code == 401
    
    def test_get_current_user_expired_token(self, client: TestClient):
        """
        Test retrieving current user with expired token.
        
        Given: Expired authentication token
        When: GET request to /auth/me
        Then: 401 unauthorized error is returned
        """
        from datetime import timedelta
        from app.core.security import create_access_token
        
        # Create token that expires immediately
        expired_token = create_access_token(
            data={"sub": "test@example.com"},
            expires_delta=timedelta(seconds=-1)
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401


class TestTokenSecurity:
    """Test cases for token security."""
    
    def test_token_contains_user_email(self, user_token: str):
        """
        Test that token contains user email in payload.
        
        Given: Valid access token
        When: Token is decoded
        Then: User email is in the payload
        """
        from app.core.security import decode_access_token
        
        token_data = decode_access_token(user_token)
        assert token_data is not None
        assert token_data.email == "test@example.com"
    
    def test_token_has_expiration(self, user_token: str):
        """
        Test that token has expiration claim.
        
        Given: Valid access token
        When: Token is decoded
        Then: Expiration claim exists
        """
        from jose import jwt
        from app.core.config import settings
        
        payload = jwt.decode(
            user_token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        
        assert "exp" in payload
        assert "iat" in payload
    
    def test_tampered_token_rejected(self, user_token: str, client: TestClient):
        """
        Test that tampered token is rejected.
        
        Given: Token that has been modified
        When: GET request to protected endpoint
        Then: 401 unauthorized error is returned
        """
        # Tamper with token
        tampered_token = user_token[:-10] + "tampered"
        
        headers = {"Authorization": f"Bearer {tampered_token}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
