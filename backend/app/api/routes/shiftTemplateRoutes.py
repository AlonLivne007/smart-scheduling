"""
Shift template routes module.

This module defines the REST API endpoints for shift template management operations.
Routes use repository dependency injection - no direct DB access.
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.controllers.shiftTemplateController import (
    create_shift_template,
    get_all_shift_templates,
    get_shift_template,
    update_shift_template,
    delete_shift_template
)
from app.api.dependencies.repositories import (
    get_shift_template_repository,
    get_role_repository,
    get_shift_repository
)
from app.db.session import get_db
from app.schemas.shiftTemplateSchema import (
    ShiftTemplateCreate,
    ShiftTemplateUpdate,
    ShiftTemplateRead
)

# AuthN/Authorization
from app.api.dependencies.auth import require_auth, require_manager
from app.repositories.shift_template_repository import ShiftTemplateRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.shift_repository import ShiftRepository

router = APIRouter(prefix="/shift-templates", tags=["Shift Templates"])


# ---------------------- Collection routes -------------------

@router.post(
    "/",
    response_model=ShiftTemplateRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new shift template",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def create_template(
    shift_template_data: ShiftTemplateCreate,
    template_repository: ShiftTemplateRepository = Depends(get_shift_template_repository),
    role_repository: RoleRepository = Depends(get_role_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await create_shift_template(
        shift_template_data,
        template_repository,
        role_repository,
        db
    )


@router.get(
    "/",
    response_model=List[ShiftTemplateRead],
    status_code=status.HTTP_200_OK,
    summary="Get all shift templates",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def list_all_templates(
    template_repository: ShiftTemplateRepository = Depends(get_shift_template_repository)
):
    return await get_all_shift_templates(template_repository)


# ---------------------- Resource routes ---------------------

@router.get(
    "/{template_id}",
    response_model=ShiftTemplateRead,
    status_code=status.HTTP_200_OK,
    summary="Get a shift template by ID",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_one_template(
    template_id: int,
    template_repository: ShiftTemplateRepository = Depends(get_shift_template_repository)
):
    return await get_shift_template(template_id, template_repository)


@router.put(
    "/{template_id}",
    response_model=ShiftTemplateRead,
    status_code=status.HTTP_200_OK,
    summary="Update a shift template",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def update_template(
    template_id: int,
    shift_template_data: ShiftTemplateUpdate,
    template_repository: ShiftTemplateRepository = Depends(get_shift_template_repository),
    role_repository: RoleRepository = Depends(get_role_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await update_shift_template(
        template_id,
        shift_template_data,
        template_repository,
        role_repository,
        db
    )


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a shift template",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def delete_template(
    template_id: int,
    template_repository: ShiftTemplateRepository = Depends(get_shift_template_repository),
    shift_repository: ShiftRepository = Depends(get_shift_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await delete_shift_template(
        template_id,
        template_repository,
        shift_repository,
        db
    )
