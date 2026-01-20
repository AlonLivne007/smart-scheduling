"""
Scheduling run routes module.

This module defines the REST API endpoints for scheduling run management operations.
Routes use repository dependency injection - no direct DB access.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session

from app.api.controllers import scheduling_run_controller
from app.api.controllers.scheduling_run_controller import (
    create_scheduling_run,
    get_scheduling_run,
    update_scheduling_run,
    delete_scheduling_run,
    get_solutions_for_run,
    apply_solution_to_schedule
)
from app.api.controllers.auth_controller import get_current_user
from app.api.dependencies.repositories import (
    get_scheduling_run_repository,
    get_scheduling_solution_repository,
    get_weekly_schedule_repository,
    get_user_repository,
    get_shift_assignment_repository
)
from app.data.session import get_db
from app.schemas.scheduling_run_schema import (
    SchedulingRunCreate,
    SchedulingRunUpdate,
    SchedulingRunRead
)
from app.schemas.scheduling_solution_schema import SchedulingSolutionRead
from app.data.models.scheduling_run_model import SchedulingRunStatus
from app.data.models.user_model import UserModel

# AuthN/Authorization
from app.api.dependencies.auth import require_auth, require_manager
from app.data.repositories.scheduling_run_repository import SchedulingRunRepository
from app.data.repositories.scheduling_solution_repository import SchedulingSolutionRepository
from app.data.repositories.weekly_schedule_repository import WeeklyScheduleRepository
from app.data.repositories.user_repository import UserRepository
from app.data.repositories.shift_repository import ShiftAssignmentRepository

router = APIRouter(prefix="/scheduling-runs", tags=["Scheduling Runs"])


# ---------------------- Collection routes -------------------

@router.post(
    "/",
    response_model=SchedulingRunRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new scheduling run",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def create_run(
    run_data: SchedulingRunCreate,
    current_user: UserModel = Depends(get_current_user),
    run_repository: SchedulingRunRepository = Depends(get_scheduling_run_repository),
    schedule_repository: WeeklyScheduleRepository = Depends(get_weekly_schedule_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await create_scheduling_run(
        run_data,
        current_user.user_id,
        run_repository,
        schedule_repository,
        user_repository,
        db
    )


@router.get(
    "/",
    response_model=List[SchedulingRunRead],
    status_code=status.HTTP_200_OK,
    summary="Get all scheduling runs",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def list_runs(
    run_repository: SchedulingRunRepository = Depends(get_scheduling_run_repository),
    weekly_schedule_id: Optional[int] = Query(None, description="Filter by weekly schedule ID"),
    status_filter: Optional[str] = Query(None, description="Filter by status")
):
    status_enum = None
    if status_filter:
        try:
            status_enum = SchedulingRunStatus[status_filter.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {[s.name for s in SchedulingRunStatus]}"
            )
    
    return await scheduling_run_controller.list_scheduling_runs(
        run_repository,
        weekly_schedule_id,
        status_enum
    )


# ---------------------- Resource routes ---------------------

@router.get(
    "/{run_id}",
    response_model=SchedulingRunRead,
    status_code=status.HTTP_200_OK,
    summary="Get a scheduling run by ID",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_run(
    run_id: int,
    run_repository: SchedulingRunRepository = Depends(get_scheduling_run_repository)
):
    return await get_scheduling_run(run_id, run_repository)


@router.put(
    "/{run_id}",
    response_model=SchedulingRunRead,
    status_code=status.HTTP_200_OK,
    summary="Update a scheduling run",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def update_run(
    run_id: int,
    run_data: SchedulingRunUpdate,
    run_repository: SchedulingRunRepository = Depends(get_scheduling_run_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await update_scheduling_run(run_id, run_data, run_repository, db)


@router.delete(
    "/{run_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a scheduling run",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def delete_run(
    run_id: int,
    run_repository: SchedulingRunRepository = Depends(get_scheduling_run_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await delete_scheduling_run(run_id, run_repository, db)


# ---------------------- Solution routes ---------------------

@router.get(
    "/{run_id}/solutions",
    response_model=List[SchedulingSolutionRead],
    status_code=status.HTTP_200_OK,
    summary="Get all solutions for a run",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_run_solutions(
    run_id: int,
    solution_repository: SchedulingSolutionRepository = Depends(get_scheduling_solution_repository),
    run_repository: SchedulingRunRepository = Depends(get_scheduling_run_repository)
):
    return await get_solutions_for_run(run_id, solution_repository, run_repository)


@router.post(
    "/{run_id}/apply",
    status_code=status.HTTP_200_OK,
    summary="Apply solution to create shift assignments",
    dependencies=[Depends(require_manager)],  # MANAGER ONLY
)
async def apply_solution(
    run_id: int,
    run_repository: SchedulingRunRepository = Depends(get_scheduling_run_repository),
    solution_repository: SchedulingSolutionRepository = Depends(get_scheduling_solution_repository),
    assignment_repository: ShiftAssignmentRepository = Depends(get_shift_assignment_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await apply_solution_to_schedule(
        run_id,
        solution_repository,
        assignment_repository,
        run_repository,
        db
    )
