"""
Time-off request controller module.

This module contains business logic for time-off request management operations including
creation, retrieval, updating, approval, and rejection of time-off requests.
Controllers use repositories for database access - no direct ORM access.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session  # Only for type hints

from app.repositories.time_off_request_repository import TimeOffRequestRepository
from app.repositories.user_repository import UserRepository
from app.db.models.timeOffRequestModel import (
    TimeOffRequestStatus,
    TimeOffRequestType
)
from app.schemas.timeOffRequestSchema import (
    TimeOffRequestCreate,
    TimeOffRequestUpdate,
    TimeOffRequestRead,
    TimeOffRequestAction,
)
from app.db.models.userModel import UserModel
from app.exceptions.repository import NotFoundError, ConflictError
from app.db.session_manager import transaction


def _serialize_time_off_request(request) -> TimeOffRequestRead:
    """
    Convert ORM object to Pydantic schema.
    """
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
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before or equal to end date"
        )


async def create_time_off_request(
    request_data: TimeOffRequestCreate,
    user_id: int,
    time_off_repository: TimeOffRequestRepository,
    user_repository: UserRepository,
    db: Session  # For transaction management
) -> TimeOffRequestRead:
    """
    Create a new time-off request.
    
    Business logic:
    - Validate date range
    - Verify user exists
    - Create request
    """
    try:
        # Business rule: Validate date range
        _validate_date_range(request_data.start_date, request_data.end_date)
        
        # Business rule: Verify user exists
        user_repository.get_or_raise(user_id)
        
        with transaction(db):
            request = time_off_repository.create(
                user_id=user_id,
                start_date=request_data.start_date,
                end_date=request_data.end_date,
                request_type=request_data.request_type,
                status=TimeOffRequestStatus.PENDING,
                requested_at=datetime.utcnow(),
            )
            
            # Get request with relationships for serialization
            request = time_off_repository.get_with_relationships(request.request_id)
            return _serialize_time_off_request(request)
            
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


async def list_time_off_requests(
    current_user: UserModel,
    time_off_repository: TimeOffRequestRepository,
    user_id: Optional[int] = None,
    status_filter: Optional[TimeOffRequestStatus] = None
) -> List[TimeOffRequestRead]:
    """
    Retrieve all time-off requests, optionally filtered by user or status.
    
    Business logic:
    - Employees can only see their own requests
    - Managers can see all requests
    """
    # Business rule: Employees can only see their own requests
    if not current_user.is_manager:
        user_id = current_user.user_id
    
    requests = time_off_repository.get_all_with_relationships(
        user_id=user_id,
        status_filter=status_filter
    )
    return [_serialize_time_off_request(r) for r in requests]


async def get_time_off_request(
    request_id: int,
    current_user: UserModel,
    time_off_repository: TimeOffRequestRepository
) -> TimeOffRequestRead:
    """
    Retrieve a single time-off request by ID.
    
    Business logic:
    - Employees can only view their own requests
    - Managers can view any request
    """
    try:
        request = time_off_repository.get_with_relationships(request_id)
        if not request:
            raise NotFoundError(f"Time-off request {request_id} not found")
        
        # Business rule: Employees can only view their own requests
        if not current_user.is_manager and request.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own time-off requests"
            )
        
        return _serialize_time_off_request(request)
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time-off request not found"
        )


async def update_time_off_request(
    request_id: int,
    request_data: TimeOffRequestUpdate,
    user_id: int,
    time_off_repository: TimeOffRequestRepository,
    db: Session  # For transaction management
) -> TimeOffRequestRead:
    """
    Update a time-off request. Only pending requests can be updated.
    Only the user who created the request can update it.
    
    Business logic:
    - Only pending requests can be updated
    - Only the creator can update
    - Validate date range
    """
    try:
        request = time_off_repository.get_or_raise(request_id)
        
        # Business rule: Only pending requests can be updated
        if request.status != TimeOffRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending requests can be updated"
            )
        
        # Business rule: Only the creator can update
        if request.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own time-off requests"
            )
        
        # Validate date range if dates are being updated
        start_date = request_data.start_date if request_data.start_date else request.start_date
        end_date = request_data.end_date if request_data.end_date else request.end_date
        _validate_date_range(start_date, end_date)
        
        with transaction(db):
            # Update fields
            update_data = {}
            if request_data.start_date is not None:
                update_data["start_date"] = request_data.start_date
            if request_data.end_date is not None:
                update_data["end_date"] = request_data.end_date
            if request_data.request_type is not None:
                update_data["request_type"] = request_data.request_type
            
            if update_data:
                time_off_repository.update(request_id, **update_data)
            
            # Get updated request with relationships
            request = time_off_repository.get_with_relationships(request_id)
            return _serialize_time_off_request(request)
            
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time-off request not found"
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


async def delete_time_off_request(
    request_id: int,
    user_id: int,
    time_off_repository: TimeOffRequestRepository,
    db: Session  # For transaction management
) -> None:
    """
    Delete a time-off request. Only pending requests can be deleted.
    Only the user who created the request can delete it.
    
    Business logic:
    - Only pending requests can be deleted
    - Only the creator can delete
    """
    try:
        request = time_off_repository.get_or_raise(request_id)
        
        # Business rule: Only pending requests can be deleted
        if request.status != TimeOffRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending requests can be deleted"
            )
        
        # Business rule: Only the creator can delete
        if request.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own time-off requests"
            )
        
        with transaction(db):
            time_off_repository.delete(request_id)
            
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time-off request not found"
        )


async def approve_time_off_request(
    request_id: int,
    manager_id: int,
    time_off_repository: TimeOffRequestRepository,
    user_repository: UserRepository,
    db: Session  # For transaction management
) -> TimeOffRequestRead:
    """
    Approve a time-off request. Only managers can approve.
    
    Business logic:
    - Verify manager exists and is manager
    - Only pending requests can be approved
    - Approve request
    """
    try:
        request = time_off_repository.get_or_raise(request_id)
        
        # Business rule: Only pending requests can be approved
        if request.status != TimeOffRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request is already {request.status.value.lower()}"
            )
        
        # Business rule: Verify manager exists and is manager
        manager = user_repository.get_or_raise(manager_id)
        if not manager.is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only managers can approve time-off requests"
            )
        
        with transaction(db):
            updated_request = time_off_repository.approve_request(request_id, manager_id)
            request = time_off_repository.get_with_relationships(request_id)
            return _serialize_time_off_request(request)
            
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


async def reject_time_off_request(
    request_id: int,
    manager_id: int,
    time_off_repository: TimeOffRequestRepository,
    user_repository: UserRepository,
    db: Session  # For transaction management
) -> TimeOffRequestRead:
    """
    Reject a time-off request. Only managers can reject.
    
    Business logic:
    - Verify manager exists and is manager
    - Only pending requests can be rejected
    - Reject request
    """
    try:
        request = time_off_repository.get_or_raise(request_id)
        
        # Business rule: Only pending requests can be rejected
        if request.status != TimeOffRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request is already {request.status.value.lower()}"
            )
        
        # Business rule: Verify manager exists and is manager
        manager = user_repository.get_or_raise(manager_id)
        if not manager.is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only managers can reject time-off requests"
            )
        
        with transaction(db):
            updated_request = time_off_repository.reject_request(request_id, manager_id)
            request = time_off_repository.get_with_relationships(request_id)
            return _serialize_time_off_request(request)
            
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
