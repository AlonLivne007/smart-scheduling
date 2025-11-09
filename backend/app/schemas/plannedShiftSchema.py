"""
Planned shift schema definitions.

This module defines Pydantic schemas for planned shift data validation and serialization
in API requests and responses.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
import datetime
from typing import Optional, List
from enum import Enum
from app.schemas.shiftAssignmentSchema import ShiftAssignmentRead


# ----------- Enum for status -----------
class PlannedShiftStatus(str, Enum):
    """Enumeration for planned shift status states."""
    PLANNED = "PLANNED"
    PARTIALLY_ASSIGNED = "PARTIALLY_ASSIGNED"
    FULLY_ASSIGNED = "FULLY_ASSIGNED"
    CANCELLED = "CANCELLED"


# ----------- Base Schema -----------
class PlannedShiftBase(BaseModel):
    """Base schema for planned shifts with common fields."""
    weekly_schedule_id: int = Field(..., description="ID of the weekly schedule containing this shift", gt=0)
    shift_template_id: int = Field(..., description="ID of the shift template this shift is based on", gt=0)
    date: datetime.date = Field(..., description="Date of the shift")
    start_time: datetime.datetime = Field(..., description="Start date and time of the shift")
    end_time: datetime.datetime = Field(..., description="End date and time of the shift")
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
class PlannedShiftCreate(BaseModel):
    """
    Schema for creating a new planned shift.
    If start_time, end_time, or location are not provided, they will be taken from the shift template.
    """
    weekly_schedule_id: int = Field(..., description="ID of the weekly schedule containing this shift", gt=0)
    shift_template_id: int = Field(..., description="ID of the shift template this shift is based on", gt=0)
    date: datetime.date = Field(..., description="Date of the shift")
    start_time: Optional[datetime.datetime] = Field(
        default=None,
        description="Start date and time of the shift. If not provided, will be taken from template."
    )
    end_time: Optional[datetime.datetime] = Field(
        default=None,
        description="End date and time of the shift. If not provided, will be taken from template."
    )
    location: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Location where the shift takes place. If not provided, will be taken from template."
    )
    status: PlannedShiftStatus = Field(
        default=PlannedShiftStatus.PLANNED,
        description="Current assignment status of the shift"
    )


# ----------- Update Schema -----------
class PlannedShiftUpdate(BaseModel):
    """
    Schema for updating an existing planned shift.
    All fields are optional to allow partial updates.
    """
    weekly_schedule_id: Optional[int] = Field(
        default=None,
        description="ID of the weekly schedule containing this shift",
        gt=0
    )
    shift_template_id: Optional[int] = Field(
        default=None,
        description="ID of the shift template this shift is based on",
        gt=0
    )
    date: Optional[datetime.date] = Field(
        default=None,
        description="Date of the shift"
    )
    start_time: Optional[datetime.datetime] = Field(
        default=None,
        description="Start date and time of the shift"
    )
    end_time: Optional[datetime.datetime] = Field(
        default=None,
        description="End date and time of the shift"
    )
    location: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Location where the shift takes place"
    )
    status: Optional[PlannedShiftStatus] = Field(
        default=None,
        description="Current assignment status of the shift"
    )


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
