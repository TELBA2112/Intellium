"""
Request/response logging middleware.

This module provides middleware to log all HTTP requests and responses
with structured logging using loguru.
"""

import time
from typing import Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log HTTP requests and responses.
    
    Logs include:
    - Request method, path, client IP
    - Response status code
    - Request processing time
    - Request/response body sizes
    
    Example:
        >>> from fastapi import FastAPI
        >>> from app.middleware import LoggingMiddleware
        >>> 
        >>> app = FastAPI()
        >>> app.add_middleware(LoggingMiddleware)
    """
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request and log details.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            Response: The HTTP response
            
        Example:
            This is called automatically by FastAPI for each request.
        """
        # Start timer
        start_time = time.time()
        
        # Extract request details
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        
        # Log incoming request
        logger.info(
            "Incoming request",
            method=method,
            path=path,
            client_ip=client_ip,
            query_params=query_params if query_params else None,
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                method=method,
                path=path,
                status_code=response.status_code,
                process_time_ms=round(process_time * 1000, 2),
                client_ip=client_ip,
            )
            
            # Add custom headers
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                method=method,
                path=path,
                error=str(e),
                error_type=type(e).__name__,
                process_time_ms=round(process_time * 1000, 2),
                client_ip=client_ip,
            )
            
            # Re-raise to be handled by error handler
            raise
