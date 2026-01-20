# backend/app/api/routes/usersRoutes.py
"""
User routes module.

This module defines the REST API endpoints for user management operations
including CRUD operations for user records.
Routes use repository dependency injection - no direct DB access.
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.controllers import user_controller
from app.api.controllers.user_controller import (
    create_user, get_user, update_user, delete_user,
    authenticate_user
)
from app.api.dependencies.repositories import get_user_repository, get_role_repository
from app.data.session import get_db
from app.schemas.user_schema import (
    UserCreate, UserRead, UserUpdate, UserLogin, LoginResponse
)

# AuthN/Authorization
from app.api.controllers.auth_controller import get_current_user
from app.api.dependencies.auth import require_auth, require_manager
from app.data.models.user_model import UserModel
from app.data.repositories.user_repository import UserRepository
from app.data.repositories.role_repository import RoleRepository

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user",
)
async def login_user(
    payload: UserLogin,
    user_repository: UserRepository = Depends(get_user_repository)
):
    """
    Authenticate a user by email and password.

    Returns:
        JWT access token and user data (includes is_manager).
    """
    return await authenticate_user(payload, user_repository)


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
async def add_user(
    payload: UserCreate,
    user_repository: UserRepository = Depends(get_user_repository),
    role_repository: RoleRepository = Depends(get_role_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await create_user(payload, user_repository, role_repository, db)


@router.get(
    "/",
    response_model=List[UserRead],
    status_code=status.HTTP_200_OK,
    summary="Get all users",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def list_users(
    user_repository: UserRepository = Depends(get_user_repository)
):
    return await user_controller.list_users(user_repository)


# ---------------------- Resource routes ---------------------

@router.get(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get a user by ID",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_single_user(
    user_id: int,
    user_repository: UserRepository = Depends(get_user_repository)
):
    return await get_user(user_id, user_repository)


@router.put(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Update a user",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def edit_user(
    user_id: int,
    payload: UserUpdate,
    user_repository: UserRepository = Depends(get_user_repository),
    role_repository: RoleRepository = Depends(get_role_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await update_user(user_id, payload, user_repository, role_repository, db)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a user",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def remove_user(
    user_id: int,
    user_repository: UserRepository = Depends(get_user_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await delete_user(user_id, user_repository, db)
