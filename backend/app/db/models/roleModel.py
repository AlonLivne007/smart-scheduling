"""
Role model definition.

This module defines the Role ORM model, representing specific employee positions
or responsibilities (e.g., 'Waiter', 'Bartender', 'Host'). Each user can hold multiple roles.

"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.session import Base


class RoleModel(Base):
    """
    Represents a specific role within an organization.

    Attributes:
        role_id (int): Unique identifier for the role.
        role_name (str): Name of the role.
        users (list[UserModel]): Users who hold this role (many-to-many relationship).
    """

    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String, unique=True, nullable=False)

    # Many-to-many relationship with UserModel through the association table 'user_roles'
    users = relationship(
        "UserModel",
        secondary="user_roles",      # שם הטבלה (לא אובייקט)
        back_populates="roles",
        lazy="selectin"
    )

    def __repr__(self):
        """Readable string representation of the Role."""
        return f"<Role(name='{self.role_name}')>"