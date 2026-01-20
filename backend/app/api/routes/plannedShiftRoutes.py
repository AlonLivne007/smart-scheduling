"""
Planned shift routes module.

This module defines the REST API endpoints for planned shift management operations.
Routes use repository dependency injection - no direct DB access.
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.controllers import plannedShiftController
from app.api.controllers.plannedShiftController import (
    create_planned_shift,
    get_planned_shift,
    update_planned_shift,
    delete_planned_shift
)
from app.api.dependencies.repositories import (
    get_shift_repository,
    get_shift_template_repository
)
from app.db.session import get_db
from app.schemas.plannedShiftSchema import (
    PlannedShiftCreate,
    PlannedShiftUpdate,
    PlannedShiftRead
)

# AuthN/Authorization
from app.api.dependencies.auth import require_auth, require_manager
from app.repositories.shift_repository import ShiftRepository
from app.repositories.shift_template_repository import ShiftTemplateRepository

router = APIRouter(prefix="/planned-shifts", tags=["Planned Shifts"])


# ---------------------- Collection routes -------------------

@router.post(
    "/",
    response_model=PlannedShiftRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new planned shift",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def create_shift(
    planned_shift_data: PlannedShiftCreate,
    shift_repository: ShiftRepository = Depends(get_shift_repository),
    template_repository: ShiftTemplateRepository = Depends(get_shift_template_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await create_planned_shift(
        planned_shift_data,
        shift_repository,
        template_repository,
        db
    )


@router.get(
    "/",
    response_model=List[PlannedShiftRead],
    status_code=status.HTTP_200_OK,
    summary="Get all planned shifts",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def list_all_shifts(
    shift_repository: ShiftRepository = Depends(get_shift_repository)
):
    return await plannedShiftController.list_planned_shifts(shift_repository)


# ---------------------- Resource routes ---------------------

@router.get(
    "/{shift_id}",
    response_model=PlannedShiftRead,
    status_code=status.HTTP_200_OK,
    summary="Get a planned shift by ID",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_one_shift(
    shift_id: int,
    shift_repository: ShiftRepository = Depends(get_shift_repository)
):
    return await get_planned_shift(shift_id, shift_repository)


@router.put(
    "/{shift_id}",
    response_model=PlannedShiftRead,
    status_code=status.HTTP_200_OK,
    summary="Update a planned shift",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def update_shift(
    shift_id: int,
    planned_shift_data: PlannedShiftUpdate,
    shift_repository: ShiftRepository = Depends(get_shift_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await update_planned_shift(
        shift_id,
        planned_shift_data,
        shift_repository,
        db
    )


@router.delete(
    "/{shift_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a planned shift",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def delete_shift(
    shift_id: int,
    shift_repository: ShiftRepository = Depends(get_shift_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await delete_planned_shift(shift_id, shift_repository, db)
