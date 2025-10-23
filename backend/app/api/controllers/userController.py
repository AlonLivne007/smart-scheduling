
"""
User controller module.

This module contains business logic for user management operations including
creation, retrieval, updating, and deletion of user records.
"""

from werkzeug.security import generate_password_hash
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from app.db.models.userModel import UserModel
from app.db.models.roleModel import RoleModel
from app.schemas.userSchema import UserCreate, UserUpdate


def _resolve_roles(db: Session, role_ids: Optional[List[int]] = None) -> List[RoleModel]:
    """
    Validate and fetch roles by their IDs.
    
    Args:
        db: Database session
        role_ids: List of role IDs to validate
        
    Returns:
        List of valid RoleModel instances
        
    Raises:
        HTTPException: If any role IDs don't exist
    """
    if not role_ids:
        return []

    roles = db.query(RoleModel).filter(RoleModel.role_id.in_(role_ids)).all()
    found_ids = {r.role_id for r in roles}
    missing = [r for r in role_ids if r not in found_ids]

    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The following role IDs do not exist: {missing}"
        )

    return roles


async def create_user(db: Session, data: UserCreate) -> UserModel:
    """
    Create a new user with optional role assignments.
    
    Args:
        db: Database session
        data: User creation data
        
    Returns:
        Created UserModel instance
        
    Raises:
        HTTPException: If email exists or database error occurs
    """
    try:
        # Check for unique email
        if db.query(UserModel).filter(UserModel.user_email == data.user_email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{data.user_email}' is already in use."
            )
        
        # Hash password and create user
        hashed_pw = generate_password_hash(data.user_password)
        user = UserModel(
            user_full_name=data.user_full_name,
            user_email=data.user_email,
            user_status=data.user_status,
            hashed_password=hashed_pw,
            is_manager=data.is_manager,
        )

        # Assign roles if provided
        roles = _resolve_roles(db, data.roles_by_id)
        if roles:
            user.roles = roles

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_all_users(db: Session) -> List[UserModel]:
    """
    Retrieve all users from the database.
    
    Args:
        db: Database session
        
    Returns:
        List of all UserModel instances
        
    Raises:
        HTTPException: If database error occurs
    """
    try:
        return db.query(UserModel).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def get_user(db: Session, user_id: int) -> UserModel:
    """
    Retrieve a single user by ID.
    
    Args:
        db: Database session
        user_id: User identifier
        
    Returns:
        UserModel instance
        
    Raises:
        HTTPException: If user not found or database error occurs
    """
    try:
        user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def update_user(db: Session, user_id: int, data: UserUpdate) -> UserModel:
    """
    Update an existing user's information.
    
    Args:
        db: Database session
        user_id: User identifier
        data: Update data
        
    Returns:
        Updated UserModel instance
        
    Raises:
        HTTPException: If user not found, email conflict, or database error occurs
    """
    try:
        user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Validate email uniqueness if changed
        if data.user_email and data.user_email != user.user_email:
            if db.query(UserModel).filter(UserModel.user_email == data.user_email).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{data.user_email}' is already in use."
                )

        # Apply field updates
        if data.user_full_name is not None:
            user.user_full_name = data.user_full_name
        if data.user_email is not None:
            user.user_email = data.user_email
        if data.user_status is not None:
            user.user_status = data.user_status
        if data.is_manager is not None:
            user.is_manager = data.is_manager

        # Update roles if provided
        if data.roles_by_id is not None:
            roles = _resolve_roles(db, data.roles_by_id)
            user.roles = roles

        db.commit()
        db.refresh(user)
        return user

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def delete_user(db: Session, user_id: int) -> dict:
    """
    Delete a user from the database.
    
    Args:
        db: Database session
        user_id: User identifier
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If user not found or database error occurs
    """
    try:
        user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        db.delete(user)
        db.commit()
        return {"message": "User deleted successfully"}

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
