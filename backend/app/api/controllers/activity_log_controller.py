"""
Activity log controller.

Business logic for activity logging and retrieval.
Controllers use repositories for database access - no direct ORM access.
"""

from typing import List, Optional
from sqlalchemy.orm import Session  # Only for type hints

from app.repositories.activity_log_repository import ActivityLogRepository
from app.data.models.activity_log_model import ActivityActionType, ActivityEntityType
from app.schemas.activity_log_schema import ActivityLogCreate, ActivityLogRead
from app.exceptions.repository import NotFoundError
from app.data.session_manager import transaction


async def log_activity(
    activity_log_repository: ActivityLogRepository,
    action_type: ActivityActionType,
    entity_type: ActivityEntityType,
    entity_id: int,
    user_id: Optional[int] = None,
    details: Optional[str] = None,
    db: Session = None  # For transaction management
) -> ActivityLogRead:
    """
    Log an activity to the database.
    
    Uses repository to create activity log entry.
    
    Args:
        activity_log_repository: Activity log repository
        action_type: Type of action (CREATE, UPDATE, DELETE, etc.)
        entity_type: Type of entity (SCHEDULE, SHIFT, etc.)
        entity_id: ID of the affected entity
        user_id: ID of user who performed the action
        details: Additional details about the action
        db: Database session (for transaction)
        
    Returns:
        Created activity log entry
    """
    if db:
        with transaction(db):
            activity = activity_log_repository.create(
                action_type=action_type,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                details=details
            )
    else:
        # If no transaction context, just create
        activity = activity_log_repository.create(
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            details=details
        )
    
    # Get activity with relationships for serialization
    activity = activity_log_repository.get_with_user(activity.activity_id)
    return _build_activity_read(activity)


async def get_recent_activities(
    activity_log_repository: ActivityLogRepository,
    limit: int = 50,
    user_id: Optional[int] = None,
    entity_type: Optional[ActivityEntityType] = None
) -> List[ActivityLogRead]:
    """
    Get recent activities with optional filtering.
    
    Uses repository to get activities.
    
    Args:
        activity_log_repository: Activity log repository
        limit: Maximum number of activities to return
        user_id: Optional filter by user ID
        entity_type: Optional filter by entity type
        
    Returns:
        List of recent activities
    """
    activities = activity_log_repository.get_recent(
        limit=limit,
        user_id=user_id,
        entity_type=entity_type
    )
    
    return [_build_activity_read(activity) for activity in activities]


def _build_activity_read(activity) -> ActivityLogRead:
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
