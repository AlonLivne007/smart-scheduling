"""
Authentication controller module.

This module handles JWT token creation, verification, and user authentication
for the Smart Scheduling application.

Controllers use repositories for database access - no direct ORM access.
"""
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.core.config import settings
from app.data.models.user_model import UserModel
from app.data.repositories.user_repository import UserRepository
from app.api.dependencies.repositories import get_user_repository

# Matches your /users/login route
bearer_scheme = HTTPBearer()


def create_access_token(data: dict) -> str:
    """
    Create a JWT token with expiration time.
    
    Args:
        data: Dictionary containing token payload (typically user_email and user_id)
        
    Returns:
        str: Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string to verify
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserModel:
    """
    Dependency function to get the current authenticated user from JWT token.
    
    Uses repository for database access - no direct ORM access.
    
    Args:
        creds: HTTP authorization credentials from header
        user_repository: UserRepository instance (dependency injection)
        
    Returns:
        UserModel: The authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = creds.credentials

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload.get("sub")         # you encode sub = user_email
        uid = payload.get("user_id")       # and also user_id
    except JWTError:
        raise credentials_exception

    user = None
    if uid is not None:
        user = user_repository.get_by_id(int(uid))
    if user is None and email:
        user = user_repository.get_by_email(email)

    if not user:
        raise credentials_exception

    return user
