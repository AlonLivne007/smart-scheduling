"""
Employee preferences routes module.

This module defines the REST API endpoints for employee preference management operations
including CRUD operations for shift preferences.
"""

from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.api.controllers.employeePreferencesController import (
    create_employee_preference,
    get_employee_preferences_by_user,
    get_employee_preference,
    update_employee_preference,
    delete_employee_preference,
)
from app.db.session import get_db
from app.schemas.employeePreferencesSchema import (
    EmployeePreferencesCreate,
    EmployeePreferencesRead,
    EmployeePreferencesUpdate,
)
from app.api.controllers.authController import get_current_user
from app.api.dependencies.auth import require_auth
from app.db.models.userModel import UserModel

router = APIRouter(prefix="/employees", tags=["Employee Preferences"])


# ---------------------- User-specific preference routes -------------------

@router.post(
    "/{user_id}/preferences",
    response_model=EmployeePreferencesRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new employee preference",
    dependencies=[Depends(require_auth)],
)
async def create_preference(
    user_id: int,
    payload: EmployeePreferencesCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new employee preference.
    
    Employees can only create preferences for themselves.
    Managers can create preferences for any employee.
    """
    # Authorization: employees can only create their own preferences
    if not current_user.is_manager and user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create preferences for yourself"
        )
    
    return await create_employee_preference(db, user_id, payload)


@router.get(
    "/{user_id}/preferences",
    response_model=List[EmployeePreferencesRead],
    status_code=status.HTTP_200_OK,
    summary="Get all preferences for a specific employee",
    dependencies=[Depends(require_auth)],
)
async def list_preferences_for_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all preferences for a specific employee.
    
    Employees can only view their own preferences.
    Managers can view any employee's preferences.
    """
    # Authorization: employees can only view their own preferences
    if not current_user.is_manager and user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own preferences"
        )
    
    return await get_employee_preferences_by_user(db, user_id)


# ---------------------- Individual preference routes -------------------

@router.get(
    "/{user_id}/preferences/{preference_id}",
    response_model=EmployeePreferencesRead,
    status_code=status.HTTP_200_OK,
    summary="Get a single preference by ID",
    dependencies=[Depends(require_auth)],
)
async def get_preference(
    user_id: int,
    preference_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get a single preference by ID.
    
    Employees can only view their own preferences.
    Managers can view any employee's preferences.
    """
    # Get the preference first to check ownership
    preference = await get_employee_preference(db, preference_id)
    
    # Verify it belongs to the specified user
    if preference.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preference {preference_id} does not belong to user {user_id}"
        )
    
    # Authorization: employees can only view their own preferences
    if not current_user.is_manager and user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own preferences"
        )
    
    return preference


@router.put(
    "/{user_id}/preferences/{preference_id}",
    response_model=EmployeePreferencesRead,
    status_code=status.HTTP_200_OK,
    summary="Update an employee preference",
    dependencies=[Depends(require_auth)],
)
async def update_preference(
    user_id: int,
    preference_id: int,
    payload: EmployeePreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update an employee preference.
    
    Employees can only update their own preferences.
    Managers can update any employee's preferences.
    """
    # For managers, allow updating any user's preferences
    # For regular employees, the controller will check ownership
    if current_user.is_manager:
        # Manager can update any preference, use the target user_id
        effective_user_id = user_id
    else:
        # Regular employee, use their own user_id (controller will validate)
        effective_user_id = current_user.user_id
    
    return await update_employee_preference(db, preference_id, payload, effective_user_id)


@router.delete(
    "/{user_id}/preferences/{preference_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an employee preference",
    dependencies=[Depends(require_auth)],
)
async def delete_preference(
    user_id: int,
    preference_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Delete an employee preference.
    
    Employees can only delete their own preferences.
    Managers can delete any employee's preferences.
    """
    # For managers, allow deleting any user's preferences
    # For regular employees, the controller will check ownership
    if current_user.is_manager:
        # Manager can delete any preference, use the target user_id
        effective_user_id = user_id
    else:
        # Regular employee, use their own user_id (controller will validate)
        effective_user_id = current_user.user_id
    
    return await delete_employee_preference(db, preference_id, effective_user_id)
