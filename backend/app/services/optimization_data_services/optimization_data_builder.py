"""
Optimization Data Builder service.

This module is responsible for orchestration and DB access only.
It extracts data from the database and coordinates the precomputation logic.
This file should be the only one touching SQLAlchemy sessions.
"""

from typing import Dict, List, Set, Tuple, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select
import numpy as np
from datetime import datetime, time

from app.db.models.userModel import UserModel
from app.db.models.plannedShiftModel import PlannedShiftModel, PlannedShiftStatus
from app.db.models.roleModel import RoleModel
from app.db.models.weeklyScheduleModel import WeeklyScheduleModel
from app.db.models.employeePreferencesModel import EmployeePreferencesModel, DayOfWeek
from app.db.models.timeOffRequestModel import TimeOffRequestModel, TimeOffRequestStatus
from app.db.models.shiftTemplateModel import ShiftTemplateModel
from app.db.models.shiftAssignmentModel import ShiftAssignmentModel
from app.db.models.systemConstraintsModel import SystemConstraintsModel, SystemConstraintType

from app.services.optimization_data_services.optimization_data import OptimizationData
from app.services.optimization_data_services.optimization_precompute import (
    build_shift_overlaps,
    build_shift_durations,
    build_time_off_conflicts,
)


class OptimizationDataBuilder:
    """
    Service for building optimization data from database entities.
    
    This service extracts data from the database and coordinates the precomputation
    logic to build a complete OptimizationData object suitable for MIP model construction.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the data builder with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def build(self, weekly_schedule_id: int) -> OptimizationData:
        """
        Main orchestrator method to prepare all optimization data.
        
        This method coordinates all data extraction and transformation steps
        to build a complete OptimizationData object.
        
        Args:
            weekly_schedule_id: ID of the weekly schedule to optimize
            
        Returns:
            OptimizationData object with all required data structures
        """
        data = OptimizationData()
        
        # Verify weekly schedule exists
        weekly_schedule = self.db.query(WeeklyScheduleModel).filter(
            WeeklyScheduleModel.weekly_schedule_id == weekly_schedule_id
        ).first()
        
        if not weekly_schedule:
            raise ValueError(f"Weekly schedule {weekly_schedule_id} not found")
        
        # Load data from database
        data.employees = self.build_employee_set()
        data.shifts = self.build_shift_set(weekly_schedule_id)
        data.roles = self.build_role_set()
        
        if not data.employees:
            raise ValueError("No eligible employees found")
        
        if not data.shifts:
            raise ValueError(f"No planned shifts found for weekly schedule {weekly_schedule_id}")
        
        # Build index mappings
        data.employee_index = {emp['user_id']: idx for idx, emp in enumerate(data.employees)}
        data.shift_index = {shift['planned_shift_id']: idx for idx, shift in enumerate(data.shifts)}
        
        # Build role mappings
        data.role_requirements = self.build_role_requirements(data.shifts)
        data.employee_roles = self.build_employee_roles(data.employees)
        
        # Build existing assignments (for preserving preferred assignments)
        data.existing_assignments = self.build_existing_assignments(weekly_schedule_id)
        
        # Compute schedule date range to filter time-off requests
        schedule_min_date = min(shift['date'] for shift in data.shifts) if data.shifts else None
        schedule_max_date = max(shift['date'] for shift in data.shifts) if data.shifts else None
        
        # Build time-off map once, reused in availability and conflicts
        time_off_map = self._build_time_off_map(schedule_min_date, schedule_max_date)
        
        # Build matrices
        data.availability_matrix = self.build_availability_matrix(
            data.employees, data.shifts, data.employee_index, data.shift_index,
            data.existing_assignments, time_off_map
        )
        
        data.preference_scores = self.build_preference_scores(
            data.employees, data.shifts, data.employee_index, data.shift_index
        )
        
        # Detect shift overlaps (using improved overlap detection)
        data.shift_overlaps = self.detect_shift_overlaps(data.shifts, data.shift_index)
        
        # Build shift durations (needed for max-hours and workload fairness constraints)
        data.shift_durations = build_shift_durations(data.shifts)
        
        # Build system constraints (loads once to keep MIP builder clean)
        data.system_constraints = self.build_system_constraints()
        
        # Build time-off conflicts
        data.time_off_conflicts = build_time_off_conflicts(
            data.employees, data.shifts, time_off_map
        )
        
        return data
    
    def build_employee_set(self) -> List[Dict]:
        """
        Extract eligible employees (active, with at least one role).
        
        Returns:
            List of employee dictionaries with user_id, name, email, roles
        """
        employees = self.db.query(UserModel).filter(
            UserModel.user_status.in_(["ACTIVE", "active"])
        ).all()
        
        # Filter to only employees with at least one role
        eligible_employees = []
        for emp in employees:
            if emp.roles and len(emp.roles) > 0:
                eligible_employees.append({
                    'user_id': emp.user_id,
                    'user_full_name': emp.user_full_name,
                    'user_email': emp.user_email,
                    'is_manager': emp.is_manager,
                    'roles': [role.role_id for role in emp.roles]
                })
        
        return eligible_employees
    
    def build_shift_set(self, weekly_schedule_id: int) -> List[Dict]:
        """
        Extract planned shifts from weekly schedule.
        
        Optimized: Fetches all role requirements in a single batch query
        instead of querying per shift.
        
        Args:
            weekly_schedule_id: ID of the weekly schedule
            
        Returns:
            List of shift dictionaries with shift details and requirements
        """
        shifts = self.db.query(PlannedShiftModel).filter(
            PlannedShiftModel.weekly_schedule_id == weekly_schedule_id,
            PlannedShiftModel.status != PlannedShiftStatus.CANCELLED
        ).all()
        
        # Fetch template role map for all templates in one query
        shift_list = []
        template_ids = {shift.shift_template_id for shift in shifts if shift.shift_template_id}
        template_role_map = self._fetch_template_role_map(template_ids)
        
        for shift in shifts:
            shift_dict = {
                'planned_shift_id': shift.planned_shift_id,
                'weekly_schedule_id': shift.weekly_schedule_id,
                'shift_template_id': shift.shift_template_id,
                'date': shift.date,
                'start_time': shift.start_time,
                'end_time': shift.end_time,
                'location': shift.location,
                'status': shift.status.value,
                'required_roles': []
            }
            
            # Use pre-fetched template role map
            if shift.shift_template_id and shift.shift_template_id in template_role_map:
                for role_id, required_count in template_role_map[shift.shift_template_id].items():
                    shift_dict['required_roles'].append({
                        'role_id': role_id,
                        'required_count': required_count
                    })
            
            shift_list.append(shift_dict)
        
        return shift_list
    
    def _fetch_template_role_map(self, template_ids: Set[int]) -> Dict[int, Dict[int, int]]:
        """
        Fetch template role requirements mapping from database.
        
        Fetches all role requirements for all templates in a single query.
        This is much more efficient than querying per shift.
        
        Args:
            template_ids: Set of template IDs to fetch requirements for
            
        Returns:
            Dictionary mapping template_id to {role_id: required_count}
        """
        if not template_ids:
            return {}
        
        # Import the association table
        from app.db.models.shiftRoleRequirementsTabel import shift_role_requirements
        
        # Fetch all role requirements for all templates in one query
        all_requirements = self.db.execute(
            select(
                shift_role_requirements.c.shift_template_id,
                shift_role_requirements.c.role_id,
                shift_role_requirements.c.required_count
            ).where(
                shift_role_requirements.c.shift_template_id.in_(template_ids)
            )
        ).all()
        
        # Build template -> role -> count mapping
        template_role_map: Dict[int, Dict[int, int]] = {}
        for row in all_requirements:
            template_id = row.shift_template_id
            if template_id not in template_role_map:
                template_role_map[template_id] = {}
            template_role_map[template_id][row.role_id] = row.required_count
        
        return template_role_map
    
    def build_role_set(self) -> List[Dict]:
        """
        Extract all roles in the system.
        
        Returns:
            List of role dictionaries with role_id and role_name
        """
        roles = self.db.query(RoleModel).all()
        
        return [
            {
                'role_id': role.role_id,
                'role_name': role.role_name
            }
            for role in roles
        ]
    
    def build_role_requirements(self, shifts: List[Dict]) -> Dict[int, List[int]]:
        """
        Build role requirements mapping for each shift.
        
        Args:
            shifts: List of shift dictionaries
            
        Returns:
            Dictionary mapping shift_id -> list of required role_ids
        """
        role_requirements = {}
        
        for shift in shifts:
            shift_id = shift['planned_shift_id']
            role_requirements[shift_id] = [
                req['role_id'] for req in shift['required_roles']
            ]
        
        return role_requirements
    
    def build_employee_roles(self, employees: List[Dict]) -> Dict[int, List[int]]:
        """
        Build employee roles mapping.
        
        Args:
            employees: List of employee dictionaries
            
        Returns:
            Dictionary mapping user_id -> list of role_ids
        """
        return {
            emp['user_id']: emp['roles'] 
            for emp in employees
        }
    
    def build_existing_assignments(self, weekly_schedule_id: int) -> Set[Tuple[int, int, int]]:
        """
        Build set of existing assignments: {(employee_id, shift_id, role_id)}.
        
        Args:
            weekly_schedule_id: ID of the weekly schedule
            
        Returns:
            Set of tuples (employee_id, shift_id, role_id)
        """
        # Get all planned shifts for this schedule
        planned_shifts = (
            self.db.query(PlannedShiftModel.planned_shift_id)
            .filter(PlannedShiftModel.weekly_schedule_id == weekly_schedule_id)
            .all()
        )
        
        shift_id_list = [ps.planned_shift_id for ps in planned_shifts]
        
        if not shift_id_list:
            return set()
        
        # Get all assignments for these shifts
        assignments = (
            self.db.query(ShiftAssignmentModel)
            .filter(ShiftAssignmentModel.planned_shift_id.in_(shift_id_list))
            .all()
        )
        
        assignment_set = set()
        for assignment in assignments:
            assignment_set.add((
                assignment.user_id,
                assignment.planned_shift_id,
                assignment.role_id
            ))
        
        return assignment_set
    
    def build_system_constraints(self) -> Dict[SystemConstraintType, Tuple[float, bool]]:
        """
        Build system constraints mapping: {SystemConstraintType: (value, is_hard)}.
        
        Queries SystemConstraintsModel once to load all system-wide constraints.
        This keeps the MIP builder clean (no DB queries needed).
        
        Returns:
            Dictionary mapping constraint type to (value, is_hard) tuple
        """
        constraints = self.db.query(SystemConstraintsModel).all()
        
        system_constraints: Dict[SystemConstraintType, Tuple[float, bool]] = {}
        
        for constraint in constraints:
            system_constraints[constraint.constraint_type] = (
                constraint.constraint_value,
                constraint.is_hard_constraint
            )
        
        return system_constraints
    
    def _build_time_off_map(
        self,
        schedule_min_date: Optional[date],
        schedule_max_date: Optional[date]
    ) -> Dict[int, List[Tuple[date, date]]]:
        """
        Build time-off map: {user_id: [(start_date, end_date), ...]}.
        
        Optimized: Only fetches time-off requests that overlap with the schedule date range.
        A time-off request overlaps if: (start_date <= schedule_max_date AND end_date >= schedule_min_date)
        
        Args:
            schedule_min_date: Minimum date in the schedule (None if no shifts)
            schedule_max_date: Maximum date in the schedule (None if no shifts)
            
        Returns:
            Dictionary mapping user_id to list of time-off date ranges
        """
        # Build query for approved time-off requests
        query = self.db.query(TimeOffRequestModel).filter(
            TimeOffRequestModel.status == TimeOffRequestStatus.APPROVED
        )
        
        # Filter to only requests that overlap with schedule date range
        if schedule_min_date is not None and schedule_max_date is not None:
            # Overlap condition: start_date <= schedule_max_date AND end_date >= schedule_min_date
            query = query.filter(
                TimeOffRequestModel.start_date <= schedule_max_date,
                TimeOffRequestModel.end_date >= schedule_min_date
            )
        
        time_off_requests = query.all()
        
        time_off_map: Dict[int, List[Tuple[date, date]]] = {}
        for tor in time_off_requests:
            if tor.user_id not in time_off_map:
                time_off_map[tor.user_id] = []
            time_off_map[tor.user_id].append((tor.start_date, tor.end_date))
        
        return time_off_map
    
    def build_availability_matrix(
        self, 
        employees: List[Dict], 
        shifts: List[Dict],
        employee_index: Dict[int, int],
        shift_index: Dict[int, int],
        existing_assignments: Set[Tuple[int, int, int]],
        time_off_map: Dict[int, List[Tuple[date, date]]]
    ) -> np.ndarray:
        """
        Build availability matrix (employees × shifts).
        
        An employee is available for a shift if:
        1. They don't have approved time-off for that shift's date
        2. They're not already assigned to this shift (existing assignments)
        3. The shift doesn't overlap with another shift they're already assigned to
        4. They have at least one role matching the shift's requirements
        
        Args:
            employees: List of employee dictionaries
            shifts: List of shift dictionaries
            employee_index: Mapping of user_id -> array index
            shift_index: Mapping of shift_id -> array index
            existing_assignments: Set of (employee_id, shift_id, role_id) tuples
            time_off_map: Precomputed time-off map {user_id: [(start_date, end_date), ...]}
            
        Returns:
            2D numpy array where 1 = available, 0 = not available
        """
        n_employees = len(employees)
        n_shifts = len(shifts)
        availability = np.ones((n_employees, n_shifts), dtype=int)
        
        # Build set of (employee_id, shift_id) that are already assigned
        assigned_pairs = {(emp_id, shift_id) for (emp_id, shift_id, _) in existing_assignments}
        
        # Mark unavailable due to time-off
        for emp in employees:
            user_id = emp['user_id']
            emp_idx = employee_index[user_id]
            
            if user_id in time_off_map:
                for shift in shifts:
                    shift_idx = shift_index[shift['planned_shift_id']]
                    shift_date = shift['date']
                    
                    # Check if shift date falls within any time-off period
                    for start_date, end_date in time_off_map[user_id]:
                        if start_date <= shift_date <= end_date:
                            availability[emp_idx, shift_idx] = 0
                            break
        
        # Mark unavailable if already assigned to this shift
        for emp in employees:
            user_id = emp['user_id']
            emp_idx = employee_index[user_id]
            
            for shift in shifts:
                shift_id = shift['planned_shift_id']
                shift_idx = shift_index[shift_id]
                
                if (user_id, shift_id) in assigned_pairs:
                    availability[emp_idx, shift_idx] = 0
        
        # Mark unavailable if employee doesn't have required roles
        for emp in employees:
            user_id = emp['user_id']
            emp_idx = employee_index[user_id]
            emp_role_set = set(emp['roles'])
            
            for shift in shifts:
                shift_idx = shift_index[shift['planned_shift_id']]
                required_role_ids = [req['role_id'] for req in shift['required_roles']]
                
                # If shift requires roles and employee has none of them, mark unavailable
                if required_role_ids:
                    has_required_role = any(role_id in emp_role_set for role_id in required_role_ids)
                    if not has_required_role:
                        availability[emp_idx, shift_idx] = 0
        
        return availability
    
    def build_preference_scores(
        self,
        employees: List[Dict],
        shifts: List[Dict],
        employee_index: Dict[int, int],
        shift_index: Dict[int, int]
    ) -> np.ndarray:
        """
        Build preference scores matrix (employees × shifts).
        
        Preference scores are calculated based on:
        1. Preferred shift template matches
        2. Preferred day of week matches
        3. Preferred time range overlaps
        4. Weighted by preference_weight
        
        Score range: 0.0 (no preference/dislike) to 1.0 (strong preference)
        Default score: 0.5 (neutral)
        
        Args:
            employees: List of employee dictionaries
            shifts: List of shift dictionaries
            employee_index: Mapping of user_id -> array index
            shift_index: Mapping of shift_id -> array index
            
        Returns:
            2D numpy array of preference scores
        """
        n_employees = len(employees)
        n_shifts = len(shifts)
        preferences = np.full((n_employees, n_shifts), 0.5, dtype=float)  # Default neutral
        
        # Get all employee preferences
        all_preferences = self.db.query(EmployeePreferencesModel).all()
        
        # Build preference mapping: user_id -> list of preferences
        pref_map = {}
        for pref in all_preferences:
            if pref.user_id not in pref_map:
                pref_map[pref.user_id] = []
            pref_map[pref.user_id].append(pref)
        
        # Calculate preference scores
        for emp in employees:
            user_id = emp['user_id']
            emp_idx = employee_index[user_id]
            
            if user_id not in pref_map:
                continue  # No preferences, use default 0.5
            
            for shift in shifts:
                shift_idx = shift_index[shift['planned_shift_id']]
                shift_template_id = shift['shift_template_id']
                shift_date = shift['date']
                shift_day_of_week = self._date_to_day_of_week(shift_date)
                shift_start_time = shift['start_time'].time() if isinstance(shift['start_time'], datetime) else shift['start_time']
                shift_end_time = shift['end_time'].time() if isinstance(shift['end_time'], datetime) else shift['end_time']
                
                # Aggregate all matching preferences
                total_score = 0.0
                total_weight = 0.0
                
                for pref in pref_map[user_id]:
                    score = 0.0
                    
                    # Check shift template match
                    if pref.preferred_shift_template_id == shift_template_id:
                        score = 1.0
                    # Check day of week match
                    elif pref.preferred_day_of_week and pref.preferred_day_of_week.value == shift_day_of_week:
                        score = 0.8
                    # Check time range overlap
                    elif pref.preferred_start_time and pref.preferred_end_time:
                        overlap = self._calculate_time_overlap(
                            pref.preferred_start_time,
                            pref.preferred_end_time,
                            shift_start_time,
                            shift_end_time
                        )
                        if overlap > 0:
                            score = 0.6 * overlap  # Scale by overlap percentage
                    
                    # Weight the score by preference weight
                    if score > 0:
                        total_score += score * pref.preference_weight
                        total_weight += pref.preference_weight
                
                # Calculate weighted average
                if total_weight > 0:
                    preferences[emp_idx, shift_idx] = min(total_score / total_weight, 1.0)
        
        return preferences
    
    def detect_shift_overlaps(
        self,
        shifts: List[Dict],
        shift_index: Dict[int, int]
    ) -> Dict[int, List[int]]:
        """
        Detect overlapping shifts.
        
        Uses improved overlap detection from precompute module that handles:
        - Full datetime comparison (date + time)
        - Overnight shifts (end_time < start_time means end is next day)
        - Cross-day overlaps
        
        Args:
            shifts: List of shift dictionaries
            shift_index: Mapping of shift_id -> array index (unused but kept for compatibility)
            
        Returns:
            Dictionary mapping shift_id -> list of overlapping shift_ids
        """
        # Use improved overlap detection from precompute module
        overlaps_set = build_shift_overlaps(shifts)
        
        # Convert sets to lists for backward compatibility
        overlaps = {shift_id: list(overlapping_ids) for shift_id, overlapping_ids in overlaps_set.items()}
        
        # Ensure all shifts have an entry (even if empty)
        for shift in shifts:
            shift_id = shift['planned_shift_id']
            if shift_id not in overlaps:
                overlaps[shift_id] = []
        
        return overlaps
    
    # Helper methods
    
    def _date_to_day_of_week(self, date) -> str:
        """Convert date to day of week string (MONDAY, TUESDAY, etc.)."""
        day_names = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']
        return day_names[date.weekday()]
    
    def _calculate_time_overlap(
        self, 
        pref_start: time, 
        pref_end: time, 
        shift_start: time, 
        shift_end: time
    ) -> float:
        """
        Calculate the percentage overlap between preferred time and shift time.
        Handles overnight time ranges (end < start).
        
        Returns:
            Overlap percentage (0.0 to 1.0)
        """
        # Convert times to minutes since midnight for easier calculation
        def time_to_minutes(t: time) -> int:
            return t.hour * 60 + t.minute
        
        pref_start_min = time_to_minutes(pref_start)
        pref_end_min = time_to_minutes(pref_end)
        shift_start_min = time_to_minutes(shift_start)
        shift_end_min = time_to_minutes(shift_end)
        
        # Handle overnight ranges: if end < start, end is next day (add 24*60 minutes)
        if pref_end < pref_start:
            pref_end_min += 24 * 60
        if shift_end < shift_start:
            shift_end_min += 24 * 60
        
        # Calculate overlap
        overlap_start = max(pref_start_min, shift_start_min)
        overlap_end = min(pref_end_min, shift_end_min)
        
        if overlap_start >= overlap_end:
            return 0.0
        
        overlap_duration = overlap_end - overlap_start
        shift_duration = shift_end_min - shift_start_min
        
        if shift_duration == 0:
            return 0.0
        
        return min(overlap_duration / shift_duration, 1.0)

