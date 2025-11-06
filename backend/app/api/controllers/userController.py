
"""
User controller module.

This module contains business logic for user management operations including
creation, retrieval, updating, and deletion of user records.
"""
from datetime import datetime, timedelta
import os

from werkzeug.security import generate_password_hash, check_password_hash
from jose import JWTError, jwt
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.db.models.userModel import UserModel
from app.db.models.roleModel import RoleModel
from app.schemas.userSchema import UserCreate, UserUpdate, UserLogin, \
    LoginResponse, UserRead

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRE_DAYS", "3"))


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

    return list(set(roles))


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

    except HTTPException:
        # Re-raise HTTPException (e.g., 404, 400) without modification
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        # Check if it's a unique constraint violation for email
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        if 'unique' in error_str.lower() or 'duplicate' in error_str.lower():
            if 'user_email' in error_str.lower() or 'email' in error_str.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{data.user_email}' is already in use."
                )
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



def create_access_token(data: dict) -> str:
    """
    Create a JWT token with expiration time.
    
    Args:
        data: Dictionary containing user data to encode in token
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string to verify
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid or expired token"
        )


async def authenticate_user(db: Session, data: UserLogin) -> LoginResponse:
    """
    Authenticate user and return JWT token if valid.
    
    Args:
        db: Database session
        data: Login credentials
        
    Returns:
        LoginResponse containing JWT token and user data
        
    Raises:
        HTTPException: If user not found or password invalid
    """
    user = db.query(UserModel).filter(UserModel.user_email == data.user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )

    if not check_password_hash(user.hashed_password, data.user_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid email or password"
        )

    # Create JWT token
    access_token = create_access_token(
        data={"sub": user.user_email, "user_id": user.user_id}
    )

    # Convert user to response format
    user_data = UserRead.model_validate(user)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_data
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
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
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
    except HTTPException:
        # Re-raise HTTPException (e.g., 404) without modification
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
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

    except HTTPException:
        # Re-raise HTTPException (e.g., 404, 400) without modification
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        # Check if it's a unique constraint violation for email
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        if 'unique' in error_str.lower() or 'duplicate' in error_str.lower():
            if 'user_email' in error_str.lower() or 'email' in error_str.lower():
                email = data.user_email if data.user_email else user.user_email
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{email}' is already in use."
                )
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

    except HTTPException:
        # Re-raise HTTPException (e.g., 404, 400) without modification
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        # Check if it's a unique constraint violation for email
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        if 'unique' in error_str.lower() or 'duplicate' in error_str.lower():
            if 'user_email' in error_str.lower() or 'email' in error_str.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{data.user_email}' is already in use."
                )
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
