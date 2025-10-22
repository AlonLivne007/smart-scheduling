from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class UserStatus(str, Enum):
    ACTIVE = "active"
    VACATION = "vacation"
    SICK = "sick"


class RoleSummary(BaseModel):
    role_id: int
    role_name: str

    class Config:
        model_config = {"from_attributes": True}


class UserBase(BaseModel):
    user_full_name: str = Field(..., min_length=2)
    user_email: EmailStr
    user_status: UserStatus = UserStatus.ACTIVE
    is_manager: bool = False


class UserCreate(UserBase):
    user_password: str = Field(..., min_length=6)
    roles_by_id: Optional[List[int]] = None


class UserUpdate(BaseModel):
    user_full_name: Optional[str] = None
    user_email: Optional[EmailStr] = None
    user_status: Optional[UserStatus] = None
    is_manager: Optional[bool] = None
    roles_by_id: Optional[List[int]] = None


class UserRead(BaseModel):
    user_id: int
    user_full_name: str
    user_email: EmailStr
    user_status: UserStatus
    is_manager: bool
    roles: List[RoleSummary] = []

    class Config:
        model_config = {"from_attributes": True}
