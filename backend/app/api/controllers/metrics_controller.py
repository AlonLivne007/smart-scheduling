"""
Metrics Controller
Handles calculation of dashboard metrics like employee count,
shift statistics, and coverage rates.
Controllers use repositories for database access - no direct ORM access.
"""

from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session  # Only for type hints

from app.repositories.user_repository import UserRepository
from app.repositories.shift_repository import ShiftRepository
from app.repositories.shift_repository import ShiftAssignmentRepository
from app.repositories.weekly_schedule_repository import WeeklyScheduleRepository
from app.repositories.time_off_request_repository import TimeOffRequestRepository
from app.data.models.time_off_request_model import TimeOffRequestStatus


async def get_dashboard_metrics(
    user_repository: UserRepository,
    shift_repository: ShiftRepository,
    assignment_repository: ShiftAssignmentRepository,
    schedule_repository: WeeklyScheduleRepository,
    time_off_repository: TimeOffRequestRepository
) -> Dict[str, Any]:
    """
    Calculate and return key dashboard metrics
    
    Uses repositories to get all data.
    
    Returns:
        Dict containing:
        - total_employees: Count of active employees
        - upcoming_shifts: Shifts in the next 7 days
        - coverage_rate: Percentage of shifts that are assigned
        - total_schedules: Total weekly schedules created
        - published_schedules: Number of published schedules
        - pending_time_off: Count of pending time-off requests
    """
    # Total employees
    all_users = user_repository.get_all()
    total_employees = len(all_users)
    
    # Upcoming shifts (next 7 days)
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    
    all_shifts = shift_repository.get_all()
    upcoming_shifts = [s for s in all_shifts if today <= s.date < next_week]
    upcoming_shift_count = len(upcoming_shifts)
    
    # Coverage rate - assigned shifts vs total shifts (next 7 days)
    total_upcoming_shifts = upcoming_shift_count
    assigned_shift_ids = set()
    
    for shift in upcoming_shifts:
        assignments = assignment_repository.get_by_shift(shift.planned_shift_id)
        if assignments:
            assigned_shift_ids.add(shift.planned_shift_id)
    
    assigned_shifts = len(assigned_shift_ids)
    coverage_rate = round((assigned_shifts / total_upcoming_shifts * 100), 1) if total_upcoming_shifts > 0 else 0
    
    # Total schedules created
    all_schedules = schedule_repository.get_all()
    total_schedules = len(all_schedules)
    
    # Published schedules
    published_schedules = len([s for s in all_schedules if s.status.value == 'PUBLISHED'])
    
    # Pending time-off requests
    pending_requests = time_off_repository.get_all_with_relationships(
        status_filter=TimeOffRequestStatus.PENDING
    )
    pending_time_off = len(pending_requests)
    
    return {
        "total_employees": total_employees,
        "upcoming_shifts": upcoming_shift_count,
        "coverage_rate": coverage_rate,
        "total_schedules": total_schedules,
        "published_schedules": published_schedules,
        "pending_time_off": pending_time_off
    }
