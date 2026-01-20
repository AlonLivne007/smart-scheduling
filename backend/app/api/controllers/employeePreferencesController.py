"""
Employee preferences controller module.

This module contains business logic for employee preference management operations including
creation, retrieval, updating, and deletion of shift preferences.
Controllers use repositories for database access - no direct ORM access.
"""

from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session  # Only for type hints

from app.repositories.employee_preferences_repository import EmployeePreferencesRepository
from app.repositories.user_repository import UserRepository
from app.repositories.shift_template_repository import ShiftTemplateRepository
from app.schemas.employeePreferencesSchema import (
    EmployeePreferencesCreate,
    EmployeePreferencesUpdate,
    EmployeePreferencesRead,
)
from app.db.models.userModel import UserModel
from app.exceptions.repository import NotFoundError, ConflictError
from app.db.session_manager import transaction


def _serialize_employee_preferences(preference) -> EmployeePreferencesRead:
    """
    Convert ORM object to Pydantic schema.
    """
    user_full_name = preference.user.user_full_name if preference.user else None
    shift_template_name = preference.shift_template.shift_template_name if preference.shift_template else None
    
    return EmployeePreferencesRead(
        preference_id=preference.preference_id,
        user_id=preference.user_id,
        preferred_shift_template_id=preference.preferred_shift_template_id,
        preferred_day_of_week=preference.preferred_day_of_week,
        preferred_start_time=preference.preferred_start_time,
        preferred_end_time=preference.preferred_end_time,
        preference_weight=preference.preference_weight,
        user_full_name=user_full_name,
        shift_template_name=shift_template_name,
    )


def _validate_time_range(start_time, end_time):
    """
    Validate that start_time is before end_time if both are provided.
    """
    if start_time and end_time and start_time >= end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Preferred start time must be before preferred end time"
        )


async def create_employee_preference(
    user_id: int,
    preference_data: EmployeePreferencesCreate,
    current_user: UserModel,
    preferences_repository: EmployeePreferencesRepository,
    user_repository: UserRepository,
    template_repository: ShiftTemplateRepository,
    db: Session  # For transaction management
) -> EmployeePreferencesRead:
    """
    Create a new employee preference.
    
    Business logic:
    - Authorization: employees can only create their own preferences
    - Validate user exists
    - Validate shift template exists if provided
    - Validate time range
    - Create preference
    """
    try:
        # Business rule: Authorization - employees can only create their own preferences
        if not current_user.is_manager and user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create preferences for yourself"
            )
        
        # Business rule: Validate user exists
        user_repository.get_or_raise(user_id)
        
        # Business rule: Validate shift template if provided
        if preference_data.preferred_shift_template_id:
            template_repository.get_or_raise(preference_data.preferred_shift_template_id)
        
        # Business rule: Validate time range
        _validate_time_range(
            preference_data.preferred_start_time,
            preference_data.preferred_end_time
        )
        
        with transaction(db):
            preference = preferences_repository.create(
                user_id=user_id,
                preferred_shift_template_id=preference_data.preferred_shift_template_id,
                preferred_day_of_week=preference_data.preferred_day_of_week,
                preferred_start_time=preference_data.preferred_start_time,
                preferred_end_time=preference_data.preferred_end_time,
                preference_weight=preference_data.preference_weight,
            )
            
            # Get preference with relationships for serialization
            # Need to refresh to load relationships
            preference = preferences_repository.get_by_id(preference.preference_id)
            # Load relationships manually
            if preference:
                _ = preference.user
                _ = preference.shift_template
            
            return _serialize_employee_preferences(preference)
            
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


async def get_employee_preferences_by_user(
    user_id: int,
    current_user: UserModel,
    preferences_repository: EmployeePreferencesRepository,
    user_repository: UserRepository
) -> List[EmployeePreferencesRead]:
    """
    Get all preferences for a specific user.
    
    Business logic:
    - Authorization: employees can only view their own preferences
    - Validate user exists
    - Get preferences
    """
    try:
        # Business rule: Authorization - employees can only view their own preferences
        if not current_user.is_manager and user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own preferences"
            )
        
        # Business rule: Validate user exists
        user_repository.get_or_raise(user_id)
        
        # Get preferences
        preferences = preferences_repository.get_by_user(user_id)
        return [_serialize_employee_preferences(p) for p in preferences]
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


async def get_employee_preference(
    preference_id: int,
    user_id: int,
    current_user: UserModel,
    preferences_repository: EmployeePreferencesRepository,
    user_repository: UserRepository
) -> EmployeePreferencesRead:
    """
    Get a single preference by ID.
    
    Business logic:
    - Verify preference exists and belongs to user
    - Authorization: employees can only view their own preferences
    """
    try:
        preference = preferences_repository.get_or_raise(preference_id)
        
        # Business rule: Verify it belongs to the specified user
        if preference.user_id != user_id:
            raise NotFoundError(f"Preference {preference_id} does not belong to user {user_id}")
        
        # Business rule: Authorization - employees can only view their own preferences
        if not current_user.is_manager and user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own preferences"
            )
        
        # Load relationships
        _ = preference.user
        _ = preference.shift_template
        
        return _serialize_employee_preferences(preference)
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preference with ID {preference_id} not found"
        )


async def update_employee_preference(
    preference_id: int,
    preference_data: EmployeePreferencesUpdate,
    current_user: UserModel,
    target_user_id: Optional[int],
    preferences_repository: EmployeePreferencesRepository,
    user_repository: UserRepository,
    template_repository: ShiftTemplateRepository,
    db: Session  # For transaction management
) -> EmployeePreferencesRead:
    """
    Update an existing employee preference.
    
    Business logic:
    - Authorization: only the owner can update
    - Validate shift template if provided
    - Validate time range
    - Update preference
    """
    try:
        preference = preferences_repository.get_or_raise(preference_id)
        
        # Business rule: Determine effective user ID
        if current_user.is_manager and target_user_id is not None:
            effective_user_id = target_user_id
        else:
            effective_user_id = current_user.user_id
        
        # Business rule: Only the owner can update
        if preference.user_id != effective_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own preferences"
            )
        
        # Business rule: Validate shift template if provided
        if preference_data.preferred_shift_template_id is not None:
            template_repository.get_or_raise(preference_data.preferred_shift_template_id)
        
        # Business rule: Validate time range
        start_time = preference_data.preferred_start_time if preference_data.preferred_start_time else preference.preferred_start_time
        end_time = preference_data.preferred_end_time if preference_data.preferred_end_time else preference.preferred_end_time
        _validate_time_range(start_time, end_time)
        
        with transaction(db):
            # Update fields
            update_data = {}
            if preference_data.preferred_shift_template_id is not None:
                update_data["preferred_shift_template_id"] = preference_data.preferred_shift_template_id
            if preference_data.preferred_day_of_week is not None:
                update_data["preferred_day_of_week"] = preference_data.preferred_day_of_week
            if preference_data.preferred_start_time is not None:
                update_data["preferred_start_time"] = preference_data.preferred_start_time
            if preference_data.preferred_end_time is not None:
                update_data["preferred_end_time"] = preference_data.preferred_end_time
            if preference_data.preference_weight is not None:
                update_data["preference_weight"] = preference_data.preference_weight
            
            if update_data:
                preferences_repository.update(preference_id, **update_data)
            
            # Get updated preference with relationships
            preference = preferences_repository.get_by_id(preference_id)
            _ = preference.user
            _ = preference.shift_template
            
            return _serialize_employee_preferences(preference)
            
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


async def delete_employee_preference(
    preference_id: int,
    current_user: UserModel,
    preferences_repository: EmployeePreferencesRepository,
    db: Session  # For transaction management
) -> None:
    """
    Delete an employee preference.
    
    Business logic:
    - Authorization: only the owner can delete
    - Delete preference
    """
    try:
        preference = preferences_repository.get_or_raise(preference_id)
        
        # Business rule: Only the owner can delete
        if not current_user.is_manager and preference.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own preferences"
            )
        
        with transaction(db):
            preferences_repository.delete(preference_id)
            
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preference with ID {preference_id} not found"
        )
