"""
Planned shift schema definitions.

This module defines Pydantic schemas for planned shift data validation and serialization
in API requests and responses.
"""

from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List
from enum import Enum
from app.schemas.shiftAssignmentSchema import ShiftAssignmentRead


# ----------- Enum for status -----------
class PlannedShiftStatus(str, Enum):
    """Enumeration for planned shift status states."""
    PLANNED = "planned"
    PARTIALLY_ASSIGNED = "partially_assigned"
    FULLY_ASSIGNED = "fully_assigned"
    CANCELLED = "cancelled"


# ----------- Base Schema -----------
class PlannedShiftBase(BaseModel):
    """Base schema for planned shifts with common fields."""
    weekly_schedule_id: int = Field(..., description="ID of the weekly schedule containing this shift", gt=0)
    shift_template_id: int = Field(..., description="ID of the shift template this shift is based on", gt=0)
    date: date = Field(..., description="Date of the shift")
    start_time: datetime = Field(..., description="Start date and time of the shift")
    end_time: datetime = Field(..., description="End date and time of the shift")
    location: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Location where the shift takes place"
    )
    status: PlannedShiftStatus = Field(
        default=PlannedShiftStatus.PLANNED,
        description="Current assignment status of the shift"
    )


# ----------- Create Schema -----------
class PlannedShiftCreate(PlannedShiftBase):
    """
    Schema for creating a new planned shift.
    """
    pass


# ----------- Read Schema -----------
class PlannedShiftRead(PlannedShiftBase):
    """
    Schema for planned shift data in API responses.
    Includes related assignments and template info.
    """
    planned_shift_id: int = Field(..., description="Unique planned shift identifier")
    shift_template_name: Optional[str] = Field(
        default=None,
        description="Name of the shift template (convenient to include in responses)"
    )
    assignments: List[ShiftAssignmentRead] = Field(
        default_factory=list,
        description="List of user assignments for this shift"
    )

    model_config = {"from_attributes": True}
