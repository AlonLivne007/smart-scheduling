"""
Activity log routes.

API endpoints for retrieving activity logs.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.data.session import get_db
from app.api.dependencies.auth import get_current_user
from app.data.models.user_model import UserModel
from app.data.models.activity_log_model import ActivityEntityType
from app.schemas.activity_log_schema import ActivityLogRead
from app.api.controllers.activity_log_controller import get_recent_activities

router = APIRouter(prefix="/activities", tags=["Activity Logs"])


@router.get(
    "/",
    response_model=List[ActivityLogRead],
    summary="Get recent activities"
)
async def list_activities(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of activities to return"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    entity_type: Optional[ActivityEntityType] = Query(None, description="Filter by entity type"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recent activity logs.
    
    Returns up to `limit` most recent activities, optionally filtered by user or entity type.
    
    Args:
        limit: Maximum number of activities (1-100, default 50)
        user_id: Optional filter by user ID
        entity_type: Optional filter by entity type
        current_user: Authenticated user (injected)
        db: Database session (injected)
        
    Returns:
        List of recent activities
    """
    return await get_recent_activities(db, limit, user_id, entity_type)
