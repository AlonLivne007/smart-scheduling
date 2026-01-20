"""
System constraints controller module.

This module contains business logic for system constraints management operations.
Controllers use repositories for database access - no direct ORM access.
"""

from typing import List
from sqlalchemy.orm import Session  # Only for type hints

from app.data.repositories.system_constraints_repository import SystemConstraintsRepository
from app.schemas.system_constraints_schema import (
    SystemConstraintCreate,
    SystemConstraintUpdate,
    SystemConstraintRead
)
from app.core.exceptions.repository import ConflictError
from app.data.session_manager import transaction


async def create_system_constraint(
    constraint_data: SystemConstraintCreate,
    constraints_repository: SystemConstraintsRepository,
    db: Session  # For transaction management
) -> SystemConstraintRead:
    """
    Create a new system constraint.
    
    Business logic:
    - Check if constraint type already exists (unique constraint)
    - Create constraint
    """
    # Business rule: Check if constraint type already exists
    existing = constraints_repository.get_by_type(constraint_data.constraint_type)
    if existing:
        raise ConflictError(
            f"Constraint with type {constraint_data.constraint_type.value} already exists"
        )
    
    with transaction(db):
        constraint = constraints_repository.create(**constraint_data.model_dump())
        return SystemConstraintRead.model_validate(constraint)


async def get_system_constraint(
    constraint_id: int,
    constraints_repository: SystemConstraintsRepository
) -> SystemConstraintRead:
    """
    Get a system constraint by ID.
    """
    constraint = constraints_repository.get_or_raise(constraint_id)
    return SystemConstraintRead.model_validate(constraint)


async def list_system_constraints(
    constraints_repository: SystemConstraintsRepository
) -> List[SystemConstraintRead]:
    """
    Retrieve all system constraints from the database.
    """
    constraints = constraints_repository.get_all()
    return [SystemConstraintRead.model_validate(c) for c in constraints]


async def update_system_constraint(
    constraint_id: int,
    constraint_data: SystemConstraintUpdate,
    constraints_repository: SystemConstraintsRepository,
    db: Session  # For transaction management
) -> SystemConstraintRead:
    """
    Update an existing system constraint.
    
    Business logic:
    - Verify constraint exists
    - Update only provided fields
    """
    constraint = constraints_repository.get_or_raise(constraint_id)
    
    with transaction(db):
        # Build update data from provided fields
        update_data = {}
        if constraint_data.constraint_value is not None:
            update_data["constraint_value"] = constraint_data.constraint_value
        if constraint_data.is_hard_constraint is not None:
            update_data["is_hard_constraint"] = constraint_data.is_hard_constraint
        
        updated_constraint = constraints_repository.update(constraint_id, **update_data)
        return SystemConstraintRead.model_validate(updated_constraint)


async def delete_system_constraint(
    constraint_id: int,
    constraints_repository: SystemConstraintsRepository,
    db: Session  # For transaction management
) -> dict:
    """
    Delete a system constraint.
    
    Business logic:
    - Verify constraint exists
    - Delete constraint
    """
    constraint = constraints_repository.get_or_raise(constraint_id)
    
    with transaction(db):
        constraints_repository.delete(constraint_id)
        return {"message": "Constraint deleted successfully"}
