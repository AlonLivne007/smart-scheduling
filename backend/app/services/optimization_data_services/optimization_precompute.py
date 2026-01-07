"""
Optimization precomputation logic.

This module contains all derived/computed logic that works on already-loaded data.
No DB queries in this module.
"""

from typing import Dict, List, Set, Tuple
from datetime import date, datetime, time, timedelta

from app.services.utils.datetime_utils import normalize_shift_datetimes
from app.services.utils.overlap_utils import shifts_overlap, build_shift_overlaps


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


def build_rest_conflicts(
    shifts: List[Dict],
    min_rest_hours: float
) -> Dict[int, Set[int]]:
    """
    Build rest conflicts mapping: {shift_id: {conflicting_shift_ids}}.
    
    Two shifts conflict if:
    - They overlap, OR
    - The rest period between them is less than min_rest_hours
    
    This is used to enforce MIN_REST_HOURS constraint in the MIP model.
    For each employee and conflicting shift pair (s1, s2):
        sum_r x[i,s1,r] + sum_r x[i,s2,r] <= 1
    
    Args:
        shifts: List of shift dictionaries
        min_rest_hours: Minimum required rest hours between shifts
        
    Returns:
        Dictionary mapping shift_id to set of conflicting shift IDs
    """
    rest_conflicts: Dict[int, Set[int]] = {}
    
    for i, shift1 in enumerate(shifts):
        shift_id1 = shift1["planned_shift_id"]
        if shift_id1 not in rest_conflicts:
            rest_conflicts[shift_id1] = set()
        
        start1_dt, end1_dt = normalize_shift_datetimes(shift1)
        
        for shift2 in shifts[i+1:]:
            shift_id2 = shift2["planned_shift_id"]
            start2_dt, end2_dt = normalize_shift_datetimes(shift2)
            
            # Check if shifts overlap using shared utility
            if shifts_overlap(shift1, shift2):
                rest_conflicts[shift_id1].add(shift_id2)
                if shift_id2 not in rest_conflicts:
                    rest_conflicts[shift_id2] = set()
                rest_conflicts[shift_id2].add(shift_id1)
                continue
            
            # Check rest period between shifts
            # Calculate rest hours for both orderings
            # shift1 -> shift2: rest = start2 - end1
            if end1_dt < start2_dt:
                rest_hours_1_to_2 = (start2_dt - end1_dt).total_seconds() / 3600.0
                if rest_hours_1_to_2 < min_rest_hours:
                    rest_conflicts[shift_id1].add(shift_id2)
                    if shift_id2 not in rest_conflicts:
                        rest_conflicts[shift_id2] = set()
                    rest_conflicts[shift_id2].add(shift_id1)
            
            # shift2 -> shift1: rest = start1 - end2
            if end2_dt < start1_dt:
                rest_hours_2_to_1 = (start1_dt - end2_dt).total_seconds() / 3600.0
                if rest_hours_2_to_1 < min_rest_hours:
                    rest_conflicts[shift_id1].add(shift_id2)
                    if shift_id2 not in rest_conflicts:
                        rest_conflicts[shift_id2] = set()
                    rest_conflicts[shift_id2].add(shift_id1)
    
    return rest_conflicts

