"""
Planned shift controller module.

This module contains business logic for planned shift management operations including
creation, retrieval, updating, and deletion of planned shift records.
Controllers use repositories for database access - no direct ORM access.
"""

from datetime import date, datetime
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session  # Only for type hints

from app.repositories.shift_repository import ShiftRepository
from app.repositories.shift_template_repository import ShiftTemplateRepository
from app.schemas.planned_shift_schema import (
    PlannedShiftCreate,
    PlannedShiftUpdate,
    PlannedShiftRead,
)
from app.schemas.shift_assignment_schema import ShiftAssignmentRead
from app.exceptions.repository import NotFoundError, ConflictError
from app.data.session_manager import transaction


def _serialize_planned_shift(shift) -> PlannedShiftRead:
    """
    Convert ORM object to response schema.
    """
    shift_template_name = None
    if shift.shift_template:
        shift_template_name = shift.shift_template.shift_template_name

    # Convert assignments with proper user and role data
    assignments = []
    if shift.assignments:
        for a in shift.assignments:
            user_full_name = a.user.user_full_name if a.user else None
            role_name = a.role.role_name if a.role else None
            assignments.append(ShiftAssignmentRead(
                assignment_id=a.assignment_id,
                planned_shift_id=a.planned_shift_id,
                user_id=a.user_id,
                role_id=a.role_id,
                user_full_name=user_full_name,
                role_name=role_name,
            ))

    return PlannedShiftRead(
        planned_shift_id=shift.planned_shift_id,
        weekly_schedule_id=shift.weekly_schedule_id,
        shift_template_id=shift.shift_template_id,
        shift_template_name=shift_template_name,
        date=shift.date,
        start_time=shift.start_time,
        end_time=shift.end_time,
        location=shift.location,
        status=shift.status,
        assignments=assignments,
    )


async def create_planned_shift(
    planned_shift_data: PlannedShiftCreate,
    shift_repository: ShiftRepository,
    template_repository: ShiftTemplateRepository,
    db: Session  # For transaction management
) -> PlannedShiftRead:
    """
    Create a new planned shift for a given week and template.
    If start_time, end_time, or location are not provided, they will be taken from the shift template.
    
    Business logic:
    - Get template for default values
    - Combine date with template times if needed
    - Use template location if not provided
    - Create shift
    """
    # Get template to get default values
    template = template_repository.get_or_raise(planned_shift_data.shift_template_id)
    
    # Use provided values or fall back to template values
    start_datetime = planned_shift_data.start_time
    end_datetime = planned_shift_data.end_time
    location = planned_shift_data.location
    
    # If times not provided, combine date with template times
    if not start_datetime or not end_datetime:
        if not template.start_time or not template.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Shift template '{template.shift_template_name}' is missing start_time or end_time, and no override was provided"
            )
        if not start_datetime:
            start_datetime = datetime.combine(planned_shift_data.date, template.start_time)
        if not end_datetime:
            end_datetime = datetime.combine(planned_shift_data.date, template.end_time)
    
    # If location not provided, use template location
    if not location:
        if not template.location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Shift template '{template.shift_template_name}' has no location, and no location was provided"
            )
        location = template.location
    
    with transaction(db):
        shift = shift_repository.create(
            weekly_schedule_id=planned_shift_data.weekly_schedule_id,
            shift_template_id=planned_shift_data.shift_template_id,
            date=planned_shift_data.date,
            start_time=start_datetime,
            end_time=end_datetime,
            location=location,
            status=planned_shift_data.status,
        )
        
        # Get shift with relationships for serialization
        shift = shift_repository.get_with_template_and_assignments(shift.planned_shift_id)
        return _serialize_planned_shift(shift)


async def list_planned_shifts(
    shift_repository: ShiftRepository
) -> List[PlannedShiftRead]:
    """
    Retrieve all planned shifts from the database.
    """
    shifts = shift_repository.get_all_with_template_and_assignments()
    return [_serialize_planned_shift(s) for s in shifts]


async def get_planned_shift(
    shift_id: int,
    shift_repository: ShiftRepository
) -> PlannedShiftRead:
    """
    Retrieve a single planned shift by ID.
    """
    shift = shift_repository.get_with_template_and_assignments(shift_id)
    if not shift:
        raise NotFoundError(f"Planned shift {shift_id} not found")
    return _serialize_planned_shift(shift)


async def update_planned_shift(
    shift_id: int,
    planned_shift_data: PlannedShiftUpdate,
    shift_repository: ShiftRepository,
    db: Session  # For transaction management
) -> PlannedShiftRead:
    """
    Update an existing planned shift.
    
    Business logic:
    - Update fields if provided
    - Return updated shift with relationships
    """
    shift_repository.get_or_raise(shift_id)  # Verify exists
    
    with transaction(db):
        # Update fields
        update_data = {}
        if planned_shift_data.weekly_schedule_id is not None:
            update_data["weekly_schedule_id"] = planned_shift_data.weekly_schedule_id
        if planned_shift_data.shift_template_id is not None:
            update_data["shift_template_id"] = planned_shift_data.shift_template_id
        if planned_shift_data.date is not None:
            update_data["date"] = planned_shift_data.date
        if planned_shift_data.start_time is not None:
            update_data["start_time"] = planned_shift_data.start_time
        if planned_shift_data.end_time is not None:
            update_data["end_time"] = planned_shift_data.end_time
        if planned_shift_data.location is not None:
            update_data["location"] = planned_shift_data.location
        if planned_shift_data.status is not None:
            update_data["status"] = planned_shift_data.status
        
        if update_data:
            shift_repository.update(shift_id, **update_data)
        
        # Get updated shift with relationships
        shift = shift_repository.get_with_template_and_assignments(shift_id)
        return _serialize_planned_shift(shift)


async def delete_planned_shift(
    shift_id: int,
    shift_repository: ShiftRepository,
    db: Session  # For transaction management
) -> None:
    """
    Delete a planned shift and all its assignments.
    
    Business logic:
    - Verify shift exists
    - Delete shift (assignments cascade automatically)
    """
    shift_repository.get_or_raise(shift_id)  # Verify exists
    
    with transaction(db):
        shift_repository.delete(shift_id)
