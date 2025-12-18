"""
Optimization Data Builder service.

This module contains the OptimizationDataBuilder service that transforms database
entities into structured data for MIP model building. It extracts employees, shifts,
role requirements, availability, and overlap information needed for optimization.
"""

from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.userModel import UserModel
from app.db.models.plannedShiftModel import PlannedShiftModel, PlannedShiftStatus
from app.db.models.shiftRoleRequirementsTabel import shift_role_requirements
from app.db.models.timeOffRequestModel import TimeOffRequestModel, TimeOffRequestStatus
from app.db.models.shiftAssignmentModel import ShiftAssignmentModel


class OptimizationData:
    """
    Data structure for optimization input.
    
    This class holds all the structured data needed to build a MIP model.
    """
    
    def __init__(self):
        # List of eligible employees with their roles
        self.employees: List[Dict] = []  # [{user_id, name, role_ids: [1, 2, ...]}]
        
        # List of planned shifts
        self.shifts: List[Dict] = []  # [{shift_id, date, start_time, end_time, template_id, location}]
        
        # Role requirements per shift: {shift_id: {role_id: required_count}}
        self.role_requirements: Dict[int, Dict[int, int]] = {}
        
        # Available pairs: {(employee_id, shift_id)} - only stores available assignments
        self.available_pairs: Set[Tuple[int, int]] = set()
        
        # Shift overlaps: {shift_id: {overlapping_shift_ids}}
        self.shift_overlaps: Dict[int, Set[int]] = {}
        
        # Time-off conflicts: {employee_id: [shift_ids]}
        self.time_off_conflicts: Dict[int, List[int]] = {}
        
        # Existing assignments: {(employee_id, shift_id, role_id): bool}
        self.existing_assignments: Set[Tuple[int, int, int]] = set()


class OptimizationDataBuilder:
    """
    Service for building optimization data from database entities.
    
    This service extracts and transforms database data into structured formats
    suitable for MIP model construction.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the data builder with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def prepare_optimization_data(self, weekly_schedule_id: int) -> OptimizationData:
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
        
        data.employees = self.build_employee_set()
        data.shifts = self.build_shift_set(weekly_schedule_id)
        data.role_requirements = self.build_role_requirements(data.shifts)
        
        # Build these first as they're needed for availability checks
        data.shift_overlaps = self.build_shift_overlaps(data.shifts)
        data.existing_assignments = self.build_existing_assignments(weekly_schedule_id)
        
        # Compute schedule date range to filter time-off requests
        schedule_min_date = min(shift["date"] for shift in data.shifts) if data.shifts else None
        schedule_max_date = max(shift["date"] for shift in data.shifts) if data.shifts else None
        
        # Build time-off map once, reused in availability and conflicts
        time_off_map = self._build_time_off_map(schedule_min_date, schedule_max_date)
        
        data.available_pairs = self.build_available_pairs(
            data.employees,
            data.shifts,
            data.role_requirements,
            time_off_map,
            data.existing_assignments,
            data.shift_overlaps
        )
        
        data.time_off_conflicts = self.build_time_off_conflicts(
            data.employees, data.shifts, time_off_map
        )
        
        return data
    
    def build_employee_set(self) -> List[Dict]:
        """
        Extract eligible employees (active, with at least one role).
        
        Returns:
            List of employee dictionaries with user_id, name, and role_ids
        """
        employees = (
            self.db.query(UserModel)
            .join(UserModel.roles)
            .distinct()
            .all()
        )
        
        employee_list = []
        for emp in employees:
            role_ids = [role.role_id for role in emp.roles]
            if role_ids:  # Only include employees with roles
                employee_list.append({
                    "user_id": emp.user_id,
                    "name": emp.user_full_name,
                    "role_ids": role_ids
                })
        
        return employee_list
    
    def build_shift_set(self, weekly_schedule_id: int) -> List[Dict]:
        """
        Extract planned shifts from a weekly schedule.
        
        Only includes shifts that are not cancelled.
        
        Args:
            weekly_schedule_id: ID of the weekly schedule
            
        Returns:
            List of shift dictionaries with shift_id, date, start_time, end_time, etc.
        """
        shifts = (
            self.db.query(PlannedShiftModel)
            .filter(
                PlannedShiftModel.weekly_schedule_id == weekly_schedule_id,
                PlannedShiftModel.status != PlannedShiftStatus.CANCELLED
            )
            .order_by(PlannedShiftModel.date, PlannedShiftModel.start_time)
            .all()
        )
        
        shift_list = []
        for shift in shifts:
            shift_list.append({
                "shift_id": shift.planned_shift_id,
                "date": shift.date,
                "start_time": shift.start_time,
                "end_time": shift.end_time,
                "template_id": shift.shift_template_id,
                "location": shift.location,
                "status": shift.status.value
            })
        
        return shift_list
    
    def build_role_requirements(self, shifts: List[Dict]) -> Dict[int, Dict[int, int]]:
        """
        Build role requirements mapping: {shift_id: {role_id: required_count}}.
        
        Optimized: Fetches all template requirements in a single query.
        Reuses pre-loaded shifts instead of querying the database again.
        
        Args:
            shifts: List of shift dictionaries (from build_shift_set)
            
        Returns:
            Dictionary mapping shift_id to role requirements
        """
        if not shifts:
            return {}
        
        template_ids = {shift["template_id"] for shift in shifts}
        
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
        
        # Map shifts to their role requirements
        requirements = {}
        for shift in shifts:
            template_id = shift["template_id"]
            if template_id in template_role_map:
                requirements[shift["shift_id"]] = template_role_map[template_id]
        
        return requirements
    
    def build_available_pairs(
        self,
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
    
    def build_shift_overlaps(self, shifts: List[Dict]) -> Dict[int, Set[int]]:
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
                
                if self._shifts_overlap(shift1, shift2):
                    shift_overlaps[shift_id1].add(shift_id2)
                    # Initialize set for shift2 if not exists
                    if shift_id2 not in shift_overlaps:
                        shift_overlaps[shift_id2] = set()
                    shift_overlaps[shift_id2].add(shift_id1)
        
        return shift_overlaps
    
    def build_time_off_conflicts(
        self,
        employees: List[Dict],
        shifts: List[Dict],
        time_off_map: Dict[int, List[Tuple[date, date]]]
    ) -> Dict[int, List[int]]:
        """
        Build time-off conflicts: {employee_id: [conflicting_shift_ids]}.
        
        Args:
            employees: List of employee dictionaries
            shifts: List of shift dictionaries
            time_off_map: Precomputed time-off map {user_id: [(start_date, end_date), ...]}
            
        Returns:
            Dictionary mapping employee_id to list of conflicting shift IDs
        """
        conflicts = {}
        
        for emp in employees:
            emp_id = emp["user_id"]
            conflicting_shifts = []
            
            # Find time-off periods for this employee
            if emp_id in time_off_map:
                for start_date, end_date in time_off_map[emp_id]:
                    # Find shifts that fall within this time-off period
                    for shift in shifts:
                        shift_date = shift["date"]
                        if start_date <= shift_date <= end_date:
                            if shift["shift_id"] not in conflicting_shifts:
                                conflicting_shifts.append(shift["shift_id"])
            
            if conflicting_shifts:
                conflicts[emp_id] = conflicting_shifts
        
        return conflicts
    
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
    
    def _shifts_overlap(self, shift1: Dict, shift2: Dict) -> bool:
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

