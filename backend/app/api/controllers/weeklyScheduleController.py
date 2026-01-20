"""
Weekly schedule controller module.

This module contains business logic for weekly schedule management operations including
creation, retrieval, and deletion of weekly schedule records.
Controllers use repositories for database access - no direct ORM access.
"""

from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session  # Only for type hints

from app.repositories.weekly_schedule_repository import WeeklyScheduleRepository
from app.repositories.shift_template_repository import ShiftTemplateRepository
from app.repositories.user_repository import UserRepository
from app.schemas.weeklyScheduleSchema import WeeklyScheduleCreate, WeeklyScheduleRead
from app.schemas.plannedShiftSchema import PlannedShiftRead
from app.exceptions.repository import NotFoundError, ConflictError
from app.db.session_manager import transaction


def _serialize_weekly_schedule(
    schedule,
    template_repository: ShiftTemplateRepository
) -> WeeklyScheduleRead:
    """
    Convert ORM object to schema including creator name and planned shifts.
    
    Uses repository to get role requirements.
    """
    created_by_name = schedule.created_by.user_full_name if schedule.created_by else None
    published_by_name = schedule.published_by.user_full_name if schedule.published_by else None
    
    planned_shifts = []
    if schedule.planned_shifts:
        template_ids = [ps.shift_template_id for ps in schedule.planned_shifts if ps.shift_template_id]
        
        # Get role requirements for all templates
        required_by_template = {}
        if template_ids:
            template_role_map = template_repository.get_role_requirements_with_counts(template_ids)
            for template_id, role_map in template_role_map.items():
                required_by_template[template_id] = sum(role_map.values())
        
        for ps in schedule.planned_shifts:
            ps_read = PlannedShiftRead.model_validate(ps)
            template_name = ps.shift_template.shift_template_name if ps.shift_template else None
            required_positions = required_by_template.get(ps.shift_template_id, 0)
            planned_shifts.append(
                ps_read.model_copy(
                    update={
                        "shift_template_name": template_name,
                        "required_positions": required_positions,
                    }
                )
            )
    
    return WeeklyScheduleRead(
        weekly_schedule_id=schedule.weekly_schedule_id,
        week_start_date=schedule.week_start_date,
        created_by_id=schedule.created_by_id,
        created_by_name=created_by_name,
        status=schedule.status.value if schedule.status else "DRAFT",
        published_at=schedule.published_at,
        published_by_id=schedule.published_by_id,
        published_by_name=published_by_name,
        planned_shifts=planned_shifts,
    )


async def create_weekly_schedule(
    schedule_data: WeeklyScheduleCreate,
    user_id: int,
    schedule_repository: WeeklyScheduleRepository,
    template_repository: ShiftTemplateRepository,
    user_repository: UserRepository,
    db: Session  # For transaction management
) -> WeeklyScheduleRead:
    """
    Create a new weekly schedule.
    
    Business logic:
    - Verify user exists
    - Check if schedule for this week already exists
    - Create schedule
    """
    try:
        # Business rule: Verify user exists
        user_repository.get_by_id_or_raise(user_id)
        
        # Business rule: Check if schedule for this week already exists
        existing = schedule_repository.get_by_week_start(schedule_data.week_start_date)
        if existing:
            raise ConflictError(f"Schedule for week starting {schedule_data.week_start_date} already exists")
        
        with transaction(db):
            schedule = schedule_repository.create(
                week_start_date=schedule_data.week_start_date,
                created_by_id=user_id,
            )
            
            # Get schedule with relationships for serialization
            schedule = schedule_repository.get_with_all_relationships(schedule.weekly_schedule_id)
            return _serialize_weekly_schedule(schedule, template_repository)
            
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


async def get_all_weekly_schedules(
    schedule_repository: WeeklyScheduleRepository,
    template_repository: ShiftTemplateRepository
) -> List[WeeklyScheduleRead]:
    """
    Retrieve all weekly schedules from the database.
    """
    schedules = schedule_repository.get_all_with_relationships()
    return [_serialize_weekly_schedule(s, template_repository) for s in schedules]


async def get_weekly_schedule(
    schedule_id: int,
    schedule_repository: WeeklyScheduleRepository,
    template_repository: ShiftTemplateRepository
) -> WeeklyScheduleRead:
    """
    Retrieve a single weekly schedule by ID.
    """
    try:
        schedule = schedule_repository.get_with_all_relationships(schedule_id)
        if not schedule:
            raise NotFoundError(f"Weekly schedule {schedule_id} not found")
        return _serialize_weekly_schedule(schedule, template_repository)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weekly schedule not found"
        )


async def delete_weekly_schedule(
    schedule_id: int,
    schedule_repository: WeeklyScheduleRepository,
    db: Session  # For transaction management
) -> None:
    """
    Delete a weekly schedule from the database.
    Planned shifts will be automatically deleted via CASCADE.
    
    Business logic:
    - Verify schedule exists
    - Delete schedule (cascade handles shifts)
    """
    try:
        schedule_repository.get_by_id_or_raise(schedule_id)  # Verify exists
        
        with transaction(db):
            schedule_repository.delete(schedule_id)
            
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weekly schedule not found"
        )
