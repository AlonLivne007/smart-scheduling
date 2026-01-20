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

from app.data.repositories.base import BaseRepository
from app.data.repositories.user_repository import UserRepository
from app.data.repositories.role_repository import RoleRepository
from app.data.repositories.shift_repository import ShiftRepository, ShiftAssignmentRepository
from app.data.repositories.shift_template_repository import ShiftTemplateRepository
from app.data.repositories.weekly_schedule_repository import WeeklyScheduleRepository
from app.data.repositories.time_off_request_repository import TimeOffRequestRepository
from app.data.repositories.system_constraints_repository import SystemConstraintsRepository
from app.data.repositories.employee_preferences_repository import EmployeePreferencesRepository
from app.data.repositories.optimization_config_repository import OptimizationConfigRepository
from app.data.repositories.scheduling_run_repository import SchedulingRunRepository
from app.data.repositories.scheduling_solution_repository import SchedulingSolutionRepository
from app.data.repositories.activity_log_repository import ActivityLogRepository

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
