"""
Schedule publishing routes.

API endpoints for publishing schedules and notifying employees.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db.session import get_db
from app.api.dependencies.auth import require_manager, get_current_user
from app.db.models.userModel import UserModel
from app.api.controllers.schedulePublishingController import (
    publish_schedule,
    unpublish_schedule
)

router = APIRouter(prefix="/schedules", tags=["Schedule Publishing"])


@router.post(
    "/{schedule_id}/publish",
    dependencies=[Depends(require_manager)],
    response_model=Dict[str, Any]
)
async def publish_schedule_endpoint(
    schedule_id: int,
    notify_employees: bool = Query(True, description="Send notifications to employees"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Publish a weekly schedule.
    
    Changes the schedule status to PUBLISHED and optionally notifies
    all employees with assignments in this schedule.
    
    Requirements:
    - Schedule must have at least one shift assignment
    - Schedule must be in DRAFT status
    - Only managers can publish schedules
    
    Args:
        schedule_id: ID of the schedule to publish
        notify_employees: Whether to send notifications (default: True)
        current_user: Authenticated user (injected)
        db: Database session (injected)
        
    Returns:
        Publication details including notification status
    """
    return await publish_schedule(
        db=db,
        schedule_id=schedule_id,
        published_by_id=current_user.user_id,
        notify_employees=notify_employees
    )


@router.post(
    "/{schedule_id}/unpublish",
    dependencies=[Depends(require_manager)],
    response_model=Dict[str, Any]
)
async def unpublish_schedule_endpoint(
    schedule_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unpublish a schedule (revert to DRAFT).
    
    Allows managers to make changes to a published schedule.
    Employees will not be automatically notified of the change.
    
    Args:
        schedule_id: ID of the schedule to unpublish
        current_user: Authenticated user (injected)
        db: Database session (injected)
        
    Returns:
        Status update
    """
    return await unpublish_schedule(db=db, schedule_id=schedule_id, user_id=current_user.user_id)
