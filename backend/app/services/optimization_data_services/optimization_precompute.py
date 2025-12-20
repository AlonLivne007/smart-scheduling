"""
Optimization precomputation logic.

This module contains all derived/computed logic that works on already-loaded data.
No DB queries in this module.
"""

from typing import Dict, List, Set, Tuple
from datetime import date, timedelta


def build_role_requirements(
    shifts: List[Dict],
    template_role_map: Dict[int, Dict[int, int]]
) -> Dict[int, Dict[int, int]]:
    """
    Build role requirements mapping: {shift_id: {role_id: required_count}}.
    
    Maps shifts to their role requirements using pre-fetched template requirements.
    
    Args:
        shifts: List of shift dictionaries (from build_shift_set)
        template_role_map: Pre-fetched template -> role -> count mapping
        
    Returns:
        Dictionary mapping shift_id to role requirements
    """
    if not shifts:
        return {}
    
    # Map shifts to their role requirements
    requirements = {}
    for shift in shifts:
        template_id = shift["template_id"]
        if template_id in template_role_map:
            requirements[shift["shift_id"]] = template_role_map[template_id]
    
    return requirements


def build_shift_overlaps(shifts: List[Dict]) -> Dict[int, Set[int]]:
    """
    Build shift overlaps mapping: {shift_id: {overlapping_shift_ids}}.
    
    Memory-efficient: only stores overlapping pairs, not a full O(S²) matrix.
    Two shifts overlap if their time ranges intersect.
    
    Args:
        shifts: List of shift dictionaries
        
    Returns:
        Dictionary mapping shift_id to set of overlapping shift IDs
    """
    shift_overlaps: Dict[int, Set[int]] = {}
    
    for i, shift1 in enumerate(shifts):
        shift_id1 = shift1["shift_id"]
        if shift_id1 not in shift_overlaps:
            shift_overlaps[shift_id1] = set()
        
        for shift2 in shifts[i+1:]:
            shift_id2 = shift2["shift_id"]
            
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
        shift_id = shift["shift_id"]
        start_time = shift["start_time"]
        end_time = shift["end_time"]
        
        # Compute duration in hours
        duration_delta = end_time - start_time
        duration_hours = duration_delta.total_seconds() / 3600.0
        
        durations[shift_id] = duration_hours
    
    return durations


def build_available_pairs(
    employees: List[Dict],
    shifts: List[Dict],
    role_requirements: Dict[int, Dict[int, int]],
    time_off_map: Dict[int, List[Tuple[date, date]]],
    existing_assignments: Set[Tuple[int, int, int]],
    shift_overlaps: Dict[int, Set[int]]
) -> Set[Tuple[int, int]]:
    """
    Build available pairs: {(employee_id, shift_id)}.
    
    Only stores available assignments (missing pairs = unavailable).
    Memory-efficient: O(available_pairs) instead of O(E*S).
    
    An employee is available for a shift if:
    1. They have the required role for that shift
    2. They don't have approved time-off during that shift
    3. They're not already assigned to an overlapping shift
    
    Args:
        employees: List of employee dictionaries
        shifts: List of shift dictionaries
        role_requirements: Precomputed role requirements {shift_id: {role_id: count}}
        time_off_map: Precomputed time-off map {user_id: [(start_date, end_date), ...]}
        existing_assignments: Precomputed existing assignments {(emp_id, shift_id, role_id)}
        shift_overlaps: Precomputed shift overlaps {shift_id: {overlapping_shift_ids}}
        
    Returns:
        Set of (employee_id, shift_id) tuples for available assignments
    """
    available_pairs = set()
    
    # Build set of (employee_id, shift_id) that are already assigned
    assigned_shifts: Set[Tuple[int, int]] = {
        (emp_id, shift_id) for (emp_id, shift_id, _) in existing_assignments
    }
    
    # Pre-group assignments by employee: {emp_id: [shift_ids]}
    assigned_shift_ids_by_emp: Dict[int, Set[int]] = {}
    for (emp_id, shift_id, _) in existing_assignments:
        if emp_id not in assigned_shift_ids_by_emp:
            assigned_shift_ids_by_emp[emp_id] = set()
        assigned_shift_ids_by_emp[emp_id].add(shift_id)
    
    # Check availability for each employee-shift pair
    for emp in employees:
        emp_id = emp["user_id"]
        emp_roles = set(emp["role_ids"])
        
        # Get shifts this employee is already assigned to
        assigned_shift_ids = assigned_shift_ids_by_emp.get(emp_id, set())
        
        for shift in shifts:
            shift_id = shift["shift_id"]
            shift_date = shift["date"]
            
            # Check if employee has any required role for this shift
            shift_roles = role_requirements.get(shift_id, {})
            has_required_role = any(role_id in emp_roles for role_id in shift_roles.keys())
            
            if not has_required_role:
                continue
            
            # Check time-off conflicts
            is_on_time_off = False
            if emp_id in time_off_map:
                for start_date, end_date in time_off_map[emp_id]:
                    if start_date <= shift_date <= end_date:
                        is_on_time_off = True
                        break
            
            if is_on_time_off:
                continue
            
            # Check if already assigned to this shift
            if (emp_id, shift_id) in assigned_shifts:
                continue
            
            # Check for overlapping assignments using precomputed shift overlaps
            overlapping_shifts = shift_overlaps.get(shift_id, set())
            is_overlapping = bool(assigned_shift_ids & overlapping_shifts)
            
            if is_overlapping:
                continue
            
            # Employee is available - add to set
            available_pairs.add((emp_id, shift_id))
    
    return available_pairs


def build_eligible_roles(
    employees: List[Dict],
    shifts: List[Dict],
    role_requirements: Dict[int, Dict[int, int]],
    available_pairs: Set[Tuple[int, int]]
) -> Dict[Tuple[int, int], Set[int]]:
    """
    Build eligible roles mapping: {(employee_id, shift_id): {role_id, ...}}.
    
    For each available employee-shift pair, computes the intersection of:
    - Roles the employee is qualified for
    - Roles required by the shift
    
    This is used to generate decision variables x[i,j,k] only for valid triples,
    instead of adding constraints to forbid invalid roles.
    
    Args:
        employees: List of employee dictionaries with role_ids
        shifts: List of shift dictionaries
        role_requirements: Precomputed role requirements {shift_id: {role_id: count}}
        available_pairs: Precomputed available pairs {(emp_id, shift_id)}
        
    Returns:
        Dictionary mapping (employee_id, shift_id) to set of eligible role IDs
    """
    eligible_roles = {}
    
    # Build employee role lookup for fast access
    emp_roles_map: Dict[int, Set[int]] = {
        emp["user_id"]: set(emp["role_ids"]) for emp in employees
    }
    
    # For each available pair, compute eligible roles
    for emp_id, shift_id in available_pairs:
        emp_roles = emp_roles_map.get(emp_id, set())
        shift_required_roles = set(role_requirements.get(shift_id, {}).keys())
        
        # Eligible roles = intersection of employee roles and shift required roles
        eligible = emp_roles & shift_required_roles
        
        if eligible:  # Only store if there are eligible roles
            eligible_roles[(emp_id, shift_id)] = eligible
    
    return eligible_roles


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
        shift_id = shift["shift_id"]
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


def build_fixed_assignments(
    existing_assignments: Set[Tuple[int, int, int]]
) -> Dict[Tuple[int, int], int]:
    """
    Build fixed assignments mapping: {(employee_id, shift_id): role_id}.
    
    Used by MIP builder to:
    - Fix x[i,j,k_assigned] = 1
    - Prevent other roles for the same (i,j) pair
    
    Args:
        existing_assignments: Set of (employee_id, shift_id, role_id) tuples
        
    Returns:
        Dictionary mapping (employee_id, shift_id) to assigned role_id
    """
    fixed = {}
    
    for emp_id, shift_id, role_id in existing_assignments:
        fixed[(emp_id, shift_id)] = role_id
    
    return fixed


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
    start1_dt = shift1["start_time"]
    end1_dt = shift1["end_time"]
    start2_dt = shift2["start_time"]
    end2_dt = shift2["end_time"]
    
    # Shifts overlap if one starts before the other ends
    return start1_dt < end2_dt and start2_dt < end1_dt

