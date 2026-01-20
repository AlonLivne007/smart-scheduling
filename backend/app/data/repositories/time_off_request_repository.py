"""
Time off request repository for database operations on time off requests.

This repository handles all database access for TimeOffRequestModel.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session, joinedload

from app.repositories.base import BaseRepository
from app.data.models.time_off_request_model import (
    TimeOffRequestModel,
    TimeOffRequestStatus,
    TimeOffRequestType
)
from app.exceptions.repository import NotFoundError


class TimeOffRequestRepository(BaseRepository[TimeOffRequestModel]):
    """Repository for time off request database operations."""
    
    def __init__(self, db: Session):
        """Initialize time off request repository."""
        super().__init__(db, TimeOffRequestModel)
    
    def get_by_user(self, user_id: int) -> List[TimeOffRequestModel]:
        """Get all requests for a user."""
        return self.find_by(user_id=user_id)
    
    def get_approved_by_user(self, user_id: int) -> List[TimeOffRequestModel]:
        """Get all approved requests for a user."""
        return (
            self.db.query(TimeOffRequestModel)
            .filter(
                TimeOffRequestModel.user_id == user_id,
                TimeOffRequestModel.status == TimeOffRequestStatus.APPROVED
            )
            .all()
        )
    
    def get_approved_in_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[TimeOffRequestModel]:
        """
        Get all approved requests that overlap with the date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            List of approved time off requests
        """
        return (
            self.db.query(TimeOffRequestModel)
            .filter(
                TimeOffRequestModel.status == TimeOffRequestStatus.APPROVED,
                TimeOffRequestModel.start_date <= end_date,
                TimeOffRequestModel.end_date >= start_date
            )
            .all()
        )
    
    def get_with_relationships(self, request_id: int) -> Optional[TimeOffRequestModel]:
        """Get a request with user and approved_by relationships loaded."""
        return (
            self.db.query(TimeOffRequestModel)
            .options(
                joinedload(TimeOffRequestModel.user),
                joinedload(TimeOffRequestModel.approved_by)
            )
            .filter(TimeOffRequestModel.request_id == request_id)
            .first()
        )
    
    def get_all_with_relationships(
        self,
        user_id: Optional[int] = None,
        status_filter: Optional[TimeOffRequestStatus] = None
    ) -> List[TimeOffRequestModel]:
        """
        Get all requests with relationships, optionally filtered.
        
        Args:
            user_id: Optional user ID to filter by
            status_filter: Optional status to filter by
            
        Returns:
            List of requests with relationships loaded
        """
        query = (
            self.db.query(TimeOffRequestModel)
            .options(
                joinedload(TimeOffRequestModel.user),
                joinedload(TimeOffRequestModel.approved_by)
            )
        )
        
        if user_id:
            query = query.filter(TimeOffRequestModel.user_id == user_id)
        
        if status_filter:
            query = query.filter(TimeOffRequestModel.status == status_filter)
        
        return query.order_by(TimeOffRequestModel.requested_at.desc()).all()
    
    def get_pending_requests(self) -> List[TimeOffRequestModel]:
        """Get all pending requests."""
        return self.find_by(status=TimeOffRequestStatus.PENDING)
    
    def approve_request(
        self,
        request_id: int,
        approved_by_id: int
    ) -> TimeOffRequestModel:
        """
        Approve a time off request.
        
        Args:
            request_id: Request ID
            approved_by_id: User ID who approved
            
        Returns:
            Updated request
        """
        from datetime import datetime
        return self.update(
            request_id,
            status=TimeOffRequestStatus.APPROVED,
            approved_by_id=approved_by_id,
            approved_at=datetime.now()
        )
    
    def reject_request(
        self,
        request_id: int,
        approved_by_id: int
    ) -> TimeOffRequestModel:
        """
        Reject a time off request.
        
        Args:
            request_id: Request ID
            approved_by_id: User ID who rejected
            
        Returns:
            Updated request
        """
        from datetime import datetime
        return self.update(
            request_id,
            status=TimeOffRequestStatus.REJECTED,
            approved_by_id=approved_by_id,
            approved_at=datetime.now()
        )
