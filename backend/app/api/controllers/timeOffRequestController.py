"""
Time-off request controller module.

This module contains business logic for time-off request management operations including
creation, retrieval, updating, approval, and rejection of time-off requests.
"""

from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List, Optional
from app.db.models.timeOffRequestModel import (
    TimeOffRequestModel,
    TimeOffRequestStatus,
    TimeOffRequestType
)
from app.db.models.userModel import UserModel
from app.schemas.timeOffRequestSchema import (
    TimeOffRequestCreate,
    TimeOffRequestUpdate,
    TimeOffRequestRead,
    TimeOffRequestAction,
)


# ------------------------
# Helper Functions
# ------------------------

def _serialize_time_off_request(request: TimeOffRequestModel) -> TimeOffRequestRead:
    """
    Convert ORM object to Pydantic schema.
    
    Args:
        request: TimeOffRequestModel instance
        
    Returns:
        TimeOffRequestRead instance
    """
    # Extract relationship data explicitly
    user_full_name = request.user.user_full_name if request.user else None
    approved_by_name = request.approved_by.user_full_name if request.approved_by else None
    
    return TimeOffRequestRead(
        request_id=request.request_id,
        user_id=request.user_id,
        start_date=request.start_date,
        end_date=request.end_date,
        request_type=request.request_type,
        status=request.status,
        requested_at=request.requested_at,
        approved_by_id=request.approved_by_id,
        approved_at=request.approved_at,
        user_full_name=user_full_name,
        approved_by_name=approved_by_name,
    )


def _validate_date_range(start_date, end_date):
    """
    Validate that start_date is before or equal to end_date.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Raises:
        HTTPException: If start_date is after end_date
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before or equal to end date"
        )


# ------------------------
# CRUD Functions
# ------------------------

async def create_time_off_request(
    db: Session,
    request_data: TimeOffRequestCreate,
    user_id: int
) -> TimeOffRequestRead:
    """
    Create a new time-off request.
    
    Args:
        db: Database session
        request_data: Time-off request creation data
        user_id: ID of the user creating the request
        
    Returns:
        Created TimeOffRequestRead instance
        
    Raises:
        HTTPException: If validation fails or database error occurs
    """
    try:
        # Validate date range
        _validate_date_range(request_data.start_date, request_data.end_date)
        
        # Verify user exists
        user = db.get(UserModel, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        request = TimeOffRequestModel(
            user_id=user_id,
            start_date=request_data.start_date,
            end_date=request_data.end_date,
            request_type=request_data.request_type,
            status=TimeOffRequestStatus.PENDING,
            requested_at=datetime.utcnow(),
        )
        
        db.add(request)
        db.commit()
        db.refresh(request)
        
        # Ensure relationships are loaded
        _ = request.user  # Trigger lazy load
        
        return _serialize_time_off_request(request)
    
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {error_str}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_all_time_off_requests(
    db: Session,
    user_id: Optional[int] = None,
    status_filter: Optional[TimeOffRequestStatus] = None
) -> List[TimeOffRequestRead]:
    """
    Retrieve all time-off requests, optionally filtered by user or status.
    
    Args:
        db: Database session
        user_id: Optional user ID to filter by
        status_filter: Optional status to filter by
        
    Returns:
        List of TimeOffRequestRead instances
        
    Raises:
        HTTPException: If database error occurs
    """
    try:
        query = db.query(TimeOffRequestModel).options(
            joinedload(TimeOffRequestModel.user),
            joinedload(TimeOffRequestModel.approved_by)
        )
        
        if user_id:
            query = query.filter(TimeOffRequestModel.user_id == user_id)
        
        if status_filter:
            query = query.filter(TimeOffRequestModel.status == status_filter)
        
        requests = query.order_by(TimeOffRequestModel.requested_at.desc()).all()
        return [_serialize_time_off_request(r) for r in requests]
    
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_time_off_request(
    db: Session,
    request_id: int
) -> TimeOffRequestRead:
    """
    Retrieve a single time-off request by ID.
    
    Args:
        db: Database session
        request_id: Time-off request identifier
        
    Returns:
        TimeOffRequestRead instance
        
    Raises:
        HTTPException: If request not found or database error occurs
    """
    try:
        request = db.query(TimeOffRequestModel).options(
            joinedload(TimeOffRequestModel.user),
            joinedload(TimeOffRequestModel.approved_by)
        ).filter(TimeOffRequestModel.request_id == request_id).first()
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time-off request not found"
            )
        
        return _serialize_time_off_request(request)
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def update_time_off_request(
    db: Session,
    request_id: int,
    request_data: TimeOffRequestUpdate,
    user_id: int
) -> TimeOffRequestRead:
    """
    Update a time-off request. Only pending requests can be updated.
    Only the user who created the request can update it.
    
    Args:
        db: Database session
        request_id: Time-off request identifier
        request_data: Update data
        user_id: ID of the user attempting to update
        
    Returns:
        Updated TimeOffRequestRead instance
        
    Raises:
        HTTPException: If request not found, not pending, unauthorized, or database error occurs
    """
    try:
        request = db.get(TimeOffRequestModel, request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time-off request not found"
            )
        
        # Only pending requests can be updated
        if request.status != TimeOffRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending requests can be updated"
            )
        
        # Only the user who created the request can update it
        if request.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own time-off requests"
            )
        
        # Update fields if provided
        if request_data.start_date is not None:
            request.start_date = request_data.start_date
        if request_data.end_date is not None:
            request.end_date = request_data.end_date
        if request_data.request_type is not None:
            request.request_type = request_data.request_type
        
        # Validate date range if dates were updated
        _validate_date_range(request.start_date, request.end_date)
        
        db.commit()
        db.refresh(request)
        
        # Ensure relationships are loaded
        _ = request.user
        _ = request.approved_by
        
        return _serialize_time_off_request(request)
    
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {error_str}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def delete_time_off_request(
    db: Session,
    request_id: int,
    user_id: int
) -> None:
    """
    Delete a time-off request. Only pending requests can be deleted.
    Only the user who created the request can delete it.
    
    Args:
        db: Database session
        request_id: Time-off request identifier
        user_id: ID of the user attempting to delete
        
    Raises:
        HTTPException: If request not found, not pending, unauthorized, or database error occurs
    """
    try:
        request = db.get(TimeOffRequestModel, request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time-off request not found"
            )
        
        # Only pending requests can be deleted
        if request.status != TimeOffRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending requests can be deleted"
            )
        
        # Only the user who created the request can delete it
        if request.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own time-off requests"
            )
        
        db.delete(request)
        db.commit()
    
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {error_str}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


# ------------------------
# Approval/Rejection Functions
# ------------------------

async def process_time_off_request(
    db: Session,
    request_id: int,
    manager_id: int,
    new_status: TimeOffRequestStatus,
    action_data: Optional[TimeOffRequestAction] = None
) -> TimeOffRequestRead:
    """
    Process a time-off request (approve or reject). Only managers can process requests.
    
    Args:
        db: Database session
        request_id: Time-off request identifier
        manager_id: ID of the manager processing the request
        new_status: New status (APPROVED or REJECTED)
        action_data: Optional notes about the action
        
    Returns:
        Updated TimeOffRequestRead instance
        
    Raises:
        HTTPException: If request not found, already processed, invalid status, or database error occurs
    """
    try:
        # Validate status
        if new_status not in [TimeOffRequestStatus.APPROVED, TimeOffRequestStatus.REJECTED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status must be either APPROVED or REJECTED"
            )
        
        request = db.get(TimeOffRequestModel, request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time-off request not found"
            )
        
        # Only pending requests can be processed
        if request.status != TimeOffRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request is already {request.status.value.lower()}"
            )
        
        # Verify manager exists
        manager = db.get(UserModel, manager_id)
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manager not found"
            )
        
        if not manager.is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only managers can process time-off requests"
            )
        
        # Update request
        request.status = new_status
        request.approved_by_id = manager_id
        request.approved_at = datetime.utcnow()
        
        db.commit()
        db.refresh(request)
        
        # Ensure relationships are loaded
        _ = request.user
        _ = request.approved_by
        
        return _serialize_time_off_request(request)
    
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {error_str}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


# Convenience functions for backward compatibility (optional)
async def approve_time_off_request(
    db: Session,
    request_id: int,
    manager_id: int,
    action_data: Optional[TimeOffRequestAction] = None
) -> TimeOffRequestRead:
    """Approve a time-off request. Convenience wrapper around process_time_off_request."""
    return await process_time_off_request(
        db, request_id, manager_id, TimeOffRequestStatus.APPROVED, action_data
    )


async def reject_time_off_request(
    db: Session,
    request_id: int,
    manager_id: int,
    action_data: Optional[TimeOffRequestAction] = None
) -> TimeOffRequestRead:
    """Reject a time-off request. Convenience wrapper around process_time_off_request."""
    return await process_time_off_request(
        db, request_id, manager_id, TimeOffRequestStatus.REJECTED, action_data
    )


