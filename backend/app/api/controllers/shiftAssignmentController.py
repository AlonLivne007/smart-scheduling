"""
Shift assignment controller module.

This module contains business logic for shift assignment management operations including
creation, retrieval, and deletion of shift assignment records.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List
from app.db.models.shiftAssignmentModel import ShiftAssignmentModel
from app.schemas.shiftAssignmentSchema import (
    ShiftAssignmentCreate,
    ShiftAssignmentRead,
)


# ------------------------
# Helper Functions
# ------------------------

def _serialize_assignment(assignment: ShiftAssignmentModel) -> ShiftAssignmentRead:
    """
    Convert ORM object to Pydantic schema.
    
    Args:
        assignment: ShiftAssignmentModel instance
        
    Returns:
        ShiftAssignmentRead instance
    """
    # Extract relationship data explicitly
    user_full_name = assignment.user.user_full_name if assignment.user else None
    role_name = assignment.role.role_name if assignment.role else None
    
    return ShiftAssignmentRead(
        assignment_id=assignment.assignment_id,
        planned_shift_id=assignment.planned_shift_id,
        user_id=assignment.user_id,
        role_id=assignment.role_id,
        user_full_name=user_full_name,
        role_name=role_name,
    )


# ------------------------
# CRUD Functions
# ------------------------

async def create_shift_assignment(db: Session, shift_assignment_data: ShiftAssignmentCreate) -> ShiftAssignmentRead:
    """
    Assign a user to a planned shift in a specific role.
    
    Args:
        db: Database session
        shift_assignment_data: Shift assignment creation data
        
    Returns:
        Created ShiftAssignmentRead instance
        
    Raises:
        HTTPException: If constraint violation (e.g., duplicate assignment) or database error occurs
    """
    try:
        assignment = ShiftAssignmentModel(
            planned_shift_id=shift_assignment_data.planned_shift_id,
            user_id=shift_assignment_data.user_id,
            role_id=shift_assignment_data.role_id,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        # Ensure relationships are loaded
        _ = assignment.user  # Trigger lazy load
        _ = assignment.role  # Trigger lazy load
        return _serialize_assignment(assignment)
    
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


async def get_all_shift_assignments(db: Session) -> List[ShiftAssignmentRead]:
    """
    Retrieve all shift assignments from the database.
    
    Args:
        db: Database session
        
    Returns:
        List of all ShiftAssignmentRead instances
        
    Raises:
        HTTPException: If database error occurs
    """
    try:
        assignments = db.query(ShiftAssignmentModel).options(
            joinedload(ShiftAssignmentModel.user),
            joinedload(ShiftAssignmentModel.role)
        ).all()
        return [_serialize_assignment(a) for a in assignments]
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_shift_assignment(db: Session, assignment_id: int) -> ShiftAssignmentRead:
    """
    Retrieve a single shift assignment by ID.
    
    Args:
        db: Database session
        assignment_id: Shift assignment identifier
        
    Returns:
        ShiftAssignmentRead instance
        
    Raises:
        HTTPException: If assignment not found or database error occurs
    """
    try:
        assignment = db.query(ShiftAssignmentModel).options(
            joinedload(ShiftAssignmentModel.user),
            joinedload(ShiftAssignmentModel.role)
        ).filter(ShiftAssignmentModel.assignment_id == assignment_id).first()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shift assignment not found"
            )
        return _serialize_assignment(assignment)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_assignments_by_shift(db: Session, shift_id: int) -> List[ShiftAssignmentRead]:
    """
    Retrieve all assignments for a given planned shift.
    
    Args:
        db: Database session
        shift_id: Planned shift identifier
        
    Returns:
        List of ShiftAssignmentRead instances for the shift
        
    Raises:
        HTTPException: If database error occurs
    """
    try:
        assignments = db.query(ShiftAssignmentModel).options(
            joinedload(ShiftAssignmentModel.user),
            joinedload(ShiftAssignmentModel.role)
        ).filter(
            ShiftAssignmentModel.planned_shift_id == shift_id
        ).all()
        return [_serialize_assignment(a) for a in assignments]
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_assignments_by_user(db: Session, user_id: int) -> List[ShiftAssignmentRead]:
    """
    Retrieve all assignments for a specific user.
    
    Args:
        db: Database session
        user_id: User identifier
        
    Returns:
        List of ShiftAssignmentRead instances for the user
        
    Raises:
        HTTPException: If database error occurs
    """
    try:
        assignments = db.query(ShiftAssignmentModel).options(
            joinedload(ShiftAssignmentModel.user),
            joinedload(ShiftAssignmentModel.role)
        ).filter(
            ShiftAssignmentModel.user_id == user_id
        ).all()
        return [_serialize_assignment(a) for a in assignments]
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def delete_shift_assignment(db: Session, assignment_id: int) -> None:
    """
    Delete a shift assignment.
    
    Args:
        db: Database session
        assignment_id: Shift assignment identifier
        
    Raises:
        HTTPException: If assignment not found or database error occurs
    """
    try:
        assignment = db.get(ShiftAssignmentModel, assignment_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shift assignment not found"
            )
        
        db.delete(assignment)
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

