"""
Scheduling optimization routes module.

This module defines the REST API endpoints for scheduling optimization operations.
Routes use repository dependency injection - no direct DB access.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.api.controllers.schedulingController import (
    trigger_optimization,
    get_scheduling_run_with_metrics,
    get_schedule_runs_with_metrics
)
from app.api.dependencies.repositories import (
    get_weekly_schedule_repository,
    get_scheduling_run_repository,
    get_optimization_config_repository,
    get_shift_template_repository
)
from app.db.session import get_db

# AuthN/Authorization
from app.api.dependencies.auth import require_auth, require_manager
from app.repositories.weekly_schedule_repository import WeeklyScheduleRepository
from app.repositories.scheduling_run_repository import SchedulingRunRepository
from app.repositories.optimization_config_repository import OptimizationConfigRepository
from app.repositories.shift_template_repository import ShiftTemplateRepository

router = APIRouter(prefix="/scheduling", tags=["Scheduling"])


# ---------------------- Optimization routes -------------------

@router.post(
    "/optimize",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger optimization for a weekly schedule",
    dependencies=[Depends(require_manager)],  # MANAGER ONLY
)
async def optimize_schedule(
    weekly_schedule_id: int = Query(..., description="Weekly schedule ID to optimize"),
    config_id: Optional[int] = Query(None, description="Optional optimization config ID"),
    schedule_repository: WeeklyScheduleRepository = Depends(get_weekly_schedule_repository),
    config_repository: OptimizationConfigRepository = Depends(get_optimization_config_repository),
    run_repository: SchedulingRunRepository = Depends(get_scheduling_run_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await trigger_optimization(
        weekly_schedule_id,
        config_id,
        schedule_repository,
        config_repository,
        run_repository,
        db
    )


@router.get(
    "/runs/{run_id}/metrics",
    status_code=status.HTTP_200_OK,
    summary="Get scheduling run with metrics",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_run_metrics(
    run_id: int,
    run_repository: SchedulingRunRepository = Depends(get_scheduling_run_repository),
    schedule_repository: WeeklyScheduleRepository = Depends(get_weekly_schedule_repository),
    template_repository: ShiftTemplateRepository = Depends(get_shift_template_repository)
):
    return await get_scheduling_run_with_metrics(
        run_id,
        run_repository,
        schedule_repository,
        template_repository
    )


@router.get(
    "/schedules/{weekly_schedule_id}/runs",
    status_code=status.HTTP_200_OK,
    summary="Get all runs for a schedule with metrics",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_schedule_runs(
    weekly_schedule_id: int,
    run_repository: SchedulingRunRepository = Depends(get_scheduling_run_repository),
    schedule_repository: WeeklyScheduleRepository = Depends(get_weekly_schedule_repository),
    template_repository: ShiftTemplateRepository = Depends(get_shift_template_repository)
):
    return await get_schedule_runs_with_metrics(
        weekly_schedule_id,
        run_repository,
        schedule_repository,
        template_repository
    )
