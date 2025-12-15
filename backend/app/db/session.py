"""
Database session configuration.

This module configures the database connection and session management
for the Smart Scheduling application using SQLAlchemy with PostgreSQL.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create database engine
engine = create_engine(settings.DATABASE_URL)

# Configure session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for ORM models
Base = declarative_base()


def get_db():
    """
    Database session dependency for FastAPI routes.
    
    Provides a database session that is automatically created for each
    request and properly closed when the request completes.
    
    Yields:
        db: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
