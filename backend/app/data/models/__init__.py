"""
Data models package.

This module exports all ORM models for easy importing.
All models use snake_case naming convention.
"""

# Import all models
from app.data.models.activity_log_model import ActivityLogModel, ActivityActionType, ActivityEntityType
from app.data.models.employee_preferences_model import EmployeePreferencesModel, DayOfWeek
from app.data.models.optimization_config_model import OptimizationConfigModel
from app.data.models.planned_shift_model import PlannedShiftModel, PlannedShiftStatus
from app.data.models.role_model import RoleModel
from app.data.models.scheduling_run_model import SchedulingRunModel, SchedulingRunStatus, SolverStatus
from app.data.models.scheduling_solution_model import SchedulingSolutionModel
from app.data.models.shift_assignment_model import ShiftAssignmentModel
from app.data.models.shift_role_requirements_table import shift_role_requirements
from app.data.models.shift_template_model import ShiftTemplateModel
from app.data.models.system_constraints_model import SystemConstraintsModel, SystemConstraintType
from app.data.models.time_off_request_model import TimeOffRequestModel, TimeOffRequestStatus, TimeOffRequestType
from app.data.models.user_model import UserModel
from app.data.models.user_role_model import UserRoleModel, user_roles
from app.data.models.weekly_schedule_model import WeeklyScheduleModel, ScheduleStatus

# Export with snake_case aliases for backward compatibility
# These aliases allow imports like: from app.data.models import role_model
role_model = RoleModel
user_model = UserModel
user_role_model = UserRoleModel
shift_template_model = ShiftTemplateModel
shift_role_requirements_table = shift_role_requirements
weekly_schedule_model = WeeklyScheduleModel
planned_shift_model = PlannedShiftModel
shift_assignment_model = ShiftAssignmentModel
time_off_request_model = TimeOffRequestModel
system_constraints_model = SystemConstraintsModel
employee_preferences_model = EmployeePreferencesModel
optimization_config_model = OptimizationConfigModel
scheduling_run_model = SchedulingRunModel
scheduling_solution_model = SchedulingSolutionModel
activity_log_model = ActivityLogModel

__all__ = [
    # Models
    "ActivityLogModel",
    "EmployeePreferencesModel",
    "OptimizationConfigModel",
    "PlannedShiftModel",
    "RoleModel",
    "SchedulingRunModel",
    "SchedulingSolutionModel",
    "ShiftAssignmentModel",
    "ShiftTemplateModel",
    "SystemConstraintsModel",
    "TimeOffRequestModel",
    "UserModel",
    "UserRoleModel",
    "WeeklyScheduleModel",
    # Enums
    "ActivityActionType",
    "ActivityEntityType",
    "DayOfWeek",
    "PlannedShiftStatus",
    "ScheduleStatus",
    "SchedulingRunStatus",
    "SolverStatus",
    "SystemConstraintType",
    "TimeOffRequestStatus",
    "TimeOffRequestType",
    # Tables
    "shift_role_requirements",
    "user_roles",
    # Aliases (snake_case)
    "role_model",
    "user_model",
    "user_role_model",
    "shift_template_model",
    "shift_role_requirements_table",
    "weekly_schedule_model",
    "planned_shift_model",
    "shift_assignment_model",
    "time_off_request_model",
    "system_constraints_model",
    "employee_preferences_model",
    "optimization_config_model",
    "scheduling_run_model",
    "scheduling_solution_model",
    "activity_log_model",
]
