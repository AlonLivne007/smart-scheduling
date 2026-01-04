"""
Weekly schedule routes module.

This module defines the REST API endpoints for weekly schedule management operations
including CRUD operations for weekly schedule records.
"""

from fastapi import APIRouter, Depends, status
from typing import List
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.userModel import UserModel
from app.api.controllers.authController import get_current_user
from app.api.dependencies.auth import require_auth
from app.schemas.weeklyScheduleSchema import WeeklyScheduleCreate, WeeklyScheduleRead
from app.api.controllers.weeklyScheduleController import (
    create_weekly_schedule,
    get_all_weekly_schedules,
    get_weekly_schedule,
    delete_weekly_schedule,
)

router = APIRouter(prefix="/weekly-schedules", tags=["Weekly Schedules"])


@router.post("/", response_model=WeeklyScheduleRead, status_code=status.HTTP_201_CREATED,
             summary="Create a new weekly schedule",
             dependencies=[Depends(require_auth)])
async def create_schedule(
    schedule_data: WeeklyScheduleCreate, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new weekly schedule.
    
    Args:
        schedule_data: Weekly schedule creation data
        db: Database session dependency
        current_user: Authenticated user (from JWT token)
        
    Returns:
        Created weekly schedule data
    """
    schedule = await create_weekly_schedule(db, schedule_data, current_user.user_id)
    return schedule


@router.get("/", response_model=List[WeeklyScheduleRead], status_code=status.HTTP_200_OK,
            summary="List all weekly schedules")
async def get_all_schedules(db: Session = Depends(get_db)):
    """
    Retrieve all weekly schedules from the system.
    
    Args:
        db: Database session dependency
        
    Returns:
        List of all weekly schedules
    """
    schedules = await get_all_weekly_schedules(db)
    return schedules


@router.get("/{schedule_id}", response_model=WeeklyScheduleRead, status_code=status.HTTP_200_OK,
            summary="Get a weekly schedule by ID")
async def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific weekly schedule by its ID.
    
    Args:
        schedule_id: Weekly schedule identifier
        db: Database session dependency
        
    Returns:
        Weekly schedule data
    """
    schedule = await get_weekly_schedule(db, schedule_id)
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a weekly schedule")
async def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """
    Delete a weekly schedule from the system.
    Planned shifts will be automatically deleted via CASCADE.
    
    Args:
        schedule_id: Weekly schedule identifier
        db: Database session dependency
        
    Returns:
        No content (204)
    """
    await delete_weekly_schedule(db, schedule_id)
