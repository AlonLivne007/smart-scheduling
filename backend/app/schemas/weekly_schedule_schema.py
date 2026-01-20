"""
Weekly schedule schema definitions.

This module defines Pydantic schemas for weekly schedule data validation and serialization
in API requests and responses.
"""

from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List, Optional
from app.schemas.planned_shift_schema import PlannedShiftRead


# ---------- Base ----------
class WeeklyScheduleBase(BaseModel):
    """Base schema for weekly schedules with common fields."""
    week_start_date: date = Field(..., description="Start date of the week being scheduled")


# ---------- Create ----------
class WeeklyScheduleCreate(WeeklyScheduleBase):
    """
    Schema for creating a new weekly schedule.
    Note: created_by_id is set automatically from the authenticated user.
    """
    # created_by_id is now set from the authenticated user, not from the request


# ---------- Read ----------
class WeeklyScheduleRead(WeeklyScheduleBase):
    """
    Schema for weekly schedule data in API responses.
    Includes planned shifts and creator info.
    """
    weekly_schedule_id: int = Field(..., description="Unique weekly schedule identifier")
    created_by_id: int = Field(..., description="ID of the user who created this schedule")
    created_by_name: Optional[str] = Field(
        default=None,
        description="Full name of the user who created this schedule (convenient to include in responses)"
    )
    status: str = Field(default="DRAFT", description="Publication status (DRAFT, PUBLISHED, ARCHIVED)")
    published_at: Optional[datetime] = Field(default=None, description="Timestamp when schedule was published")
    published_by_id: Optional[int] = Field(default=None, description="ID of the user who published this schedule")
    published_by_name: Optional[str] = Field(default=None, description="Name of the user who published this schedule")
    planned_shifts: List[PlannedShiftRead] = Field(
        default_factory=list,
        description="List of all planned shifts in this weekly schedule"
    )

    model_config = {"from_attributes": True}
