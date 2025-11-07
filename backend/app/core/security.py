"""
Security utilities for authentication and authorization.

This module provides:
- Password hashing and verification
- JWT token creation and validation
- User authentication helpers
- Security decorators
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import JWTError, jwt
from loguru import logger
from passlib.context import CryptContext
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.auth import TokenData

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
        
    Examples:
        >>> hashed = get_password_hash("secret123")
        >>> verify_password("secret123", hashed)
        True
        >>> verify_password("wrong", hashed)
        False
    """
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        logger.debug("Password verification", result=result)
        return result
    except Exception as e:
        logger.error("Password verification failed", error=str(e))
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
        
    Examples:
        >>> hashed = get_password_hash("mypassword")
        >>> len(hashed) > 0
        True
    """
    hashed = pwd_context.hash(password)
    logger.debug("Password hashed successfully")
    return hashed


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary of claims to encode in token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token string
        
    Examples:
        >>> token = create_access_token({"sub": "user@example.com"})
        >>> len(token) > 0
        True
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=ALGORITHM
    )
    
    logger.info(
        "Access token created",
        subject=data.get("sub"),
        expires_at=expire.isoformat()
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        TokenData object if valid, None otherwise
        
    Examples:
        >>> token = create_access_token({"sub": "user@example.com"})
        >>> data = decode_access_token(token)
        >>> data.email
        'user@example.com'
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        email: Optional[str] = payload.get("sub")
        
        if email is None:
            logger.warning("Token missing subject claim")
            return None
        
        token_data = TokenData(email=email)
        logger.debug("Token decoded successfully", email=email)
        return token_data
        
    except JWTError as e:
        logger.warning("JWT decode error", error=str(e))
        return None
    except ValidationError as e:
        logger.warning("Token data validation error", error=str(e))
        return None
    except Exception as e:
        logger.error("Unexpected error decoding token", error=str(e))
        return None


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Dictionary of claims to encode in token
        expires_delta: Optional expiration time delta (default: 7 days)
        
    Returns:
        Encoded JWT refresh token string
    """
    if expires_delta is None:
        expires_delta = timedelta(days=7)
    
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=ALGORITHM
    )
    
    logger.info(
        "Refresh token created",
        subject=data.get("sub"),
        expires_at=expire.isoformat()
    )
    
    return encoded_jwt
