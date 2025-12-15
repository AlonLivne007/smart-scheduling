"""
Time-off request schema definitions.

This module defines Pydantic schemas for time-off request data validation and serialization
in API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from enum import Enum


class TimeOffRequestType(str, Enum):
    """Time-off request type enumeration."""
    VACATION = "VACATION"
    SICK = "SICK"
    PERSONAL = "PERSONAL"
    OTHER = "OTHER"


class TimeOffRequestStatus(str, Enum):
    """Time-off request status enumeration."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ----------- Base Schema -----------
class TimeOffRequestBase(BaseModel):
    """Base schema for time-off requests with common fields."""
    start_date: date = Field(..., description="Start date of the time-off period")
    end_date: date = Field(..., description="End date of the time-off period")
    request_type: TimeOffRequestType = Field(
        default=TimeOffRequestType.VACATION,
        description="Type of time-off request"
    )


# ----------- Create Schema -----------
class TimeOffRequestCreate(BaseModel):
    """
    Schema for creating a new time-off request.
    User ID is extracted from the authenticated user's token.
    """
    start_date: date = Field(..., description="Start date of the time-off period")
    end_date: date = Field(..., description="End date of the time-off period")
    request_type: TimeOffRequestType = Field(
        default=TimeOffRequestType.VACATION,
        description="Type of time-off request"
    )


# ----------- Update Schema -----------
class TimeOffRequestUpdate(BaseModel):
    """
    Schema for updating a time-off request.
    Only pending requests can be updated.
    """
    start_date: Optional[date] = Field(
        default=None,
        description="Start date of the time-off period"
    )
    end_date: Optional[date] = Field(
        default=None,
        description="End date of the time-off period"
    )
    request_type: Optional[TimeOffRequestType] = Field(
        default=None,
        description="Type of time-off request"
    )


# ----------- Read Schema -----------
class TimeOffRequestRead(BaseModel):
    """
    Schema for time-off request data in API responses.
    Includes extra info about the user and approver for convenience.
    """
    request_id: int = Field(..., description="Unique time-off request identifier")
    user_id: int = Field(..., description="ID of the user who requested time off")
    start_date: date = Field(..., description="Start date of the time-off period")
    end_date: date = Field(..., description="End date of the time-off period")
    request_type: TimeOffRequestType = Field(..., description="Type of time-off request")
    status: TimeOffRequestStatus = Field(..., description="Current status of the request")
    requested_at: datetime = Field(..., description="Timestamp when the request was created")
    approved_by_id: Optional[int] = Field(
        default=None,
        description="ID of the manager who approved/rejected the request"
    )
    approved_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the request was approved/rejected"
    )
    user_full_name: Optional[str] = Field(
        default=None,
        description="Full name of the user who requested time off (convenient to include in responses)"
    )
    approved_by_name: Optional[str] = Field(
        default=None,
        description="Full name of the manager who approved/rejected (convenient to include in responses)"
    )

    model_config = {"from_attributes": True}


# ----------- Approve/Reject Schema -----------
class TimeOffRequestAction(BaseModel):
    """
    Schema for approving or rejecting a time-off request.
    Currently empty, but can be extended in the future if needed.
    """
    pass

