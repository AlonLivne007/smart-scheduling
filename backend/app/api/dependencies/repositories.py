"""
Repository dependency injection for FastAPI.

This module provides FastAPI dependencies for repositories, ensuring
each request gets its own repository instances with the correct session.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.data.session import get_db
from app.data.repositories.user_repository import UserRepository
from app.data.repositories import RoleRepository
from app.data.repositories.shift_repository import ShiftRepository, ShiftAssignmentRepository
from app.data.repositories import ShiftTemplateRepository
from app.data.repositories.weekly_schedule_repository import WeeklyScheduleRepository
from app.data.repositories.time_off_request_repository import TimeOffRequestRepository
from app.data.repositories.system_constraints_repository import SystemConstraintsRepository
from app.data.repositories.employee_preferences_repository import EmployeePreferencesRepository
from app.data.repositories.optimization_config_repository import OptimizationConfigRepository
from app.data.repositories.scheduling_run_repository import SchedulingRunRepository
from app.data.repositories import SchedulingSolutionRepository
from app.data.repositories import ActivityLogRepository


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency to get UserRepository instance for the current request."""
    return UserRepository(db)


def get_role_repository(db: Session = Depends(get_db)) -> RoleRepository:
    """Dependency to get RoleRepository instance for the current request."""
    return RoleRepository(db)


def get_shift_repository(db: Session = Depends(get_db)) -> ShiftRepository:
    """Dependency to get ShiftRepository instance for the current request."""
    return ShiftRepository(db)


def get_shift_assignment_repository(db: Session = Depends(get_db)) -> ShiftAssignmentRepository:
    """Dependency to get ShiftAssignmentRepository instance for the current request."""
    return ShiftAssignmentRepository(db)


def get_shift_template_repository(db: Session = Depends(get_db)) -> ShiftTemplateRepository:
    """Dependency to get ShiftTemplateRepository instance for the current request."""
    return ShiftTemplateRepository(db)


def get_weekly_schedule_repository(db: Session = Depends(get_db)) -> WeeklyScheduleRepository:
    """Dependency to get WeeklyScheduleRepository instance for the current request."""
    return WeeklyScheduleRepository(db)


def get_time_off_request_repository(db: Session = Depends(get_db)) -> TimeOffRequestRepository:
    """Dependency to get TimeOffRequestRepository instance for the current request."""
    return TimeOffRequestRepository(db)


def get_system_constraints_repository(db: Session = Depends(get_db)) -> SystemConstraintsRepository:
    """Dependency to get SystemConstraintsRepository instance for the current request."""
    return SystemConstraintsRepository(db)


def get_employee_preferences_repository(db: Session = Depends(get_db)) -> EmployeePreferencesRepository:
    """Dependency to get EmployeePreferencesRepository instance for the current request."""
    return EmployeePreferencesRepository(db)


def get_optimization_config_repository(db: Session = Depends(get_db)) -> OptimizationConfigRepository:
    """Dependency to get OptimizationConfigRepository instance for the current request."""
    return OptimizationConfigRepository(db)


def get_scheduling_run_repository(db: Session = Depends(get_db)) -> SchedulingRunRepository:
    """Dependency to get SchedulingRunRepository instance for the current request."""
    return SchedulingRunRepository(db)


def get_scheduling_solution_repository(db: Session = Depends(get_db)) -> SchedulingSolutionRepository:
    """Dependency to get SchedulingSolutionRepository instance for the current request."""
    return SchedulingSolutionRepository(db)


def get_activity_log_repository(db: Session = Depends(get_db)) -> ActivityLogRepository:
    """Dependency to get ActivityLogRepository instance for the current request."""
    return ActivityLogRepository(db)
