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
    Fetch roles by their IDs.
    
    Note: Foreign key constraint will validate role existence on commit.
    
    Args:
        db: Database session
        role_ids: List of role IDs to fetch
        
    Returns:
        List of RoleModel instances (empty list if role_ids is None/empty)
    """
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
    """
    Create a new user with optional role assignments.
    
    Args:
        db: Database session
        user_data: User creation data
        
    Returns:
        Created UserModel instance
        
    Raises:
        HTTPException: If email exists or database error occurs
    """
    try:
        # Hash password and create user
        hashed_pw = generate_password_hash(user_data.user_password)
        user = UserModel(
            user_full_name=user_data.user_full_name,
            user_email=user_data.user_email,
            user_status=user_data.user_status,
            hashed_password=hashed_pw,
            is_manager=user_data.is_manager,
        )

        # Assign roles if provided
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


async def authenticate_user(db: Session, user_login_data: UserLogin) -> LoginResponse:
    """
    Authenticate user and return JWT token if valid.
    
    Args:
        db: Database session
        user_login_data: Login credentials
        
    Returns:
        LoginResponse containing JWT token and user data
        
    Raises:
        HTTPException: If user not found, password invalid, or database error occurs
    """
    try:
        user = db.query(UserModel).filter(UserModel.user_email == user_login_data.user_email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User not found"
            )

        if not check_password_hash(user.hashed_password, user_login_data.user_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid email or password"
            )

        # Create JWT token
        access_token = create_access_token(
            data={"sub": user.user_email, "user_id": user.user_id}
        )

        # Convert user to response format
        user_read = UserRead.model_validate(user)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_read
        )
    except HTTPException:
        raise
    except SQLAlchemyError as e:
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


async def update_user(db: Session, user_id: int, user_data: UserUpdate) -> UserModel:
    """
    Update an existing user's information.
    
    Args:
        db: Database session
        user_id: User identifier
        user_data: Update data
        
    Returns:
        Updated UserModel instance
        
    Raises:
        HTTPException: If user not found, email conflict, or database error occurs
    """
    try:
        user = db.get(UserModel, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Apply field updates
        if user_data.user_full_name is not None:
            user.user_full_name = user_data.user_full_name
        if user_data.user_email is not None:
            user.user_email = user_data.user_email
        if user_data.user_status is not None:
            user.user_status = user_data.user_status
        if user_data.is_manager is not None:
            user.is_manager = user_data.is_manager

        # Update roles if provided
        if user_data.roles_by_id is not None:
            roles = _resolve_roles(db, user_data.roles_by_id)
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