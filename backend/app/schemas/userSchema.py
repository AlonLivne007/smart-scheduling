"""
Pydantic schemas for the User model.

These schemas define how User-related data is structured for requests (input)
and responses (output). They also include references to Rank and Role schemas
to represent relationships between entities.

"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.rankSchema import RankRead
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
    Includes the password field for secure input (not returned in responses).
    """
    user_password: str


class UserUpdate(BaseModel):
    """
    Schema used for updating an existing user.
    Fields are optional to support partial updates.
    """
    user_full_name: Optional[str] = None
    user_email: Optional[EmailStr] = None
    user_status: Optional[str] = None
    user_rank_id: Optional[int] = None
    user_password: Optional[str] = None


class UserRead(UserBase):
    """
    Schema used for returning user data in API responses.
    Includes related Rank and Roles for detailed information.
    """
    user_id: int
    user_created_at: datetime
    rank: Optional[RankRead] = None
    roles: List[RoleRead] = Field(default_factory=list)

    class Config:
        orm_mode = True
