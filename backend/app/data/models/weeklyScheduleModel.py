"""
Weekly schedule model definition.

This module defines the WeeklySchedule ORM model representing a weekly
scheduling period. Each weekly schedule contains multiple planned shifts
and tracks which user created the schedule and when the week starts.
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from app.data.session import Base


class ScheduleStatus(str, Enum):
    """Schedule publication status."""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class WeeklyScheduleModel(Base):
    """
    Weekly schedule model representing a scheduling period for a week.
    
    Attributes:
        weekly_schedule_id: Primary key identifier
        week_start_date: Start date of the week being scheduled
        status: Publication status (DRAFT, PUBLISHED, ARCHIVED)
        published_at: Timestamp when schedule was published
        published_by_id: Foreign key to user who published the schedule
        created_by_id: Foreign key to the user who created this schedule
        created_by: Relationship to the user who created this schedule
        published_by: Relationship to the user who published this schedule
        planned_shifts: Relationship to all planned shifts in this weekly schedule
    """
    __tablename__ = "shift_weekly_schedule"
    
    weekly_schedule_id = Column(Integer, primary_key=True, index=True)
    week_start_date = Column(Date, nullable=False, index=True)
    status = Column(
        SQLEnum(ScheduleStatus),
        nullable=False,
        default=ScheduleStatus.DRAFT,
        server_default=ScheduleStatus.DRAFT.value
    )
    published_at = Column(DateTime, nullable=True)
    published_by_id = Column(Integer, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    
    created_by = relationship("UserModel", foreign_keys=[created_by_id], back_populates="weekly_schedules", lazy="selectin")
    published_by = relationship("UserModel", foreign_keys=[published_by_id], lazy="selectin")

    planned_shifts = relationship(
        "PlannedShiftModel",
        back_populates="weekly_schedule",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    scheduling_runs = relationship(
        "SchedulingRunModel",
        back_populates="weekly_schedule",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        """String representation of the weekly schedule."""
        return f"<WeeklySchedule(id={self.weekly_schedule_id}, week_start={self.week_start_date}, status={self.status})>"
