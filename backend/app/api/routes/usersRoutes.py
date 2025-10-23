"""
User routes module.

This module defines the REST API endpoints for user management operations
including CRUD operations for user records.
"""

from typing import List

from fastapi import APIRouter, Depends, status, HTTPException, Header
from sqlalchemy.orm import Session

from app.api.controllers.userController import (
    create_user, get_all_users, get_user, update_user, delete_user,
    authenticate_user, verify_token
)
from app.db.session import get_db
from app.schemas.userSchema import UserCreate, UserRead, UserUpdate, UserLogin, \
    LoginResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED,
             summary="Create a new user")
async def add_user(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.
    
    Args:
        payload: User creation data
        db: Database session dependency
        
    Returns:
        Created user data
    """
    user = await create_user(db, payload)
    return user


@router.post("/login", response_model=LoginResponse,
             status_code=status.HTTP_200_OK, summary="Authenticate user")
async def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate a user by email and password.
    
    Args:
        payload: Login credentials
        db: Database session dependency
        
    Returns:
        JWT access token and user data
    """
    return await authenticate_user(db, payload)


@router.get("/profile", response_model=UserRead, status_code=status.HTTP_200_OK,
            summary="Get current user profile")
async def get_current_user_profile(
    authorization: str = Header(..., description="Bearer token"),
    db: Session = Depends(get_db)
):
    """
    Get the current user's profile using JWT token.
    
    Args:
        authorization: Bearer token in Authorization header
        db: Database session dependency
        
    Returns:
        Current user's profile data
    """
    try:
        # Extract token from "Bearer <token>"
        token = authorization.split(" ")[1]
        payload = verify_token(token)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        user = await get_user(db, user_id)
        return user
        
    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )


@router.get("/", response_model=List[UserRead], status_code=status.HTTP_200_OK,
            summary="Get all users")
async def list_users(db: Session = Depends(get_db)):
    """
    Retrieve all users from the system.
    
    Args:
        db: Database session dependency
        
    Returns:
        List of all users
    """
    users = await get_all_users(db)
    return users


@router.get("/{user_id}", response_model=UserRead,
            status_code=status.HTTP_200_OK, summary="Get a user by ID")
async def get_single_user(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific user by their ID.
    
    Args:
        user_id: User identifier
        db: Database session dependency
        
    Returns:
        User data
    """
    user = await get_user(db, user_id)
    return user


@router.put("/{user_id}", response_model=UserRead,
            status_code=status.HTTP_200_OK, summary="Update a user")
async def edit_user(user_id: int, payload: UserUpdate,
                    db: Session = Depends(get_db)):
    """
    Update an existing user's information.
    
    Args:
        user_id: User identifier
        payload: Update data
        db: Database session dependency
        
    Returns:
        Updated user data
    """
    user = await update_user(db, user_id, payload)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_200_OK,
               summary="Delete a user")
async def remove_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete a user from the system.
    
    Args:
        user_id: User identifier
        db: Database session dependency
        
    Returns:
        Deletion confirmation message
    """
    result = await delete_user(db, user_id)
    return result
