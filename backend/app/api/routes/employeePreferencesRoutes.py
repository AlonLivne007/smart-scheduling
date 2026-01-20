"""
Employee preferences routes module.

This module defines the REST API endpoints for employee preference management operations.
Routes use repository dependency injection - no direct DB access.
"""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.controllers.employeePreferencesController import (
    create_employee_preference,
    get_employee_preferences_by_user,
    get_employee_preference,
    update_employee_preference,
    delete_employee_preference
)
from app.api.controllers.authController import get_current_user
from app.api.dependencies.repositories import (
    get_employee_preferences_repository,
    get_user_repository,
    get_shift_template_repository
)
from app.db.session import get_db
from app.schemas.employeePreferencesSchema import (
    EmployeePreferencesCreate,
    EmployeePreferencesUpdate,
    EmployeePreferencesRead
)

# AuthN/Authorization
from app.api.dependencies.auth import require_auth, require_manager
from app.repositories.employee_preferences_repository import EmployeePreferencesRepository
from app.repositories.user_repository import UserRepository
from app.repositories.shift_template_repository import ShiftTemplateRepository
from app.db.models.userModel import UserModel

router = APIRouter(prefix="/employee-preferences", tags=["Employee Preferences"])


# ---------------------- Collection routes -------------------

@router.post(
    "/users/{user_id}",
    response_model=EmployeePreferencesRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new employee preference",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def create_preference(
    user_id: int,
    preference_data: EmployeePreferencesCreate,
    current_user: UserModel = Depends(get_current_user),
    preferences_repository: EmployeePreferencesRepository = Depends(get_employee_preferences_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    template_repository: ShiftTemplateRepository = Depends(get_shift_template_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await create_employee_preference(
        user_id,
        preference_data,
        current_user,
        preferences_repository,
        user_repository,
        template_repository,
        db
    )


@router.get(
    "/users/{user_id}",
    response_model=List[EmployeePreferencesRead],
    status_code=status.HTTP_200_OK,
    summary="Get all preferences for a user",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def list_preferences(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    preferences_repository: EmployeePreferencesRepository = Depends(get_employee_preferences_repository),
    user_repository: UserRepository = Depends(get_user_repository)
):
    return await get_employee_preferences_by_user(
        user_id,
        current_user,
        preferences_repository,
        user_repository
    )


# ---------------------- Resource routes ---------------------

@router.get(
    "/users/{user_id}/preferences/{preference_id}",
    response_model=EmployeePreferencesRead,
    status_code=status.HTTP_200_OK,
    summary="Get a preference by ID",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def get_preference(
    preference_id: int,
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    preferences_repository: EmployeePreferencesRepository = Depends(get_employee_preferences_repository),
    user_repository: UserRepository = Depends(get_user_repository)
):
    return await get_employee_preference(
        preference_id,
        user_id,
        current_user,
        preferences_repository,
        user_repository
    )


@router.put(
    "/users/{user_id}/preferences/{preference_id}",
    response_model=EmployeePreferencesRead,
    status_code=status.HTTP_200_OK,
    summary="Update a preference",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def update_preference(
    preference_id: int,
    user_id: int,
    preference_data: EmployeePreferencesUpdate,
    current_user: UserModel = Depends(get_current_user),
    preferences_repository: EmployeePreferencesRepository = Depends(get_employee_preferences_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    template_repository: ShiftTemplateRepository = Depends(get_shift_template_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await update_employee_preference(
        preference_id,
        preference_data,
        current_user,
        user_id,
        preferences_repository,
        user_repository,
        template_repository,
        db
    )


@router.delete(
    "/users/{user_id}/preferences/{preference_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a preference",
    dependencies=[Depends(require_auth)],  # AUTH REQUIRED
)
async def delete_preference(
    preference_id: int,
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    preferences_repository: EmployeePreferencesRepository = Depends(get_employee_preferences_repository),
    db: Session = Depends(get_db)  # For transaction management
):
    return await delete_employee_preference(
        preference_id,
        current_user,
        preferences_repository,
        db
    )
