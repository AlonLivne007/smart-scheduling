"""
Shift template model definition.

This module defines the ShiftTemplate ORM model representing predefined types
of shifts (e.g., 'Morning Shift', 'Evening Shift'). Templates define the
structure, timing, location, and required roles for shifts that can be
instantiated in weekly schedules.
"""

from sqlalchemy import Column, Integer, String, Time, Index
from sqlalchemy.orm import relationship
from app.data.session import Base
from app.data.models.shift_role_requirements_table import shift_role_requirements


class ShiftTemplateModel(Base):
    """
    Shift template model representing a predefined type of shift.
    
    Attributes:
        shift_template_id: Primary key identifier
        shift_template_name: Name of the shift type (unique)
        start_time: Shift start time (time only, not date)
        end_time: Shift end time (time only, not date)
        location: Where the shift takes place
        required_roles: List of roles needed for this shift (many-to-many)
        planned_shifts: Relationship to planned shift instances created from this template
    """
    __tablename__ = "shift_templates"

    shift_template_id = Column(Integer, primary_key=True, index=True)
    shift_template_name = Column(String(255), unique=True, nullable=False, index=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    location = Column(String(255), nullable=True)

    # Many-to-many relationship with roles
    required_roles = relationship(
        "RoleModel",
        secondary=shift_role_requirements,
        back_populates="shift_templates",
        lazy="selectin"
    )

    planned_shifts = relationship(
        "PlannedShiftModel",
        back_populates="shift_template",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<ShiftTemplate(name='{self.shift_template_name}', location='{self.location}')>"
