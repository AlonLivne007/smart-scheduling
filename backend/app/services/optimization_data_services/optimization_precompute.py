"""
Optimization precomputation logic.

This module contains all derived/computed logic that works on already-loaded data.
No DB queries in this module.
"""

from typing import Dict, List, Set, Tuple
from datetime import date, datetime, time, timedelta


def normalize_shift_datetimes(shift: Dict) -> Tuple[datetime, datetime]:
    """
    Normalize shift start/end times to datetime objects, handling overnight shifts.
    
    If end_time < start_time (time-only), assumes end is next day.
    If both are datetime objects, returns as-is.
    
    Args:
        shift: Shift dictionary with 'date', 'start_time', and 'end_time'
        
    Returns:
        Tuple of (start_dt, end_dt) as datetime objects
    """
    start = shift["start_time"]
    end = shift["end_time"]
    shift_date = shift.get("date")
    
    # Convert to datetime if needed
    if isinstance(start, time):
        if shift_date is None:
            raise ValueError("Cannot normalize time without date")
        start_dt = datetime.combine(shift_date, start)
    else:
        start_dt = start
    
    if isinstance(end, time):
        if shift_date is None:
            raise ValueError("Cannot normalize time without date")
        end_dt = datetime.combine(shift_date, end)
        # Handle overnight: if end < start, end is next day
        if end < start:
            end_dt += timedelta(days=1)
    else:
        end_dt = end
        # If both are datetime and end < start on same date, assume overnight
        if end_dt.date() == start_dt.date() and end_dt < start_dt:
            end_dt += timedelta(days=1)
    
    return start_dt, end_dt


def _shifts_overlap(shift1: Dict, shift2: Dict) -> bool:
    """
    Check if two shifts overlap in time.
    
    Handles:
    - Full datetime comparison (date + time)
    - Overnight shifts (end_time < start_time means end is next day)
    
    Args:
        shift1: First shift dictionary with 'date' and 'start_time'/'end_time'
        shift2: Second shift dictionary with 'date' and 'start_time'/'end_time'
        
    Returns:
        True if shifts overlap, False otherwise
    """
    start1_dt, end1_dt = normalize_shift_datetimes(shift1)
    start2_dt, end2_dt = normalize_shift_datetimes(shift2)
    
    # Shifts overlap if one starts before the other ends
    return start1_dt < end2_dt and start2_dt < end1_dt


def build_shift_overlaps(shifts: List[Dict]) -> Dict[int, Set[int]]:
    """
    Build shift overlaps mapping: {shift_id: {overlapping_shift_ids}}.
    
    Memory-efficient: only stores overlapping pairs, not a full O(S²) matrix.
    Two shifts overlap if their time ranges intersect.
    Uses proper datetime overlap detection (handles overnight shifts).
    
    Args:
        shifts: List of shift dictionaries
        
    Returns:
        Dictionary mapping shift_id to set of overlapping shift IDs
    """
    shift_overlaps: Dict[int, Set[int]] = {}
    
    for i, shift1 in enumerate(shifts):
        shift_id1 = shift1["planned_shift_id"]
        if shift_id1 not in shift_overlaps:
            shift_overlaps[shift_id1] = set()
        
        for shift2 in shifts[i+1:]:
            shift_id2 = shift2["planned_shift_id"]
            
            if _shifts_overlap(shift1, shift2):
                shift_overlaps[shift_id1].add(shift_id2)
                # Initialize set for shift2 if not exists
                if shift_id2 not in shift_overlaps:
                    shift_overlaps[shift_id2] = set()
                shift_overlaps[shift_id2].add(shift_id1)
    
    return shift_overlaps


def build_shift_durations(shifts: List[Dict]) -> Dict[int, float]:
    """
    Build shift durations mapping: {shift_id: duration_hours}.
    
    Computes duration in hours from start_time and end_time.
    Needed for max-hours and workload fairness constraints.
    
    Args:
        shifts: List of shift dictionaries with start_time and end_time (DateTime objects)
        
    Returns:
        Dictionary mapping shift_id to duration in hours
    """
    durations = {}
    
    for shift in shifts:
        shift_id = shift["planned_shift_id"]
        start_dt, end_dt = normalize_shift_datetimes(shift)
        
        # Compute duration in hours
        duration_delta = end_dt - start_dt
        duration_hours = duration_delta.total_seconds() / 3600.0
        
        durations[shift_id] = duration_hours
    
    return durations


def build_time_off_conflicts(
    employees: List[Dict],
    shifts: List[Dict],
    time_off_map: Dict[int, List[Tuple[date, date]]]
) -> Dict[int, List[int]]:
    """
    Build time-off conflicts: {employee_id: [conflicting_shift_ids]}.
    
    Optimized: Builds shifts_by_date lookup once, then iterates over dates
    in time-off periods instead of all shifts.
    
    Args:
        employees: List of employee dictionaries
        shifts: List of shift dictionaries
        time_off_map: Precomputed time-off map {user_id: [(start_date, end_date), ...]}
        
    Returns:
        Dictionary mapping employee_id to list of conflicting shift IDs
    """
    # Build shifts_by_date lookup once: O(S)
    shifts_by_date: Dict[date, List[int]] = {}
    for shift in shifts:
        shift_date = shift["date"]
        shift_id = shift["planned_shift_id"]
        if shift_date not in shifts_by_date:
            shifts_by_date[shift_date] = []
        shifts_by_date[shift_date].append(shift_id)
    
    conflicts = {}
    
    for emp in employees:
        emp_id = emp["user_id"]
        conflicting_shifts_set = set()
        
        # Find time-off periods for this employee
        if emp_id in time_off_map:
            for start_date, end_date in time_off_map[emp_id]:
                # Iterate over dates in the time-off period
                current_date = start_date
                while current_date <= end_date:
                    # Collect shift_ids for this date
                    if current_date in shifts_by_date:
                        conflicting_shifts_set.update(shifts_by_date[current_date])
                    # Move to next day
                    current_date = current_date + timedelta(days=1)
        
        if conflicting_shifts_set:
            conflicts[emp_id] = list(conflicting_shifts_set)
    
    return conflicts

