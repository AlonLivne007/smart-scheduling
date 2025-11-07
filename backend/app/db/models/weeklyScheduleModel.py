"""
Weekly schedule model definition.

This module defines the WeeklySchedule ORM model representing a weekly
scheduling period. Each weekly schedule contains multiple planned shifts
and tracks which user created the schedule and when the week starts.
"""

from sqlalchemy import Column, Integer, Date, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.db.session import Base


class WeeklyScheduleModel(Base):
    """
    Weekly schedule model representing a scheduling period for a week.
    
    Attributes:
        weekly_schedule_id: Primary key identifier
        week_start_date: Start date of the week being scheduled
        created_by_id: Foreign key to the user who created this schedule
        created_by: Relationship to the user who created this schedule
        planned_shifts: Relationship to all planned shifts in this weekly schedule
    """
    __tablename__ = "shift_weekly_schedule"
    weekly_schedule_id = Column(Integer, primary_key=True, index=True)
    week_start_date = Column(Date, nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    created_by = relationship("UserModel", back_populates="weekly_schedules", lazy="selectin")

    planned_shifts = relationship(
        "PlannedShiftModel",
        back_populates="weekly_schedule",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        """String representation of the weekly schedule."""
        return f"<WeeklySchedule(id={self.weekly_schedule_id}, week_start={self.week_start_date})>"
