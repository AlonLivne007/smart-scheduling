"""
Application exceptions.

This module defines domain-level exceptions that are raised by repositories
and services. Controllers map these to appropriate HTTP responses.
"""

from app.exceptions.repository import (
    RepositoryError,
    NotFoundError,
    ConflictError,
    DatabaseError,
)
from app.exceptions.service import (
    ServiceError,
    ValidationError,
    BusinessRuleError,
)

__all__ = [
    "RepositoryError",
    "NotFoundError",
    "ConflictError",
    "DatabaseError",
    "ServiceError",
    "ValidationError",
    "BusinessRuleError",
]
