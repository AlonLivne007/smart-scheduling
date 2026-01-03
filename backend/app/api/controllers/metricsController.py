"""
Metrics Controller
Handles calculation of dashboard metrics like employee count,
shift statistics, and coverage rates.
"""

from sqlalchemy import func, and_, distinct
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any

from app.db.models.userModel import UserModel
from app.db.models.plannedShiftModel import PlannedShiftModel
from app.db.models.shiftAssignmentModel import ShiftAssignmentModel
from app.db.models.weeklyScheduleModel import WeeklyScheduleModel


async def get_dashboard_metrics(db: Session) -> Dict[str, Any]:
    """
    Calculate and return key dashboard metrics
    
    Returns:
        Dict containing:
        - total_employees: Count of active employees
        - upcoming_shifts: Shifts in the next 7 days
        - coverage_rate: Percentage of shifts that are assigned
        - total_schedules: Total weekly schedules created
        - published_schedules: Number of published schedules
        - pending_time_off: Count of pending time-off requests
    """
    
    # Total active employees
    total_employees = db.query(func.count(UserModel.user_id)).filter(
        UserModel.user_status == 'ACTIVE'
    ).scalar() or 0
    
    # Upcoming shifts (next 7 days)
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    
    upcoming_shifts = db.query(func.count(PlannedShiftModel.planned_shift_id)).filter(
        PlannedShiftModel.date >= today,
        PlannedShiftModel.date < next_week
    ).scalar() or 0
    
    # Coverage rate - assigned shifts vs total shifts (next 7 days)
    total_upcoming_shifts = upcoming_shifts
    assigned_shifts = db.query(func.count(distinct(ShiftAssignmentModel.planned_shift_id))).join(
        PlannedShiftModel,
        ShiftAssignmentModel.planned_shift_id == PlannedShiftModel.planned_shift_id
    ).filter(
        PlannedShiftModel.date >= today,
        PlannedShiftModel.date < next_week
    ).scalar() or 0
    
    coverage_rate = round((assigned_shifts / total_upcoming_shifts * 100), 1) if total_upcoming_shifts > 0 else 0
    
    # Total schedules created
    total_schedules = db.query(func.count(WeeklyScheduleModel.weekly_schedule_id)).scalar() or 0
    
    # Published schedules
    published_schedules = db.query(func.count(WeeklyScheduleModel.weekly_schedule_id)).filter(
        WeeklyScheduleModel.status == 'PUBLISHED'
    ).scalar() or 0
    
    # Pending time-off requests
    from app.db.models.timeOffRequestModel import TimeOffRequestModel
    pending_time_off = db.query(func.count(TimeOffRequestModel.request_id)).filter(
        TimeOffRequestModel.status == 'PENDING'
    ).scalar() or 0
    
    return {
        "total_employees": total_employees,
        "upcoming_shifts": upcoming_shifts,
        "coverage_rate": coverage_rate,
        "total_schedules": total_schedules,
        "published_schedules": published_schedules,
        "pending_time_off": pending_time_off
    }
