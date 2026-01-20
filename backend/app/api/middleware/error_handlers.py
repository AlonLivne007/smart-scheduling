"""
Centralized exception handlers for FastAPI.

This module provides exception handlers that convert domain exceptions
(RepositoryError, ServiceError) to appropriate HTTP responses.

All handlers are registered in server.py and apply globally to all routes.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions.repository import (
    RepositoryError,
    NotFoundError,
    ConflictError,
    DatabaseError,
)
from app.core.exceptions.service import (
    ServiceError,
    ValidationError,
    BusinessRuleError,
)


async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """
    Handle NotFoundError exceptions.
    
    Maps to HTTP 404 Not Found.
    Uses the exception message for the error detail.
    """
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc) if str(exc) else "Resource not found"}
    )


async def conflict_error_handler(request: Request, exc: ConflictError) -> JSONResponse:
    """
    Handle ConflictError exceptions.
    
    Maps to HTTP 400 Bad Request (conflict with current state).
    Uses the exception message for the error detail.
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc) if str(exc) else "Conflict occurred"}
    )


async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """
    Handle DatabaseError exceptions.
    
    Maps to HTTP 500 Internal Server Error.
    Uses a generic message to avoid exposing internal database details.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "A database error occurred. Please try again later."}
    )


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Handle ValidationError exceptions.
    
    Maps to HTTP 400 Bad Request.
    Uses the exception message for the error detail.
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc) if str(exc) else "Validation failed"}
    )


async def business_rule_error_handler(request: Request, exc: BusinessRuleError) -> JSONResponse:
    """
    Handle BusinessRuleError exceptions.
    
    Maps to HTTP 422 Unprocessable Entity (business rule violation).
    Uses the exception message for the error detail.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc) if str(exc) else "Business rule violation"}
    )


async def repository_error_handler(request: Request, exc: RepositoryError) -> JSONResponse:
    """
    Fallback handler for any RepositoryError that isn't handled by specific handlers.
    
    Maps to HTTP 500 Internal Server Error.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "A repository error occurred. Please try again later."}
    )


async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    """
    Fallback handler for any ServiceError that isn't handled by specific handlers.
    
    Maps to HTTP 400 Bad Request.
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc) if str(exc) else "A service error occurred"}
    )
