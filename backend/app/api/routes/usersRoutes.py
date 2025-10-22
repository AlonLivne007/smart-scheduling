from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.userSchema import UserCreate, UserRead, UserUpdate
from app.api.controllers.userController import (
    create_user, get_all_users, get_user, update_user, delete_user
)

router = APIRouter(prefix="/users", tags=["Users"])

# ➕ Create user
@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Create a new user")
async def add_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = await create_user(db, payload)
    return user

# 📋 List users
@router.get("/", response_model=List[UserRead], status_code=status.HTTP_200_OK, summary="Get all users")
async def list_users(db: Session = Depends(get_db)):
    users = await get_all_users(db)
    return users

# 🔍 Get single user
@router.get("/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK, summary="Get a user by ID")
async def get_single_user(user_id: int, db: Session = Depends(get_db)):
    user = await get_user(db, user_id)
    return user

# ✏️ Update user
@router.put("/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK, summary="Update a user")
async def edit_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = await update_user(db, user_id, payload)
    return user

# ❌ Delete user
@router.delete("/{user_id}", status_code=status.HTTP_200_OK, summary="Delete a user")
async def remove_user(user_id: int, db: Session = Depends(get_db)):
    result = await delete_user(db, user_id)
    return result
