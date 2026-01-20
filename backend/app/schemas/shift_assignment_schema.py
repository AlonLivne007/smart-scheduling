"""
Shift assignment schema definitions.

This module defines Pydantic schemas for shift assignment data validation and serialization
in API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ----------- Base Schema -----------
class ShiftAssignmentBase(BaseModel):
    """Base schema for shift assignments with common fields."""
    planned_shift_id: int = Field(..., description="ID of the planned shift", gt=0)
    user_id: int = Field(..., description="ID of the assigned user", gt=0)
    role_id: int = Field(..., description="ID of the role the user plays in this shift", gt=0)


# ----------- Create Schema -----------
class ShiftAssignmentCreate(ShiftAssignmentBase):
    """
    Schema for creating a new shift assignment.
    """
    pass


# ----------- Read Schema -----------
class ShiftAssignmentRead(ShiftAssignmentBase):
    """
    Schema for shift assignment data in API responses.
    Includes extra info about the user and role for convenience.
    """
    assignment_id: int = Field(..., description="Unique shift assignment identifier")
    user_full_name: Optional[str] = Field(
        default=None,
        description="Full name of the assigned user (convenient to include in responses)"
    )
    role_name: Optional[str] = Field(
        default=None,
        description="Name of the role (convenient to include in responses)"
    )

    model_config = {"from_attributes": True}
