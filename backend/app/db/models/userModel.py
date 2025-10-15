"""
User model definition.

This module defines the User ORM model, representing employees in the scheduling system.
Each user has a rank, a status, and can be assigned to multiple roles.

"""

from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
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


class User(Base):
    """
    Represents an employee in the scheduling system.

    Attributes:
        user_id (int): Unique identifier for the user.
        user_full_name (str): Full name of the user.
        user_email (str): Email address (must be unique).
        user_hashed_password (str): Encrypted user password.
        user_rank_id (int): Foreign key linking to the user's Rank.
        user_status (UserStatus): Current status (active, vacation, or sick).
        user_created_at (datetime): Timestamp when the user was created.
        rank (Rank): Relationship to the user's rank.
        roles (list[Role]): List of roles assigned to the user.
    """

    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    user_full_name = Column(String, nullable=False)
    user_email = Column(String, unique=True, nullable=False)
    user_hashed_password = Column(String, nullable=False)
    user_rank_id = Column(Integer, ForeignKey("ranks.rank_id"), nullable=True)
    user_status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    user_created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    rank = relationship("Rank", back_populates="users")
    roles = relationship("Role", secondary=user_roles, back_populates="users")

    def __repr__(self):
        """Return a readable string representation of the User object."""
        return f"<User(name='{self.user_full_name}', status='{self.user_status.value}')>"
