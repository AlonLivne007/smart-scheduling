"""
System constraints routes module.

This module defines the REST API endpoints for system-wide constraint
management operations.
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.controllers.systemConstraintsController import (
    create_system_constraint,
    get_all_system_constraints,
    get_system_constraint,
    update_system_constraint,
    delete_system_constraint,
)
from app.db.session import get_db
from app.schemas.systemConstraintsSchema import (
    SystemConstraintCreate,
    SystemConstraintRead,
    SystemConstraintUpdate,
)
from app.api.dependencies.auth import require_auth, require_manager

router = APIRouter(prefix="/system/constraints", tags=["System Constraints"])


# ---------------------- Collection routes -------------------

@router.get(
    "/",
    response_model=List[SystemConstraintRead],
    status_code=status.HTTP_200_OK,
    summary="Get all system constraints",
    dependencies=[Depends(require_auth)],
)
async def list_constraints(db: Session = Depends(get_db)):
    """Retrieve all system-wide constraints."""
    return await get_all_system_constraints(db)


@router.post(
    "/",
    response_model=SystemConstraintRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new system constraint",
    dependencies=[Depends(require_manager)],
)
async def add_constraint(
    payload: SystemConstraintCreate,
    db: Session = Depends(get_db),
):
    """Create a new system-wide constraint (manager only)."""
    return await create_system_constraint(db, payload)


# ---------------------- Resource routes ---------------------

@router.get(
    "/{constraint_id}",
    response_model=SystemConstraintRead,
    status_code=status.HTTP_200_OK,
    summary="Get a system constraint by ID",
    dependencies=[Depends(require_auth)],
)
async def get_constraint(
    constraint_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve a single system-wide constraint by ID."""
    return await get_system_constraint(db, constraint_id)


@router.put(
    "/{constraint_id}",
    response_model=SystemConstraintRead,
    status_code=status.HTTP_200_OK,
    summary="Update a system constraint",
    dependencies=[Depends(require_manager)],
)
async def edit_constraint(
    constraint_id: int,
    payload: SystemConstraintUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing system-wide constraint (manager only)."""
    return await update_system_constraint(db, constraint_id, payload)


@router.delete(
    "/{constraint_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a system constraint",
    dependencies=[Depends(require_manager)],
)
async def remove_constraint(
    constraint_id: int,
    db: Session = Depends(get_db),
):
    """Delete a system-wide constraint (manager only)."""
    await delete_system_constraint(db, constraint_id)
    return {"message": "System constraint deleted successfully"}

