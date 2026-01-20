"""
System constraints routes module.

This module defines the REST API endpoints for system constraints management operations.
Routes use repository dependency injection - no direct DB access.
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.controllers.systemConstraintsController import (
    create_system_constraint,
    get_system_constraint,
    get_all_system_constraints,
    update_system_constraint,
    delete_system_constraint
)
from app.api.dependencies.repositories import get_system_constraints_repository
from app.db.session import get_db
from app.schemas.systemConstraintsSchema import (
    SystemConstraintCreate,
    SystemConstraintUpdate,
    SystemConstraintRead
)

# AuthN/Authorization
from app.api.dependencies.auth import require_auth, require_manager
from app.repositories.system_constraints_repository import SystemConstraintsRepository

router = APIRouter(prefix="/system-constraints", tags=["System Constraints"])


# ---------------------- Collection routes -------------------

@router.post(
    "/",
    response_model=SystemConstraintRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new system constraint",
    dependencies=[Depends(require_manager)],  # MANAGER ONLY
)
async def create_constraint(
    constraint_data: SystemConstraintCreate,
    constraints_repository: SystemConstraintsRepository = Depends(get_system_constraints_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await create_system_constraint(constraint_data, constraints_repository, db)


@router.get(
    "/",
    response_model=List[SystemConstraintRead],
    status_code=status.HTTP_200_OK,
    summary="Get all system constraints",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def list_constraints(
    constraints_repository: SystemConstraintsRepository = Depends(get_system_constraints_repository)
):
    return await get_all_system_constraints(constraints_repository)


# ---------------------- Resource routes ---------------------

@router.get(
    "/{constraint_id}",
    response_model=SystemConstraintRead,
    status_code=status.HTTP_200_OK,
    summary="Get a system constraint by ID",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_constraint(
    constraint_id: int,
    constraints_repository: SystemConstraintsRepository = Depends(get_system_constraints_repository)
):
    return await get_system_constraint(constraint_id, constraints_repository)


@router.put(
    "/{constraint_id}",
    response_model=SystemConstraintRead,
    status_code=status.HTTP_200_OK,
    summary="Update a system constraint",
    dependencies=[Depends(require_manager)],  # MANAGER ONLY
)
async def update_constraint(
    constraint_id: int,
    constraint_data: SystemConstraintUpdate,
    constraints_repository: SystemConstraintsRepository = Depends(get_system_constraints_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await update_system_constraint(constraint_id, constraint_data, constraints_repository, db)


@router.delete(
    "/{constraint_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a system constraint",
    dependencies=[Depends(require_manager)],  # MANAGER ONLY
)
async def delete_constraint(
    constraint_id: int,
    constraints_repository: SystemConstraintsRepository = Depends(get_system_constraints_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await delete_system_constraint(constraint_id, constraints_repository, db)
