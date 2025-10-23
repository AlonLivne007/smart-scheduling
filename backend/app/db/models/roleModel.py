"""
Role model definition.

This module defines the Role ORM model representing job positions or responsibilities
within the organization (e.g., 'Waiter', 'Bartender', 'Host'). Users can be assigned
multiple roles through a many-to-many relationship.
"""

from sqlalchemy import Column, Integer, String
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
    role_name = Column(String, unique=True, nullable=False)

    # Many-to-many relationship with users
    users = relationship(
        "UserModel",
        secondary="user_roles",
        back_populates="roles",
        lazy="selectin"
    )

    def __repr__(self):
        """String representation of the role."""
        return f"<Role(name='{self.role_name}')>"