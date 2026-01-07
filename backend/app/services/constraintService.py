"""
Constraint Validation Service.

This service validates scheduling assignments against system constraints,
employee availability, time-off requests, and shift overlaps.
"""

from typing import Dict, List, Tuple, Set, Optional
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.models.userModel import UserModel
from app.db.models.plannedShiftModel import PlannedShiftModel
from app.db.models.shiftAssignmentModel import ShiftAssignmentModel
from app.db.models.timeOffRequestModel import TimeOffRequestModel, TimeOffRequestStatus
from app.db.models.systemConstraintsModel import SystemConstraintsModel, SystemConstraintType
from app.db.models.roleModel import RoleModel
from app.services.utils.datetime_utils import normalize_shift_datetimes
from app.services.utils.overlap_utils import shifts_overlap


class ValidationError:
    """Represents a constraint violation."""
    
    def __init__(self, constraint_type: str, severity: str, message: str, details: Dict = None):
        """
        Initialize validation error.
        
        Args:
            constraint_type: Type of constraint violated (e.g., "TIME_OFF", "AVAILABILITY")
            severity: "HARD" or "SOFT"
            message: Human-readable error message
            details: Additional context about the violation
        """
        self.constraint_type = constraint_type
        self.severity = severity
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'constraint_type': self.constraint_type,
            'severity': self.severity,
            'message': self.message,
            'details': self.details
        }
    
    def __repr__(self):
        return f"<ValidationError({self.severity}): {self.message}>"


class ValidationResult:
    """Result of constraint validation."""
    
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
    
    def add_error(self, error: ValidationError):
        """Add an error to the result."""
        if error.severity == "HARD":
            self.errors.append(error)
        else:
            self.warnings.append(error)
    
    def is_valid(self) -> bool:
        """Check if there are no hard constraint violations."""
        return len(self.errors) == 0
    
    def has_warnings(self) -> bool:
        """Check if there are soft constraint violations."""
        return len(self.warnings) > 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'is_valid': self.is_valid(),
            'has_warnings': self.has_warnings(),
            'errors': [e.to_dict() for e in self.errors],
            'warnings': [w.to_dict() for w in self.warnings]
        }
    
    def __repr__(self):
        return f"<ValidationResult(valid={self.is_valid()}, errors={len(self.errors)}, warnings={len(self.warnings)})>"


class ConstraintService:
    """Service for validating scheduling constraints."""
    
    def __init__(self, db: Session):
        """
        Initialize the constraint service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self._system_constraints_cache = None
    
    def _load_system_constraints(self):
        """
        Load system constraints from database (lazy loading).
        
        Constraints are cached per instance. Call refresh_constraints() to reload.
        """
        if self._system_constraints_cache is None:
            constraints = self.db.query(SystemConstraintsModel).all()
            self._system_constraints_cache = {
                c.constraint_type: {
                    'value': c.constraint_value,
                    'is_hard': c.is_hard_constraint
                }
                for c in constraints
            }
        return self._system_constraints_cache
    
    @property
    def system_constraints(self):
        """
        Get system constraints (lazy-loaded).
        
        Returns:
            Dictionary mapping constraint_type to {'value': float, 'is_hard': bool}
        """
        return self._load_system_constraints()
    
    def refresh_constraints(self):
        """
        Refresh system constraints from database.
        
        Use this method if constraints may have changed in the database
        and you need to reload them.
        """
        self._system_constraints_cache = None
        return self._load_system_constraints()
    
    def validate_assignment(
        self,
        user_id: int,
        planned_shift_id: int,
        role_id: int,
        existing_assignments: List[Dict] = None
    ) -> ValidationResult:
        """
        Validate a single shift assignment against all constraints.
        
        Args:
            user_id: ID of the employee being assigned
            planned_shift_id: ID of the shift being assigned
            role_id: ID of the role for this assignment
            existing_assignments: List of existing assignments to consider (optional)
        
        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult()
        
        # Get employee and shift
        user = self.db.query(UserModel).filter(UserModel.user_id == user_id).first()
        shift = self.db.query(PlannedShiftModel).filter(
            PlannedShiftModel.planned_shift_id == planned_shift_id
        ).first()
        
        if not user:
            result.add_error(ValidationError(
                "EMPLOYEE_NOT_FOUND",
                "HARD",
                f"Employee {user_id} not found"
            ))
            return result
        
        if not shift:
            result.add_error(ValidationError(
                "SHIFT_NOT_FOUND",
                "HARD",
                f"Shift {planned_shift_id} not found"
            ))
            return result
        
        # Run all validations
        self._check_employee_availability(user, shift, result)
        self._check_time_off_conflicts(user, shift, result)
        self._check_role_qualifications(user, role_id, result)
        self._check_shift_overlaps(user, shift, existing_assignments, result)
        self._check_rest_periods(user, shift, existing_assignments, result)
        
        return result
    
    def validate_weekly_schedule(
        self,
        weekly_schedule_id: int,
        proposed_assignments: List[Dict]
    ) -> ValidationResult:
        """
        Validate an entire weekly schedule against all constraints.
        
        Args:
            weekly_schedule_id: ID of the weekly schedule
            proposed_assignments: List of proposed assignments
                Each dict should have: user_id, planned_shift_id, role_id
        
        Returns:
            ValidationResult with all errors and warnings
        """
        result = ValidationResult()
        
        # Group assignments by employee
        assignments_by_employee = {}
        for assignment in proposed_assignments:
            user_id = assignment['user_id']
            if user_id not in assignments_by_employee:
                assignments_by_employee[user_id] = []
            assignments_by_employee[user_id].append(assignment)
        
        # Validate each employee's assignments
        for user_id, user_assignments in assignments_by_employee.items():
            # Validate individual assignments
            for assignment in user_assignments:
                assign_result = self.validate_assignment(
                    assignment['user_id'],
                    assignment['planned_shift_id'],
                    assignment['role_id'],
                    user_assignments
                )
                result.errors.extend(assign_result.errors)
                result.warnings.extend(assign_result.warnings)
            
            # Validate weekly constraints
            self._check_weekly_hours(user_id, user_assignments, result)
            self._check_weekly_shifts(user_id, user_assignments, result)
            self._check_consecutive_days(user_id, user_assignments, result)
        
        return result
    
    # Individual validation methods
    
    def _check_employee_availability(
        self,
        user: UserModel,
        shift: PlannedShiftModel,
        result: ValidationResult
    ):
        """Check if employee is active and available."""
        if user.user_status not in ["ACTIVE", "active"]:
            result.add_error(ValidationError(
                "EMPLOYEE_INACTIVE",
                "HARD",
                f"Employee {user.user_full_name} is not active (status: {user.user_status})",
                {'user_id': user.user_id, 'status': user.user_status}
            ))
    
    def _check_time_off_conflicts(
        self,
        user: UserModel,
        shift: PlannedShiftModel,
        result: ValidationResult
    ):
        """Check for approved time-off requests."""
        time_off_requests = self.db.query(TimeOffRequestModel).filter(
            TimeOffRequestModel.user_id == user.user_id,
            TimeOffRequestModel.status == TimeOffRequestStatus.APPROVED,
            TimeOffRequestModel.start_date <= shift.date,
            TimeOffRequestModel.end_date >= shift.date
        ).all()
        
        if time_off_requests:
            for request in time_off_requests:
                result.add_error(ValidationError(
                    "TIME_OFF_CONFLICT",
                    "HARD",
                    f"Employee {user.user_full_name} has approved time-off on {shift.date}",
                    {
                        'user_id': user.user_id,
                        'shift_id': shift.planned_shift_id,
                        'shift_date': str(shift.date),
                        'time_off_request_id': request.request_id,
                        'time_off_type': request.request_type.value
                    }
                ))
    
    def _check_role_qualifications(
        self,
        user: UserModel,
        role_id: int,
        result: ValidationResult
    ):
        """Check if employee has the required role."""
        user_role_ids = [role.role_id for role in user.roles]
        
        if role_id not in user_role_ids:
            role = self.db.query(RoleModel).filter(RoleModel.role_id == role_id).first()
            role_name = role.role_name if role else f"Role {role_id}"
            
            result.add_error(ValidationError(
                "ROLE_QUALIFICATION",
                "HARD",
                f"Employee {user.user_full_name} does not have role '{role_name}'",
                {
                    'user_id': user.user_id,
                    'required_role_id': role_id,
                    'user_roles': user_role_ids
                }
            ))
    
    def _check_shift_overlaps(
        self,
        user: UserModel,
        shift: PlannedShiftModel,
        existing_assignments: List[Dict],
        result: ValidationResult
    ):
        """Check for overlapping shift assignments using datetime range overlap."""
        if not existing_assignments:
            existing_assignments = []
        
        # Get all shifts for this employee (removed date filter to handle cross-day overlaps)
        shift_ids = [a['planned_shift_id'] for a in existing_assignments]
        
        if not shift_ids:
            return
        
        overlapping_shifts = self.db.query(PlannedShiftModel).filter(
            PlannedShiftModel.planned_shift_id.in_(shift_ids)
        ).all()
        
        for other_shift in overlapping_shifts:
            if other_shift.planned_shift_id == shift.planned_shift_id:
                continue
            
            # Check time overlap using shared utility
            if shifts_overlap(shift, other_shift):
                result.add_error(ValidationError(
                    "SHIFT_OVERLAP",
                    "HARD",
                    f"Employee {user.user_full_name} assigned to overlapping shifts",
                    {
                        'user_id': user.user_id,
                        'shift1_id': shift.planned_shift_id,
                        'shift1_date': str(shift.date),
                        'shift1_time': f"{shift.start_time}-{shift.end_time}",
                        'shift2_id': other_shift.planned_shift_id,
                        'shift2_date': str(other_shift.date),
                        'shift2_time': f"{other_shift.start_time}-{other_shift.end_time}"
                    }
                ))
    
    def _check_rest_periods(
        self,
        user: UserModel,
        shift: PlannedShiftModel,
        existing_assignments: List[Dict],
        result: ValidationResult
    ):
        """Check minimum rest hours between shifts."""
        min_rest_constraint = self.system_constraints.get(SystemConstraintType.MIN_REST_HOURS)
        
        if not min_rest_constraint:
            return
        
        min_rest_hours = min_rest_constraint['value']
        is_hard = min_rest_constraint['is_hard']
        
        if not existing_assignments:
            return
        
        # Get all shifts for this employee
        shift_ids = [a['planned_shift_id'] for a in existing_assignments]
        
        if not shift_ids:
            return
        
        other_shifts = self.db.query(PlannedShiftModel).filter(
            PlannedShiftModel.planned_shift_id.in_(shift_ids)
        ).all()
        
        for other_shift in other_shifts:
            if other_shift.planned_shift_id == shift.planned_shift_id:
                continue
            
            # Calculate hours between shifts
            hours_between = self._calculate_hours_between_shifts(shift, other_shift)
            
            if hours_between < min_rest_hours:
                severity = "HARD" if is_hard else "SOFT"
                result.add_error(ValidationError(
                    "INSUFFICIENT_REST",
                    severity,
                    f"Employee {user.user_full_name} has only {hours_between:.1f} hours rest between shifts (minimum: {min_rest_hours})",
                    {
                        'user_id': user.user_id,
                        'shift1_id': shift.planned_shift_id,
                        'shift2_id': other_shift.planned_shift_id,
                        'hours_between': hours_between,
                        'min_required': min_rest_hours
                    }
                ))
    
    def _check_weekly_hours(
        self,
        user_id: int,
        assignments: List[Dict],
        result: ValidationResult
    ):
        """Check if total weekly hours are within limits."""
        max_hours_constraint = self.system_constraints.get(SystemConstraintType.MAX_HOURS_PER_WEEK)
        min_hours_constraint = self.system_constraints.get(SystemConstraintType.MIN_HOURS_PER_WEEK)
        
        # Get all shifts for these assignments
        shift_ids = [a['planned_shift_id'] for a in assignments]
        shifts = self.db.query(PlannedShiftModel).filter(
            PlannedShiftModel.planned_shift_id.in_(shift_ids)
        ).all()
        
        # Calculate total hours
        total_hours = 0.0
        for shift in shifts:
            hours = self._calculate_shift_hours(shift)
            total_hours += hours
        
        user = self.db.query(UserModel).filter(UserModel.user_id == user_id).first()
        
        # Check max hours
        if max_hours_constraint:
            max_hours = max_hours_constraint['value']
            is_hard = max_hours_constraint['is_hard']
            
            if total_hours > max_hours:
                severity = "HARD" if is_hard else "SOFT"
                result.add_error(ValidationError(
                    "MAX_HOURS_EXCEEDED",
                    severity,
                    f"Employee {user.user_full_name} assigned {total_hours:.1f} hours (max: {max_hours})",
                    {
                        'user_id': user_id,
                        'total_hours': total_hours,
                        'max_hours': max_hours,
                        'excess_hours': total_hours - max_hours
                    }
                ))
        
        # Check min hours
        if min_hours_constraint:
            min_hours = min_hours_constraint['value']
            is_hard = min_hours_constraint['is_hard']
            
            if total_hours < min_hours:
                severity = "HARD" if is_hard else "SOFT"
                result.add_error(ValidationError(
                    "MIN_HOURS_NOT_MET",
                    severity,
                    f"Employee {user.user_full_name} assigned {total_hours:.1f} hours (min: {min_hours})",
                    {
                        'user_id': user_id,
                        'total_hours': total_hours,
                        'min_hours': min_hours,
                        'deficit_hours': min_hours - total_hours
                    }
                ))
    
    def _check_weekly_shifts(
        self,
        user_id: int,
        assignments: List[Dict],
        result: ValidationResult
    ):
        """Check if number of shifts is within limits."""
        max_shifts_constraint = self.system_constraints.get(SystemConstraintType.MAX_SHIFTS_PER_WEEK)
        min_shifts_constraint = self.system_constraints.get(SystemConstraintType.MIN_SHIFTS_PER_WEEK)
        
        shift_count = len(assignments)
        user = self.db.query(UserModel).filter(UserModel.user_id == user_id).first()
        
        # Check max shifts
        if max_shifts_constraint:
            max_shifts = int(max_shifts_constraint['value'])
            is_hard = max_shifts_constraint['is_hard']
            
            if shift_count > max_shifts:
                severity = "HARD" if is_hard else "SOFT"
                result.add_error(ValidationError(
                    "MAX_SHIFTS_EXCEEDED",
                    severity,
                    f"Employee {user.user_full_name} assigned {shift_count} shifts (max: {max_shifts})",
                    {
                        'user_id': user_id,
                        'shift_count': shift_count,
                        'max_shifts': max_shifts
                    }
                ))
        
        # Check min shifts
        if min_shifts_constraint:
            min_shifts = int(min_shifts_constraint['value'])
            is_hard = min_shifts_constraint['is_hard']
            
            if shift_count < min_shifts:
                severity = "HARD" if is_hard else "SOFT"
                result.add_error(ValidationError(
                    "MIN_SHIFTS_NOT_MET",
                    severity,
                    f"Employee {user.user_full_name} assigned {shift_count} shifts (min: {min_shifts})",
                    {
                        'user_id': user_id,
                        'shift_count': shift_count,
                        'min_shifts': min_shifts
                    }
                ))
    
    def _check_consecutive_days(
        self,
        user_id: int,
        assignments: List[Dict],
        result: ValidationResult
    ):
        """Check maximum consecutive working days."""
        max_consecutive_constraint = self.system_constraints.get(SystemConstraintType.MAX_CONSECUTIVE_DAYS)
        
        if not max_consecutive_constraint:
            return
        
        max_consecutive = int(max_consecutive_constraint['value'])
        is_hard = max_consecutive_constraint['is_hard']
        
        # Get all shifts and sort by date
        shift_ids = [a['planned_shift_id'] for a in assignments]
        shifts = self.db.query(PlannedShiftModel).filter(
            PlannedShiftModel.planned_shift_id.in_(shift_ids)
        ).order_by(PlannedShiftModel.date).all()
        
        # Get unique dates
        work_dates = sorted(set(shift.date for shift in shifts))
        
        # Find consecutive sequences
        if not work_dates:
            return
        
        consecutive_count = 1
        max_found = 1
        
        for i in range(1, len(work_dates)):
            if (work_dates[i] - work_dates[i-1]).days == 1:
                consecutive_count += 1
                max_found = max(max_found, consecutive_count)
            else:
                consecutive_count = 1
        
        user = self.db.query(UserModel).filter(UserModel.user_id == user_id).first()
        
        if max_found > max_consecutive:
            severity = "HARD" if is_hard else "SOFT"
            result.add_error(ValidationError(
                "MAX_CONSECUTIVE_DAYS_EXCEEDED",
                severity,
                f"Employee {user.user_full_name} works {max_found} consecutive days (max: {max_consecutive})",
                {
                    'user_id': user_id,
                    'consecutive_days': max_found,
                    'max_consecutive': max_consecutive
                }
            ))
    
    # Helper methods
    
    def _times_overlap(
        self,
        start1: Optional[datetime],
        end1: Optional[datetime],
        start2: Optional[datetime],
        end2: Optional[datetime],
        shift1: Optional[PlannedShiftModel] = None,
        shift2: Optional[PlannedShiftModel] = None
    ) -> bool:
        """
        Check if two time ranges overlap using full datetime comparison.
        
        If shift1 and shift2 are provided, uses shared utility for proper normalization.
        Otherwise, assumes start1/end1 and start2/end2 are already datetime objects.
        
        Note: This method is kept for backward compatibility. New code should use
        shifts_overlap() from app.services.utils.overlap_utils directly.
        """
        if shift1 is not None and shift2 is not None:
            # Use shared utility for proper datetime normalization
            return shifts_overlap(shift1, shift2)
        else:
            # Fallback: assume datetime objects
            if not isinstance(start1, datetime):
                raise ValueError("start1 must be datetime when shift1 not provided")
            if not isinstance(start2, datetime):
                raise ValueError("start2 must be datetime when shift2 not provided")
            return start1 < end2 and start2 < end1
    
    def _calculate_hours_between_shifts(self, shift1: PlannedShiftModel, shift2: PlannedShiftModel) -> float:
        """
        Calculate hours between two shifts (rest period).
        
        Returns:
            Hours between shifts. If negative, shifts overlap.
        """
        start1_dt, end1_dt = normalize_shift_datetimes(shift1)
        start2_dt, end2_dt = normalize_shift_datetimes(shift2)
        
        # Determine which shift comes first
        # Rest period = (later_shift.start - earlier_shift.end)
        if end1_dt <= start2_dt:
            # shift1 ends before or at the same time as shift2 starts
            # Rest period is from end1 to start2
            diff = start2_dt - end1_dt
        elif end2_dt <= start1_dt:
            # shift2 ends before or at the same time as shift1 starts
            # Rest period is from end2 to start1
            diff = start1_dt - end2_dt
        else:
            # Shifts overlap - return negative value
            # Calculate overlap duration
            overlap_start = max(start1_dt, start2_dt)
            overlap_end = min(end1_dt, end2_dt)
            diff = overlap_start - overlap_end  # Negative value
        
        return diff.total_seconds() / 3600.0
    
    def _calculate_shift_hours(self, shift: PlannedShiftModel) -> float:
        """Calculate duration of a shift in hours, handling overnight shifts."""
        start_dt, end_dt = normalize_shift_datetimes(shift)
        diff = end_dt - start_dt
        return diff.total_seconds() / 3600.0
