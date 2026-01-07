"""
Datetime utility functions for shift normalization.

This module provides unified datetime normalization logic that handles
both PlannedShiftModel objects and shift dictionaries, ensuring consistent
handling of overnight shifts across the codebase.
"""

from typing import Tuple, Union, Dict
from datetime import datetime, date, time, timedelta

# Type hint for shift-like objects
ShiftLike = Union['PlannedShiftModel', Dict]


def normalize_shift_datetimes(shift: ShiftLike) -> Tuple[datetime, datetime]:
    """
    Normalize shift start/end times to datetime objects, handling overnight shifts.
    
    This function works with both PlannedShiftModel objects and shift dictionaries,
    providing a unified interface for datetime normalization across the codebase.
    
    Handles:
    - Time objects that need to be combined with a date
    - Datetime objects that are already normalized
    - Overnight shifts where end_time < start_time (end is next day)
    - Cross-day overlaps
    
    Args:
        shift: Either a PlannedShiftModel object or a dictionary with:
            - 'date' (date object)
            - 'start_time' (time or datetime)
            - 'end_time' (time or datetime)
    
    Returns:
        Tuple of (start_dt, end_dt) as datetime objects
    
    Raises:
        ValueError: If shift is a dict and date is missing when time objects are provided
        AttributeError: If shift doesn't have required attributes
    """
    # Handle PlannedShiftModel objects
    if hasattr(shift, 'date') and hasattr(shift, 'start_time') and hasattr(shift, 'end_time'):
        shift_date = shift.date
        start = shift.start_time
        end = shift.end_time
    # Handle dictionaries
    elif isinstance(shift, dict):
        shift_date = shift.get('date')
        start = shift.get('start_time')
        end = shift.get('end_time')
    else:
        raise ValueError(f"Unsupported shift type: {type(shift)}")
    
    # Convert start_time to datetime
    if isinstance(start, time):
        if shift_date is None:
            raise ValueError("Cannot normalize time without date")
        start_dt = datetime.combine(shift_date, start)
    elif isinstance(start, datetime):
        start_dt = start
    else:
        raise ValueError(f"Unsupported start_time type: {type(start)}")
    
    # Convert end_time to datetime
    if isinstance(end, time):
        if shift_date is None:
            raise ValueError("Cannot normalize time without date")
        end_dt = datetime.combine(shift_date, end)
        # Handle overnight: if end < start (time-only), end is next day
        if end < start:
            end_dt += timedelta(days=1)
    elif isinstance(end, datetime):
        end_dt = end
        # If both are datetime and end < start on same date, assume overnight
        if end_dt.date() == start_dt.date() and end_dt < start_dt:
            end_dt += timedelta(days=1)
    else:
        raise ValueError(f"Unsupported end_time type: {type(end)}")
    
    return start_dt, end_dt

