"""
Role model definition.

This module defines the Role ORM model, representing specific employee positions
or responsibilities (e.g., 'Waiter', 'Bartender', 'Host'). Each user can hold multiple roles.

"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.models.userRoleModel import user_roles
from app.db.session import Base


class Role(Base):
    """
    Represents a specific role within an organization.

    Attributes:
        role_id (int): Unique identifier for the role.
        role_name (str): Name of the role.
        users (list[User]): List of users assigned to this role (many-to-many relationship).
    """

    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String, unique=True, nullable=False)

    # Many-to-many relationship: a Role can belong to many Users
    users = relationship("User", secondary=user_roles, back_populates="roles")

    def __repr__(self):
        """Return a readable string representation of the Role object."""
        return f"<Role(name='{self.role_name}')>"
