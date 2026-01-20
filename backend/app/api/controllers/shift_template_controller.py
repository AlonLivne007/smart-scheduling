"""
Shift template controller module.

This module contains business logic for shift template management operations including
creation, retrieval, updating, and deletion of shift template records.
Controllers use repositories for database access - no direct ORM access.
"""

from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session  # Only for type hints

from app.data.repositories import ShiftTemplateRepository
from app.data.repositories import RoleRepository
from app.data.repositories.shift_repository import ShiftRepository
from app.schemas.shift_template_schema import (
    ShiftTemplateCreate,
    ShiftTemplateUpdate,
    ShiftTemplateRead,
    RoleRequirementRead,
)
from app.core.exceptions.repository import ConflictError
from app.data.session_manager import transaction


def _serialize_template(
    template_repository: ShiftTemplateRepository,
    template_id: int
) -> ShiftTemplateRead:
    """
    Convert ORM object to Pydantic model.
    
    Uses repository to fetch role requirements.
    """
    template = template_repository.get_or_raise(template_id)
    role_requirements = template_repository.get_role_requirements_for_template(template_id)
    
    return ShiftTemplateRead(
        shift_template_id=template.shift_template_id,
        shift_template_name=template.shift_template_name,
        start_time=template.start_time,
        end_time=template.end_time,
        location=template.location,
        required_roles=[
            RoleRequirementRead(
                role_id=req['role_id'],
                required_count=req['required_count'],
                role_name=req['role_name']
            )
            for req in role_requirements
        ],
    )


async def create_shift_template(
    shift_template_data: ShiftTemplateCreate,
    template_repository: ShiftTemplateRepository,
    role_repository: RoleRepository,
    db: Session  # For transaction management
) -> ShiftTemplateRead:
    """
    Create a new shift template with optional required roles.
    
    Business logic:
    - Check if template name already exists
    - Validate roles exist
    - Create template and assign roles
    """
    # Business rule: Check name uniqueness
    existing = template_repository.get_by_name(shift_template_data.shift_template_name)
    if existing:
        raise ConflictError(f"Shift template with name '{shift_template_data.shift_template_name}' already exists")
    
    # Validate roles exist if provided
    if shift_template_data.required_roles:
        role_ids = [r.role_id for r in shift_template_data.required_roles]
        for role_id in role_ids:
            role_repository.get_or_raise(role_id)
    
    with transaction(db):
        # Create template
        template = template_repository.create(
            shift_template_name=shift_template_data.shift_template_name,
            start_time=shift_template_data.start_time,
            end_time=shift_template_data.end_time,
            location=shift_template_data.location,
        )
        
        # Add role requirements if provided
        if shift_template_data.required_roles:
            role_requirements = [
                {'role_id': r.role_id, 'required_count': r.required_count or 1}
                for r in shift_template_data.required_roles
            ]
            template_repository.set_role_requirements(template.shift_template_id, role_requirements)
        
        return _serialize_template(template_repository, template.shift_template_id)


async def list_shift_templates(
    template_repository: ShiftTemplateRepository
) -> List[ShiftTemplateRead]:
    """
    Retrieve all shift templates from the database.
    """
    templates = template_repository.get_all()
    return [_serialize_template(template_repository, t.shift_template_id) for t in templates]


async def get_shift_template(
    template_id: int,
    template_repository: ShiftTemplateRepository
) -> ShiftTemplateRead:
    """
    Retrieve a single shift template by ID.
    """
    template_repository.get_or_raise(template_id)  # Verify exists
    return _serialize_template(template_repository, template_id)


async def update_shift_template(
    template_id: int,
    shift_template_data: ShiftTemplateUpdate,
    template_repository: ShiftTemplateRepository,
    role_repository: RoleRepository,
    db: Session  # For transaction management
) -> ShiftTemplateRead:
    """
    Update an existing shift template.
    
    Business logic:
    - Check name uniqueness if name is being changed
    - Validate roles exist if updating roles
    - Update template and role requirements
    """
    template = template_repository.get_or_raise(template_id)
    
    # Business rule: Check name uniqueness if name is being changed
    if shift_template_data.shift_template_name and shift_template_data.shift_template_name != template.shift_template_name:
        existing = template_repository.get_by_name(shift_template_data.shift_template_name)
        if existing:
            raise ConflictError(f"Shift template name '{shift_template_data.shift_template_name}' already exists")
    
    # Validate roles exist if updating roles
    if shift_template_data.required_roles is not None:
        role_ids = [r.role_id for r in shift_template_data.required_roles]
        for role_id in role_ids:
            role_repository.get_or_raise(role_id)
    
    with transaction(db):
        # Update template fields
        update_data = {}
        if shift_template_data.shift_template_name is not None:
            update_data["shift_template_name"] = shift_template_data.shift_template_name
        if shift_template_data.start_time is not None:
            update_data["start_time"] = shift_template_data.start_time
        if shift_template_data.end_time is not None:
            update_data["end_time"] = shift_template_data.end_time
        if shift_template_data.location is not None:
            update_data["location"] = shift_template_data.location
        
        if update_data:
            template_repository.update(template_id, **update_data)
        
        # Update role requirements if provided
        if shift_template_data.required_roles is not None:
            role_requirements = [
                {'role_id': r.role_id, 'required_count': r.required_count or 1}
                for r in shift_template_data.required_roles
            ]
            template_repository.set_role_requirements(template_id, role_requirements)
        
        return _serialize_template(template_repository, template_id)


async def delete_shift_template(
    template_id: int,
    template_repository: ShiftTemplateRepository,
    shift_repository: ShiftRepository,
    db: Session  # For transaction management
) -> None:
    """
    Delete a shift template from the database.
    
    Business logic:
    - Check if template is used in planned shifts
    - Delete template (role requirements cascade)
    """
    template = template_repository.get_or_raise(template_id)
    
    # Business rule: Check if template is used in planned shifts
    # Get all shifts using this template
    all_shifts = shift_repository.get_all()
    shifts_using_template = [
        s for s in all_shifts if s.shift_template_id == template_id
    ]
    
    if shifts_using_template:
        count = len(shifts_using_template)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete shift template '{template.shift_template_name}'. It is currently used in {count} planned shift(s). Please remove all planned shifts using this template before deleting."
        )
    
    with transaction(db):
        template_repository.delete(template_id)
