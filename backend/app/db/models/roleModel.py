"""
Role model definition.

This module defines the Role ORM model representing job positions or responsibilities
within the organization (e.g., 'Waiter', 'Bartender', 'Host'). Users can be assigned
multiple roles through a many-to-many relationship.
"""

from sqlalchemy import Column, Integer, String, Index
from sqlalchemy.orm import relationship
from app.db.session import Base


class RoleModel(Base):
    """
    Role model representing a job position or responsibility.
    
    Attributes:
        role_id: Primary key identifier
        role_name: Name of the role (unique)
        users: Users assigned to this role
    """
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(100), unique=True, nullable=False, index=True)

    # Many-to-many relationship with users
    users = relationship(
        "UserModel",
        secondary="user_roles",
        back_populates="roles",
        lazy="selectin"
    )

    shift_templates = relationship(
        "ShiftTemplateModel",
        secondary="shift_role_requirements",
        back_populates="required_roles",
        lazy="selectin"
    )

    assignments = relationship(
        "ShiftAssignmentModel",
        back_populates="role",
        lazy="selectin"
    )

    def __repr__(self):
        """String representation of the role."""
        return f"<Role(name='{self.role_name}')>"