from sqlalchemy import Column, Integer, Date, ForeignKey, String, Enum, \
    DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum


class PlannedShiftStatus(enum.Enum):
    PLANNED = "planned"
    PARTIALLY_ASSIGNED = "partially_assigned"
    FULLY_ASSIGNED = "fully_assigned"
    CANCELLED = "cancelled"


class PlannedShiftModel(Base):
    """
    Represents a specific scheduled shift (instance of a ShiftTemplate)
    within a weekly schedule.

    Example: "Morning shift on Monday, Nov 4, 08:00–14:00"
    """

    __tablename__ = "planned_shifts"

    planned_shift_id = Column(Integer, primary_key=True, index=True)

    weekly_schedule_id = Column(
        Integer,
        ForeignKey("shift_weekly_schedule.weekly_schedule_id"),
        nullable=False
    )

    shift_template_id = Column(
        Integer,
        ForeignKey("shift_templates.shift_template_id"),
        nullable=False
    )

    date = Column(Date, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=False)

    status = Column(
        Enum(PlannedShiftStatus),
        nullable=False,
        default=PlannedShiftStatus.PLANNED
    )

    weekly_schedule = relationship(
        "WeeklyScheduleModel",
        back_populates="planned_shifts"
    )

    shift_template = relationship(
        "ShiftTemplateModel",
        back_populates="planned_shifts"
    )

    assignments = relationship(
        "ShiftAssignmentModel",
        back_populates="planned_shift",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<PlannedShift("
            f"date={self.date}, "
            f"template_id={self.shift_template_id}, "
            f"location='{self.location}', "
            f"status='{self.status.value}')>"
        )
