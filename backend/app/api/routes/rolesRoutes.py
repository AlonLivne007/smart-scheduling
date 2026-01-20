"""
Role routes module.

This module defines the REST API endpoints for role management operations
including CRUD operations for role records.
Routes use repository dependency injection - no direct DB access.
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.controllers.roleController import (
    create_role, get_all_roles, get_role, update_role, delete_role
)
from app.api.dependencies.repositories import get_role_repository
from app.db.session import get_db
from app.schemas.roleSchema import RoleCreate, RoleRead, RoleUpdate

# AuthN/Authorization
from app.api.dependencies.auth import require_auth, require_manager
from app.repositories.role_repository import RoleRepository
from app.db.models.roleModel import RoleModel

router = APIRouter(prefix="/roles", tags=["Roles"])


# ---------------------- Collection routes -------------------

@router.post(
    "/",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def add_role(
    role_data: RoleCreate,
    role_repository: RoleRepository = Depends(get_role_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await create_role(role_data, role_repository, db)


@router.get(
    "/",
    response_model=List[RoleRead],
    status_code=status.HTTP_200_OK,
    summary="Get all roles",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def list_roles(
    role_repository: RoleRepository = Depends(get_role_repository)
):
    return await get_all_roles(role_repository)


# ---------------------- Resource routes ---------------------

@router.get(
    "/{role_id}",
    response_model=RoleRead,
    status_code=status.HTTP_200_OK,
    summary="Get a role by ID",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_single_role(
    role_id: int,
    role_repository: RoleRepository = Depends(get_role_repository)
):
    return await get_role(role_id, role_repository)


@router.put(
    "/{role_id}",
    response_model=RoleRead,
    status_code=status.HTTP_200_OK,
    summary="Update a role",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def update_single_role(
    role_id: int,
    payload: RoleUpdate,
    role_repository: RoleRepository = Depends(get_role_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await update_role(role_id, payload, role_repository, db)


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a role",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def remove_role(
    role_id: int,
    role_repository: RoleRepository = Depends(get_role_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await delete_role(role_id, role_repository, db)
