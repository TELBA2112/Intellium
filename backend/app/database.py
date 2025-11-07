"""
Database connection and session management.

This module provides database session and dependency injection
for FastAPI endpoints.
"""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Create database engine with optimized connection pooling
engine = create_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,  # Verify connections before using
    pool_size=settings.DB_POOL_SIZE,  # Number of connections to maintain
    max_overflow=settings.DB_POOL_MAX_OVERFLOW,  # Max overflow connections
    pool_timeout=settings.DB_POOL_TIMEOUT,  # Timeout for getting connection
    pool_recycle=settings.DB_POOL_RECYCLE,  # Recycle connections after N seconds
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.
    
    Yields a database session and ensures it's closed after use.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        >>> from fastapi import Depends
        >>> from sqlalchemy.orm import Session
        >>> 
        >>> @router.get("/users")
        >>> async def list_users(db: Session = Depends(get_db)):
        ...     users = db.query(User).all()
        ...     return users
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
