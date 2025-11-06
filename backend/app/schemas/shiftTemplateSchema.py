"""
Shift template schema definitions.

This module defines Pydantic schemas for shift template data validation and serialization
in API requests and responses.
"""

from pydantic import BaseModel, Field
from datetime import time
from typing import Optional, List


# ----------- nested schema for role requirements -----------
class RoleRequirementBase(BaseModel):
    """Base schema for role requirements in shift templates."""
    role_id: int = Field(..., description="ID of the required role", gt=0)
    required_count: int = Field(
        default=1,
        ge=1,
        description="Number of employees needed for this role (must be at least 1)"
    )


class RoleRequirementRead(RoleRequirementBase):
    """Schema for role requirements in API responses."""
    role_name: Optional[str] = Field(
        default=None,
        description="Name of the role (convenient to include in responses)"
    )
    model_config = {"from_attributes": True}


# ----------- main ShiftTemplate schemas --------------------
class ShiftTemplateBase(BaseModel):
    """Base shift template schema with common fields."""
    shift_template_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the shift template (e.g., 'Morning Shift', 'Evening Shift')"
    )
    start_time: Optional[time] = Field(
        default=None,
        description="Start time of the shift (time only, not date)"
    )
    end_time: Optional[time] = Field(
        default=None,
        description="End time of the shift (time only, not date)"
    )
    location: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Location where the shift takes place"
    )


class ShiftTemplateCreate(ShiftTemplateBase):
    """
    Schema for creating a new shift template.
    Includes the list of required roles and counts.
    """
    required_roles: Optional[List[RoleRequirementBase]] = Field(
        default_factory=list,
        description="List of roles required for this shift template and their counts"
    )


class ShiftTemplateRead(ShiftTemplateBase):
    """
    Schema for shift template data in API responses.
    Includes role info and template ID.
    """
    shift_template_id: int = Field(..., description="Unique shift template identifier")
    required_roles: List[RoleRequirementRead] = Field(
        default_factory=list,
        description="List of roles required for this shift template with their details"
    )

    model_config = {"from_attributes": True}
