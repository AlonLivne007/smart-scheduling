# app/db/models/shiftTemplateModel.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.models.shiftRoleRequirementsTabel import shift_role_requirements


class ShiftTemplateModel(Base):
    """
    ShiftTemplateModel represents a predefined type of shift.
    For example: 'Morning Shift' or 'Evening Shift'.

    Attributes:
        shift_template_id: Unique identifier
        shift_template_name: Name of the shift type
        start_time: Shift start time
        end_time: Shift end time
        location: Where the shift takes place
        required_roles: List of roles needed for this shift (many-to-many)
    """
    __tablename__ = "shift_templates"

    shift_template_id = Column(Integer, primary_key=True, index=True)
    shift_template_name = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
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
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ShiftTemplate(name='{self.shift_template_name}', location='{self.location}')>"
