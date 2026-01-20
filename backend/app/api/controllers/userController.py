"""
User controller module.

This module contains business logic for user management operations including
creation, retrieval, updating, and deletion of user records.
Controllers use repositories for database access - no direct ORM access.
"""
from typing import List
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session  # Only for type hints
from fastapi import HTTPException, status

from app.api.controllers.authController import create_access_token
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.schemas.userSchema import (
    UserCreate, UserUpdate, UserLogin, LoginResponse, UserRead
)
from app.exceptions.repository import NotFoundError, ConflictError
from app.db.session_manager import transaction


async def create_user(
    user_data: UserCreate,
    user_repository: UserRepository,
    role_repository: RoleRepository,
    db: Session  # For transaction management
) -> UserRead:
    """
    Create a new user with optional role assignments.
    
    Business logic:
    - Check if email already exists
    - Hash password
    - Validate roles exist
    - Create user and assign roles
    """
    try:
        # Business rule: Check if email already exists
        existing = user_repository.get_by_email(user_data.user_email)
        if existing:
            raise ConflictError(f"User with email {user_data.user_email} already exists")
        
        # Hash password
        hashed_password = generate_password_hash(user_data.user_password)
        
        with transaction(db):
            # Create user
            user = user_repository.create(
                user_full_name=user_data.user_full_name,
                user_email=user_data.user_email,
                hashed_password=hashed_password,
                is_manager=user_data.is_manager,
                user_status="ACTIVE"
            )
            
            # Assign roles if provided
            if user_data.roles_by_id:
                # Validate roles exist
                for role_id in user_data.roles_by_id:
                    role_repository.get_by_id_or_raise(role_id)
                user = user_repository.assign_roles(user.user_id, user_data.roles_by_id)
            
            return UserRead.model_validate(user)
            
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


async def authenticate_user(
    user_login_data: UserLogin,
    user_repository: UserRepository
) -> LoginResponse:
    """
    Authenticate user and return JWT token if valid.
    
    Business logic:
    - Find user by email
    - Verify password
    - Generate JWT token
    """
    user = user_repository.get_by_email(user_login_data.user_email)
    
    if not user or not check_password_hash(user.hashed_password, user_login_data.user_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(
        data={"sub": user.user_email, "user_id": user.user_id}
    )
    user_data = UserRead.model_validate(user)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_data
    )


async def get_all_users(user_repository: UserRepository) -> List[UserRead]:
    """Get all users with their roles."""
    users = user_repository.get_all_with_roles()
    return [UserRead.model_validate(user) for user in users]


async def get_user(user_id: int, user_repository: UserRepository) -> UserRead:
    """Get a user by ID."""
    try:
        user = user_repository.get_by_id_or_raise(user_id)
        return UserRead.model_validate(user)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


async def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_repository: UserRepository,
    role_repository: RoleRepository,
    db: Session  # For transaction management
) -> UserRead:
    """
    Update an existing user.
    
    Business logic:
    - Check email uniqueness if email is being changed
    - Update fields
    - Update roles if provided
    - Hash new password if provided
    """
    try:
        user = user_repository.get_by_id_or_raise(user_id)
        
        # Business rule: Check email uniqueness if email is being changed
        if user_data.user_email and user_data.user_email != user.user_email:
            existing = user_repository.get_by_email(user_data.user_email)
            if existing:
                raise ConflictError(f"Email {user_data.user_email} is already taken")
        
        with transaction(db):
            # Update fields
            update_data = {}
            if user_data.user_full_name is not None:
                update_data["user_full_name"] = user_data.user_full_name
            if user_data.user_email is not None:
                update_data["user_email"] = user_data.user_email
            if user_data.is_manager is not None:
                update_data["is_manager"] = user_data.is_manager
            if user_data.new_password:
                update_data["hashed_password"] = generate_password_hash(user_data.new_password)
            
            updated_user = user_repository.update(user_id, **update_data)
            
            # Update roles if provided
            if user_data.roles_by_id is not None:
                # Validate roles exist
                for role_id in user_data.roles_by_id:
                    role_repository.get_by_id_or_raise(role_id)
                updated_user = user_repository.assign_roles(user_id, user_data.roles_by_id)
            
            return UserRead.model_validate(updated_user)
            
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


async def delete_user(
    user_id: int,
    user_repository: UserRepository,
    db: Session  # For transaction management
) -> dict:
    """
    Delete a user.
    
    Business logic:
    - Verify user exists
    - Delete user (cascade will handle related records)
    """
    try:
        user_repository.get_by_id_or_raise(user_id)  # Verify exists
        
        with transaction(db):
            user_repository.delete(user_id)
            return {"message": "User deleted successfully"}
            
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )