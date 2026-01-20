"""
Schedule publishing controller.

Handles publishing weekly schedules and notifying employees.
Controllers use repositories for database access - no direct ORM access.
"""

from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session  # Only for type hints

from app.repositories.weekly_schedule_repository import WeeklyScheduleRepository
from app.repositories.shift_repository import ShiftRepository, ShiftAssignmentRepository
from app.repositories.user_repository import UserRepository
from app.repositories.activity_log_repository import ActivityLogRepository
from app.api.controllers.activityLogController import log_activity
from app.db.models.activityLogModel import ActivityActionType, ActivityEntityType
from app.db.models.weeklyScheduleModel import ScheduleStatus
from app.exceptions.repository import NotFoundError, ConflictError
from app.db.session_manager import transaction


async def publish_schedule(
    schedule_id: int,
    published_by_id: int,
    schedule_repository: WeeklyScheduleRepository,
    shift_repository: ShiftRepository,
    assignment_repository: ShiftAssignmentRepository,
    user_repository: UserRepository,
    activity_log_repository: ActivityLogRepository,
    notify_employees: bool = True,
    db: Session = None  # For transaction management
) -> dict:
    """
    Publish a weekly schedule.
    
    Changes status from DRAFT to PUBLISHED, locks the schedule from further
    modifications, and optionally notifies employees.
    
    Business logic:
    - Verify schedule exists
    - Check if already published
    - Check if schedule has assignments
    - Update status to PUBLISHED
    - Notify employees (if requested)
    - Log activity
    """
    try:
        schedule = schedule_repository.get_with_all_relationships(schedule_id)
        if not schedule:
            raise NotFoundError(f"Weekly schedule {schedule_id} not found")
        
        # Business rule: Check if already published
        if schedule.status == ScheduleStatus.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Schedule is already published"
            )
        
        # Business rule: Check if schedule has any shifts
        if not schedule.planned_shifts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot publish schedule with no shifts"
            )
        
        # Business rule: Check if schedule has assignments
        shift_ids = [ps.planned_shift_id for ps in schedule.planned_shifts]
        assignment_count = 0
        for shift_id in shift_ids:
            assignments = assignment_repository.get_by_shift(shift_id)
            assignment_count += len(assignments)
        
        if assignment_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot publish schedule with no shift assignments. Run optimization or assign shifts manually first."
            )
        
        with transaction(db):
            # Update schedule status
            schedule_repository.update_status(
                schedule_id,
                ScheduleStatus.PUBLISHED,
                published_by_id=published_by_id
            )
            
            # Get all employees with assignments in this schedule
            employees_notified = []
            if notify_employees:
                employee_ids = set()
                for shift_id in shift_ids:
                    assignments = assignment_repository.get_by_shift(shift_id)
                    for assignment in assignments:
                        if assignment.user_id:
                            employee_ids.add(assignment.user_id)
                
                # Get employee details
                for emp_id in employee_ids:
                    employee = user_repository.get_by_id(emp_id)
                    if employee:
                        employees_notified.append({
                            "user_id": employee.user_id,
                            "email": employee.user_email,
                            "full_name": employee.user_full_name
                        })
                
                print(f"📧 Would notify {len(employees_notified)} employees about published schedule")
                # In production, send actual notifications here
            
            # Log the activity
            await log_activity(
                activity_log_repository=activity_log_repository,
                action_type=ActivityActionType.PUBLISH,
                entity_type=ActivityEntityType.SCHEDULE,
                entity_id=schedule_id,
                user_id=published_by_id,
                details=f"Published schedule for week of {schedule.week_start_date}. Notified {len(employees_notified)} employees.",
                db=db
            )
            
            return {
                "schedule_id": schedule_id,
                "status": ScheduleStatus.PUBLISHED.value,
                "published_at": datetime.now().isoformat(),
                "published_by_id": published_by_id,
                "assignment_count": assignment_count,
                "employees_notified": len(employees_notified),
                "notification_details": employees_notified if notify_employees else [],
                "message": f"Schedule published successfully. {len(employees_notified)} employees will be notified."
            }
            
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


async def unpublish_schedule(
    schedule_id: int,
    user_id: int,
    schedule_repository: WeeklyScheduleRepository,
    activity_log_repository: ActivityLogRepository,
    db: Session = None  # For transaction management
) -> dict:
    """
    Unpublish a schedule (revert to DRAFT status).
    
    Allows managers to make changes to a published schedule if needed.
    
    Business logic:
    - Verify schedule exists
    - Check if schedule is published
    - Revert to DRAFT
    - Log activity
    """
    try:
        schedule = schedule_repository.get_by_id_or_raise(schedule_id)
        
        # Business rule: Check if schedule is published
        if schedule.status != ScheduleStatus.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Schedule is not published"
            )
        
        with transaction(db):
            # Revert to draft
            schedule_repository.update_status(
                schedule_id,
                ScheduleStatus.DRAFT,
                published_by_id=None
            )
            
            # Also clear published_at and published_by_id
            schedule_repository.update(
                schedule_id,
                published_at=None,
                published_by_id=None
            )
            
            # Log the activity
            await log_activity(
                activity_log_repository=activity_log_repository,
                action_type=ActivityActionType.UNPUBLISH,
                entity_type=ActivityEntityType.SCHEDULE,
                entity_id=schedule_id,
                user_id=user_id,
                details=f"Unpublished schedule for week of {schedule.week_start_date}",
                db=db
            )
            
            return {
                "schedule_id": schedule_id,
                "status": ScheduleStatus.DRAFT.value,
                "message": "Schedule unpublished and reverted to DRAFT status"
            }
            
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
