"""
Shift assignment routes module.

This module defines the REST API endpoints for shift assignment management operations
including CRUD operations for shift assignment records.
"""

from fastapi import APIRouter, Depends, status
from typing import List
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.shiftAssignmentSchema import (
    ShiftAssignmentCreate,
    ShiftAssignmentRead,
)
from app.api.controllers.shiftAssignmentController import (
    create_shift_assignment,
    get_all_shift_assignments,
    get_shift_assignment,
    get_assignments_by_shift,
    get_assignments_by_user,
    delete_shift_assignment,
)

router = APIRouter(
    prefix="/shift-assignments", tags=["Shift Assignments"]
)


# ------------------------
# Collection Routes
# ------------------------

@router.post("/", response_model=ShiftAssignmentRead, status_code=status.HTTP_201_CREATED,
             summary="Create a new shift assignment")
async def create_assignment(shift_assignment_data: ShiftAssignmentCreate, db: Session = Depends(get_db)):
    """
    Assign a user to a planned shift in a specific role.
    
    Args:
        shift_assignment_data: Shift assignment creation data
        db: Database session dependency
        
    Returns:
        Created shift assignment data
    """
    assignment = await create_shift_assignment(db, shift_assignment_data)
    return assignment


@router.get("/", response_model=List[ShiftAssignmentRead], status_code=status.HTTP_200_OK,
            summary="List all shift assignments")
async def list_all_assignments(db: Session = Depends(get_db)):
    """
    Retrieve all shift assignments from the system.
    
    Args:
        db: Database session dependency
        
    Returns:
        List of all shift assignments
    """
    assignments = await get_all_shift_assignments(db)
    return assignments


# ------------------------
# Filter Routes (specific before parameterized)
# ------------------------

@router.get("/by-shift/{shift_id}", response_model=List[ShiftAssignmentRead], status_code=status.HTTP_200_OK,
            summary="Get assignments by planned shift")
async def get_assignments_for_shift(shift_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all assignments for a specific planned shift.
    
    Args:
        shift_id: Planned shift identifier
        db: Database session dependency
        
    Returns:
        List of shift assignments for the specified shift
    """
    assignments = await get_assignments_by_shift(db, shift_id)
    return assignments


@router.get("/by-user/{user_id}", response_model=List[ShiftAssignmentRead], status_code=status.HTTP_200_OK,
            summary="Get assignments by user")
async def get_assignments_for_user(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all assignments for a specific user.
    
    Args:
        user_id: User identifier
        db: Database session dependency
        
    Returns:
        List of shift assignments for the specified user
    """
    assignments = await get_assignments_by_user(db, user_id)
    return assignments


# ------------------------
# Resource Routes
# ------------------------

@router.get("/{assignment_id}", response_model=ShiftAssignmentRead, status_code=status.HTTP_200_OK,
            summary="Get a shift assignment by ID")
async def get_one_assignment(assignment_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific shift assignment by its ID.
    
    Args:
        assignment_id: Shift assignment identifier
        db: Database session dependency
        
    Returns:
        Shift assignment data
    """
    assignment = await get_shift_assignment(db, assignment_id)
    return assignment


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a shift assignment")
async def delete_assignment(assignment_id: int, db: Session = Depends(get_db)):
    """
    Delete a shift assignment from the system.
    
    Args:
        assignment_id: Shift assignment identifier
        db: Database session dependency
        
    Returns:
        No content (204)
    """
    await delete_shift_assignment(db, assignment_id)
