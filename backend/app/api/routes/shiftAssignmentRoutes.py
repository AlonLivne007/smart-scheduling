"""
Shift assignment routes module.

This module defines the REST API endpoints for shift assignment management operations.
Routes use repository dependency injection - no direct DB access.
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.controllers import shift_assignment_controller
from app.api.controllers.shift_assignment_controller import (
    create_shift_assignment,
    get_shift_assignment,
    get_assignments_by_shift,
    get_assignments_by_user,
    delete_shift_assignment
)
from app.api.dependencies.repositories import (
    get_shift_assignment_repository,
    get_shift_repository
)
from app.data.session import get_db
from app.schemas.shift_assignment_schema import (
    ShiftAssignmentCreate,
    ShiftAssignmentRead
)

# AuthN/Authorization
from app.api.dependencies.auth import require_auth, require_manager
from app.data.repositories.shift_repository import ShiftRepository, ShiftAssignmentRepository

router = APIRouter(prefix="/shift-assignments", tags=["Shift Assignments"])


# ---------------------- Collection routes -------------------

@router.post(
    "/",
    response_model=ShiftAssignmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new shift assignment",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def create_assignment(
    shift_assignment_data: ShiftAssignmentCreate,
    assignment_repository: ShiftAssignmentRepository = Depends(get_shift_assignment_repository),
    shift_repository: ShiftRepository = Depends(get_shift_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await create_shift_assignment(
        shift_assignment_data,
        assignment_repository,
        shift_repository,
        db
    )


@router.get(
    "/",
    response_model=List[ShiftAssignmentRead],
    status_code=status.HTTP_200_OK,
    summary="Get all shift assignments",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def list_all_assignments(
    assignment_repository: ShiftAssignmentRepository = Depends(get_shift_assignment_repository)
):
    return await shift_assignment_controller.list_shift_assignments(assignment_repository)


# ---------------------- Resource routes ---------------------

@router.get(
    "/shift/{shift_id}",
    response_model=List[ShiftAssignmentRead],
    status_code=status.HTTP_200_OK,
    summary="Get all assignments for a planned shift",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_assignments_for_shift(
    shift_id: int,
    assignment_repository: ShiftAssignmentRepository = Depends(get_shift_assignment_repository)
):
    return await get_assignments_by_shift(shift_id, assignment_repository)


@router.get(
    "/user/{user_id}",
    response_model=List[ShiftAssignmentRead],
    status_code=status.HTTP_200_OK,
    summary="Get all assignments for a user",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_assignments_for_user(
    user_id: int,
    assignment_repository: ShiftAssignmentRepository = Depends(get_shift_assignment_repository)
):
    return await get_assignments_by_user(user_id, assignment_repository)


@router.get(
    "/{assignment_id}",
    response_model=ShiftAssignmentRead,
    status_code=status.HTTP_200_OK,
    summary="Get a shift assignment by ID",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_one_assignment(
    assignment_id: int,
    assignment_repository: ShiftAssignmentRepository = Depends(get_shift_assignment_repository)
):
    return await get_shift_assignment(assignment_id, assignment_repository)


@router.delete(
    "/{assignment_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a shift assignment",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def delete_assignment(
    assignment_id: int,
    assignment_repository: ShiftAssignmentRepository = Depends(get_shift_assignment_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await delete_shift_assignment(assignment_id, assignment_repository, db)
