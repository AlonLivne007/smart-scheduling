"""
Repository layer exceptions.

These exceptions are raised by repositories when database operations fail.
They should be caught by services and converted to domain-level errors.
"""


class RepositoryError(Exception):
    """Base exception for all repository errors."""
    pass


class NotFoundError(RepositoryError):
    """Raised when an entity is not found."""
    pass


class ConflictError(RepositoryError):
    """Raised when a database constraint is violated (e.g., unique constraint)."""
    pass


class DatabaseError(RepositoryError):
    """Raised when a general database error occurs."""
    pass
