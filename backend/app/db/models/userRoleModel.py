"""
User-Role association model.

This module defines the association table for the many-to-many relationship
between users and roles, enabling users to have multiple roles.
"""

from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.db.session import Base


class UserRoleModel(Base):
    """
    Association table linking users to their assigned roles.
    
    Attributes:
        user_id: Foreign key to users table
        role_id: Foreign key to roles table
    """
    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True)

    # Ensure unique user-role combinations
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )
