"""
Activity log repository for database operations on activity logs.

This repository handles all database access for ActivityLogModel.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.data.repositories.base import BaseRepository
from app.data.models.activity_log_model import (
    ActivityLogModel,
    ActivityActionType,
    ActivityEntityType
)


class ActivityLogRepository(BaseRepository[ActivityLogModel]):
    """Repository for activity log database operations."""
    
    def __init__(self, db: Session):
        """Initialize activity log repository."""
        super().__init__(db, ActivityLogModel)
    
    def get_by_user(self, user_id: int, limit: Optional[int] = None) -> List[ActivityLogModel]:
        """Get all activities for a user."""
        query = self.db.query(ActivityLogModel).filter(
            ActivityLogModel.user_id == user_id
        ).order_by(ActivityLogModel.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_by_entity(
        self,
        entity_type: ActivityEntityType,
        entity_id: int
    ) -> List[ActivityLogModel]:
        """Get all activities for a specific entity."""
        return (
            self.db.query(ActivityLogModel)
            .filter(
                ActivityLogModel.entity_type == entity_type,
                ActivityLogModel.entity_id == entity_id
            )
            .order_by(ActivityLogModel.created_at.desc())
            .all()
        )
    
    def get_by_action_type(
        self,
        action_type: ActivityActionType,
        limit: Optional[int] = None
    ) -> List[ActivityLogModel]:
        """Get all activities of a specific action type."""
        query = (
            self.db.query(ActivityLogModel)
            .filter(ActivityLogModel.action_type == action_type)
            .order_by(ActivityLogModel.created_at.desc())
        )
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def create_activity(
        self,
        action_type: ActivityActionType,
        entity_type: ActivityEntityType,
        entity_id: int,
        user_id: Optional[int] = None,
        details: Optional[str] = None
    ) -> ActivityLogModel:
        """
        Create a new activity log entry.
        
        Args:
            action_type: Type of action
            entity_type: Type of entity
            entity_id: Entity ID
            user_id: User ID who performed the action
            details: Additional details
            
        Returns:
            Created activity log
        """
        return self.create(
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            details=details,
            created_at=datetime.now()
        )
    
    def get_recent(
        self,
        limit: int = 50,
        user_id: Optional[int] = None,
        entity_type: Optional[ActivityEntityType] = None
    ) -> List[ActivityLogModel]:
        """
        Get recent activities with optional filtering.
        
        Args:
            limit: Maximum number of activities to return
            user_id: Optional filter by user ID
            entity_type: Optional filter by entity type
            
        Returns:
            List of recent activities
        """
        query = self.db.query(ActivityLogModel)
        
        if user_id is not None:
            query = query.filter(ActivityLogModel.user_id == user_id)
        
        if entity_type is not None:
            query = query.filter(ActivityLogModel.entity_type == entity_type)
        
        return query.order_by(ActivityLogModel.created_at.desc()).limit(limit).all()
    
    def get_with_user(self, activity_id: int) -> Optional[ActivityLogModel]:
        """Get an activity with user relationship loaded."""
        from sqlalchemy.orm import joinedload
        return (
            self.db.query(ActivityLogModel)
            .options(joinedload(ActivityLogModel.user))
            .filter(ActivityLogModel.activity_id == activity_id)
            .first()
        )
