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

from app.db.models.userModel import UserModel
from app.db.models.plannedShiftModel import PlannedShiftModel, PlannedShiftStatus
from app.db.models.shiftRoleRequirementsTabel import shift_role_requirements
from app.db.models.timeOffRequestModel import TimeOffRequestModel, TimeOffRequestStatus
from app.db.models.shiftAssignmentModel import ShiftAssignmentModel
from app.db.models.systemConstraintsModel import SystemConstraintsModel, SystemConstraintType

from app.services.optimization_data_services.optimization_data import OptimizationData
from app.services.optimization_data_services.optimization_precompute import (
    build_role_requirements,
    build_shift_overlaps,
    build_shift_durations,
    build_available_pairs,
    build_eligible_roles,
    build_time_off_conflicts,
    build_fixed_assignments,
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
        
        # Load data from database
        data.employees = self.build_employee_set()
        data.shifts = self.build_shift_set(weekly_schedule_id)
        data.existing_assignments = self.build_existing_assignments(weekly_schedule_id)
        
        # Fetch template role map for role requirements computation
        template_role_map = self._fetch_template_role_map(data.shifts)
        
        # Precompute derived data (no DB queries)
        data.role_requirements = build_role_requirements(data.shifts, template_role_map)
        data.shift_overlaps = build_shift_overlaps(data.shifts)
        
        # Compute schedule date range to filter time-off requests
        schedule_min_date = min(shift["date"] for shift in data.shifts) if data.shifts else None
        schedule_max_date = max(shift["date"] for shift in data.shifts) if data.shifts else None
        
        # Build time-off map once, reused in availability and conflicts
        time_off_map = self._build_time_off_map(schedule_min_date, schedule_max_date)
        
        # Precompute availability and related data
        data.available_pairs = build_available_pairs(
            data.employees,
            data.shifts,
            data.role_requirements,
            time_off_map,
            data.existing_assignments,
            data.shift_overlaps
        )
        
        # Build eligible roles for available pairs (for optimization variables)
        data.eligible_roles = build_eligible_roles(
            data.employees,
            data.shifts,
            data.role_requirements,
            data.available_pairs
        )
        
        # Build shift durations (needed for max-hours and workload fairness constraints)
        data.shift_durations = build_shift_durations(data.shifts)
        
        # Build fixed assignments mapping (for MIP variable fixing)
        data.fixed_assignments = build_fixed_assignments(data.existing_assignments)
        
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
    
    def _fetch_template_role_map(self, shifts: List[Dict]) -> Dict[int, Dict[int, int]]:
        """
        Fetch template role requirements mapping from database.
        
        Fetches all role requirements for all templates in a single query.
        
        Args:
            shifts: List of shift dictionaries
            
        Returns:
            Dictionary mapping template_id to {role_id: required_count}
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
        
        return template_role_map

