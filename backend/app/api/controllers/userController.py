"""
User controller module.

This module contains business logic for user management operations including
creation, retrieval, updating, and deletion of user records.
"""
from typing import List, Optional

from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.api.controllers.authController import create_access_token
from app.db.models.userModel import UserModel
from app.db.models.roleModel import RoleModel
from app.schemas.userSchema import (
    UserCreate, UserUpdate, UserLogin, LoginResponse, UserRead
)


def _resolve_roles(db: Session, role_ids: Optional[List[int]] = None) -> List[RoleModel]:
    """Validate and fetch roles by their IDs."""
    if not role_ids:
        return []

    # Fetch roles - database foreign key will validate existence on commit
    roles = db.query(RoleModel).filter(RoleModel.role_id.in_(role_ids)).all()
    
    # Remove duplicates 
    unique_roles = list(set(roles))
    
    # Validate all requested roles were found (foreign key will also catch this, but this provides better UX)
    found_ids = {r.role_id for r in unique_roles}
    missing = [rid for rid in role_ids if rid not in found_ids]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The following role IDs do not exist: {missing}"
        )
    
    return unique_roles


async def create_user(db: Session, user_data: UserCreate) -> UserModel:
    """Create a new user with optional role assignments."""
    try:
        hashed_pw = generate_password_hash(user_data.user_password)
        user = UserModel(
            user_full_name=user_data.user_full_name,
            user_email=user_data.user_email,
            hashed_password=hashed_pw,
            is_manager=user_data.is_manager,
        )

        roles = _resolve_roles(db, user_data.roles_by_id)
        if roles:
            user.roles = roles

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {error_str}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def authenticate_user(db: Session, user_login_data: UserLogin) -> LoginResponse:
    """
    Authenticate user and return JWT token if valid.

    Security/UX: unify errors → 401 for both unknown user and bad password.
    """
    user = db.query(UserModel).filter(UserModel.user_email == user_login_data.user_email).first()
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


async def get_all_users(db: Session) -> List[UserModel]:
    """Retrieve all users from the database."""
    try:
        return db.query(UserModel).all()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_user(db: Session, user_id: int) -> UserModel:
    """Retrieve a single user by ID."""
    try:
        user = db.get(UserModel, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def update_user(db: Session, user_id: int, data: UserUpdate) -> UserModel:
    """Update an existing user's information (incl. optional password, roles)."""
    try:
        user = db.get(UserModel, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if data.user_full_name is not None:
            user.user_full_name = data.user_full_name
        if data.user_email is not None:
            user.user_email = data.user_email
        if data.is_manager is not None:
            user.is_manager = data.is_manager

        # NEW: password change
        if data.new_password:
            user.hashed_password = generate_password_hash(data.new_password)

        # Replace role set if provided
        if data.roles_by_id is not None:
            roles = _resolve_roles(db, data.roles_by_id)
            user.roles = roles

        db.commit()
        db.refresh(user)
        return user

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {error_str}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def delete_user(db: Session, user_id: int) -> dict:
    """Delete a user from the database."""
    try:
        user = db.get(UserModel, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        db.delete(user)
        db.commit()
        return {"message": "User deleted successfully"}

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {error_str}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )