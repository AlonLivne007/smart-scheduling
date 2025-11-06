"""
User model definition.

This module defines the User ORM model representing employees in the scheduling system.
Users can have multiple roles and different status states (active, vacation, sick).
"""

from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.db.session import Base


class UserStatus(PyEnum):
    """Employee status enumeration."""
    ACTIVE = "active"
    VACATION = "vacation"
    SICK = "sick"


class UserModel(Base):
    """
    User model representing an employee in the scheduling system.
    
    Attributes:
        user_id: Primary key identifier
        user_full_name: Employee's full name
        user_email: Unique email address
        user_status: Current employment status
        hashed_password: Encrypted password
        is_manager: Managerial privileges flag
        roles: Associated role assignments
    """
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    user_full_name = Column(String(255), nullable=False)
    user_email = Column(String(255), unique=True, index=True, nullable=False)
    user_status = Column(String(50), nullable=False,
                         default=UserStatus.ACTIVE.value)
    hashed_password = Column(String(255), nullable=False)
    is_manager = Column(Boolean, default=False)

    # Many-to-many relationship with roles
    roles = relationship(
        "RoleModel",
        secondary="user_roles",
        lazy="selectin",
    )

    weekly_schedules = relationship(
        "WeeklyScheduleModel",
        back_populates="created_by",
        lazy="selectin"
    )

    assignments = relationship(
        "ShiftAssignmentModel",
        back_populates="user",
        cascade="all, delete-orphan"
    )

