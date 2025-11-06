"""
Shift template controller module.

This module contains business logic for shift template management operations including
creation, retrieval, updating, and deletion of shift template records.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, insert
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List
from app.db.models.shiftTemplateModel import ShiftTemplateModel
from app.db.models.roleModel import RoleModel
from app.db.models.plannedShiftModel import PlannedShiftModel
from app.db.models.shiftRoleRequirementsTabel import shift_role_requirements
from app.schemas.shiftTemplateSchema import (
    ShiftTemplateCreate,
    ShiftTemplateUpdate,
    ShiftTemplateRead,
    RoleRequirementBase,
    RoleRequirementRead,
)


# ------------------------
# Helper functions
# ------------------------

def _ensure_roles_exist(db: Session, role_reqs: List[RoleRequirementBase]) -> None:
    """Validate all role IDs exist."""
    if not role_reqs:
        return
    role_ids = {r.role_id for r in role_reqs}
    found = db.execute(
        select(RoleModel.role_id).where(RoleModel.role_id.in_(role_ids))
    ).scalars().all()
    missing = role_ids.difference(found)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role IDs not found: {sorted(list(missing))}",
        )


def _fetch_role_requirements(db: Session, template_id: int) -> List[RoleRequirementRead]:
    """Return the roles + required_count for a given template."""
    rows = db.execute(
        select(
            shift_role_requirements.c.role_id,
            shift_role_requirements.c.required_count,
            RoleModel.role_name,
        )
        .join(RoleModel, RoleModel.role_id == shift_role_requirements.c.role_id)
        .where(shift_role_requirements.c.shift_template_id == template_id)
    ).all()

    return [
        RoleRequirementRead(
            role_id=row.role_id,
            required_count=row.required_count,
            role_name=row.role_name,
        )
        for row in rows
    ]


def _serialize_template(db: Session, template: ShiftTemplateModel) -> ShiftTemplateRead:
    """Convert ORM object to Pydantic model."""
    return ShiftTemplateRead(
        shift_template_id=template.shift_template_id,
        shift_template_name=template.shift_template_name,
        start_time=template.start_time,
        end_time=template.end_time,
        location=template.location,
        required_roles=_fetch_role_requirements(db, template.shift_template_id),
    )


# ------------------------
# CRUD functions
# ------------------------

def create_shift_template(db: Session, shift_template_data: ShiftTemplateCreate) -> ShiftTemplateRead:
    """
    Create a new shift template with optional required roles.
    
    Args:
        db: Database session
        shift_template_data: Shift template creation data
        
    Returns:
        Created ShiftTemplateRead instance
        
    Raises:
        HTTPException: If template name exists or database error occurs
    """
    try:
        _ensure_roles_exist(db, shift_template_data.required_roles or [])

        template = ShiftTemplateModel(
            shift_template_name=shift_template_data.shift_template_name,
            start_time=shift_template_data.start_time,
            end_time=shift_template_data.end_time,
            location=shift_template_data.location,
        )
        db.add(template)
        db.flush()

        # Add required roles
        if shift_template_data.required_roles:
            db.execute(
                insert(shift_role_requirements),
                [
                    {
                        "shift_template_id": template.shift_template_id,
                        "role_id": r.role_id,
                        "required_count": r.required_count or 1,
                    }
                    for r in shift_template_data.required_roles
                ],
            )

        db.commit()
        db.refresh(template)
        return _serialize_template(db, template)
    
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        # Check if it's a unique constraint violation
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        if 'unique' in error_str.lower() or 'duplicate' in error_str.lower():
            if 'shift_template_name' in error_str.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Shift template '{shift_template_data.shift_template_name}' already exists"
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


def list_shift_templates(db: Session) -> List[ShiftTemplateRead]:
    """
    Retrieve all shift templates from the database.
    
    Args:
        db: Database session
        
    Returns:
        List of all ShiftTemplateRead instances
        
    Raises:
        HTTPException: If database error occurs
    """
    try:
        templates = db.execute(select(ShiftTemplateModel)).scalars().all()
        return [_serialize_template(db, t) for t in templates]
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


def get_shift_template(db: Session, template_id: int) -> ShiftTemplateRead:
    """
    Retrieve a single shift template by ID.
    
    Args:
        db: Database session
        template_id: Shift template identifier
        
    Returns:
        ShiftTemplateRead instance
        
    Raises:
        HTTPException: If template not found or database error occurs
    """
    try:
        template = db.get(ShiftTemplateModel, template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shift template not found"
            )
        return _serialize_template(db, template)
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


def update_shift_template(db: Session, template_id: int, shift_template_data: ShiftTemplateUpdate) -> ShiftTemplateRead:
    """
    Update an existing shift template.
    
    Args:
        db: Database session
        template_id: Shift template identifier
        shift_template_data: Update data
        
    Returns:
        Updated ShiftTemplateRead instance
        
    Raises:
        HTTPException: If template not found, name conflict, or database error occurs
    """
    try:
        template = db.get(ShiftTemplateModel, template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shift template not found"
            )

        # Update fields (only if provided)
        if shift_template_data.shift_template_name is not None:
            template.shift_template_name = shift_template_data.shift_template_name
        if shift_template_data.start_time is not None:
            template.start_time = shift_template_data.start_time
        if shift_template_data.end_time is not None:
            template.end_time = shift_template_data.end_time
        if shift_template_data.location is not None:
            template.location = shift_template_data.location

        # Update roles if provided
        if shift_template_data.required_roles is not None:
            _ensure_roles_exist(db, shift_template_data.required_roles)
            db.execute(
                delete(shift_role_requirements).where(
                    shift_role_requirements.c.shift_template_id == template_id
                )
            )
            if shift_template_data.required_roles:
                db.execute(
                    insert(shift_role_requirements),
                    [
                        {
                            "shift_template_id": template_id,
                            "role_id": r.role_id,
                            "required_count": r.required_count or 1,
                        }
                        for r in shift_template_data.required_roles
                    ],
                )

        db.commit()
        db.refresh(template)
        return _serialize_template(db, template)
    
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        # Check if it's a unique constraint violation
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        if 'unique' in error_str.lower() or 'duplicate' in error_str.lower():
            if 'shift_template_name' in error_str.lower() and shift_template_data.shift_template_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Shift template '{shift_template_data.shift_template_name}' already exists"
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


def delete_shift_template(db: Session, template_id: int) -> None:
    """
    Delete a shift template from the database.
    
    Args:
        db: Database session
        template_id: Shift template identifier
        
    Raises:
        HTTPException: If template not found, template is in use, or database error occurs
    """
    try:
        template = db.get(ShiftTemplateModel, template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shift template not found"
            )

        # Check if template is being used in planned shifts (RESTRICT constraint)
        planned_shift_count = db.execute(
            select(PlannedShiftModel).where(
                PlannedShiftModel.shift_template_id == template_id
            )
        ).scalars().all()
        
        if planned_shift_count:
            count = len(planned_shift_count)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete shift template '{template.shift_template_name}'. It is currently used in {count} planned shift(s). Please remove all planned shifts using this template before deleting."
            )

        # Delete template (role requirements will be automatically deleted via CASCADE)
        db.delete(template)
        db.commit()
    
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete shift template: {str(e)}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
