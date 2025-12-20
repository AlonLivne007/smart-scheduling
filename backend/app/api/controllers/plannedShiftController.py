"""
Planned shift controller module.

This module contains business logic for planned shift management operations including
creation, retrieval, updating, and deletion of planned shift records.
"""

from datetime import date, datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List
from app.db.models.plannedShiftModel import PlannedShiftModel
from app.db.models.shiftTemplateModel import ShiftTemplateModel
from app.schemas.plannedShiftSchema import (
    PlannedShiftCreate,
    PlannedShiftUpdate,
    PlannedShiftRead,
)
from app.schemas.shiftAssignmentSchema import ShiftAssignmentRead


# ------------------------
# Helper Functions
# ------------------------

def _serialize_planned_shift(db: Session, shift: PlannedShiftModel) -> PlannedShiftRead:
    """
    Convert ORM object to response schema.
    
    Args:
        db: Database session
        shift: PlannedShiftModel instance
        
    Returns:
        PlannedShiftRead instance
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


# ------------------------
# CRUD Functions
# ------------------------

async def create_planned_shift(db: Session, planned_shift_data: PlannedShiftCreate) -> PlannedShiftRead:
    """
    Create a new planned shift for a given week and template.
    If start_time, end_time, or location are not provided, they will be taken from the shift template.
    
    Args:
        db: Database session
        planned_shift_data: Planned shift creation data
        
    Returns:
        Created PlannedShiftRead instance
        
    Raises:
        HTTPException: If template not found, missing template data, or database error occurs
    """
    try:
        # Fetch template to get default values if not provided
        template = db.get(ShiftTemplateModel, planned_shift_data.shift_template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shift template not found"
            )
        
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
        
        new_shift = PlannedShiftModel(
            weekly_schedule_id=planned_shift_data.weekly_schedule_id,
            shift_template_id=planned_shift_data.shift_template_id,
            date=planned_shift_data.date,
            start_time=start_datetime,
            end_time=end_datetime,
            location=location,
            status=planned_shift_data.status,
        )
        db.add(new_shift)
        db.commit()
        db.refresh(new_shift)
        return _serialize_planned_shift(db, new_shift)
    
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


async def get_all_planned_shifts(db: Session) -> List[PlannedShiftRead]:
    """
    Retrieve all planned shifts from the database.
    
    Args:
        db: Database session
        
    Returns:
        List of all PlannedShiftRead instances
        
    Raises:
        HTTPException: If database error occurs
    """
    try:
        shifts = db.query(PlannedShiftModel).all()
        return [_serialize_planned_shift(db, s) for s in shifts]
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_planned_shift(db: Session, shift_id: int) -> PlannedShiftRead:
    """
    Retrieve a single planned shift by ID.
    
    Args:
        db: Database session
        shift_id: Planned shift identifier
        
    Returns:
        PlannedShiftRead instance
        
    Raises:
        HTTPException: If shift not found or database error occurs
    """
    try:
        shift = db.get(PlannedShiftModel, shift_id)
        if not shift:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Planned shift not found"
            )
        return _serialize_planned_shift(db, shift)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def update_planned_shift(db: Session, shift_id: int, planned_shift_data: PlannedShiftUpdate) -> PlannedShiftRead:
    """
    Update an existing planned shift.
    
    Args:
        db: Database session
        shift_id: Planned shift identifier
        planned_shift_data: Update data
        
    Returns:
        Updated PlannedShiftRead instance
        
    Raises:
        HTTPException: If shift not found, constraint violation, or database error occurs
    """
    try:
        shift = db.get(PlannedShiftModel, shift_id)
        if not shift:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Planned shift not found"
            )

        # Update fields (only if provided)
        if planned_shift_data.weekly_schedule_id is not None:
            shift.weekly_schedule_id = planned_shift_data.weekly_schedule_id
        if planned_shift_data.shift_template_id is not None:
            shift.shift_template_id = planned_shift_data.shift_template_id
        if planned_shift_data.date is not None:
            shift.date = planned_shift_data.date
        if planned_shift_data.start_time is not None:
            shift.start_time = planned_shift_data.start_time
        if planned_shift_data.end_time is not None:
            shift.end_time = planned_shift_data.end_time
        if planned_shift_data.location is not None:
            shift.location = planned_shift_data.location
        if planned_shift_data.status is not None:
            shift.status = planned_shift_data.status

        db.commit()
        db.refresh(shift)
        return _serialize_planned_shift(db, shift)
    
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


async def delete_planned_shift(db: Session, shift_id: int) -> None:
    """
    Delete a planned shift and all its assignments.
    
    Args:
        db: Database session
        shift_id: Planned shift identifier
        
    Raises:
        HTTPException: If shift not found or database error occurs
    """
    try:
        shift = db.get(PlannedShiftModel, shift_id)
        if not shift:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Planned shift not found"
            )
        
        # Delete shift (assignments will be automatically deleted via CASCADE)
        db.delete(shift)
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

