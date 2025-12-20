"""
Role controller module.

This module contains business logic for role management operations including
creation, retrieval, and deletion of role records.
"""

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session
from typing import List

from app.db.models.roleModel import RoleModel
from app.schemas.roleSchema import RoleCreate, RoleUpdate


async def create_role(db: Session, role_data: RoleCreate) -> RoleModel:
    """
    Create a new role.
    
    Args:
        db: Database session
        role_data: Role creation data
        
    Returns:
        Created RoleModel instance
        
    Raises:
        HTTPException: If role name exists or database error occurs
    """
    try:
        new_role = RoleModel(**role_data.model_dump())
        db.add(new_role)
        db.commit()
        db.refresh(new_role)

        return new_role

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
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


async def get_all_roles(db: Session) -> List[RoleModel]:
    """
    Retrieve all roles from the database.
    
    Args:
        db: Database session
        
    Returns:
        List of all RoleModel instances
        
    Raises:
        HTTPException: If database error occurs
    """
    try:
        roles = db.query(RoleModel).all()
        return roles
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_role(db: Session, role_id: int) -> RoleModel:
    """
    Retrieve a single role by ID.
    
    Args:
        db: Database session
        role_id: Role identifier
        
    Returns:
        RoleModel instance
        
    Raises:
        HTTPException: If role not found or database error occurs
    """
    try:
        role = db.get(RoleModel, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        return role
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def delete_role(db: Session, role_id: int) -> dict:
    """
    Delete a role from the database.
    
    Args:
        db: Database session
        role_id: Role identifier
        
    Returns:
        Success message dictionary
        
    Raises:
        HTTPException: If role not found or database error occurs
    """
    try:
        role = db.get(RoleModel, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )

        db.delete(role)
        db.commit()

        return {
            "message": "Role deleted successfully"
        }

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
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


async def update_role(db: Session, role_id: int, role_data: RoleUpdate) -> RoleModel:
    """Update an existing role's name."""
    try:
        role = db.get(RoleModel, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )

        role.role_name = role_data.role_name
        db.add(role)
        db.commit()
        db.refresh(role)
        return role

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
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
