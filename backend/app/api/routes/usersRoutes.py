# backend/app/api/routes/usersRoutes.py
"""
User routes module.

This module defines the REST API endpoints for user management operations
including CRUD operations for user records.
"""

from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.api.controllers.userController import (
    create_user, get_all_users, get_user, update_user, delete_user,
    authenticate_user
)
from app.db.session import get_db
from app.schemas.userSchema import (
    UserCreate, UserRead, UserUpdate, UserLogin, LoginResponse
)

# AuthN/Authorization
from app.api.controllers.authController import get_current_user
from app.api.dependencies.auth import require_auth, require_manager
from app.db.models.userModel import UserModel

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user",
)
async def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate a user by email and password.

    Returns:
        JWT access token and user data (includes is_manager).
    """
    return await authenticate_user(db, payload)


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user",
    dependencies=[Depends(require_auth)],
)
async def get_me(current_user: UserModel = Depends(get_current_user)):
    return current_user


# ---------------------- Collection routes -------------------

@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def add_user(payload: UserCreate, db: Session = Depends(get_db)):
    return await create_user(db, payload)


@router.get(
    "/",
    response_model=List[UserRead],
    status_code=status.HTTP_200_OK,
    summary="Get all users",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def list_users(db: Session = Depends(get_db)):
    return await get_all_users(db)


# ---------------------- Resource routes ---------------------

@router.get(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get a user by ID",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_single_user(user_id: int, db: Session = Depends(get_db)):
    return await get_user(db, user_id)


@router.put(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Update a user",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def edit_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    return await update_user(db, user_id, payload)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a user",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def remove_user(user_id: int, db: Session = Depends(get_db)):
    return await delete_user(db, user_id)