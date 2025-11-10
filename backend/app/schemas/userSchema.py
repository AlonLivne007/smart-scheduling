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
    ACTIVE = "ACTIVE"
    VACATION = "VACATION"
    SICK = "SICK"


class RoleSummary(BaseModel):
    """Simplified role representation for user responses."""
    role_id: int
    role_name: str = Field(..., max_length=100, description="Name of the role")

    model_config = {"from_attributes": True}


class UserBase(BaseModel):
    """Base user schema with common fields."""
    user_full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Employee's full name"
    )
    user_email: EmailStr = Field(..., description="Unique email address")
    user_status: UserStatus = Field(
        default=UserStatus.ACTIVE,
        description="Current employment status"
    )
    is_manager: bool = Field(
        default=False,
        description="Managerial privileges flag"
    )


class UserCreate(UserBase):
    """Schema for creating new users."""
    user_password: str = Field(
        ...,
        min_length=6,
        max_length=255,
        description="User password (will be hashed before storage)"
    )
    roles_by_id: Optional[List[int]] = Field(
        default=None,
        description="List of role IDs to assign to the user"
    )


class UserUpdate(BaseModel):
    """Schema for updating existing users."""
    user_full_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255,
        description="Employee's full name"
    )
    user_email: Optional[EmailStr] = Field(
        default=None,
        description="Unique email address"
    )
    user_status: Optional[UserStatus] = Field(
        default=None,
        description="Current employment status"
    )
    is_manager: Optional[bool] = Field(
        default=None,
        description="Managerial privileges flag"
    )
    # NEW: optional password change
    new_password: Optional[str] = Field(
        default=None,
        min_length=6,
        max_length=255,
        description="If provided, replaces the current password"
    )
    # If provided, replaces the full role set for the user
    roles_by_id: Optional[List[int]] = Field(
        default=None,
        description="List of role IDs to assign to the user"
    )


class UserRead(BaseModel):
    """Schema for user data in API responses."""
    user_id: int = Field(..., description="Unique user identifier")
    user_full_name: str = Field(..., description="Employee's full name")
    user_email: EmailStr = Field(..., description="Unique email address")
    user_status: UserStatus = Field(..., description="Current employment status")
    is_manager: bool = Field(..., description="Managerial privileges flag")
    roles: List[RoleSummary] = Field(
        default_factory=list,
        description="List of roles assigned to the user"
    )

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    """Schema for user authentication."""
    user_email: EmailStr = Field(..., description="User email address")
    user_password: str = Field(
        ...,
        min_length=1,
        description="User password"
    )


class LoginResponse(BaseModel):
    """Schema for login response containing JWT token and user data."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')"
    )
    user: UserRead = Field(..., description="Authenticated user data")
