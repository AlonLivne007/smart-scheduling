"""
Repository layer for database access.

This module provides the repository pattern implementation, ensuring that
only repositories access the database directly. Controllers and services
must use repositories, never SQLAlchemy Session or models directly.

Architecture:
- Controllers: Contain business logic and use repositories directly
- Services: Only for complex business logic (scheduling, optimization), use repositories
- Repositories: Only layer that accesses the database
"""

from app.repositories.base import BaseRepository
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.shift_repository import ShiftRepository, ShiftAssignmentRepository
from app.repositories.shift_template_repository import ShiftTemplateRepository
from app.repositories.weekly_schedule_repository import WeeklyScheduleRepository
from app.repositories.time_off_request_repository import TimeOffRequestRepository
from app.repositories.system_constraints_repository import SystemConstraintsRepository
from app.repositories.employee_preferences_repository import EmployeePreferencesRepository
from app.repositories.optimization_config_repository import OptimizationConfigRepository
from app.repositories.scheduling_run_repository import SchedulingRunRepository
from app.repositories.scheduling_solution_repository import SchedulingSolutionRepository
from app.repositories.activity_log_repository import ActivityLogRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "RoleRepository",
    "ShiftRepository",
    "ShiftAssignmentRepository",
    "ShiftTemplateRepository",
    "WeeklyScheduleRepository",
    "TimeOffRequestRepository",
    "SystemConstraintsRepository",
    "EmployeePreferencesRepository",
    "OptimizationConfigRepository",
    "SchedulingRunRepository",
    "SchedulingSolutionRepository",
    "ActivityLogRepository",
]
