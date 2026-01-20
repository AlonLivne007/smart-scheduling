"""
Scheduling run schema definitions.

This module contains Pydantic schemas for SchedulingRun API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.data.models.scheduling_run_model import SchedulingRunStatus, SolverStatus


class SchedulingRunBase(BaseModel):
    """Base schema with common fields for scheduling run."""
    
    weekly_schedule_id: int = Field(
        ...,
        description="ID of the weekly schedule being optimized"
    )
    
    config_id: Optional[int] = Field(
        None,
        description="ID of the optimization configuration to use (null = default)"
    )


class SchedulingRunCreate(SchedulingRunBase):
    """
    Schema for creating a new scheduling run.
    
    Example:
        {
            "weekly_schedule_id": 1,
            "config_id": 2
        }
    """
    pass


class SchedulingRunUpdate(BaseModel):
    """
    Schema for updating a scheduling run.
    
    Typically used internally by the system to update status and results.
    """
    
    status: Optional[SchedulingRunStatus] = Field(
        None,
        description="Run status"
    )
    
    solver_status: Optional[SolverStatus] = Field(
        None,
        description="Solver status"
    )
    
    completed_at: Optional[datetime] = Field(
        None,
        description="Completion timestamp"
    )
    
    runtime_seconds: Optional[float] = Field(
        None,
        ge=0.0,
        description="Runtime in seconds"
    )
    
    objective_value: Optional[float] = Field(
        None,
        description="Objective function value"
    )
    
    mip_gap: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Final optimality gap achieved"
    )
    
    total_assignments: Optional[int] = Field(
        None,
        ge=0,
        description="Number of assignments in solution"
    )
    
    error_message: Optional[str] = Field(
        None,
        description="Error message if run failed"
    )


class SchedulingRunRead(SchedulingRunBase):
    """
    Schema for reading scheduling run data.
    
    Includes all fields plus metadata and results.
    """
    
    run_id: int = Field(..., description="Run identifier")
    status: SchedulingRunStatus = Field(..., description="Current run status")
    solver_status: Optional[SolverStatus] = Field(None, description="Solver result status")
    started_at: datetime = Field(..., description="When optimization started")
    completed_at: Optional[datetime] = Field(None, description="When optimization completed")
    runtime_seconds: Optional[float] = Field(None, description="Total runtime in seconds")
    objective_value: Optional[float] = Field(None, description="Final objective value")
    mip_gap: Optional[float] = Field(None, description="Final optimality gap")
    total_assignments: Optional[int] = Field(None, description="Number of assignments")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Optional nested config data
    config_name: Optional[str] = Field(None, description="Name of config used")

    class Config:
        from_attributes = True
        use_enum_values = True


class SchedulingRunSummary(BaseModel):
    """
    Minimal schema for listing scheduling runs.
    
    Used for list views to reduce payload size.
    """
    
    run_id: int
    weekly_schedule_id: int
    status: SchedulingRunStatus
    solver_status: Optional[SolverStatus]
    started_at: datetime
    completed_at: Optional[datetime]
    runtime_seconds: Optional[float]
    total_assignments: Optional[int]

    class Config:
        from_attributes = True
        use_enum_values = True
