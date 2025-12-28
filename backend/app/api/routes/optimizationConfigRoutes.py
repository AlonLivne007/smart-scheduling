"""
Optimization configuration routes module.

This module defines the REST API endpoints for optimization configuration
management operations.
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.controllers.optimizationConfigController import (
    create_optimization_config,
    get_all_optimization_configs,
    get_optimization_config,
    get_default_optimization_config,
    update_optimization_config,
    delete_optimization_config,
)
from app.db.session import get_db
from app.schemas.optimizationConfigSchema import (
    OptimizationConfigCreate,
    OptimizationConfigRead,
    OptimizationConfigUpdate,
)
from app.api.dependencies.auth import require_auth, require_manager

router = APIRouter(prefix="/optimization-configs", tags=["Optimization Configuration"])


# ---------------------- Collection routes -------------------

@router.get(
    "/",
    response_model=List[OptimizationConfigRead],
    status_code=status.HTTP_200_OK,
    summary="Get all optimization configurations",
    dependencies=[Depends(require_auth)],
)
async def list_configs(db: Session = Depends(get_db)):
    """
    Retrieve all optimization configurations.
    
    Returns configurations ordered by default status (default first),
    then alphabetically by name.
    """
    return await get_all_optimization_configs(db)


@router.post(
    "/",
    response_model=OptimizationConfigRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new optimization configuration",
    dependencies=[Depends(require_manager)],
)
async def create_config(
    payload: OptimizationConfigCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new optimization configuration (manager only).
    
    If is_default is set to true, all other configurations will
    automatically be unmarked as default.
    """
    return await create_optimization_config(db, payload)


@router.get(
    "/default",
    response_model=OptimizationConfigRead,
    status_code=status.HTTP_200_OK,
    summary="Get the default optimization configuration",
    dependencies=[Depends(require_auth)],
)
async def get_default_config(db: Session = Depends(get_db)):
    """
    Retrieve the default optimization configuration.
    
    This is the configuration that will be used when triggering
    optimization without specifying a config_id.
    """
    return await get_default_optimization_config(db)


# ---------------------- Resource routes ---------------------

@router.get(
    "/{config_id}",
    response_model=OptimizationConfigRead,
    status_code=status.HTTP_200_OK,
    summary="Get an optimization configuration by ID",
    dependencies=[Depends(require_auth)],
)
async def get_config(
    config_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve a single optimization configuration by ID."""
    return await get_optimization_config(db, config_id)


@router.put(
    "/{config_id}",
    response_model=OptimizationConfigRead,
    status_code=status.HTTP_200_OK,
    summary="Update an optimization configuration",
    dependencies=[Depends(require_manager)],
)
async def update_config(
    config_id: int,
    payload: OptimizationConfigUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an optimization configuration (manager only).
    
    All fields are optional for partial updates.
    If is_default is set to true, all other configurations will
    automatically be unmarked as default.
    """
    return await update_optimization_config(db, config_id, payload)


@router.delete(
    "/{config_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an optimization configuration",
    dependencies=[Depends(require_manager)],
)
async def delete_config(
    config_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete an optimization configuration (manager only).
    
    Cannot delete the default configuration. Set another config
    as default first, then delete this one.
    
    Cannot delete if the configuration is referenced by any
    optimization runs.
    """
    await delete_optimization_config(db, config_id)
    return {"message": "Optimization configuration deleted successfully"}
