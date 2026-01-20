"""
Validation utilities for common validation operations.

This module provides centralized validation functions that can be reused
across different controllers and services.

These functions raise domain exceptions (ValidationError) which are
handled by the centralized error handler in the API layer.
"""

from datetime import date
from app.core.exceptions.service import ValidationError


def validate_date_range(start_date: date, end_date: date) -> None:
    """
    Validate that start_date is before or equal to end_date.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Raises:
        ValidationError: If start_date is after end_date
    """
    if start_date > end_date:
        raise ValidationError("Start date must be before or equal to end date")


def validate_date_not_past(date_value: date) -> None:
    """
    Validate that date is not in the past.
    
    Args:
        date_value: Date to validate
        
    Raises:
        ValidationError: If date is in the past
    """
    if date_value < date.today():
        raise ValidationError("Date cannot be in the past")


def validate_time_range(start_time: str, end_time: str) -> None:
    """
    Validate that start_time is before end_time if both are provided.
    
    Args:
        start_time: Start time as string (HH:MM format)
        end_time: End time as string (HH:MM format)
        
    Raises:
        ValidationError: If start_time is after or equal to end_time
    """
    if start_time and end_time and start_time >= end_time:
        raise ValidationError("Preferred start time must be before preferred end time")
