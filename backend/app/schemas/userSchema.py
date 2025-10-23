"""
User schema definitions.

This module defines Pydantic schemas for user data validation and serialization
in API requests and responses.
"""

from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class UserStatus(str, Enum):
    """User employment status enumeration."""
    ACTIVE = "active"
    VACATION = "vacation"
    SICK = "sick"


class RoleSummary(BaseModel):
    """Simplified role representation for user responses."""
    role_id: int
    role_name: str

    class Config:
        model_config = {"from_attributes": True}


class UserBase(BaseModel):
    """Base user schema with common fields."""
    user_full_name: str = Field(..., min_length=2)
    user_email: EmailStr
    user_status: UserStatus = UserStatus.ACTIVE
    is_manager: bool = False


class UserCreate(UserBase):
    """Schema for creating new users."""
    user_password: str = Field(..., min_length=6)
    roles_by_id: Optional[List[int]] = None


class UserLogin(BaseModel):
    """Schema for user authentication."""
    user_email: EmailStr
    user_password: str = Field(...)


class UserUpdate(BaseModel):
    """Schema for updating existing users."""
    user_full_name: Optional[str] = None
    user_email: Optional[EmailStr] = None
    user_status: Optional[UserStatus] = None
    is_manager: Optional[bool] = None
    roles_by_id: Optional[List[int]] = None


class UserRead(BaseModel):
    """Schema for user data in API responses."""
    user_id: int
    user_full_name: str
    user_email: EmailStr
    user_status: UserStatus
    is_manager: bool
    roles: List[RoleSummary] = []

    class Config:
        model_config = {"from_attributes": True}
