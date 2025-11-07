"""
Global error handling middleware.

This module provides centralized error handling with structured responses.
"""

from typing import Union

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorResponse(BaseModel):
    """
    Standardized error response model.
    
    Attributes:
        error: Error type or category
        message: Human-readable error message
        details: Optional additional error details
        path: Request path where error occurred
    """
    error: str
    message: str
    details: Union[dict, list, None] = None
    path: str


def setup_error_handlers(app: FastAPI) -> None:
    """
    Setup global error handlers for FastAPI application.
    
    Handles:
    - HTTP exceptions (4xx, 5xx)
    - Validation errors (422)
    - Database errors
    - Unexpected exceptions
    
    Args:
        app: FastAPI application instance
        
    Example:
        >>> from fastapi import FastAPI
        >>> from app.middleware import setup_error_handlers
        >>> 
        >>> app = FastAPI()
        >>> setup_error_handlers(app)
    """
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """
        Handle HTTP exceptions.
        
        Args:
            request: The incoming request
            exc: The HTTP exception
            
        Returns:
            JSONResponse with error details
        """
        logger.warning(
            "HTTP exception",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method,
        )
        
        error_response = ErrorResponse(
            error=f"HTTP_{exc.status_code}",
            message=exc.detail,
            path=request.url.path,
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict(),
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handle request validation errors.
        
        Args:
            request: The incoming request
            exc: The validation error
            
        Returns:
            JSONResponse with validation error details
        """
        logger.warning(
            "Validation error",
            path=request.url.path,
            method=request.method,
            errors=exc.errors(),
        )
        
        error_response = ErrorResponse(
            error="VALIDATION_ERROR",
            message="Request validation failed",
            details=exc.errors(),
            path=request.url.path,
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.dict(),
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        """
        Handle database errors.
        
        Args:
            request: The incoming request
            exc: The database error
            
        Returns:
            JSONResponse with error details
        """
        logger.error(
            "Database error",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            error_type=type(exc).__name__,
        )
        
        error_response = ErrorResponse(
            error="DATABASE_ERROR",
            message="A database error occurred",
            path=request.url.path,
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.dict(),
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Handle unexpected exceptions.
        
        Args:
            request: The incoming request
            exc: The exception
            
        Returns:
            JSONResponse with error details
        """
        logger.error(
            "Unexpected error",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        
        error_response = ErrorResponse(
            error="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            path=request.url.path,
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.dict(),
        )
    
    logger.info("Error handlers configured")
