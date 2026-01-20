"""
Optimization configuration routes module.

This module defines the REST API endpoints for optimization configuration management operations.
Routes use repository dependency injection - no direct DB access.
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.controllers.optimizationConfigController import (
    create_optimization_config,
    list_optimization_configs,
    get_optimization_config,
    get_default_optimization_config,
    update_optimization_config,
    delete_optimization_config
)
from app.api.dependencies.repositories import get_optimization_config_repository
from app.db.session import get_db
from app.schemas.optimizationConfigSchema import (
    OptimizationConfigCreate,
    OptimizationConfigUpdate,
    OptimizationConfigRead
)

# AuthN/Authorization
from app.api.dependencies.auth import require_auth, require_manager
from app.repositories.optimization_config_repository import OptimizationConfigRepository

router = APIRouter(prefix="/optimization-configs", tags=["Optimization Configs"])


# ---------------------- Collection routes -------------------

@router.post(
    "/",
    response_model=OptimizationConfigRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new optimization configuration",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def create_config(
    config_data: OptimizationConfigCreate,
    config_repository: OptimizationConfigRepository = Depends(get_optimization_config_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await create_optimization_config(config_data, config_repository, db)


@router.get(
    "/",
    response_model=List[OptimizationConfigRead],
    status_code=status.HTTP_200_OK,
    summary="Get all optimization configurations",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def list_configs(
    config_repository: OptimizationConfigRepository = Depends(get_optimization_config_repository)
):
    return await list_optimization_configs(config_repository)


@router.get(
    "/default",
    response_model=OptimizationConfigRead,
    status_code=status.HTTP_200_OK,
    summary="Get the default optimization configuration",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_default_config(
    config_repository: OptimizationConfigRepository = Depends(get_optimization_config_repository)
):
    return await get_default_optimization_config(config_repository)


# ---------------------- Resource routes ---------------------

@router.get(
    "/{config_id}",
    response_model=OptimizationConfigRead,
    status_code=status.HTTP_200_OK,
    summary="Get an optimization configuration by ID",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_config(
    config_id: int,
    config_repository: OptimizationConfigRepository = Depends(get_optimization_config_repository)
):
    return await get_optimization_config(config_id, config_repository)


@router.put(
    "/{config_id}",
    response_model=OptimizationConfigRead,
    status_code=status.HTTP_200_OK,
    summary="Update an optimization configuration",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def update_config(
    config_id: int,
    config_data: OptimizationConfigUpdate,
    config_repository: OptimizationConfigRepository = Depends(get_optimization_config_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await update_optimization_config(config_id, config_data, config_repository, db)


@router.delete(
    "/{config_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an optimization configuration",
    dependencies=[Depends(require_manager)],  # ADMIN ONLY
)
async def delete_config(
    config_id: int,
    config_repository: OptimizationConfigRepository = Depends(get_optimization_config_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await delete_optimization_config(config_id, config_repository, db)
