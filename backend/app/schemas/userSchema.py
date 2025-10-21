"""
Pydantic schemas for the User model.

These schemas define how User-related data is structured for requests (input)
and responses (output). users can have
multiple roles and may possess managerial privileges (is_manager).

"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.roleSchema import RoleRead


class UserBase(BaseModel):
    """
    Base schema shared by all User operations.
    Contains non-sensitive user information.
    """
    user_full_name: str
    user_email: EmailStr
    user_status: Optional[str] = "active"


class UserCreate(UserBase):
    """
        Schema used for user registration or creation.
        Includes password and optional role/manager fields.
        """
    user_password: str
    is_manager: Optional[bool] = False  # חדש
    roles: List[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """
    Schema used for updating an existing user.
    Fields are optional to support partial updates.
    """
    user_full_name: Optional[str] = None
    user_email: Optional[EmailStr] = None
    user_status: Optional[str] = None
    is_manager: Optional[bool] = None
    user_password: Optional[str] = None


class UserRead(UserBase):
    """
    Schema used for returning user data in API responses.
    Includes related Roles.
    """
    user_id: int
    roles: List[RoleRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}
