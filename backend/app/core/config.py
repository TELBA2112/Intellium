"""
Application configuration using Pydantic settings.

This module defines all configuration variables loaded from environment
variables or .env file.
"""

from typing import List, Optional

from pydantic import PostgresDsn, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        PROJECT_NAME: Name of the application
        VERSION: Application version
        API_V1_STR: API version prefix
        SECRET_KEY: Secret key for JWT encoding
        ACCESS_TOKEN_EXPIRE_MINUTES: Token expiration time
        DATABASE_URL: PostgreSQL connection string
        REDIS_URL: Redis connection string
        CORS_ORIGINS: List of allowed CORS origins
        MINIO_ENDPOINT: MinIO server endpoint
        MINIO_ACCESS_KEY: MinIO access key
        MINIO_SECRET_KEY: MinIO secret key
        MINIO_BUCKET: Default bucket name
        STRIPE_SECRET_KEY: Stripe API secret key
        STRIPE_PUBLISHABLE_KEY: Stripe publishable key
        TESSERACT_CMD: Path to Tesseract executable
        LOG_LEVEL: Logging level
        JSON_LOGS: Enable JSON formatted logs
    """
    
    # Project
    PROJECT_NAME: str = "PatentGuard"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: PostgresDsn
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://intellium-admin.vercel.app",
        "https://intellium.vercel.app"
    ]
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        """
        Parse CORS origins from string or list.
        
        Args:
            v: CORS origins as string (comma-separated) or list
            
        Returns:
            List of CORS origin URLs
        """
        if isinstance(v, str) and not isinstance(v, list):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return [v]
    
    # MinIO / S3
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "documents"
    MINIO_USE_SSL: bool = False
    
    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # OCR
    TESSERACT_CMD: str = "/usr/bin/tesseract"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    JSON_LOGS: bool = False
    LOG_FILE: str = "logs/app.log"
    
    # Environment
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # Performance Configuration
    DB_POOL_SIZE: int = 20
    DB_POOL_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Monitoring
    ENABLE_METRICS: bool = True
    SENTRY_DSN: Optional[str] = None
    
    # Admin
    FIRST_SUPERUSER_EMAIL: str = "admin@patentguard.com"
    FIRST_SUPERUSER_PASSWORD: str = "changethis"
    
    class Config:
        """Pydantic config."""
        
        env_file = ".env"
        case_sensitive = True


settings = Settings()


# Global settings instance
settings = Settings()
