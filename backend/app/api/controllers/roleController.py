"""
Role controller module.

This module contains business logic for role management operations including
creation, retrieval, and deletion of role records.
Controllers use repositories for database access - no direct ORM access.
"""

from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session  # Only for type hints

from app.repositories.role_repository import RoleRepository
from app.db.models.roleModel import RoleModel
from app.schemas.roleSchema import RoleCreate, RoleUpdate
from app.exceptions.repository import NotFoundError, ConflictError
from app.db.session_manager import transaction


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
    try:
        # Business rule: Check if role name already exists
        existing = role_repository.get_by_name(role_data.role_name)
        if existing:
            raise ConflictError(f"Role with name {role_data.role_name} already exists")
        
        with transaction(db):
            role = role_repository.create(**role_data.model_dump())
            return role
            
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


async def get_all_roles(role_repository: RoleRepository) -> List[RoleModel]:
    """
    Retrieve all roles from the database.
    """
    return role_repository.get_all()


async def get_role(role_id: int, role_repository: RoleRepository) -> RoleModel:
    """
    Retrieve a single role by ID.
    """
    try:
        return role_repository.get_by_id_or_raise(role_id)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )


async def delete_role(
    role_id: int,
    role_repository: RoleRepository,
    db: Session  # For transaction management
) -> dict:
    """
    Delete a role from the database.
    """
    try:
        role_repository.get_by_id_or_raise(role_id)  # Verify exists
        
        with transaction(db):
            role_repository.delete(role_id)
            return {"message": "Role deleted successfully"}
            
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


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
    try:
        role = role_repository.get_by_id_or_raise(role_id)
        
        # Business rule: Check name uniqueness if name is being changed
        if role_data.role_name and role_data.role_name != role.role_name:
            existing = role_repository.get_by_name(role_data.role_name)
            if existing:
                raise ConflictError(f"Role name {role_data.role_name} is already taken")
        
        with transaction(db):
            return role_repository.update(role_id, role_name=role_data.role_name)
            
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
