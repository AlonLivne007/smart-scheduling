"""
Activity log schema definitions.

Pydantic schemas for activity log data validation and serialization.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class ActivityActionType(str, Enum):
    """Types of activities that can be logged."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    PUBLISH = "PUBLISH"
    UNPUBLISH = "UNPUBLISH"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    OPTIMIZE = "OPTIMIZE"
    APPLY = "APPLY"


class ActivityEntityType(str, Enum):
    """Types of entities that can have activities."""
    SCHEDULE = "SCHEDULE"
    SHIFT = "SHIFT"
    ASSIGNMENT = "ASSIGNMENT"
    TIME_OFF = "TIME_OFF"
    USER = "USER"
    CONSTRAINT = "CONSTRAINT"
    CONFIG = "CONFIG"


class ActivityLogCreate(BaseModel):
    """Schema for creating an activity log entry."""
    action_type: ActivityActionType
    entity_type: ActivityEntityType
    entity_id: int
    user_id: Optional[int] = None
    details: Optional[str] = None


class ActivityLogRead(BaseModel):
    """Schema for activity log data in API responses."""
    activity_id: int = Field(..., description="Unique activity log identifier")
    action_type: ActivityActionType = Field(..., description="Type of action performed")
    entity_type: ActivityEntityType = Field(..., description="Type of entity affected")
    entity_id: int = Field(..., description="ID of the affected entity")
    user_id: Optional[int] = Field(None, description="ID of the user who performed the action")
    user_full_name: Optional[str] = Field(None, description="Full name of the user")
    details: Optional[str] = Field(None, description="Additional details about the action")
    created_at: datetime = Field(..., description="Timestamp when the activity occurred")
    
    model_config = {"from_attributes": True}
