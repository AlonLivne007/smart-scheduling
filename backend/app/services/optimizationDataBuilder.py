"""
Optimization Data Builder Service.

This service extracts and prepares all scheduling data from the database
for the MIP solver. It builds employees sets, shift sets, availability matrices,
preference scores, and detects shift overlaps.
"""

from typing import Dict, List, Tuple, Set
from datetime import datetime, time, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import numpy as np

from app.db.models.userModel import UserModel
from app.db.models.plannedShiftModel import PlannedShiftModel, PlannedShiftStatus
from app.db.models.roleModel import RoleModel
from app.db.models.weeklyScheduleModel import WeeklyScheduleModel
from app.db.models.employeePreferencesModel import EmployeePreferencesModel, DayOfWeek
from app.db.models.timeOffRequestModel import TimeOffRequestModel, TimeOffRequestStatus
from app.db.models.shiftTemplateModel import ShiftTemplateModel


class OptimizationData:
    """
    Data class to hold all extracted optimization data.
    
    Attributes:
        employees: List of eligible employee dictionaries
        shifts: List of planned shift dictionaries
        roles: List of role dictionaries
        availability_matrix: 2D numpy array (employees × shifts) - 1 if available, 0 if not
        preference_scores: 2D numpy array (employees × shifts) - preference score 0.0-1.0
        role_requirements: Dictionary mapping shift_id -> List of required role_ids
        employee_roles: Dictionary mapping user_id -> List of role_ids
        shift_overlaps: Dictionary mapping shift_id -> List of overlapping shift_ids
        employee_index: Dictionary mapping user_id -> array index
        shift_index: Dictionary mapping planned_shift_id -> array index
    """
    
    def __init__(self):
        self.employees: List[Dict] = []
        self.shifts: List[Dict] = []
        self.roles: List[Dict] = []
        self.availability_matrix: np.ndarray = None
        self.preference_scores: np.ndarray = None
        self.role_requirements: Dict[int, List[int]] = {}
        self.employee_roles: Dict[int, List[int]] = {}
        self.shift_overlaps: Dict[int, List[int]] = {}
        self.employee_index: Dict[int, int] = {}
        self.shift_index: Dict[int, int] = {}


class OptimizationDataBuilder:
    """
    Service to build optimization data from database for MIP solver.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the data builder.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def build(self, weekly_schedule_id: int) -> OptimizationData:
        """
        Build complete optimization data for a weekly schedule.
        
        This is the main entry point that orchestrates all data extraction
        and matrix building.
        
        Args:
            weekly_schedule_id: ID of the weekly schedule to optimize
            
        Returns:
            OptimizationData object with all extracted data and matrices
            
        Raises:
            ValueError: If weekly schedule not found or has no shifts
        """
        data = OptimizationData()
        
        # Verify weekly schedule exists
        weekly_schedule = self.db.query(WeeklyScheduleModel).filter(
            WeeklyScheduleModel.weekly_schedule_id == weekly_schedule_id
        ).first()
        
        if not weekly_schedule:
            raise ValueError(f"Weekly schedule {weekly_schedule_id} not found")
        
        # Build basic sets
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
        
        # Build matrices
        data.availability_matrix = self.build_availability_matrix(
            data.employees, data.shifts, data.employee_index, data.shift_index
        )
        
        data.preference_scores = self.build_preference_scores(
            data.employees, data.shifts, data.employee_index, data.shift_index
        )
        
        # Detect shift overlaps
        data.shift_overlaps = self.detect_shift_overlaps(data.shifts, data.shift_index)
        
        return data
    
    def build_employee_set(self) -> List[Dict]:
        """
        Extract eligible employees (active status with at least one role).
        
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
        
        Args:
            weekly_schedule_id: ID of the weekly schedule
            
        Returns:
            List of shift dictionaries with shift details and requirements
        """
        shifts = self.db.query(PlannedShiftModel).filter(
            PlannedShiftModel.weekly_schedule_id == weekly_schedule_id,
            PlannedShiftModel.status != PlannedShiftStatus.CANCELLED
        ).all()
        
        # Import the association table to query role requirements
        from app.db.models.shiftRoleRequirementsTabel import shift_role_requirements
        
        shift_list = []
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
            
            # Query role requirements from association table
            if shift.shift_template_id:
                role_reqs = self.db.execute(
                    shift_role_requirements.select().where(
                        shift_role_requirements.c.shift_template_id == shift.shift_template_id
                    )
                ).fetchall()
                
                for req in role_reqs:
                    shift_dict['required_roles'].append({
                        'role_id': req.role_id,
                        'required_count': req.required_count
                    })
            
            shift_list.append(shift_dict)
        
        return shift_list
    
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
    
    def build_availability_matrix(
        self, 
        employees: List[Dict], 
        shifts: List[Dict],
        employee_index: Dict[int, int],
        shift_index: Dict[int, int]
    ) -> np.ndarray:
        """
        Build availability matrix (employees × shifts).
        
        An employee is available for a shift if:
        1. They don't have approved time-off for that shift's date
        2. The shift doesn't overlap with another shift they're already assigned to
        3. They have at least one role matching the shift's requirements
        
        Args:
            employees: List of employee dictionaries
            shifts: List of shift dictionaries
            employee_index: Mapping of user_id -> array index
            shift_index: Mapping of shift_id -> array index
            
        Returns:
            2D numpy array where 1 = available, 0 = not available
        """
        n_employees = len(employees)
        n_shifts = len(shifts)
        availability = np.ones((n_employees, n_shifts), dtype=int)
        
        # Get all approved time-off requests
        time_off_requests = self.db.query(TimeOffRequestModel).filter(
            TimeOffRequestModel.status == TimeOffRequestStatus.APPROVED
        ).all()
        
        # Build time-off mapping: user_id -> list of date ranges
        time_off_map = {}
        for request in time_off_requests:
            if request.user_id not in time_off_map:
                time_off_map[request.user_id] = []
            time_off_map[request.user_id].append({
                'start_date': request.start_date,
                'end_date': request.end_date
            })
        
        # Mark unavailable due to time-off
        for emp in employees:
            user_id = emp['user_id']
            emp_idx = employee_index[user_id]
            
            if user_id in time_off_map:
                for shift in shifts:
                    shift_idx = shift_index[shift['planned_shift_id']]
                    shift_date = shift['date']
                    
                    # Check if shift date falls within any time-off period
                    for time_off in time_off_map[user_id]:
                        if time_off['start_date'] <= shift_date <= time_off['end_date']:
                            availability[emp_idx, shift_idx] = 0
                            break
        
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
        
        Two shifts overlap if they occur on the same date and their
        time ranges overlap.
        
        Args:
            shifts: List of shift dictionaries
            shift_index: Mapping of shift_id -> array index
            
        Returns:
            Dictionary mapping shift_id -> list of overlapping shift_ids
        """
        overlaps = {shift['planned_shift_id']: [] for shift in shifts}
        
        for i, shift1 in enumerate(shifts):
            for j, shift2 in enumerate(shifts):
                if i >= j:  # Skip same shift and already compared pairs
                    continue
                
                # Check if shifts are on the same date
                if shift1['date'] != shift2['date']:
                    continue
                
                # Check if time ranges overlap
                start1 = shift1['start_time']
                end1 = shift1['end_time']
                start2 = shift2['start_time']
                end2 = shift2['end_time']
                
                # Convert datetime to time if needed
                if isinstance(start1, datetime):
                    start1 = start1.time()
                    end1 = end1.time()
                if isinstance(start2, datetime):
                    start2 = start2.time()
                    end2 = end2.time()
                
                # Check overlap
                if self._time_ranges_overlap(start1, end1, start2, end2):
                    overlaps[shift1['planned_shift_id']].append(shift2['planned_shift_id'])
                    overlaps[shift2['planned_shift_id']].append(shift1['planned_shift_id'])
        
        return overlaps
    
    # Helper methods
    
    def _date_to_day_of_week(self, date) -> str:
        """Convert date to day of week string (MONDAY, TUESDAY, etc.)."""
        day_names = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']
        return day_names[date.weekday()]
    
    def _time_ranges_overlap(self, start1: time, end1: time, start2: time, end2: time) -> bool:
        """
        Check if two time ranges overlap.
        
        Returns:
            True if ranges overlap, False otherwise
        """
        return start1 < end2 and start2 < end1
    
    def _calculate_time_overlap(
        self, 
        pref_start: time, 
        pref_end: time, 
        shift_start: time, 
        shift_end: time
    ) -> float:
        """
        Calculate the percentage overlap between preferred time and shift time.
        
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
