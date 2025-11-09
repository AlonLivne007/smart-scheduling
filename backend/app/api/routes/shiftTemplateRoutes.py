"""
Shift template routes module.

This module defines the REST API endpoints for shift template management operations
including CRUD operations for shift template records.
"""

from fastapi import APIRouter, Depends, status
from typing import List
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.shiftTemplateSchema import ShiftTemplateCreate, ShiftTemplateUpdate, ShiftTemplateRead
from app.api.controllers.shiftTemplateController import (
    create_shift_template,
    get_all_shift_templates,
    get_shift_template,
    update_shift_template,
    delete_shift_template,
)

router = APIRouter(prefix="/shift-templates", tags=["Shift Templates"])


@router.post("/", response_model=ShiftTemplateRead, status_code=status.HTTP_201_CREATED,
             summary="Create a new shift template")
async def create_template(shift_template_data: ShiftTemplateCreate, db: Session = Depends(get_db)):
    """
    Create a new shift template.
    
    Args:
        shift_template_data: Shift template creation data
        db: Database session dependency
        
    Returns:
        Created shift template data
    """
    template = await create_shift_template(db, shift_template_data)
    return template


@router.get("/", response_model=List[ShiftTemplateRead], status_code=status.HTTP_200_OK,
            summary="List all shift templates")
async def list_all_templates(db: Session = Depends(get_db)):
    """
    Retrieve all shift templates from the system.
    
    Args:
        db: Database session dependency
        
    Returns:
        List of all shift templates
    """
    templates = await get_all_shift_templates(db)
    return templates


@router.get("/{template_id}", response_model=ShiftTemplateRead, status_code=status.HTTP_200_OK,
            summary="Get a shift template by ID")
async def get_one_template(template_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific shift template by its ID.
    
    Args:
        template_id: Shift template identifier
        db: Database session dependency
        
    Returns:
        Shift template data
    """
    template = await get_shift_template(db, template_id)
    return template


@router.put("/{template_id}", response_model=ShiftTemplateRead, status_code=status.HTTP_200_OK,
            summary="Update a shift template")
async def update_template(template_id: int, shift_template_data: ShiftTemplateUpdate, db: Session = Depends(get_db)):
    """
    Update an existing shift template.
    
    Args:
        template_id: Shift template identifier
        shift_template_data: Update data
        db: Database session dependency
        
    Returns:
        Updated shift template data
    """
    template = await update_shift_template(db, template_id, shift_template_data)
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a shift template")
async def delete_template(template_id: int, db: Session = Depends(get_db)):
    """
    Delete a shift template from the system.
    
    Args:
        template_id: Shift template identifier
        db: Database session dependency
        
    Returns:
        No content (204)
    """
    await delete_shift_template(db, template_id)
