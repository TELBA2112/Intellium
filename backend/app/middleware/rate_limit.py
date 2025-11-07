"""
Rate limiting middleware using SlowAPI.

This module provides rate limiting functionality to prevent API abuse.
"""

from typing import Callable

from fastapi import FastAPI, Request, Response
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


def get_client_identifier(request: Request) -> str:
    """
    Get unique identifier for rate limiting.
    
    Uses authenticated user ID if available, otherwise falls back to IP.
    
    Args:
        request: The incoming HTTP request
        
    Returns:
        str: Client identifier for rate limiting
        
    Example:
        >>> identifier = get_client_identifier(request)
        >>> # Returns "user:123" for authenticated users
        >>> # Returns "ip:192.168.1.1" for anonymous users
    """
    # Try to get user from request state (set by auth dependency)
    user = getattr(request.state, "user", None)
    
    if user and hasattr(user, "id"):
        identifier = f"user:{user.id}"
        logger.debug("Rate limit identifier from user", identifier=identifier)
        return identifier
    
    # Fallback to IP address
    ip_address = get_remote_address(request)
    identifier = f"ip:{ip_address}"
    logger.debug("Rate limit identifier from IP", identifier=identifier)
    return identifier


# Initialize limiter with custom key function
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=["100/minute", "1000/hour"],
    storage_uri="memory://",
    strategy="fixed-window",
)


def setup_rate_limiting(app: FastAPI) -> None:
    """
    Setup rate limiting for FastAPI application.
    
    Configures SlowAPI with custom error handler and adds to app state.
    
    Args:
        app: FastAPI application instance
        
    Example:
        >>> from fastapi import FastAPI
        >>> from app.middleware import setup_rate_limiting
        >>> 
        >>> app = FastAPI()
        >>> setup_rate_limiting(app)
    """
    # Add limiter to app state
    app.state.limiter = limiter
    
    # Add exception handler for rate limit errors
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    logger.info(
        "Rate limiting configured",
        default_limits=limiter._default_limits,
        strategy="fixed-window",
    )


# Decorator for custom rate limits on specific endpoints
def rate_limit(limit: str):
    """
    Decorator to apply custom rate limit to endpoint.
    
    Args:
        limit: Rate limit string (e.g., "5/minute", "100/hour")
        
    Returns:
        Decorator function
        
    Example:
        >>> from app.middleware import limiter, rate_limit
        >>> 
        >>> @router.post("/login")
        >>> @limiter.limit("5/minute")
        >>> async def login(credentials: LoginRequest):
        >>>     ...
    """
    return limiter.limit(limit)
