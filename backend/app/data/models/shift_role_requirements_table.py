"""
Shift role requirements association table definition.

This module defines the association table for the many-to-many relationship
between shift templates and roles, specifying how many of each role are
required for a given shift template.
"""

from sqlalchemy import Column, Integer, ForeignKey, Table, CheckConstraint, Index
from app.data.session import Base

shift_role_requirements = Table(
    "shift_role_requirements",
    Base.metadata,
    Column("shift_template_id", ForeignKey("shift_templates.shift_template_id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True),
    Column("required_count", Integer, nullable=False, default=1),
    CheckConstraint("required_count > 0", name="check_required_count_positive"),
    Index("idx_shift_role_template", "shift_template_id"),
    Index("idx_shift_role_role", "role_id"),
)