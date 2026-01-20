"""
Shift assignment controller module.

This module contains business logic for shift assignment management operations including
creation, retrieval, and deletion of shift assignment records.
Controllers use repositories for database access - no direct ORM access.
"""

from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session  # Only for type hints

from app.repositories.shift_repository import ShiftAssignmentRepository
from app.repositories.shift_repository import ShiftRepository
from app.schemas.shift_assignment_schema import (
    ShiftAssignmentCreate,
    ShiftAssignmentRead,
)
from app.exceptions.repository import NotFoundError, ConflictError
from app.data.session_manager import transaction


def _serialize_assignment(assignment) -> ShiftAssignmentRead:
    """
    Convert ORM object to Pydantic schema.
    """
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


async def create_shift_assignment(
    shift_assignment_data: ShiftAssignmentCreate,
    assignment_repository: ShiftAssignmentRepository,
    shift_repository: ShiftRepository,
    db: Session  # For transaction management
) -> ShiftAssignmentRead:
    """
    Assign a user to a planned shift in a specific role.
    
    Business logic:
    - Verify shift exists
    - Create assignment (repository handles uniqueness)
    """
    # Business rule: Verify shift exists
    shift_repository.get_or_raise(shift_assignment_data.planned_shift_id)
    
    with transaction(db):
        assignment = assignment_repository.create_assignment(
            planned_shift_id=shift_assignment_data.planned_shift_id,
            user_id=shift_assignment_data.user_id,
            role_id=shift_assignment_data.role_id
        )
        # Refresh to load relationships
        assignment = assignment_repository.get_by_id(assignment.assignment_id)
        return _serialize_assignment(assignment)


async def list_shift_assignments(
    assignment_repository: ShiftAssignmentRepository
) -> List[ShiftAssignmentRead]:
    """
    Retrieve all shift assignments from the database.
    """
    assignments = assignment_repository.get_all()
    return [_serialize_assignment(a) for a in assignments]


async def get_shift_assignment(
    assignment_id: int,
    assignment_repository: ShiftAssignmentRepository
) -> ShiftAssignmentRead:
    """
    Retrieve a single shift assignment by ID.
    """
    assignment = assignment_repository.get_or_raise(assignment_id)
    return _serialize_assignment(assignment)


async def get_assignments_by_shift(
    shift_id: int,
    assignment_repository: ShiftAssignmentRepository
) -> List[ShiftAssignmentRead]:
    """
    Get all assignments for a planned shift.
    """
    assignments = assignment_repository.get_by_shift(shift_id)
    return [_serialize_assignment(a) for a in assignments]


async def get_assignments_by_user(
    user_id: int,
    assignment_repository: ShiftAssignmentRepository
) -> List[ShiftAssignmentRead]:
    """
    Get all assignments for a user.
    """
    assignments = assignment_repository.get_by_user(user_id)
    return [_serialize_assignment(a) for a in assignments]


async def delete_shift_assignment(
    assignment_id: int,
    assignment_repository: ShiftAssignmentRepository,
    db: Session  # For transaction management
) -> None:
    """
    Delete a shift assignment.
    """
    assignment_repository.get_or_raise(assignment_id)  # Verify exists
    
    with transaction(db):
        assignment_repository.delete(assignment_id)
