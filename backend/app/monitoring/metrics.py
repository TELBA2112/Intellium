"""
Prometheus metrics and monitoring.

This module provides Prometheus metrics collection and exposure.
"""

from fastapi import FastAPI
from loguru import logger
from prometheus_client import Counter, Histogram, Info
from prometheus_fastapi_instrumentator import Instrumentator


# Custom metrics
request_counter = Counter(
    "app_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status_code"],
)

request_duration = Histogram(
    "app_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
)

app_info = Info(
    "app_info",
    "Application information",
)


def setup_metrics(app: FastAPI) -> Instrumentator:
    """
    Setup Prometheus metrics for FastAPI application.
    
    Instruments the application with:
    - HTTP request metrics (count, duration, size)
    - Response metrics (status codes, size)
    - Custom business metrics
    
    Args:
        app: FastAPI application instance
        
    Returns:
        Instrumentator: Configured instrumentator instance
        
    Example:
        >>> from fastapi import FastAPI
        >>> from app.monitoring import setup_metrics
        >>> 
        >>> app = FastAPI()
        >>> instrumentator = setup_metrics(app)
    """
    # Set application info
    app_info.info(
        {
            "app_name": "Intellium Patent Guard",
            "version": "1.0.0",
            "environment": "production",
        }
    )
    
    # Create instrumentator with custom config
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health", "/docs", "/redoc", "/openapi.json"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="app_requests_inprogress",
        inprogress_labels=True,
    )
    
    # Add default metrics
    instrumentator.instrument(app)
    
    # Expose metrics endpoint
    instrumentator.expose(app, endpoint="/metrics", include_in_schema=False)
    
    logger.info(
        "Prometheus metrics configured",
        endpoint="/metrics",
        excluded_handlers=instrumentator.excluded_handlers,
    )
    
    return instrumentator


def track_request(method: str, endpoint: str, status_code: int) -> None:
    """
    Track custom request metrics.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        status_code: HTTP status code
        
    Example:
        >>> track_request("POST", "/api/auth/login", 200)
    """
    request_counter.labels(
        method=method, endpoint=endpoint, status_code=status_code
    ).inc()
