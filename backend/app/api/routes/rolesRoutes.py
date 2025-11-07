"""
Role routes module.

This module defines the REST API endpoints for role management operations
including CRUD operations for role records.
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.controllers.roleController import (create_role, get_all_roles,
                                                get_role, delete_role)
from app.db.session import get_db
from app.schemas.roleSchema import RoleRead, RoleCreate

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.post("/", response_model=RoleRead, status_code=status.HTTP_201_CREATED,
             summary="Create a new role")
async def add_role(role_data: RoleCreate, db: Session = Depends(get_db)):
    """
    Create a new role.
    
    Args:
        role_data: Role creation data
        db: Database session dependency
        
    Returns:
        Created role data
    """
    role = await create_role(db, role_data)
    return role


@router.get("/", response_model=List[RoleRead], status_code=status.HTTP_200_OK,
            summary="List all roles")
async def list_roles(db: Session = Depends(get_db)):
    """
    Retrieve all roles from the system.
    
    Args:
        db: Database session dependency
        
    Returns:
        List of all roles
    """
    roles = await get_all_roles(db)
    return roles


@router.get("/{role_id}", response_model=RoleRead,
            status_code=status.HTTP_200_OK, summary="Get a single role by ID")
async def get_single_role(role_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific role by its ID.
    
    Args:
        role_id: Role identifier
        db: Database session dependency
        
    Returns:
        Role data
    """
    role = await get_role(db, role_id)
    return role


@router.delete("/{role_id}", status_code=status.HTTP_200_OK,
               summary="Delete a role")
async def remove_role(role_id: int, db: Session = Depends(get_db)):
    """
    Delete a role from the system.
    
    Args:
        role_id: Role identifier
        db: Database session dependency
        
    Returns:
        Deletion confirmation message
    """
    result = await delete_role(db, role_id)
    return result
