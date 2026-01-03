"""
Activity log controller.

Business logic for activity logging and retrieval.
"""

from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.models.activityLogModel import ActivityLogModel, ActivityActionType, ActivityEntityType
from app.schemas.activityLogSchema import ActivityLogCreate, ActivityLogRead


async def log_activity(
    db: Session,
    action_type: ActivityActionType,
    entity_type: ActivityEntityType,
    entity_id: int,
    user_id: Optional[int] = None,
    details: Optional[str] = None
) -> ActivityLogModel:
    """
    Log an activity to the database.
    
    Args:
        db: Database session
        action_type: Type of action (CREATE, UPDATE, DELETE, etc.)
        entity_type: Type of entity (SCHEDULE, SHIFT, etc.)
        entity_id: ID of the affected entity
        user_id: ID of user who performed the action
        details: Additional details about the action
        
    Returns:
        Created activity log entry
    """
    activity = ActivityLogModel(
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        details=details
    )
    
    db.add(activity)
    db.commit()
    db.refresh(activity)
    
    return activity


async def get_recent_activities(
    db: Session,
    limit: int = 50,
    user_id: Optional[int] = None,
    entity_type: Optional[ActivityEntityType] = None
) -> List[ActivityLogRead]:
    """
    Get recent activities with optional filtering.
    
    Args:
        db: Database session
        limit: Maximum number of activities to return
        user_id: Optional filter by user ID
        entity_type: Optional filter by entity type
        
    Returns:
        List of recent activities
    """
    query = db.query(ActivityLogModel)
    
    if user_id is not None:
        query = query.filter(ActivityLogModel.user_id == user_id)
    
    if entity_type is not None:
        query = query.filter(ActivityLogModel.entity_type == entity_type)
    
    activities = query.order_by(ActivityLogModel.created_at.desc()).limit(limit).all()
    
    return [_build_activity_read(activity) for activity in activities]


def _build_activity_read(activity: ActivityLogModel) -> ActivityLogRead:
    """Build ActivityLogRead schema from model."""
    user_full_name = None
    if activity.user:
        user_full_name = activity.user.user_full_name
    
    return ActivityLogRead(
        activity_id=activity.activity_id,
        action_type=activity.action_type,
        entity_type=activity.entity_type,
        entity_id=activity.entity_id,
        user_id=activity.user_id,
        user_full_name=user_full_name,
        details=activity.details,
        created_at=activity.created_at
    )
