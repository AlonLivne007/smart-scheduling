"""
Time-off request routes module.

This module defines the REST API endpoints for time-off request management operations.
Routes use repository dependency injection - no direct DB access.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.api.controllers.timeOffRequestController import (
    create_time_off_request,
    get_all_time_off_requests,
    get_time_off_request,
    update_time_off_request,
    delete_time_off_request,
    approve_time_off_request,
    reject_time_off_request
)
from app.api.controllers.authController import get_current_user
from app.api.dependencies.repositories import (
    get_time_off_request_repository,
    get_user_repository
)
from app.db.session import get_db
from app.schemas.timeOffRequestSchema import (
    TimeOffRequestCreate,
    TimeOffRequestUpdate,
    TimeOffRequestRead,
    TimeOffRequestAction,
)
from app.db.models.timeOffRequestModel import TimeOffRequestStatus
from app.db.models.userModel import UserModel

# AuthN/Authorization
from app.api.dependencies.auth import require_auth, require_manager
from app.repositories.time_off_request_repository import TimeOffRequestRepository
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/time-off-requests", tags=["Time Off Requests"])


# ---------------------- Collection routes -------------------

@router.post(
    "/",
    response_model=TimeOffRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new time-off request",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def create_request(
    request_data: TimeOffRequestCreate,
    current_user: UserModel = Depends(get_current_user),
    time_off_repository: TimeOffRequestRepository = Depends(get_time_off_request_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await create_time_off_request(
        request_data,
        current_user.user_id,
        time_off_repository,
        user_repository,
        db
    )


@router.get(
    "/",
    response_model=List[TimeOffRequestRead],
    status_code=status.HTTP_200_OK,
    summary="Get all time-off requests",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def list_requests(
    current_user: UserModel = Depends(get_current_user),
    time_off_repository: TimeOffRequestRepository = Depends(get_time_off_request_repository),
    user_id: Optional[int] = Query(None, description="Filter by user ID (managers only)"),
    status_filter: Optional[TimeOffRequestStatus] = Query(None, description="Filter by status")
):
    return await get_all_time_off_requests(
        current_user,
        time_off_repository,
        user_id,
        status_filter
    )


# ---------------------- Resource routes ---------------------

@router.get(
    "/{request_id}",
    response_model=TimeOffRequestRead,
    status_code=status.HTTP_200_OK,
    summary="Get a time-off request by ID",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_request(
    request_id: int,
    current_user: UserModel = Depends(get_current_user),
    time_off_repository: TimeOffRequestRepository = Depends(get_time_off_request_repository)
):
    return await get_time_off_request(request_id, current_user, time_off_repository)


@router.put(
    "/{request_id}",
    response_model=TimeOffRequestRead,
    status_code=status.HTTP_200_OK,
    summary="Update a time-off request",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def update_request(
    request_id: int,
    request_data: TimeOffRequestUpdate,
    current_user: UserModel = Depends(get_current_user),
    time_off_repository: TimeOffRequestRepository = Depends(get_time_off_request_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await update_time_off_request(
        request_id,
        request_data,
        current_user.user_id,
        time_off_repository,
        db
    )


@router.delete(
    "/{request_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a time-off request",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def delete_request(
    request_id: int,
    current_user: UserModel = Depends(get_current_user),
    time_off_repository: TimeOffRequestRepository = Depends(get_time_off_request_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await delete_time_off_request(
        request_id,
        current_user.user_id,
        time_off_repository,
        db
    )


# ---------------------- Approval routes ---------------------

@router.post(
    "/{request_id}/approve",
    response_model=TimeOffRequestRead,
    status_code=status.HTTP_200_OK,
    summary="Approve a time-off request",
    dependencies=[Depends(require_manager)],  # MANAGER ONLY
)
async def approve_request(
    request_id: int,
    current_user: UserModel = Depends(get_current_user),
    time_off_repository: TimeOffRequestRepository = Depends(get_time_off_request_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await approve_time_off_request(
        request_id,
        current_user.user_id,
        time_off_repository,
        user_repository,
        db
    )


@router.post(
    "/{request_id}/reject",
    response_model=TimeOffRequestRead,
    status_code=status.HTTP_200_OK,
    summary="Reject a time-off request",
    dependencies=[Depends(require_manager)],  # MANAGER ONLY
)
async def reject_request(
    request_id: int,
    current_user: UserModel = Depends(get_current_user),
    time_off_repository: TimeOffRequestRepository = Depends(get_time_off_request_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await reject_time_off_request(
        request_id,
        current_user.user_id,
        time_off_repository,
        user_repository,
        db
    )
