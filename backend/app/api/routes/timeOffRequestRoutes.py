"""
Time-off request routes module.

This module defines the REST API endpoints for time-off request management operations
including CRUD operations and approval/rejection of time-off requests.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.controllers.timeOffRequestController import (
    create_time_off_request,
    get_all_time_off_requests,
    get_time_off_request,
    update_time_off_request,
    delete_time_off_request,
    process_time_off_request,
)
from app.db.session import get_db
from app.schemas.timeOffRequestSchema import (
    TimeOffRequestCreate,
    TimeOffRequestRead,
    TimeOffRequestUpdate,
    TimeOffRequestAction,
    TimeOffRequestStatus,
)
from app.api.controllers.authController import get_current_user
from app.api.dependencies.auth import require_auth, require_manager
from app.db.models.userModel import UserModel
from app.db.models.timeOffRequestModel import TimeOffRequestStatus as TimeOffRequestStatusEnum

router = APIRouter(prefix="/time-off/requests", tags=["Time-Off Requests"])


# ---------------------- Collection routes -------------------

@router.post(
    "/",
    response_model=TimeOffRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new time-off request",
    dependencies=[Depends(require_auth)],
)
async def create_request(
    payload: TimeOffRequestCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new time-off request.
    
    The request is created for the authenticated user automatically.
    """
    return await create_time_off_request(db, payload, current_user.user_id)


@router.get(
    "/",
    response_model=List[TimeOffRequestRead],
    status_code=status.HTTP_200_OK,
    summary="Get all time-off requests",
    dependencies=[Depends(require_auth)],
)
async def list_requests(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status_filter: Optional[str] = Query(None, description="Filter by status (PENDING, APPROVED, REJECTED)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all time-off requests.
    
    - Employees can only see their own requests
    - Managers can see all requests and filter by user_id and status
    """
    # Employees can only see their own requests
    if not current_user.is_manager:
        user_id = current_user.user_id
    
    # Parse status filter
    status_enum = None
    if status_filter:
        try:
            status_enum = TimeOffRequestStatusEnum[status_filter.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: PENDING, APPROVED, REJECTED"
            )
    
    return await get_all_time_off_requests(db, user_id=user_id, status_filter=status_enum)


# ---------------------- Resource routes ---------------------

@router.get(
    "/{request_id}",
    response_model=TimeOffRequestRead,
    status_code=status.HTTP_200_OK,
    summary="Get a time-off request by ID",
    dependencies=[Depends(require_auth)],
)
async def get_single_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get a single time-off request by ID.
    
    - Employees can only view their own requests
    - Managers can view any request
    """
    request = await get_time_off_request(db, request_id)
    
    # Employees can only view their own requests
    if not current_user.is_manager and request.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own time-off requests"
        )
    
    return request


@router.put(
    "/{request_id}",
    response_model=TimeOffRequestRead,
    status_code=status.HTTP_200_OK,
    summary="Update a time-off request",
    dependencies=[Depends(require_auth)],
)
async def update_request(
    request_id: int,
    payload: TimeOffRequestUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update a time-off request.
    
    Only pending requests can be updated, and only by the user who created them.
    """
    return await update_time_off_request(db, request_id, payload, current_user.user_id)


@router.delete(
    "/{request_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a time-off request",
    dependencies=[Depends(require_auth)],
)
async def delete_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Delete a time-off request.
    
    Only pending requests can be deleted, and only by the user who created them.
    """
    await delete_time_off_request(db, request_id, current_user.user_id)
    return {"message": "Time-off request deleted successfully"}


# ---------------------- Approval/Rejection routes ---------------------

@router.put(
    "/{request_id}/approve",
    response_model=TimeOffRequestRead,
    status_code=status.HTTP_200_OK,
    summary="Approve a time-off request",
    dependencies=[Depends(require_manager)],
)
async def approve_request(
    request_id: int,
    payload: Optional[TimeOffRequestAction] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Approve a time-off request.
    
    Only managers can approve requests. Only pending requests can be approved.
    """
    return await process_time_off_request(
        db, request_id, current_user.user_id, TimeOffRequestStatusEnum.APPROVED, payload
    )


@router.put(
    "/{request_id}/reject",
    response_model=TimeOffRequestRead,
    status_code=status.HTTP_200_OK,
    summary="Reject a time-off request",
    dependencies=[Depends(require_manager)],
)
async def reject_request(
    request_id: int,
    payload: Optional[TimeOffRequestAction] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Reject a time-off request.
    
    Only managers can reject requests. Only pending requests can be rejected.
    """
    return await process_time_off_request(
        db, request_id, current_user.user_id, TimeOffRequestStatusEnum.REJECTED, payload
    )

