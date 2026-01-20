"""
Scheduling solution schema definitions.

This module contains Pydantic schemas for SchedulingSolution API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date, time


class SchedulingSolutionBase(BaseModel):
    """Base schema with common fields for scheduling solution."""
    
    run_id: int = Field(..., description="ID of the scheduling run")
    planned_shift_id: int = Field(..., description="ID of the planned shift")
    user_id: int = Field(..., description="ID of the assigned employee")
    role_id: int = Field(..., description="ID of the assigned role")
    is_selected: bool = Field(default=True, description="Whether assignment was selected")
    assignment_score: Optional[float] = Field(None, description="Score/contribution to objective")


class SchedulingSolutionCreate(SchedulingSolutionBase):
    """
    Schema for creating a new scheduling solution.
    
    Example:
        {
            "run_id": 1,
            "planned_shift_id": 10,
            "user_id": 5,
            "role_id": 2,
            "is_selected": true,
            "assignment_score": 0.85
        }
    """
    pass


class SchedulingSolutionRead(SchedulingSolutionBase):
    """
    Schema for reading scheduling solution data.
    
    Includes all fields plus metadata and related entity names.
    """
    
    solution_id: int = Field(..., description="Solution identifier")
    created_at: datetime = Field(..., description="When solution was created")
    
    # Optional nested data for convenience
    employee_name: Optional[str] = Field(None, description="Employee full name")
    role_name: Optional[str] = Field(None, description="Role name")
    shift_date: Optional[date] = Field(None, description="Shift date")
    shift_start_time: Optional[time] = Field(None, description="Shift start time")
    shift_end_time: Optional[time] = Field(None, description="Shift end time")

    class Config:
        from_attributes = True


class SchedulingSolutionSummary(BaseModel):
    """
    Minimal schema for listing solutions.
    
    Used for solution previews before applying.
    """
    
    solution_id: int
    planned_shift_id: int
    user_id: int
    role_id: int
    employee_name: Optional[str]
    role_name: Optional[str]
    shift_date: Optional[date]
    shift_start_time: Optional[time]
    shift_end_time: Optional[time]
    assignment_score: Optional[float]

    class Config:
        from_attributes = True


class ApplySolutionRequest(BaseModel):
    """
    Schema for applying an optimization solution.
    
    Request body when converting SchedulingSolution records into ShiftAssignments.
    """
    
    overwrite_existing: bool = Field(
        default=False,
        description="Whether to overwrite existing assignments for the same shifts"
    )
    
    only_selected: bool = Field(
        default=True,
        description="Whether to apply only is_selected=true assignments"
    )


class ApplySolutionResponse(BaseModel):
    """
    Schema for apply solution response.
    
    Returns summary of what was created/updated.
    """
    
    assignments_created: int = Field(..., description="Number of new assignments created")
    assignments_skipped: int = Field(..., description="Number skipped (already exist)")
    assignments_overwritten: int = Field(..., description="Number overwritten")
    error_count: int = Field(default=0, description="Number of errors encountered")
    errors: Optional[list[str]] = Field(None, description="List of error messages")
