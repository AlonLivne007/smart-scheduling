"""
Shift role requirements association table definition.

This module defines the association table for the many-to-many relationship
between shift templates and roles, specifying how many of each role are
required for a given shift template.
"""

from sqlalchemy import Column, Integer, ForeignKey, Table
from app.db.session import Base

shift_role_requirements = Table(
    "shift_role_requirements",
    Base.metadata,
    Column("shift_template_id", ForeignKey("shift_templates.shift_template_id"), primary_key=True),
    Column("role_id", ForeignKey("roles.role_id"), primary_key=True),
    Column("required_count", Integer, nullable=False, default=1),
)