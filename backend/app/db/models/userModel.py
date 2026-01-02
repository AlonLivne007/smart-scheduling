"""
User model definition.

This module defines the User ORM model representing employees in the scheduling system.
Users can have multiple roles.
"""

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.db.models.userRoleModel import user_roles
from app.db.models.shiftAssignmentModel import ShiftAssignmentModel
from app.db.models.timeOffRequestModel import TimeOffRequestModel


class UserModel(Base):
    """
    User model representing an employee in the scheduling system.
    
    Attributes:
        user_id: Primary key identifier
        user_full_name: Employee's full name
        user_email: Unique email address
        hashed_password: Encrypted password
        is_manager: Managerial privileges flag
        roles: Associated role assignments
    """
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    user_full_name = Column(String(255), nullable=False)
    user_email = Column(String(255), unique=True, index=True, nullable=False)
    user_status = Column(String(50), nullable=False, default="ACTIVE")
    hashed_password = Column(String(255), nullable=False)
    is_manager = Column(Boolean, default=False)



    # Many-to-many relationship with roles
    roles = relationship(
        "RoleModel",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
    )

    weekly_schedules = relationship(
        "WeeklyScheduleModel",
        foreign_keys="WeeklyScheduleModel.created_by_id",
        back_populates="created_by",
        lazy="selectin"
    )

    assignments = relationship(
        ShiftAssignmentModel,
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    time_off_requests = relationship(
        TimeOffRequestModel,
        foreign_keys=[TimeOffRequestModel.user_id],
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    preferences = relationship(
        "EmployeePreferencesModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        """String representation of the user."""
        return f"<User(name='{self.user_full_name}', email='{self.user_email}')>"
