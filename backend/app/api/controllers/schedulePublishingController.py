"""
Schedule publishing controller.

Handles publishing weekly schedules and notifying employees.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.models.weeklyScheduleModel import WeeklyScheduleModel, ScheduleStatus
from app.db.models.shiftAssignmentModel import ShiftAssignmentModel
from app.db.models.userModel import UserModel
from app.api.controllers.activityLogController import log_activity
from app.db.models.activityLogModel import ActivityActionType, ActivityEntityType


async def publish_schedule(
    db: Session,
    schedule_id: int,
    published_by_id: int,
    notify_employees: bool = True
) -> dict:
    """
    Publish a weekly schedule.
    
    Changes status from DRAFT to PUBLISHED, locks the schedule from further
    modifications, and optionally notifies employees.
    
    Args:
        db: Database session
        schedule_id: ID of the schedule to publish
        published_by_id: ID of the user publishing the schedule
        notify_employees: Whether to send notifications to employees
        
    Returns:
        Dict with publication details and notification status
        
    Raises:
        404: Schedule not found
        400: Schedule already published or has no assignments
    """
    # Get the schedule
    schedule = db.query(WeeklyScheduleModel).filter(
        WeeklyScheduleModel.weekly_schedule_id == schedule_id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weekly schedule {schedule_id} not found"
        )
    
    # Check if already published
    if schedule.status == ScheduleStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schedule is already published"
        )
    
    # Check if schedule has any assignments
    shift_ids = [ps.planned_shift_id for ps in schedule.planned_shifts]
    if not shift_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot publish schedule with no shifts"
        )
    
    assignment_count = db.query(ShiftAssignmentModel).filter(
        ShiftAssignmentModel.planned_shift_id.in_(shift_ids)
    ).count()
    
    if assignment_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot publish schedule with no shift assignments. Run optimization or assign shifts manually first."
        )
    
    # Update schedule status
    schedule.status = ScheduleStatus.PUBLISHED
    schedule.published_at = datetime.now()
    schedule.published_by_id = published_by_id
    
    db.commit()
    db.refresh(schedule)
    
    # Get all employees with assignments in this schedule
    employees_notified = []
    if notify_employees:
        employee_ids = db.query(ShiftAssignmentModel.user_id).filter(
            ShiftAssignmentModel.planned_shift_id.in_(shift_ids)
        ).distinct().all()
        
        employee_ids = [eid[0] for eid in employee_ids]
        employees = db.query(UserModel).filter(
            UserModel.user_id.in_(employee_ids)
        ).all()
        
        # TODO: Implement actual notification system (email, SMS, push notifications)
        # For now, we'll just collect the employee info
        employees_notified = [
            {
                "user_id": emp.user_id,
                "email": emp.user_email,
                "full_name": emp.user_full_name
            }
            for emp in employees
        ]
        
        print(f"📧 Would notify {len(employees_notified)} employees about published schedule")
        # In production, send actual notifications here
    
    # Log the activity
    await log_activity(
        db=db,
        action_type=ActivityActionType.PUBLISH,
        entity_type=ActivityEntityType.SCHEDULE,
        entity_id=schedule.weekly_schedule_id,
        user_id=published_by_id,
        details=f"Published schedule for week of {schedule.week_start_date}. Notified {len(employees_notified)} employees."
    )
    
    return {
        "schedule_id": schedule.weekly_schedule_id,
        "status": schedule.status.value,
        "published_at": schedule.published_at.isoformat(),
        "published_by_id": schedule.published_by_id,
        "assignment_count": assignment_count,
        "employees_notified": len(employees_notified),
        "notification_details": employees_notified if notify_employees else [],
        "message": f"Schedule published successfully. {len(employees_notified)} employees will be notified."
    }


async def unpublish_schedule(
    db: Session,
    schedule_id: int,
    user_id: int
) -> dict:
    """
    Unpublish a schedule (revert to DRAFT status).
    
    Allows managers to make changes to a published schedule if needed.
    
    Args:
        db: Database session
        schedule_id: ID of the schedule to unpublish
        
    Returns:
        Dict with status update
        
    Raises:
        404: Schedule not found
        400: Schedule is not published
    """
    schedule = db.query(WeeklyScheduleModel).filter(
        WeeklyScheduleModel.weekly_schedule_id == schedule_id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weekly schedule {schedule_id} not found"
        )
    
    if schedule.status != ScheduleStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schedule is not published"
        )
    
    # Revert to draft
    schedule.status = ScheduleStatus.DRAFT
    schedule.published_at = None
    schedule.published_by_id = None
    
    db.commit()
    
    # Log the activity
    await log_activity(
        db=db,
        action_type=ActivityActionType.UNPUBLISH,
        entity_type=ActivityEntityType.SCHEDULE,
        entity_id=schedule.weekly_schedule_id,
        user_id=user_id,
        details=f"Unpublished schedule for week of {schedule.week_start_date}"
    )
    
    return {
        "schedule_id": schedule.weekly_schedule_id,
        "status": schedule.status.value,
        "message": "Schedule unpublished and reverted to DRAFT status"
    }
