"""
Session management utilities for FastAPI and Celery.

This module provides utilities for managing database sessions in different
contexts (FastAPI requests, Celery tasks) with proper transaction boundaries.
"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.data.session import SessionLocal


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Use this in Celery tasks or other contexts where you need to manage
    your own session lifecycle.
    
    Example:
        with get_db_session() as data:
            user_repo = UserRepository(data)
            user = user_repo.get_by_id(1)
            data.commit()
    
    Yields:
        Database session
        
    Note:
        The session is automatically closed when exiting the context.
        You must call data.commit() or data.rollback() explicitly.
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def transaction(db: Session) -> Generator[Session, None, None]:
    """
    Context manager for database transactions.
    
    Use this to ensure a transaction is committed on success or rolled back
    on error. Works with an existing session.
    
    Example:
        with get_db_session() as data:
            with transaction(data):
                user_repo = UserRepository(data)
                user = user_repo.create(...)
                # Transaction commits automatically on success
    
    Args:
        db: Existing database session
        
    Yields:
        The same database session
        
    Note:
        If an exception occurs, the transaction is rolled back automatically.
    """
    try:
        yield db
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
