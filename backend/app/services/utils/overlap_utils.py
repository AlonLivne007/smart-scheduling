"""
Shift overlap detection utilities.

This module provides unified overlap detection logic that works with both
PlannedShiftModel objects and shift dictionaries, ensuring consistent
overlap detection across the codebase.
"""

from typing import Dict, List, Set, Union
from datetime import datetime

from app.services.utils.datetime_utils import normalize_shift_datetimes

# Type hint for shift-like objects
ShiftLike = Union['PlannedShiftModel', Dict]


def shifts_overlap(shift1: ShiftLike, shift2: ShiftLike) -> bool:
    """
    Check if two shifts overlap in time.
    
    Handles:
    - Full datetime comparison (date + time)
    - Overnight shifts (end_time < start_time means end is next day)
    - Cross-day overlaps
    
    Args:
        shift1: First shift (PlannedShiftModel or dict with 'date', 'start_time', 'end_time')
        shift2: Second shift (PlannedShiftModel or dict with 'date', 'start_time', 'end_time')
    
    Returns:
        True if shifts overlap, False otherwise
    """
    start1_dt, end1_dt = normalize_shift_datetimes(shift1)
    start2_dt, end2_dt = normalize_shift_datetimes(shift2)
    
    # Shifts overlap if one starts before the other ends
    return start1_dt < end2_dt and start2_dt < end1_dt


def build_shift_overlaps(shifts: List[ShiftLike]) -> Dict[int, Set[int]]:
    """
    Build shift overlaps mapping: {shift_id: {overlapping_shift_ids}}.
    
    Memory-efficient: only stores overlapping pairs, not a full O(S²) matrix.
    Two shifts overlap if their time ranges intersect.
    Uses proper datetime overlap detection (handles overnight shifts).
    
    Args:
        shifts: List of shifts (PlannedShiftModel objects or dictionaries)
            Each shift must have a 'planned_shift_id' attribute or key
    
    Returns:
        Dictionary mapping shift_id to set of overlapping shift IDs
    """
    shift_overlaps: Dict[int, Set[int]] = {}
    
    for i, shift1 in enumerate(shifts):
        # Extract shift_id from either model or dict
        shift_id1 = shift1.planned_shift_id if hasattr(shift1, 'planned_shift_id') else shift1['planned_shift_id']
        if shift_id1 not in shift_overlaps:
            shift_overlaps[shift_id1] = set()
        
        for shift2 in shifts[i+1:]:
            shift_id2 = shift2.planned_shift_id if hasattr(shift2, 'planned_shift_id') else shift2['planned_shift_id']
            
            if shifts_overlap(shift1, shift2):
                shift_overlaps[shift_id1].add(shift_id2)
                # Initialize set for shift2 if not exists
                if shift_id2 not in shift_overlaps:
                    shift_overlaps[shift_id2] = set()
                shift_overlaps[shift_id2].add(shift_id1)
    
    return shift_overlaps

