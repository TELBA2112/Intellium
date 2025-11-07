"""
Main FastAPI application.

This module initializes the FastAPI app with all middleware,
routers, and monitoring.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.logging import setup_logging
from app.middleware import (
    LoggingMiddleware,
    setup_error_handlers,
    setup_rate_limiting,
)
from app.monitoring import setup_metrics

# Setup logging first
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Intellium Patent Guard API",
    description="API for patent similarity checking and document management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
@app.get("/", tags=["root"])
async def root():
    return {
        "message": "✅ Intellium Backend Running Successfully",
        "health": "/health",
        "docs": "/docs",
    }

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup request logging middleware
app.add_middleware(LoggingMiddleware)

# Setup rate limiting
setup_rate_limiting(app)

# Setup error handlers
setup_error_handlers(app)

# Setup Prometheus metrics
setup_metrics(app)

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Health status
        
    Example:
        >>> response = client.get("/health")
        >>> assert response.status_code == 200
        >>> assert response.json()["status"] == "healthy"
    """
    return {
        "status": "healthy",
        "service": "Intellium Patent Guard API",
        "version": "1.0.0",
    }


# Include routers
# Note: Import routers after app creation to avoid circular imports
try:
    from app.api import auth
    
    app.include_router(auth.router, prefix="/api")
    logger.info("Auth router registered")
except ImportError as e:
    logger.warning(f"Could not import auth router: {e}")

# Add additional routers here as they are created
# from app.api import documents, checks, payments
# app.include_router(documents.router, prefix="/api")
# app.include_router(checks.router, prefix="/api")
# app.include_router(payments.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Application starting up")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Application shutting down")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None,  # Use loguru instead
    )
