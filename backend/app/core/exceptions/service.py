"""
Service layer exceptions.

These exceptions are raised by services when business logic validation fails.
They should be caught by controllers and converted to HTTP responses.
"""


class ServiceError(Exception):
    """Base exception for all service errors."""
    pass


class ValidationError(ServiceError):
    """Raised when input validation fails."""
    pass


class BusinessRuleError(ServiceError):
    """Raised when a business rule is violated."""
    pass
