"""
Activity log model definition.

This module defines the ActivityLog ORM model for tracking all significant
actions and changes in the system for audit and activity feed purposes.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from app.db.session import Base


class ActivityActionType(str, Enum):
    """Types of activities that can be logged."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    PUBLISH = "PUBLISH"
    UNPUBLISH = "UNPUBLISH"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    OPTIMIZE = "OPTIMIZE"
    APPLY = "APPLY"


class ActivityEntityType(str, Enum):
    """Types of entities that can have activities."""
    SCHEDULE = "SCHEDULE"
    SHIFT = "SHIFT"
    ASSIGNMENT = "ASSIGNMENT"
    TIME_OFF = "TIME_OFF"
    USER = "USER"
    CONSTRAINT = "CONSTRAINT"
    CONFIG = "CONFIG"


class ActivityLogModel(Base):
    """
    Activity log model for tracking system changes and actions.
    
    Attributes:
        activity_id: Primary key identifier
        action_type: Type of action performed (CREATE, UPDATE, DELETE, etc.)
        entity_type: Type of entity affected (SCHEDULE, SHIFT, etc.)
        entity_id: ID of the affected entity
        user_id: Foreign key to the user who performed the action
        details: JSON or text description of the action
        created_at: Timestamp when the activity occurred
        user: Relationship to the user who performed the action
    """
    __tablename__ = "activity_logs"
    
    activity_id = Column(Integer, primary_key=True, index=True)
    action_type = Column(
        SQLEnum(ActivityActionType),
        nullable=False,
        index=True
    )
    entity_type = Column(
        SQLEnum(ActivityEntityType),
        nullable=False,
        index=True
    )
    entity_id = Column(Integer, nullable=False, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    details = Column(Text, nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True
    )
    
    # Relationships
    user = relationship("UserModel", foreign_keys=[user_id], lazy="selectin")
    
    def __repr__(self):
        """String representation of the activity log."""
        return f"<ActivityLog(id={self.activity_id}, action={self.action_type.value}, entity={self.entity_type.value}:{self.entity_id})>"
