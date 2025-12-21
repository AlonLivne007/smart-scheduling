"""
Scheduling run routes module.

This module defines the REST API endpoints for scheduling run management operations
including CRUD operations and solution retrieval.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.controllers.schedulingRunController import (
    create_scheduling_run,
    get_all_scheduling_runs,
    get_scheduling_run,
    update_scheduling_run,
    delete_scheduling_run,
    get_scheduling_solutions,
)
from app.db.session import get_db
from app.schemas.schedulingRunSchema import (
    SchedulingRunCreate,
    SchedulingRunRead,
    SchedulingRunUpdate,
    SchedulingRunStatus,
)
from app.schemas.schedulingSolutionSchema import SchedulingSolutionRead
from app.api.controllers.authController import get_current_user
from app.api.dependencies.auth import require_auth, require_manager
from app.db.models.userModel import UserModel
from app.db.models.schedulingRunModel import (
    SchedulingRunStatus as SchedulingRunStatusEnum
)

router = APIRouter(prefix="/scheduling/runs", tags=["Scheduling Runs"])


# ---------------------- Collection routes -------------------

@router.post(
    "/",
    response_model=SchedulingRunRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new scheduling run",
    dependencies=[Depends(require_auth)],
)
async def create_run(
    payload: SchedulingRunCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new scheduling run.
    
    The run is created with PENDING status and will be updated when optimization starts.
    """
    return await create_scheduling_run(db, payload, current_user.user_id)


@router.get(
    "/",
    response_model=List[SchedulingRunRead],
    status_code=status.HTTP_200_OK,
    summary="Get all scheduling runs",
    dependencies=[Depends(require_auth)],
)
async def list_runs(
    weekly_schedule_id: Optional[int] = Query(None, description="Filter by weekly schedule ID"),
    status_filter: Optional[str] = Query(None, description="Filter by status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all scheduling runs.
    
    - All authenticated users can view runs
    - Can filter by weekly_schedule_id and status
    """
    # Parse status filter
    status_enum = None
    if status_filter:
        try:
            status_enum = SchedulingRunStatusEnum[status_filter.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: PENDING, RUNNING, COMPLETED, FAILED, CANCELLED"
            )
    
    return await get_all_scheduling_runs(
        db,
        weekly_schedule_id=weekly_schedule_id,
        status_filter=status_enum
    )


# ---------------------- Resource routes ---------------------

@router.get(
    "/{run_id}",
    response_model=SchedulingRunRead,
    status_code=status.HTTP_200_OK,
    summary="Get a scheduling run by ID",
    dependencies=[Depends(require_auth)],
)
async def get_single_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get a single scheduling run by ID.
    
    All authenticated users can view runs.
    """
    return await get_scheduling_run(db, run_id)


@router.put(
    "/{run_id}",
    response_model=SchedulingRunRead,
    status_code=status.HTTP_200_OK,
    summary="Update a scheduling run",
    dependencies=[Depends(require_manager)],
)
async def update_run(
    run_id: int,
    payload: SchedulingRunUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update a scheduling run.
    
    Only managers can update runs. Used internally to update run status and solver results.
    """
    return await update_scheduling_run(db, run_id, payload)


@router.delete(
    "/{run_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a scheduling run",
    dependencies=[Depends(require_manager)],
)
async def delete_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Delete a scheduling run and all its solutions.
    
    Only managers can delete runs.
    """
    await delete_scheduling_run(db, run_id)
    return {"message": "Scheduling run deleted successfully"}


# ---------------------- Solution routes ---------------------

@router.get(
    "/{run_id}/solutions",
    response_model=List[SchedulingSolutionRead],
    status_code=status.HTTP_200_OK,
    summary="Get all solutions for a scheduling run",
    dependencies=[Depends(require_auth)],
)
async def get_run_solutions(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all solutions (proposed assignments) for a scheduling run.
    
    All authenticated users can view solutions.
    """
    return await get_scheduling_solutions(db, run_id)

