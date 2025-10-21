"""
API routes for user-related operations.

This module defines all endpoints related to users, such as
creating new users, retrieving users, and listing all users.

Author: Alon Livne
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.userSchema import UserCreate, UserRead
from app.api.controllers.userController import create_user, get_all_users, get_user_by_id

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserRead, status_code=201)
def add_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Endpoint: Create a new user.
    """
    return create_user(db, user_data)


@router.get("/", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    """
    Endpoint: Retrieve all users.
    """
    return get_all_users(db)


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Endpoint: Retrieve a specific user by ID.
    """
    return get_user_by_id(db, user_id)
