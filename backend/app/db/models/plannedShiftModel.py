"""
Planned shift model definition.

This module defines the PlannedShift ORM model representing a specific scheduled
shift instance within a weekly schedule. Each planned shift is an instantiation
of a shift template for a particular date and time, with assigned employees
and a status tracking its assignment completion.
"""

from sqlalchemy import Column, Integer, Date, ForeignKey, String, Enum as SqlEnum, \
    DateTime, Index
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum


class PlannedShiftStatus(enum.Enum):
    """
    Enumeration for planned shift status states.
    
    Values:
        PLANNED: Shift is created but not yet assigned
        PARTIALLY_ASSIGNED: Some but not all required roles are filled
        FULLY_ASSIGNED: All required roles have been assigned
        CANCELLED: Shift has been cancelled
    """
    PLANNED = "PLANNED"
    PARTIALLY_ASSIGNED = "PARTIALLY_ASSIGNED"
    FULLY_ASSIGNED = "FULLY_ASSIGNED"
    CANCELLED = "CANCELLED"


class PlannedShiftModel(Base):
    """
    Planned shift model representing a specific scheduled shift instance.
    
    Attributes:
        planned_shift_id: Primary key identifier
        weekly_schedule_id: Foreign key to the weekly schedule containing this shift
        shift_template_id: Foreign key to the shift template this shift is based on
        date: Date of the shift
        start_time: Start date and time of the shift
        end_time: End date and time of the shift
        location: Location where the shift takes place
        status: Current assignment status of the shift
        weekly_schedule: Relationship to the parent weekly schedule
        shift_template: Relationship to the shift template
        assignments: Relationship to user assignments for this shift
    """

    __tablename__ = "planned_shifts"

    planned_shift_id = Column(Integer, primary_key=True, index=True)

    weekly_schedule_id = Column(
        Integer,
        ForeignKey("shift_weekly_schedule.weekly_schedule_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    shift_template_id = Column(
        Integer,
        ForeignKey("shift_templates.shift_template_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    date = Column(Date, nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=False)

    status = Column(
        SqlEnum(PlannedShiftStatus, name="plannedshiftstatus"),
        nullable=False,
        default=PlannedShiftStatus.PLANNED
    )

    weekly_schedule = relationship(
        "WeeklyScheduleModel",
        back_populates="planned_shifts",
        lazy="selectin"
    )

    shift_template = relationship(
        "ShiftTemplateModel",
        back_populates="planned_shifts",
        lazy="selectin"
    )

    assignments = relationship(
        "ShiftAssignmentModel",
        back_populates="planned_shift",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        return (
            f"<PlannedShift("
            f"date={self.date}, "
            f"template_id={self.shift_template_id}, "
            f"location='{self.location}', "
            f"status='{self.status.value}')>"
        )
