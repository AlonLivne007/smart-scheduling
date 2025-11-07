"""
Role schema definitions.

This module defines Pydantic schemas for role data validation and serialization
in API requests and responses.
"""

from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    """Base role schema with common fields."""
    role_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the role (e.g., 'Waiter', 'Bartender', 'Host')"
    )



class RoleCreate(RoleBase):
    """Schema for creating new roles."""
    pass


class RoleRead(RoleBase):
    """Schema for role data in API responses."""
    role_id: int

    model_config = {"from_attributes": True}
