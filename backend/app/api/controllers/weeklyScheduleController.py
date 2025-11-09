"""
Weekly schedule controller module.

This module contains business logic for weekly schedule management operations including
creation, retrieval, and deletion of weekly schedule records.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List
from app.db.models.weeklyScheduleModel import WeeklyScheduleModel
from app.schemas.weeklyScheduleSchema import WeeklyScheduleCreate, WeeklyScheduleRead
from app.schemas.plannedShiftSchema import PlannedShiftRead


# ------------------------
# Helper Functions
# ------------------------
def _serialize_weekly_schedule(db: Session, schedule: WeeklyScheduleModel) -> WeeklyScheduleRead:
    """
    Convert ORM object to schema including creator name and planned shifts.
    
    Args:
        db: Database session
        schedule: WeeklyScheduleModel instance
        
    Returns:
        WeeklyScheduleRead instance
    """
    created_by_name = schedule.created_by.user_full_name if schedule.created_by else None
    
    # Convert planned shifts using model_validate 
    planned_shifts = [
        PlannedShiftRead.model_validate(ps) for ps in schedule.planned_shifts
    ] if schedule.planned_shifts else []

    return WeeklyScheduleRead(
        weekly_schedule_id=schedule.weekly_schedule_id,
        week_start_date=schedule.week_start_date,
        created_by_id=schedule.created_by_id,
        created_by_name=created_by_name,
        planned_shifts=planned_shifts,
    )


# ------------------------
# CRUD Functions
# ------------------------

async def create_weekly_schedule(db: Session, schedule_data: WeeklyScheduleCreate) -> WeeklyScheduleRead:
    """
    Create a new weekly schedule.
    
    Args:
        db: Database session
        schedule_data: Weekly schedule creation data
        
    Returns:
        Created WeeklyScheduleRead instance
        
    Raises:
        HTTPException: If creator user not found or database error occurs
    """
    try:
        schedule = WeeklyScheduleModel(
            week_start_date=schedule_data.week_start_date,
            created_by_id=schedule_data.created_by_id,
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)

        return _serialize_weekly_schedule(db, schedule)
    
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {error_str}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_all_weekly_schedules(db: Session) -> List[WeeklyScheduleRead]:
    """
    Retrieve all weekly schedules from the database.
    
    Args:
        db: Database session
        
    Returns:
        List of all WeeklyScheduleRead instances
        
    Raises:
        HTTPException: If database error occurs
    """
    try:
        schedules = db.query(WeeklyScheduleModel).all()
        return [_serialize_weekly_schedule(db, s) for s in schedules]
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_weekly_schedule(db: Session, schedule_id: int) -> WeeklyScheduleRead:
    """
    Retrieve a single weekly schedule by ID.
    
    Args:
        db: Database session
        schedule_id: Weekly schedule identifier
        
    Returns:
        WeeklyScheduleRead instance
        
    Raises:
        HTTPException: If schedule not found or database error occurs
    """
    try:
        schedule = db.get(WeeklyScheduleModel, schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Weekly schedule not found"
            )
        return _serialize_weekly_schedule(db, schedule)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def delete_weekly_schedule(db: Session, schedule_id: int) -> None:
    """
    Delete a weekly schedule from the database.
    Planned shifts will be automatically deleted via CASCADE.
    
    Args:
        db: Database session
        schedule_id: Weekly schedule identifier
        
    Raises:
        HTTPException: If schedule not found or database error occurs
    """
    try:
        schedule = db.get(WeeklyScheduleModel, schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Weekly schedule not found"
            )

        # Delete schedule (planned shifts will be automatically deleted via CASCADE)
        db.delete(schedule)
        db.commit()
    
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {error_str}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
