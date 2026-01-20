"""
Optimization configuration controller module.

This module contains business logic for optimization configuration management
operations including creation, retrieval, updating, and deletion of optimizer settings.
Controllers use repositories for database access - no direct ORM access.
"""

from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session  # Only for type hints

from app.repositories.optimization_config_repository import OptimizationConfigRepository
from app.schemas.optimization_config_schema import (
    OptimizationConfigCreate,
    OptimizationConfigUpdate,
    OptimizationConfigRead,
)
from app.exceptions.repository import NotFoundError, ConflictError
from app.data.session_manager import transaction


async def create_optimization_config(
    config_data: OptimizationConfigCreate,
    config_repository: OptimizationConfigRepository,
    db: Session  # For transaction management
) -> OptimizationConfigRead:
    """
    Create a new optimization configuration.
    
    Business logic:
    - Check if name already exists
    - If setting as default, unmark other defaults
    - Create config
    """
    # Business rule: Check name uniqueness
    existing = config_repository.get_by_name(config_data.config_name)
    if existing:
        raise ConflictError(f"Configuration name '{config_data.config_name}' already exists")
    
    with transaction(db):
        # If setting as default, unmark others
        if config_data.is_default:
            # Get all configs and unmark defaults
            all_configs = config_repository.get_all()
            for config in all_configs:
                if config.is_default and config.config_id:
                    config_repository.update(config.config_id, is_default=False)
        
        config = config_repository.create(**config_data.model_dump())
        return OptimizationConfigRead.model_validate(config)


async def list_optimization_configs(
    config_repository: OptimizationConfigRepository
) -> List[OptimizationConfigRead]:
    """
    Retrieve all optimization configurations.
    """
    configs = config_repository.get_all()
    # Sort: defaults first, then by name
    configs.sort(key=lambda c: (not c.is_default, c.config_name))
    return [OptimizationConfigRead.model_validate(c) for c in configs]


async def get_optimization_config(
    config_id: int,
    config_repository: OptimizationConfigRepository
) -> OptimizationConfigRead:
    """
    Retrieve a single optimization configuration by ID.
    """
    config = config_repository.get_or_raise(config_id)
    return OptimizationConfigRead.model_validate(config)


async def get_default_optimization_config(
    config_repository: OptimizationConfigRepository
) -> OptimizationConfigRead:
    """
    Retrieve the default optimization configuration.
    """
    config = config_repository.get_default_or_raise()
    return OptimizationConfigRead.model_validate(config)


async def update_optimization_config(
    config_id: int,
    config_data: OptimizationConfigUpdate,
    config_repository: OptimizationConfigRepository,
    db: Session  # For transaction management
) -> OptimizationConfigRead:
    """
    Update an optimization configuration.
    
    Business logic:
    - If setting as default, unmark other defaults
    - Update fields
    """
    config = config_repository.get_or_raise(config_id)
    
    with transaction(db):
        # If setting as default, unmark others
        if config_data.is_default is True:
            config_repository.set_default(config_id)
        
        # Update fields
        update_data = config_data.model_dump(exclude_unset=True)
        updated_config = config_repository.update(config_id, **update_data)
        
        return OptimizationConfigRead.model_validate(updated_config)


async def delete_optimization_config(
    config_id: int,
    config_repository: OptimizationConfigRepository,
    db: Session  # For transaction management
) -> None:
    """
    Delete an optimization configuration.
    
    Business logic:
    - Don't allow deleting the default config
    """
    config = config_repository.get_or_raise(config_id)
    
    # Business rule: Don't allow deleting the default config
    if config.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the default configuration. Set another config as default first."
        )
    
    with transaction(db):
        config_repository.delete(config_id)
