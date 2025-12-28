"""
Optimization configuration controller module.

This module contains business logic for optimization configuration management
operations including creation, retrieval, updating, and deletion of optimizer settings.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List, Optional

from app.db.models.optimizationConfigModel import OptimizationConfigModel
from app.schemas.optimizationConfigSchema import (
    OptimizationConfigCreate,
    OptimizationConfigUpdate,
    OptimizationConfigRead,
)


# ------------------------
# Helper Functions
# ------------------------

def _serialize_optimization_config(config: OptimizationConfigModel) -> OptimizationConfigRead:
    """
    Convert ORM object to Pydantic schema.
    
    Args:
        config: OptimizationConfigModel instance
        
    Returns:
        OptimizationConfigRead instance
    """
    return OptimizationConfigRead(
        config_id=config.config_id,
        config_name=config.config_name,
        weight_fairness=config.weight_fairness,
        weight_preferences=config.weight_preferences,
        weight_cost=config.weight_cost,
        weight_coverage=config.weight_coverage,
        max_runtime_seconds=config.max_runtime_seconds,
        mip_gap=config.mip_gap,
        is_default=config.is_default,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


def _ensure_single_default(db: Session, config_id: Optional[int] = None) -> None:
    """
    Ensure only one configuration is marked as default.
    
    If a new config is being set as default, unmark all others.
    
    Args:
        db: Database session
        config_id: ID of the config being set as default (to exclude from update)
    """
    if config_id:
        # Unmark all configs except the one being updated
        db.query(OptimizationConfigModel).filter(
            OptimizationConfigModel.config_id != config_id
        ).update({"is_default": False})
    else:
        # Unmark all configs
        db.query(OptimizationConfigModel).update({"is_default": False})


# ------------------------
# CRUD Functions
# ------------------------

async def create_optimization_config(
    db: Session,
    config_data: OptimizationConfigCreate
) -> OptimizationConfigRead:
    """
    Create a new optimization configuration.
    
    Args:
        db: Database session
        config_data: Configuration creation data
        
    Returns:
        Created OptimizationConfigRead instance
        
    Raises:
        HTTPException: If validation fails or database error occurs
    """
    try:
        # If this config is being set as default, unmark others
        if config_data.is_default:
            _ensure_single_default(db)
        
        config = OptimizationConfigModel(
            config_name=config_data.config_name,
            weight_fairness=config_data.weight_fairness,
            weight_preferences=config_data.weight_preferences,
            weight_cost=config_data.weight_cost,
            weight_coverage=config_data.weight_coverage,
            max_runtime_seconds=config_data.max_runtime_seconds,
            mip_gap=config_data.mip_gap,
            is_default=config_data.is_default,
        )
        
        db.add(config)
        db.commit()
        db.refresh(config)
        
        return _serialize_optimization_config(config)
    
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        if 'unique' in error_str.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Configuration name '{config_data.config_name}' already exists"
            )
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


async def get_all_optimization_configs(db: Session) -> List[OptimizationConfigRead]:
    """
    Retrieve all optimization configurations.
    
    Args:
        db: Database session
        
    Returns:
        List of OptimizationConfigRead instances
        
    Raises:
        HTTPException: If database error occurs
    """
    try:
        configs = db.query(OptimizationConfigModel).order_by(
            OptimizationConfigModel.is_default.desc(),
            OptimizationConfigModel.config_name
        ).all()
        
        return [_serialize_optimization_config(config) for config in configs]
    
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_optimization_config(
    db: Session,
    config_id: int
) -> OptimizationConfigRead:
    """
    Retrieve a single optimization configuration by ID.
    
    Args:
        db: Database session
        config_id: Configuration identifier
        
    Returns:
        OptimizationConfigRead instance
        
    Raises:
        HTTPException: If config not found or database error occurs
    """
    try:
        config = db.get(OptimizationConfigModel, config_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Optimization configuration with ID {config_id} not found"
            )
        
        return _serialize_optimization_config(config)
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_default_optimization_config(db: Session) -> OptimizationConfigRead:
    """
    Retrieve the default optimization configuration.
    
    Args:
        db: Database session
        
    Returns:
        Default OptimizationConfigRead instance
        
    Raises:
        HTTPException: If no default config found or database error occurs
    """
    try:
        config = db.query(OptimizationConfigModel).filter(
            OptimizationConfigModel.is_default == True
        ).first()
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No default optimization configuration found. Please create one."
            )
        
        return _serialize_optimization_config(config)
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def update_optimization_config(
    db: Session,
    config_id: int,
    config_data: OptimizationConfigUpdate
) -> OptimizationConfigRead:
    """
    Update an optimization configuration.
    
    Args:
        db: Database session
        config_id: Configuration identifier
        config_data: Update data
        
    Returns:
        Updated OptimizationConfigRead instance
        
    Raises:
        HTTPException: If config not found, validation fails, or database error occurs
    """
    try:
        config = db.get(OptimizationConfigModel, config_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Optimization configuration with ID {config_id} not found"
            )
        
        # If setting this config as default, unmark others
        if config_data.is_default is True:
            _ensure_single_default(db, config_id)
        
        # Update fields if provided
        update_data = config_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)
        
        db.commit()
        db.refresh(config)
        
        return _serialize_optimization_config(config)
    
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        if 'unique' in error_str.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Configuration name already exists"
            )
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


async def delete_optimization_config(
    db: Session,
    config_id: int
) -> None:
    """
    Delete an optimization configuration.
    
    Args:
        db: Database session
        config_id: Configuration identifier
        
    Raises:
        HTTPException: If config not found, is default, or database error occurs
    """
    try:
        config = db.get(OptimizationConfigModel, config_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Optimization configuration with ID {config_id} not found"
            )
        
        # Don't allow deleting the default config
        if config.is_default:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the default configuration. Set another config as default first."
            )
        
        db.delete(config)
        db.commit()
    
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete configuration: it may be referenced by optimization runs. {error_str}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
