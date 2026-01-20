"""
Employee preferences controller module.

This module contains business logic for employee preference management operations including
creation, retrieval, updating, and deletion of shift preferences.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List, Optional
from app.db.models.employeePreferencesModel import EmployeePreferencesModel
from app.db.models.userModel import UserModel
from app.db.models.shiftTemplateModel import ShiftTemplateModel
from app.schemas.employeePreferencesSchema import (
    EmployeePreferencesCreate,
    EmployeePreferencesUpdate,
    EmployeePreferencesRead,
)


# ------------------------
# Helper Functions
# ------------------------

def _serialize_employee_preferences(preference: EmployeePreferencesModel) -> EmployeePreferencesRead:
    """
    Convert ORM object to Pydantic schema.
    
    Args:
        preference: EmployeePreferencesModel instance
        
    Returns:
        EmployeePreferencesRead instance
    """
    # Extract relationship data explicitly
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


def _validate_user_exists(db: Session, user_id: int) -> UserModel:
    """
    Validate that a user exists in the database.
    
    Args:
        db: Database session
        user_id: ID of the user to validate
        
    Returns:
        UserModel instance if found
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return user


def _validate_shift_template_exists(db: Session, shift_template_id: Optional[int]) -> Optional[ShiftTemplateModel]:
    """
    Validate that a shift template exists if provided.
    
    Args:
        db: Database session
        shift_template_id: ID of the shift template to validate (optional)
        
    Returns:
        ShiftTemplateModel instance if found, None if not provided
        
    Raises:
        HTTPException: If shift template ID is provided but not found
    """
    if shift_template_id is None:
        return None
        
    shift_template = db.query(ShiftTemplateModel).filter(
        ShiftTemplateModel.shift_template_id == shift_template_id
    ).first()
    
    if not shift_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shift template with ID {shift_template_id} not found"
        )
    return shift_template


def _validate_time_range(start_time, end_time):
    """
    Validate that start_time is before end_time if both are provided.
    
    Args:
        start_time: Preferred start time
        end_time: Preferred end time
        
    Raises:
        HTTPException: If start_time is after or equal to end_time
    """
    if start_time and end_time and start_time >= end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Preferred start time must be before preferred end time"
        )


# ------------------------
# CRUD Functions
# ------------------------

async def create_employee_preference(
    db: Session,
    user_id: int,
    preference_data: EmployeePreferencesCreate,
    current_user: UserModel
) -> EmployeePreferencesRead:
    """
    Create a new employee preference.
    
    Args:
        db: Database session
        user_id: ID of the user creating the preference
        preference_data: Employee preference creation data
        current_user: Current authenticated user (for authorization)
        
    Returns:
        Created EmployeePreferencesRead instance
        
    Raises:
        HTTPException: If validation fails, unauthorized, or database error occurs
    """
    try:
        # Authorization: employees can only create their own preferences
        if not current_user.is_manager and user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create preferences for yourself"
            )
        
        # Validate user exists
        _validate_user_exists(db, user_id)
        
        # Validate shift template if provided
        if preference_data.preferred_shift_template_id:
            _validate_shift_template_exists(db, preference_data.preferred_shift_template_id)
        
        # Validate time range if provided
        _validate_time_range(
            preference_data.preferred_start_time,
            preference_data.preferred_end_time
        )
        
        # Create new preference
        new_preference = EmployeePreferencesModel(
            user_id=user_id,
            preferred_shift_template_id=preference_data.preferred_shift_template_id,
            preferred_day_of_week=preference_data.preferred_day_of_week,
            preferred_start_time=preference_data.preferred_start_time,
            preferred_end_time=preference_data.preferred_end_time,
            preference_weight=preference_data.preference_weight,
        )
        
        db.add(new_preference)
        db.commit()
        db.refresh(new_preference)
        
        return _serialize_employee_preferences(new_preference)
        
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e.orig)}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


async def get_employee_preferences_by_user(
    db: Session,
    user_id: int,
    current_user: UserModel
) -> List[EmployeePreferencesRead]:
    """
    Get all preferences for a specific user.
    
    Args:
        db: Database session
        user_id: ID of the user
        current_user: Current authenticated user (for authorization)
        
    Returns:
        List of EmployeePreferencesRead instances
        
    Raises:
        HTTPException: If user not found, unauthorized, or database error occurs
    """
    try:
        # Authorization: employees can only view their own preferences
        if not current_user.is_manager and user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own preferences"
            )
        
        # Validate user exists
        _validate_user_exists(db, user_id)
        
        # Fetch all preferences for the user
        preferences = db.query(EmployeePreferencesModel).filter(
            EmployeePreferencesModel.user_id == user_id
        ).all()
        
        return [_serialize_employee_preferences(pref) for pref in preferences]
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


async def get_employee_preference(
    db: Session,
    preference_id: int,
    user_id: int,
    current_user: UserModel
) -> EmployeePreferencesRead:
    """
    Get a single preference by ID.
    
    Args:
        db: Database session
        preference_id: ID of the preference
        user_id: ID of the user (for validation)
        current_user: Current authenticated user (for authorization)
        
    Returns:
        EmployeePreferencesRead instance
        
    Raises:
        HTTPException: If preference not found, unauthorized, or database error occurs
    """
    try:
        preference = db.query(EmployeePreferencesModel).filter(
            EmployeePreferencesModel.preference_id == preference_id
        ).first()
        
        if not preference:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preference with ID {preference_id} not found"
            )
        
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
        
        return _serialize_employee_preferences(preference)
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


async def update_employee_preference(
    db: Session,
    preference_id: int,
    preference_data: EmployeePreferencesUpdate,
    current_user: UserModel,
    target_user_id: Optional[int] = None
) -> EmployeePreferencesRead:
    """
    Update an existing employee preference.
    
    Args:
        db: Database session
        preference_id: ID of the preference to update
        preference_data: Employee preference update data
        current_user: Current authenticated user (for authorization)
        target_user_id: Target user ID (for managers to update other users' preferences)
        
    Returns:
        Updated EmployeePreferencesRead instance
        
    Raises:
        HTTPException: If preference not found, unauthorized, or validation fails
    """
    try:
        # Fetch existing preference
        preference = db.query(EmployeePreferencesModel).filter(
            EmployeePreferencesModel.preference_id == preference_id
        ).first()
        
        if not preference:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preference with ID {preference_id} not found"
            )
        
        # Determine effective user ID based on authorization
        if current_user.is_manager and target_user_id is not None:
            effective_user_id = target_user_id
        else:
            effective_user_id = current_user.user_id
        
        # Check authorization: only the owner can update their preferences
        if preference.user_id != effective_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own preferences"
            )
        
        # Validate shift template if being updated
        if preference_data.preferred_shift_template_id is not None:
            _validate_shift_template_exists(db, preference_data.preferred_shift_template_id)
        
        # Build updated time range (using existing values if not provided)
        start_time = (
            preference_data.preferred_start_time 
            if preference_data.preferred_start_time is not None 
            else preference.preferred_start_time
        )
        end_time = (
            preference_data.preferred_end_time 
            if preference_data.preferred_end_time is not None 
            else preference.preferred_end_time
        )
        _validate_time_range(start_time, end_time)
        
        # Update fields
        update_data = preference_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preference, field, value)
        
        db.commit()
        db.refresh(preference)
        
        return _serialize_employee_preferences(preference)
        
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e.orig)}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )


async def delete_employee_preference(
    db: Session,
    preference_id: int,
    current_user: UserModel,
    target_user_id: Optional[int] = None
) -> dict:
    """
    Delete an employee preference.
    
    Args:
        db: Database session
        preference_id: ID of the preference to delete
        current_user: Current authenticated user (for authorization)
        target_user_id: Target user ID (for managers to delete other users' preferences)
        
    Returns:
        Success message dict
        
    Raises:
        HTTPException: If preference not found or unauthorized
    """
    try:
        # Fetch existing preference
        preference = db.query(EmployeePreferencesModel).filter(
            EmployeePreferencesModel.preference_id == preference_id
        ).first()
        
        if not preference:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preference with ID {preference_id} not found"
            )
        
        # Determine effective user ID based on authorization
        if current_user.is_manager and target_user_id is not None:
            effective_user_id = target_user_id
        else:
            effective_user_id = current_user.user_id
        
        # Check authorization: only the owner can delete their preferences
        if preference.user_id != effective_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own preferences"
            )
        
        db.delete(preference)
        db.commit()
        
        return {"message": f"Preference {preference_id} deleted successfully"}
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred: {str(e)}"
        )
