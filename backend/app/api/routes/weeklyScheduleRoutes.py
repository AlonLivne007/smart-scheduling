"""
Weekly schedule routes module.

This module defines the REST API endpoints for weekly schedule management operations.
Routes use repository dependency injection - no direct DB access.
"""

from typing import List

from fastapi import APIRouter, Depends, status

from app.api.controllers.weeklyScheduleController import (
    create_weekly_schedule,
    get_all_weekly_schedules,
    get_weekly_schedule,
    delete_weekly_schedule
)
from app.api.controllers.authController import get_current_user
from app.api.dependencies.repositories import (
    get_weekly_schedule_repository,
    get_shift_template_repository,
    get_user_repository
)
from app.db.session import get_db
from app.schemas.weeklyScheduleSchema import (
    WeeklyScheduleCreate,
    WeeklyScheduleRead
)

# AuthN/Authorization
from app.api.dependencies.auth import require_auth, require_manager
from app.repositories.weekly_schedule_repository import WeeklyScheduleRepository
from app.repositories.shift_template_repository import ShiftTemplateRepository
from app.repositories.user_repository import UserRepository
from app.db.models.userModel import UserModel
from sqlalchemy.orm import Session

router = APIRouter(prefix="/weekly-schedules", tags=["Weekly Schedules"])


# ---------------------- Collection routes -------------------

@router.post(
    "/",
    response_model=WeeklyScheduleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new weekly schedule",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def create_schedule(
    schedule_data: WeeklyScheduleCreate,
    current_user: UserModel = Depends(get_current_user),
    schedule_repository: WeeklyScheduleRepository = Depends(get_weekly_schedule_repository),
    template_repository: ShiftTemplateRepository = Depends(get_shift_template_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await create_weekly_schedule(
        schedule_data,
        current_user.user_id,
        schedule_repository,
        template_repository,
        user_repository,
        db
    )


@router.get(
    "/",
    response_model=List[WeeklyScheduleRead],
    status_code=status.HTTP_200_OK,
    summary="Get all weekly schedules",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_all_schedules(
    schedule_repository: WeeklyScheduleRepository = Depends(get_weekly_schedule_repository),
    template_repository: ShiftTemplateRepository = Depends(get_shift_template_repository)
):
    return await get_all_weekly_schedules(schedule_repository, template_repository)


# ---------------------- Resource routes ---------------------

@router.get(
    "/{schedule_id}",
    response_model=WeeklyScheduleRead,
    status_code=status.HTTP_200_OK,
    summary="Get a weekly schedule by ID",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_schedule(
    schedule_id: int,
    schedule_repository: WeeklyScheduleRepository = Depends(get_weekly_schedule_repository),
    template_repository: ShiftTemplateRepository = Depends(get_shift_template_repository)
):
    return await get_weekly_schedule(schedule_id, schedule_repository, template_repository)


@router.delete(
    "/{schedule_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a weekly schedule",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def delete_schedule(
    schedule_id: int,
    schedule_repository: WeeklyScheduleRepository = Depends(get_weekly_schedule_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await delete_weekly_schedule(schedule_id, schedule_repository, db)
