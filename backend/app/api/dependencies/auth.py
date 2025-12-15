"""
Authorization dependencies for FastAPI routes.

This module provides reusable dependency functions for route-level authorization,
including authentication and role-based access control.
"""

from fastapi import Depends, HTTPException, status
from app.api.controllers.authController import get_current_user
from app.db.models.userModel import UserModel


async def require_auth(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    Dependency that requires any authenticated user.
    
    Args:
        current_user: The authenticated user from the JWT token
        
    Returns:
        UserModel: The authenticated user
        
    Raises:
        HTTPException: If user is not authenticated (handled by get_current_user)
    """
    return current_user


async def require_manager(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    Dependency that requires the user to be a manager.
    
    Args:
        current_user: The authenticated user from the JWT token
        
    Returns:
        UserModel: The authenticated manager user
        
    Raises:
        HTTPException: If user is not authenticated or not a manager
    """
    if not getattr(current_user, "is_manager", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can perform this action"
        )
    return current_user

