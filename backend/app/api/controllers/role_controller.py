"""
Role controller module.

This module contains business logic for role management operations including
creation, retrieval, and deletion of role records.
Controllers use repositories for database access - no direct ORM access.
"""

from typing import List
from sqlalchemy.orm import Session  # Only for type hints

from app.data.repositories import RoleRepository
from app.data.models.role_model import RoleModel
from app.schemas.role_schema import RoleCreate, RoleUpdate
from app.core.exceptions.repository import ConflictError
from app.data.session_manager import transaction


async def create_role(
    role_data: RoleCreate,
    role_repository: RoleRepository,
    db: Session  # For transaction management
) -> RoleModel:
    """
    Create a new role.
    
    Business logic:
    - Check if role name already exists
    - Create role
    """
    # Business rule: Check if role name already exists
    existing = role_repository.get_by_name(role_data.role_name)
    if existing:
        raise ConflictError(f"Role with name {role_data.role_name} already exists")
    
    with transaction(db):
        role = role_repository.create(**role_data.model_dump())
        return role


async def list_roles(role_repository: RoleRepository) -> List[RoleModel]:
    """
    Retrieve all roles from the database.
    """
    return role_repository.get_all()


async def get_role(role_id: int, role_repository: RoleRepository) -> RoleModel:
    """
    Retrieve a single role by ID.
    """
    return role_repository.get_or_raise(role_id)


async def delete_role(
    role_id: int,
    role_repository: RoleRepository,
    db: Session  # For transaction management
) -> dict:
    """
    Delete a role from the database.
    """
    role_repository.get_or_raise(role_id)  # Verify exists
    
    with transaction(db):
        role_repository.delete(role_id)
        return {"message": "Role deleted successfully"}


async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    role_repository: RoleRepository,
    db: Session  # For transaction management
) -> RoleModel:
    """
    Update an existing role's name.
    
    Business logic:
    - Check if new name already exists (if changed)
    - Update role
    """
    role = role_repository.get_or_raise(role_id)
    
    # Business rule: Check name uniqueness if name is being changed
    if role_data.role_name and role_data.role_name != role.role_name:
        existing = role_repository.get_by_name(role_data.role_name)
        if existing:
            raise ConflictError(f"Role name {role_data.role_name} is already taken")
    
    with transaction(db):
        return role_repository.update(role_id, role_name=role_data.role_name)
