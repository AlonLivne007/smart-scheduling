"""
Time-off request model definition.

This module defines the TimeOffRequest ORM model representing employee time-off
requests (vacation, sick leave, personal days). Managers can approve or reject
these requests, and approved requests are respected during schedule optimization.
"""

from sqlalchemy import Column, Integer, Date, ForeignKey, String, Enum as SqlEnum, \
    DateTime, Index
from sqlalchemy.orm import relationship
from app.data.session import Base
import enum


class TimeOffRequestType(enum.Enum):
    """
    Enumeration for time-off request types.
    
    Values:
        VACATION: Vacation time off
        SICK: Sick leave
        PERSONAL: Personal day
        OTHER: Other type of time off
    """
    VACATION = "VACATION"
    SICK = "SICK"
    PERSONAL = "PERSONAL"
    OTHER = "OTHER"


class TimeOffRequestStatus(enum.Enum):
    """
    Enumeration for time-off request status states.
    
    Values:
        PENDING: Request is pending manager approval
        APPROVED: Request has been approved by a manager
        REJECTED: Request has been rejected by a manager
    """
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class TimeOffRequestModel(Base):
    """
    Time-off request model representing an employee's time-off request.
    
    Attributes:
        request_id: Primary key identifier
        user_id: Foreign key to the user requesting time off
        start_date: Start date of the time-off period
        end_date: End date of the time-off period
        request_type: Type of time-off request (VACATION, SICK, PERSONAL, OTHER)
        status: Current status of the request (PENDING, APPROVED, REJECTED)
        requested_at: Timestamp when the request was created
        approved_by_id: Foreign key to the manager who approved/rejected (nullable)
        approved_at: Timestamp when the request was approved/rejected (nullable)
        user: Relationship to the user who made the request
        approved_by: Relationship to the manager who approved/rejected
    """
    __tablename__ = "time_off_requests"

    request_id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    
    request_type = Column(
        SqlEnum(TimeOffRequestType, name="timeoffrequesttype"),
        nullable=False,
        default=TimeOffRequestType.VACATION
    )
    
    status = Column(
        SqlEnum(TimeOffRequestStatus, name="timeoffrequeststatus"),
        nullable=False,
        default=TimeOffRequestStatus.PENDING,
        index=True
    )
    
    requested_at = Column(DateTime, nullable=False)
    
    approved_by_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    approved_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship(
        "UserModel",
        foreign_keys=[user_id],
        back_populates="time_off_requests",
        lazy="selectin"
    )
    
    approved_by = relationship(
        "UserModel",
        foreign_keys=[approved_by_id],
        lazy="selectin"
    )

    __table_args__ = (
        Index("idx_timeoff_user_dates", "user_id", "start_date", "end_date"),
    )

    def __repr__(self):
        """String representation of the time-off request."""
        return (
            f"<TimeOffRequest("
            f"id={self.request_id}, "
            f"user_id={self.user_id}, "
            f"type='{self.request_type.value}', "
            f"status='{self.status.value}', "
            f"dates={self.start_date} to {self.end_date})>"
        )

