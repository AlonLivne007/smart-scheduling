
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
    Fetch roles from DB by their IDs.
    Raise 400 error if some IDs do not exist.
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


# ➕ Create user
async def create_user(db: Session, data: UserCreate) -> UserModel:
    try:
        # unique email check
        if db.query(UserModel).filter(UserModel.user_email == data.user_email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{data.user_email}' is already in use."
            )
        hashed_pw = generate_password_hash(data.user_password)
        # create user object
        user = UserModel(
            user_full_name=data.user_full_name,
            user_email=data.user_email,
            user_status=data.user_status,
            hashed_password=hashed_pw,
            is_manager=data.is_manager,
        )

        # attach roles if provided
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


# 📋 Get all users
async def get_all_users(db: Session) -> List[UserModel]:
    try:
        return db.query(UserModel).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# 🔍 Get single user
async def get_user(db: Session, user_id: int) -> UserModel:
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


# ✏️ Update user
async def update_user(db: Session, user_id: int, data: UserUpdate) -> UserModel:
    try:
        user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # check for email uniqueness if changed
        if data.user_email and data.user_email != user.user_email:
            if db.query(UserModel).filter(UserModel.user_email == data.user_email).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{data.user_email}' is already in use."
                )

        # apply updates
        if data.user_full_name is not None:
            user.user_full_name = data.user_full_name
        if data.user_email is not None:
            user.user_email = data.user_email
        if data.user_status is not None:
            user.user_status = data.user_status
        if data.is_manager is not None:
            user.is_manager = data.is_manager

        # replace roles if provided
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


# ❌ Delete user
async def delete_user(db: Session, user_id: int) -> dict:
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
