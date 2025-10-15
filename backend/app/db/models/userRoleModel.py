"""
User-Role association table.

This module defines the many-to-many relationship table between Users and Roles.
Each record links one user to one role.

"""

from sqlalchemy import Table, Column, Integer, ForeignKey
from app.db.session import Base

# Association table for many-to-many relationship between Users and Roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.user_id", ondelete="CASCADE")),
    Column("role_id", Integer, ForeignKey("roles.role_id", ondelete="CASCADE"))
)
