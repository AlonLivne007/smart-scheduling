"""
Controller for user-related database operations.

This module contains the business logic for creating, reading, and managing users.
It communicates with the database using SQLAlchemy sessions.

Author: Alon Livne
"""

from sqlalchemy.orm import Session

from app.db.models.roleModel import Role
from app.db.models.userModel import User
from app.schemas.userSchema import UserCreate
from werkzeug.security import generate_password_hash
from fastapi import HTTPException


def create_user(db: Session, user_data: UserCreate):
    """
    Creates a new user in the database.

    Args:
        db (Session): SQLAlchemy database session.
        user_data (UserCreate): Validated user input from Pydantic schema.

    Returns:
        User: The newly created user record.
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.user_email == user_data.user_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    hashed_pw = generate_password_hash(user_data.user_password)

    new_user = User(
        user_full_name=user_data.user_full_name,
        user_email=user_data.user_email,
        user_hashed_password=hashed_pw,
        is_manager=user_data.is_manager,
    )
    # טיפול בתפקידים
    roles_to_add = []
    for role_name in user_data.roles:
        # חיפוש לפי שם (לא תלוי רישיות)
        db_role = db.query(Role).filter(Role.role_name.ilike(role_name)).first()
        # אם לא קיים — צור תפקיד חדש
        if not db_role:
            db_role = Role(role_name=role_name)
            db.add(db_role)
            db.flush()
        roles_to_add.append(db_role)
    new_user.roles = roles_to_add

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_all_users(db: Session):
    """
    Retrieves all users from the database.
    """
    return db.query(User).all()


def get_user_by_id(db: Session, user_id: int):
    """
    Retrieves a user by ID.
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user
