from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.db.session import Base


class UserStatus(PyEnum):
    ACTIVE = "active"
    VACATION = "vacation"
    SICK = "sick"


class UserModel(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    user_full_name = Column(String(255), nullable=False)
    user_email = Column(String(255), unique=True, index=True, nullable=False)
    user_status = Column(String(50), nullable=False,
                         default=UserStatus.ACTIVE.value)
    hashed_password = Column(String(255), nullable=False)
    is_manager = Column(Boolean, default=False)

    roles = relationship(
        "RoleModel",
        secondary="user_roles",
        lazy="selectin",
    )
