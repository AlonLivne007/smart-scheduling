"""
Optimization Data Builder service.

This module is responsible for orchestration and data extraction.
It uses repositories for all database access - no direct ORM access.
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from datetime import date, datetime
import numpy as np

from app.data.repositories.user_repository import UserRepository
from app.data.repositories.shift_repository import ShiftRepository, ShiftAssignmentRepository
from app.data.repositories import RoleRepository
from app.data.repositories.weekly_schedule_repository import WeeklyScheduleRepository
from app.data.repositories.time_off_request_repository import TimeOffRequestRepository
from app.data.repositories.system_constraints_repository import SystemConstraintsRepository
from app.data.repositories.employee_preferences_repository import EmployeePreferencesRepository
from app.data.repositories import ShiftTemplateRepository

from app.services.optimization_data_services.optimization_data import OptimizationData
from app.services.optimization_data_services.optimization_precompute import (
    build_shift_durations,
    build_time_off_conflicts,
    build_rest_conflicts,
)
from app.services.utils.overlap_utils import build_shift_overlaps
from app.data.models.system_constraints_model import SystemConstraintType
from app.data.models.planned_shift_model import PlannedShiftStatus


class OptimizationDataBuilder:
    """
    Service for building optimization data from database entities.
    
    This service uses repositories to access the database instead of direct
    SQLAlchemy queries. It orchestrates data extraction and transformation
    to build a complete OptimizationData object suitable for MIP model construction.
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        shift_repository: ShiftRepository,
        assignment_repository: ShiftAssignmentRepository,
        role_repository: RoleRepository,
        template_repository: ShiftTemplateRepository,
        schedule_repository: WeeklyScheduleRepository,
        time_off_repository: TimeOffRequestRepository,
        constraints_repository: SystemConstraintsRepository,
        preferences_repository: EmployeePreferencesRepository
    ):
        """
        Initialize the data builder with repositories.
        
        Args:
            user_repository: UserRepository instance
            shift_repository: ShiftRepository instance
            assignment_repository: ShiftAssignmentRepository instance
            role_repository: RoleRepository instance
            template_repository: ShiftTemplateRepository instance
            schedule_repository: WeeklyScheduleRepository instance
            time_off_repository: TimeOffRequestRepository instance
            constraints_repository: SystemConstraintsRepository instance
            preferences_repository: EmployeePreferencesRepository instance
        """
        self.user_repository = user_repository
        self.shift_repository = shift_repository
        self.assignment_repository = assignment_repository
        self.role_repository = role_repository
        self.template_repository = template_repository
        self.schedule_repository = schedule_repository
        self.time_off_repository = time_off_repository
        self.constraints_repository = constraints_repository
        self.preferences_repository = preferences_repository
    
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
        self._verify_weekly_schedule(weekly_schedule_id)
        
        # Extract base data from database using repositories
        data.employees, data.shifts, data.roles = self._extract_base_data(weekly_schedule_id)
        
        # Build index mappings
        data.employee_index, data.shift_index = self._build_indices(data.employees, data.shifts)
        
        # Build role mappings
        data.role_requirements = self.build_role_requirements(data.shifts)
        data.employee_roles = self.build_employee_roles(data.employees)
        
        # Build existing assignments (for preserving preferred assignments)
        data.existing_assignments = self.build_existing_assignments(weekly_schedule_id)
        
        # Build matrices and constraints
        time_off_map = self._build_time_off_map_for_schedule(data.shifts)
        data.availability_matrix, data.preference_scores = self._build_matrices(
            data.employees, data.shifts, data.employee_index, data.shift_index,
            data.existing_assignments, time_off_map
        )
        
        # Build constraints and conflicts
        data.shift_overlaps, data.shift_durations, data.system_constraints, \
        data.time_off_conflicts, data.shift_rest_conflicts = self._build_constraints_and_conflicts(
            data.employees, data.shifts, data.shift_index, time_off_map
        )
        
        return data
    
    def _verify_weekly_schedule(self, weekly_schedule_id: int) -> None:
        """
        Verify that the weekly schedule exists.
        
        Args:
            weekly_schedule_id: ID of the weekly schedule
            
        Raises:
            ValueError: If schedule not found
        """
        schedule = self.schedule_repository.get_by_id(weekly_schedule_id)
        if not schedule:
            raise ValueError(f"Weekly schedule {weekly_schedule_id} not found")
    
    def _extract_base_data(
        self,
        weekly_schedule_id: int
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Extract base data from database: employees, shifts, and roles.
        
        Uses repositories for all database access.
        
        Args:
            weekly_schedule_id: ID of the weekly schedule
            
        Returns:
            Tuple of (employees, shifts, roles)
            
        Raises:
            ValueError: If no employees or shifts found
        """
        employees = self.build_employee_set()
        shifts = self.build_shift_set(weekly_schedule_id)
        roles = self.build_role_set()
        
        if not employees:
            raise ValueError("No eligible employees found")
        
        if not shifts:
            raise ValueError(f"No planned shifts found for weekly schedule {weekly_schedule_id}")
        
        return employees, shifts, roles
    
    def _build_indices(
        self,
        employees: List[Dict[str, Any]],
        shifts: List[Dict[str, Any]]
    ) -> Tuple[Dict[int, int], Dict[int, int]]:
        """
        Build index mappings for employees and shifts.
        
        Args:
            employees: List of employee dictionaries
            shifts: List of shift dictionaries
        
        Returns:
            Tuple of (employee_index, shift_index)
        """
        employee_index = {emp['user_id']: idx for idx, emp in enumerate(employees)}
        shift_index = {shift['planned_shift_id']: idx for idx, shift in enumerate(shifts)}
        return employee_index, shift_index
    
    def _build_matrices(
        self,
        employees: List[Dict],
        shifts: List[Dict],
        employee_index: Dict[int, int],
        shift_index: Dict[int, int],
        existing_assignments: Set[Tuple[int, int, int]],
        time_off_map: Dict[int, List[Tuple[date, date]]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Build availability and preference score matrices.
        
        Args:
            employees: List of employee dictionaries
            shifts: List of shift dictionaries
            employee_index: Mapping of user_id -> array index
            shift_index: Mapping of shift_id -> array index
            existing_assignments: Set of (employee_id, shift_id, role_id) tuples
            time_off_map: Precomputed time-off map
        
        Returns:
            Tuple of (availability_matrix, preference_scores)
        """
        availability_matrix = self.build_availability_matrix(
            employees, shifts, employee_index, shift_index,
            existing_assignments, time_off_map
        )
        
        preference_scores = self.build_preference_scores(
            employees, shifts, employee_index, shift_index
        )
        
        return availability_matrix, preference_scores
    
    def _build_time_off_map_for_schedule(
        self,
        shifts: List[Dict[str, Any]]
    ) -> Dict[int, List[Tuple[date, date]]]:
        """
        Build time-off map for the schedule date range.
        
        Args:
            shifts: List of shift dictionaries
        
        Returns:
            Dictionary mapping user_id to list of time-off date ranges
        """
        # Compute schedule date range to filter time-off requests
        schedule_min_date = min(shift['date'] for shift in shifts) if shifts else None
        schedule_max_date = max(shift['date'] for shift in shifts) if shifts else None
        
        return self._build_time_off_map(schedule_min_date, schedule_max_date)
    
    def _build_constraints_and_conflicts(
        self,
        employees: List[Dict],
        shifts: List[Dict],
        shift_index: Dict[int, int],
        time_off_map: Dict[int, List[Tuple[date, date]]]
    ) -> Tuple[Dict[int, List[int]], Dict[int, float], Dict, Dict[int, List[int]], Dict[int, Set[int]]]:
        """
        Build all constraints and conflict mappings.
        
        Args:
            employees: List of employee dictionaries
            shifts: List of shift dictionaries
            shift_index: Mapping of shift_id -> array index
            time_off_map: Precomputed time-off map
        
        Returns:
            Tuple of (shift_overlaps, shift_durations, system_constraints,
                     time_off_conflicts, shift_rest_conflicts)
        """
        # Detect shift overlaps (using improved overlap detection)
        shift_overlaps = self.detect_shift_overlaps(shifts, shift_index)
        
        # Build shift durations (needed for max-hours and workload fairness constraints)
        shift_durations = build_shift_durations(shifts)
        
        # Build system constraints (loads once to keep MIP builder clean)
        system_constraints = self.build_system_constraints()
        
        # Build time-off conflicts
        time_off_conflicts = build_time_off_conflicts(employees, shifts, time_off_map)
        
        # Build rest conflicts for MIN_REST_HOURS constraint
        min_rest_constraint = system_constraints.get(SystemConstraintType.MIN_REST_HOURS)
        if min_rest_constraint and min_rest_constraint[1]:  # is_hard
            min_rest_hours = min_rest_constraint[0]
            shift_rest_conflicts = build_rest_conflicts(shifts, min_rest_hours)
        else:
            shift_rest_conflicts = {}
        
        return shift_overlaps, shift_durations, system_constraints, \
               time_off_conflicts, shift_rest_conflicts
    
    def build_employee_set(self) -> List[Dict[str, Any]]:
        """
        Extract eligible employees (active, with at least one role).
        
        Uses UserRepository for database access.
        
        Returns:
            List of employee dictionaries with user_id, name, email, roles
        """
        employees = self.user_repository.get_active_users()
        
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
        
        Uses ShiftRepository and ShiftTemplateRepository for database access.
        
        Args:
            weekly_schedule_id: ID of the weekly schedule
            
        Returns:
            List of shift dictionaries with shift details and requirements
        """
        shifts = self.shift_repository.get_by_schedule(weekly_schedule_id)
        
        # Filter out cancelled shifts
        active_shifts = [s for s in shifts if s.status != PlannedShiftStatus.CANCELLED]
        
        # Fetch template role map for all templates in one batch
        template_ids = {shift.shift_template_id for shift in active_shifts if shift.shift_template_id}
        template_role_map = self._fetch_template_role_map(template_ids)
        
        shift_list = []
        for shift in active_shifts:
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
        Fetch template role requirements mapping.
        
        Uses ShiftTemplateRepository for database access.
        
        Args:
            template_ids: Set of template IDs to fetch requirements for
            
        Returns:
            Dictionary mapping template_id to {role_id: required_count}
        """
        if not template_ids:
            return {}
        
        # Use repository method to get role requirements with counts
        return self.template_repository.get_role_requirements_with_counts(list(template_ids))
    
    def build_role_set(self) -> List[Dict[str, Any]]:
        """
        Extract all roles in the system.
        
        Uses RoleRepository for database access.
        
        Returns:
            List of role dictionaries with role_id and role_name
        """
        roles = self.role_repository.get_all()
        
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
    
    def build_employee_roles(self, employees: List[Dict[str, Any]]) -> Dict[int, List[int]]:
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
        
        Uses ShiftRepository and ShiftAssignmentRepository for database access.
        
        Args:
            weekly_schedule_id: ID of the weekly schedule
            
        Returns:
            Set of tuples (employee_id, shift_id, role_id)
        """
        # Get all shifts for this schedule
        shifts = self.shift_repository.get_by_schedule(weekly_schedule_id)
        shift_ids = [s.planned_shift_id for s in shifts]
        
        if not shift_ids:
            return set()
        
        # Get all assignments for these shifts
        assignment_set = set()
        for shift_id in shift_ids:
            assignments = self.assignment_repository.get_by_shift(shift_id)
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
        
        Uses SystemConstraintsRepository for database access.
        
        Returns:
            Dictionary mapping constraint type to (value, is_hard) tuple
        """
        constraints = self.constraints_repository.get_all()
        
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
        
        Uses TimeOffRequestRepository for database access.
        
        Args:
            schedule_min_date: Minimum date in the schedule (None if no shifts)
            schedule_max_date: Maximum date in the schedule (None if no shifts)
            
        Returns:
            Dictionary mapping user_id to list of time-off date ranges
        """
        if schedule_min_date is None or schedule_max_date is None:
            return {}
        
        # Get approved time-off requests in date range
        time_off_requests = self.time_off_repository.get_approved_in_date_range(
            schedule_min_date,
            schedule_max_date
        )
        
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
        Build availability matrix: availability[i, j] = 1 if employee i can work shift j.
        
        Args:
            employees: List of employee dictionaries
            shifts: List of shift dictionaries
            employee_index: Mapping of user_id -> array index
            shift_index: Mapping of shift_id -> array index
            existing_assignments: Set of (employee_id, shift_id, role_id) tuples
            time_off_map: Precomputed time-off map
        
        Returns:
            NumPy array of shape (num_employees, num_shifts)
        """
        num_employees = len(employees)
        num_shifts = len(shifts)
        availability = np.zeros((num_employees, num_shifts), dtype=int)
        
        for shift_idx, shift in enumerate(shifts):
            shift_date = shift['date']
            shift_id = shift['planned_shift_id']
            
            for emp_idx, emp in enumerate(employees):
                user_id = emp['user_id']
                
                # Check time-off conflicts
                has_time_off = False
                if user_id in time_off_map:
                    for start_date, end_date in time_off_map[user_id]:
                        if start_date <= shift_date <= end_date:
                            has_time_off = True
                            break
                
                if not has_time_off:
                    availability[emp_idx, shift_idx] = 1
        
        return availability
    
    def build_preference_scores(
        self,
        employees: List[Dict],
        shifts: List[Dict],
        employee_index: Dict[int, int],
        shift_index: Dict[int, int]
    ) -> np.ndarray:
        """
        Build preference score matrix.
        
        Uses EmployeePreferencesRepository for database access.
        
        Args:
            employees: List of employee dictionaries
            shifts: List of shift dictionaries
            employee_index: Mapping of user_id -> array index
            shift_index: Mapping of shift_id -> array index
        
        Returns:
            NumPy array of shape (num_employees, num_shifts) with preference scores
        """
        num_employees = len(employees)
        num_shifts = len(shifts)
        preference_scores = np.zeros((num_employees, num_shifts), dtype=float)
        
        # Get all preferences for all employees
        all_user_ids = [emp['user_id'] for emp in employees]
        all_preferences = []
        for user_id in all_user_ids:
            user_prefs = self.preferences_repository.get_by_user(user_id)
            all_preferences.extend(user_prefs)
        
        # Build preference map
        for pref in all_preferences:
            user_id = pref.user_id
            if user_id not in employee_index:
                continue
            
            emp_idx = employee_index[user_id]
            
            # Check if preference matches shift
            for shift_idx, shift in enumerate(shifts):
                score = 0.0
                
                # Check template match
                if pref.preferred_shift_template_id and shift['shift_template_id']:
                    if pref.preferred_shift_template_id == shift['shift_template_id']:
                        score += pref.preference_weight * 0.5
                
                # Check day of week match
                if pref.preferred_day_of_week:
                    shift_day = shift['date'].strftime('%A').upper()
                    if pref.preferred_day_of_week.value == shift_day:
                        score += pref.preference_weight * 0.3
                
                # Check time range match
                if pref.preferred_start_time and pref.preferred_end_time:
                    shift_start = shift['start_time'].time() if isinstance(shift['start_time'], datetime) else shift['start_time']
                    shift_end = shift['end_time'].time() if isinstance(shift['end_time'], datetime) else shift['end_time']
                    
                    if (pref.preferred_start_time <= shift_start <= pref.preferred_end_time or
                        pref.preferred_start_time <= shift_end <= pref.preferred_end_time):
                        score += pref.preference_weight * 0.2
                
                preference_scores[emp_idx, shift_idx] = max(preference_scores[emp_idx, shift_idx], score)
        
        return preference_scores
    
    def detect_shift_overlaps(
        self,
        shifts: List[Dict],
        shift_index: Dict[int, int]
    ) -> Dict[int, List[int]]:
        """
        Detect overlapping shifts.
        
        Uses overlap utility functions.
        
        Args:
            shifts: List of shift dictionaries
            shift_index: Mapping of shift_id -> array index (not used, kept for compatibility)
        
        Returns:
            Dictionary mapping shift_id -> list of overlapping shift_ids
        """
        return build_shift_overlaps(shifts)
