"""
Weekly schedule repository for database operations on weekly schedules.

This repository handles all database access for WeeklyScheduleModel.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session, joinedload

from app.repositories.base import BaseRepository
from app.data.models.weekly_schedule_model import WeeklyScheduleModel, ScheduleStatus
from app.data.models.planned_shift_model import PlannedShiftModel
from app.exceptions.repository import NotFoundError


class WeeklyScheduleRepository(BaseRepository[WeeklyScheduleModel]):
    """Repository for weekly schedule database operations."""
    
    def __init__(self, db: Session):
        """Initialize weekly schedule repository."""
        super().__init__(db, WeeklyScheduleModel)
    
    def get_by_week_start(self, week_start_date: date) -> Optional[WeeklyScheduleModel]:
        """Get a schedule by week start date."""
        return self.find_one_by(week_start_date=week_start_date)
    
    def get_with_shifts(self, schedule_id: int) -> Optional[WeeklyScheduleModel]:
        """Get a schedule with its planned shifts eagerly loaded."""
        return (
            self.db.query(WeeklyScheduleModel)
            .options(joinedload(WeeklyScheduleModel.planned_shifts))
            .filter(WeeklyScheduleModel.weekly_schedule_id == schedule_id)
            .first()
        )
    
    def get_with_relations(self, schedule_id: int) -> Optional[WeeklyScheduleModel]:
        """Get a schedule with all relationships eagerly loaded."""
        return (
            self.db.query(WeeklyScheduleModel)
            .options(
                joinedload(WeeklyScheduleModel.created_by),
                joinedload(WeeklyScheduleModel.published_by),
                joinedload(WeeklyScheduleModel.planned_shifts).joinedload(PlannedShiftModel.shift_template)
            )
            .filter(WeeklyScheduleModel.weekly_schedule_id == schedule_id)
            .first()
        )
    
    def get_all_with_relationships(self) -> List[WeeklyScheduleModel]:
        """Get all schedules with relationships eagerly loaded."""
        return (
            self.db.query(WeeklyScheduleModel)
            .options(
                joinedload(WeeklyScheduleModel.created_by),
                joinedload(WeeklyScheduleModel.published_by),
                joinedload(WeeklyScheduleModel.planned_shifts).joinedload(PlannedShiftModel.shift_template)
            )
            .all()
        )
    
    def get_published_schedules(self) -> List[WeeklyScheduleModel]:
        """Get all published schedules."""
        return self.find_by(status=ScheduleStatus.PUBLISHED)
    
    def get_draft_schedules(self) -> List[WeeklyScheduleModel]:
        """Get all draft schedules."""
        return self.find_by(status=ScheduleStatus.DRAFT)
    
    def update_status(
        self,
        schedule_id: int,
        status: ScheduleStatus,
        published_by_id: Optional[int] = None
    ) -> WeeklyScheduleModel:
        """
        Update schedule status.
        
        Args:
            schedule_id: Schedule ID
            status: New status
            published_by_id: User ID who published (if publishing)
            
        Returns:
            Updated schedule
        """
        schedule = self.get_or_raise(schedule_id)
        
        update_data = {"status": status}
        if status == ScheduleStatus.PUBLISHED and published_by_id:
            from datetime import datetime
            update_data["published_at"] = datetime.now()
            update_data["published_by_id"] = published_by_id
        
        return self.update(schedule_id, **update_data)
