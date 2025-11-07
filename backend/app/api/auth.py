"""
Authentication API endpoints.

This module provides endpoints for:
- User registration
- User login
- Token refresh
- Current user retrieval
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from loguru import logger
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.database import get_db
from app.middleware import limiter
from app.models.user import User
from app.schemas.auth import LoginResponse, Token, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    request: Request = None
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Dependency for protected endpoints that verifies JWT token
    and returns the authenticated user.
    
    Args:
        token: JWT access token from Authorization header
        db: Database session
        request: FastAPI request object (optional)
        
    Returns:
        User object if authenticated
        
    Raises:
        HTTPException: If token is invalid or user not found
        
    Examples:
        >>> from fastapi import Depends
        >>> @router.get("/me")
        >>> async def read_me(user: User = Depends(get_current_user)):
        ...     return user
    """
    from app.core.security import decode_access_token
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = decode_access_token(token)
    if token_data is None:
        logger.warning("Invalid token provided")
        raise credentials_exception
    
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        logger.warning("User not found", email=token_data.email)
        raise credentials_exception
    
    # Store user in request state for rate limiting
    if request:
        request.state.user = user
    
    logger.debug("User authenticated", user_id=user.id, email=user.email)
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")  # Rate limit registration attempts
async def register(
    request: Request,
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user.
    
    Args:
        user_in: User registration data
        db: Database session
        
    Returns:
        Created user object
        
    Raises:
        HTTPException: If email already registered
        
    Examples:
        >>> response = await register(
        ...     UserCreate(email="user@example.com", password="secret123"),
        ...     db
        ... )
    """
    logger.info("User registration attempt", email=user_in.email)
    
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        logger.warning("Email already registered", email=user_in.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        is_active=True,
        is_superuser=False,
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info("User registered successfully", user_id=db_user.id, email=db_user.email)
    return db_user


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")  # Rate limit login attempts
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible login endpoint.
    
    Rate limited to prevent brute force attacks.
    
    Args:
        request: FastAPI request object
        form_data: OAuth2 form with username (email) and password
        db: Database session
        
    Returns:
        Access token and user information
        
    Raises:
        HTTPException: If credentials are incorrect
        
    Examples:
        >>> response = await login(
        ...     OAuth2PasswordRequestForm(
        ...         username="user@example.com",
        ...         password="secret123"
        ...     ),
        ...     db
        ... )
    """
    logger.info("Login attempt", email=form_data.username)
    
    # Get user by email
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        logger.warning("Login failed - user not found", email=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        logger.warning("Login failed - incorrect password", email=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning("Login failed - inactive user", email=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    logger.info("Login successful", user_id=user.id, email=user.email)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user information.
    
    Args:
        current_user: Authenticated user from JWT token
        
    Returns:
        Current user object
        
    Examples:
        >>> user = await read_current_user(current_user)
        >>> print(user.email)
    """
    logger.debug("Current user retrieved", user_id=current_user.id)
    return current_user
