"""
Employee preferences schema definitions.

This module defines Pydantic schemas for employee shift preference data validation
and serialization in API requests and responses.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import time
from enum import Enum


class DayOfWeek(str, Enum):
    """Day of the week enumeration."""
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


# ----------- Base Schema -----------
class EmployeePreferencesBase(BaseModel):
    """Base schema for employee preferences with common fields."""
    preferred_shift_template_id: Optional[int] = Field(
        default=None,
        description="ID of the preferred shift template"
    )
    preferred_day_of_week: Optional[DayOfWeek] = Field(
        default=None,
        description="Preferred day of the week"
    )
    preferred_start_time: Optional[time] = Field(
        default=None,
        description="Preferred shift start time"
    )
    preferred_end_time: Optional[time] = Field(
        default=None,
        description="Preferred shift end time"
    )
    preference_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Importance weight (0.0 = least important, 1.0 = most important)"
    )

    @field_validator('preference_weight')
    @classmethod
    def validate_weight(cls, v):
        """Ensure preference_weight is between 0.0 and 1.0."""
        if v < 0.0 or v > 1.0:
            raise ValueError('preference_weight must be between 0.0 and 1.0')
        return v


# ----------- Create Schema -----------
class EmployeePreferencesCreate(BaseModel):
    """
    Schema for creating a new employee preference.
    User ID is extracted from the URL path parameter.
    """
    preferred_shift_template_id: Optional[int] = Field(
        default=None,
        description="ID of the preferred shift template"
    )
    preferred_day_of_week: Optional[DayOfWeek] = Field(
        default=None,
        description="Preferred day of the week"
    )
    preferred_start_time: Optional[time] = Field(
        default=None,
        description="Preferred shift start time"
    )
    preferred_end_time: Optional[time] = Field(
        default=None,
        description="Preferred shift end time"
    )
    preference_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Importance weight (0.0 = least important, 1.0 = most important)"
    )

    @field_validator('preference_weight')
    @classmethod
    def validate_weight(cls, v):
        """Ensure preference_weight is between 0.0 and 1.0."""
        if v < 0.0 or v > 1.0:
            raise ValueError('preference_weight must be between 0.0 and 1.0')
        return v


# ----------- Update Schema -----------
class EmployeePreferencesUpdate(BaseModel):
    """
    Schema for updating an employee preference.
    All fields are optional for partial updates.
    """
    preferred_shift_template_id: Optional[int] = Field(
        default=None,
        description="ID of the preferred shift template"
    )
    preferred_day_of_week: Optional[DayOfWeek] = Field(
        default=None,
        description="Preferred day of the week"
    )
    preferred_start_time: Optional[time] = Field(
        default=None,
        description="Preferred shift start time"
    )
    preferred_end_time: Optional[time] = Field(
        default=None,
        description="Preferred shift end time"
    )
    preference_weight: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Importance weight (0.0 = least important, 1.0 = most important)"
    )

    @field_validator('preference_weight')
    @classmethod
    def validate_weight(cls, v):
        """Ensure preference_weight is between 0.0 and 1.0 if provided."""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('preference_weight must be between 0.0 and 1.0')
        return v


# ----------- Read Schema -----------
class EmployeePreferencesRead(BaseModel):
    """
    Schema for employee preferences data in API responses.
    Includes extra info about the user and shift template for convenience.
    """
    preference_id: int = Field(..., description="Unique preference identifier")
    user_id: int = Field(..., description="ID of the employee who owns this preference")
    preferred_shift_template_id: Optional[int] = Field(
        default=None,
        description="ID of the preferred shift template"
    )
    preferred_day_of_week: Optional[DayOfWeek] = Field(
        default=None,
        description="Preferred day of the week"
    )
    preferred_start_time: Optional[time] = Field(
        default=None,
        description="Preferred shift start time"
    )
    preferred_end_time: Optional[time] = Field(
        default=None,
        description="Preferred shift end time"
    )
    preference_weight: float = Field(
        ...,
        description="Importance weight (0.0 = least important, 1.0 = most important)"
    )
    
    # Extra convenience fields
    user_full_name: Optional[str] = Field(
        default=None,
        description="Full name of the employee (for convenience)"
    )
    shift_template_name: Optional[str] = Field(
        default=None,
        description="Name of the preferred shift template (for convenience)"
    )

    class Config:
        from_attributes = True
