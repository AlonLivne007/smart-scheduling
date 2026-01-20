"""
System constraints schema definitions.

This module defines Pydantic schemas for system-wide constraint data validation
and serialization in API requests and responses.
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class SystemConstraintType(str, Enum):
    """System-wide constraint type enumeration."""
    MAX_HOURS_PER_WEEK = "MAX_HOURS_PER_WEEK"
    MIN_HOURS_PER_WEEK = "MIN_HOURS_PER_WEEK"
    MAX_CONSECUTIVE_DAYS = "MAX_CONSECUTIVE_DAYS"
    MIN_REST_HOURS = "MIN_REST_HOURS"
    MAX_SHIFTS_PER_WEEK = "MAX_SHIFTS_PER_WEEK"
    MIN_SHIFTS_PER_WEEK = "MIN_SHIFTS_PER_WEEK"


class SystemConstraintBase(BaseModel):
    """Base schema for system-wide constraints."""
    constraint_type: SystemConstraintType = Field(
        ..., description="Type of system-wide constraint"
    )
    constraint_value: float = Field(
        ..., description="Numeric limit value for the constraint"
    )
    is_hard_constraint: bool = Field(
        default=True,
        description="True if the constraint must be satisfied, False if soft/preferred",
    )


class SystemConstraintCreate(SystemConstraintBase):
    """Schema for creating a new system constraint."""
    pass


class SystemConstraintUpdate(BaseModel):
    """Schema for updating an existing system constraint."""
    constraint_value: Optional[float] = Field(
        default=None,
        description="Numeric limit value for the constraint",
    )
    is_hard_constraint: Optional[bool] = Field(
        default=None,
        description="True if the constraint must be satisfied, False if soft/preferred",
    )


class SystemConstraintRead(SystemConstraintBase):
    """Schema for system constraint data in API responses."""
    constraint_id: int = Field(..., description="Unique system constraint identifier")

    model_config = {"from_attributes": True}

