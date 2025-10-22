"""
User model definition.

This module defines the User ORM model representing employees in the scheduling system.
Each user may hold multiple roles (e.g., Waiter, Bartender) and can have administrative
privileges (is_manager) that grant permission to manage shifts and employees.

Author: Alon Livne
"""

from sqlalchemy import Column, Integer, String, Enum, Boolean
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from app.db.session import Base
from app.db.models.userRoleModel import user_roles


class UserStatus(PyEnum):
    """
    Enumeration for user statuses.

    Values:
        ACTIVE: The user is currently active.
        VACATION: The user is on vacation.
        SICK: The user is on sick leave.
    """
    ACTIVE = "active"
    VACATION = "vacation"
    SICK = "sick"


class UserModel(Base):
    """
    Represents a user (employee or manager) in the scheduling system.

    Attributes:
        user_id (int): Unique identifier for the user.
        user_full_name (str): Full name of the employee.
        user_email (str): Email address (unique).
        user_hashed_password (str): Encrypted password for authentication.
        is_manager (bool): Indicates whether the user has administrative privileges.
        user_status (UserStatus): Current employment status.
        roles (list[Role]): List of roles assigned to the user (many-to-many relationship).
    """

    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    user_full_name = Column(String, nullable=False)
    user_email = Column(String, unique=True, nullable=False)
    user_hashed_password = Column(String, nullable=False)
    is_manager = Column(Boolean, default=False)
    user_status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)

    # Many-to-many relationship with Role
    roles = relationship("RoleModel", secondary=user_roles, back_populates="users")

    def __repr__(self):
        """Readable string representation of a User."""
        return f"<User(name='{self.user_full_name}', is_manager={self.is_manager}, status='{self.user_status.value}')>"
