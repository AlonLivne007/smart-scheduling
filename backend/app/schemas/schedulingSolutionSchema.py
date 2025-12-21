"""
Scheduling solution schema definitions.

This module defines Pydantic schemas for scheduling solution data validation and serialization
in API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ----------- Create Schema -----------
class SchedulingSolutionCreate(BaseModel):
    """
    Schema for creating a new scheduling solution.
    Used internally when storing optimizer results.
    """
    planned_shift_id: int = Field(..., description="ID of the planned shift")
    user_id: Optional[int] = Field(
        default=None,
        description="ID of the assigned user (nullable to preserve history)"
    )
    role_id: Optional[int] = Field(
        default=None,
        description="ID of the role (nullable to preserve history)"
    )
    assignment_score: Optional[float] = Field(
        default=None,
        description="Contribution to objective function"
    )


# ----------- Bulk Create Schema -----------
class SchedulingSolutionBulkCreate(BaseModel):
    """
    Schema for bulk creating scheduling solutions.
    Used when storing all solutions from an optimization run.
    """
    solutions: list[SchedulingSolutionCreate] = Field(
        ...,
        description="List of solutions to create"
    )


# ----------- Read Schema -----------
class SchedulingSolutionRead(BaseModel):
    """
    Schema for scheduling solution data in API responses.
    Includes relationship data for convenience.
    """
    solution_id: int = Field(..., description="Unique solution identifier")
    run_id: int = Field(..., description="ID of the scheduling run")
    planned_shift_id: int = Field(..., description="ID of the planned shift")
    user_id: Optional[int] = Field(
        default=None,
        description="ID of the assigned user (nullable to preserve history)"
    )
    role_id: Optional[int] = Field(
        default=None,
        description="ID of the role (nullable to preserve history)"
    )
    assignment_score: Optional[float] = Field(
        default=None,
        description="Contribution to objective function"
    )
    created_at: datetime = Field(..., description="Timestamp when solution was created")
    user_full_name: Optional[str] = Field(
        default=None,
        description="Full name of the assigned user"
    )
    role_name: Optional[str] = Field(
        default=None,
        description="Name of the role"
    )
    shift_date: Optional[datetime] = Field(
        default=None,
        description="Date and time of the planned shift"
    )

    model_config = {"from_attributes": True}

