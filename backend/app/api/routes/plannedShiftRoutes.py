"""
Planned shift routes module.

This module defines the REST API endpoints for planned shift management operations
including CRUD operations for planned shift records.
"""

from fastapi import APIRouter, Depends, status
from typing import List
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.plannedShiftSchema import (
    PlannedShiftCreate,
    PlannedShiftUpdate,
    PlannedShiftRead,
)
from app.api.controllers.plannedShiftController import (
    create_planned_shift,
    get_all_planned_shifts,
    get_planned_shift,
    update_planned_shift,
    delete_planned_shift,
)

router = APIRouter(
    prefix="/planned-shifts", tags=["Planned Shifts"]
)


@router.post("/", response_model=PlannedShiftRead, status_code=status.HTTP_201_CREATED,
             summary="Create a new planned shift")
async def create_shift(planned_shift_data: PlannedShiftCreate, db: Session = Depends(get_db)):
    """
    Create a new planned shift for a given week and template.
    If start_time, end_time, or location are not provided, they will be taken from the shift template.
    
    Args:
        planned_shift_data: Planned shift creation data
        db: Database session dependency
        
    Returns:
        Created planned shift data
    """
    shift = await create_planned_shift(db, planned_shift_data)
    return shift


@router.get("/", response_model=List[PlannedShiftRead], status_code=status.HTTP_200_OK,
            summary="List all planned shifts")
async def list_all_shifts(db: Session = Depends(get_db)):
    """
    Retrieve all planned shifts from the system.
    
    Args:
        db: Database session dependency
        
    Returns:
        List of all planned shifts
    """
    shifts = await get_all_planned_shifts(db)
    return shifts


@router.get("/{shift_id}", response_model=PlannedShiftRead, status_code=status.HTTP_200_OK,
            summary="Get a planned shift by ID")
async def get_one_shift(shift_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific planned shift by its ID.
    
    Args:
        shift_id: Planned shift identifier
        db: Database session dependency
        
    Returns:
        Planned shift data
    """
    shift = await get_planned_shift(db, shift_id)
    return shift


@router.put("/{shift_id}", response_model=PlannedShiftRead, status_code=status.HTTP_200_OK,
            summary="Update a planned shift")
async def update_shift(shift_id: int, planned_shift_data: PlannedShiftUpdate, db: Session = Depends(get_db)):
    """
    Update an existing planned shift.
    
    Args:
        shift_id: Planned shift identifier
        planned_shift_data: Update data
        db: Database session dependency
        
    Returns:
        Updated planned shift data
    """
    shift = await update_planned_shift(db, shift_id, planned_shift_data)
    return shift


@router.delete("/{shift_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a planned shift")
async def delete_shift(shift_id: int, db: Session = Depends(get_db)):
    """
    Delete a planned shift from the system.
    Assignments will be automatically deleted via CASCADE.
    
    Args:
        shift_id: Planned shift identifier
        db: Database session dependency
        
    Returns:
        No content (204)
    """
    await delete_planned_shift(db, shift_id)