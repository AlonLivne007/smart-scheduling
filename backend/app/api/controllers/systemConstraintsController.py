"""
System constraints controller module.

This module contains business logic for system-wide constraint management
operations including creation, retrieval, updating, and deletion.
"""

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session
from typing import List

from app.db.models.systemConstraintsModel import SystemConstraintsModel, SystemConstraintType
from app.schemas.systemConstraintsSchema import (
    SystemConstraintCreate,
    SystemConstraintUpdate,
    SystemConstraintRead,
)


# ------------------------
# Helper Functions
# ------------------------

def _serialize_constraint(constraint: SystemConstraintsModel) -> SystemConstraintRead:
    """Convert ORM object to Pydantic schema."""
    return SystemConstraintRead(
        constraint_id=constraint.constraint_id,
        constraint_type=constraint.constraint_type,
        constraint_value=constraint.constraint_value,
        is_hard_constraint=constraint.is_hard_constraint,
    )


# ------------------------
# CRUD Functions
# ------------------------

async def create_system_constraint(
    db: Session,
    data: SystemConstraintCreate,
) -> SystemConstraintRead:
    """Create a new system-wide constraint.

    Only one row per constraint_type is allowed.
    """
    try:
        # Ensure no duplicate constraint_type
        existing = (
            db.query(SystemConstraintsModel)
            .filter(SystemConstraintsModel.constraint_type == data.constraint_type)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Constraint for type {data.constraint_type.value} already exists",
            )

        obj = SystemConstraintsModel(
            constraint_type=SystemConstraintType[data.constraint_type.name],
            constraint_value=data.constraint_value,
            is_hard_constraint=data.is_hard_constraint,
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)

        return _serialize_constraint(obj)

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, "orig") else str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {error_str}",
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


async def get_all_system_constraints(db: Session) -> List[SystemConstraintRead]:
    """Retrieve all system-wide constraints."""
    try:
        rows = db.query(SystemConstraintsModel).all()
        return [_serialize_constraint(r) for r in rows]
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


async def get_system_constraint(
    db: Session,
    constraint_id: int,
) -> SystemConstraintRead:
    """Retrieve a single system-wide constraint by ID."""
    try:
        obj = db.get(SystemConstraintsModel, constraint_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="System constraint not found",
            )
        return _serialize_constraint(obj)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


async def update_system_constraint(
    db: Session,
    constraint_id: int,
    data: SystemConstraintUpdate,
) -> SystemConstraintRead:
    """Update an existing system-wide constraint (value / hardness)."""
    try:
        obj = db.get(SystemConstraintsModel, constraint_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="System constraint not found",
            )

        if data.constraint_value is not None:
            obj.constraint_value = data.constraint_value
        if data.is_hard_constraint is not None:
            obj.is_hard_constraint = data.is_hard_constraint

        db.commit()
        db.refresh(obj)
        return _serialize_constraint(obj)

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, "orig") else str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {error_str}",
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


async def delete_system_constraint(
    db: Session,
    constraint_id: int,
) -> None:
    """Delete a system-wide constraint by ID."""
    try:
        obj = db.get(SystemConstraintsModel, constraint_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="System constraint not found",
            )

        db.delete(obj)
        db.commit()

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, "orig") else str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {error_str}",
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )

