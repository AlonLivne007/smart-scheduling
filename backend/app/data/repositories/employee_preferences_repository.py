"""
Employee preferences repository for database operations on employee preferences.

This repository handles all database access for EmployeePreferencesModel.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.repositories.base import BaseRepository
from app.data.models.employee_preferences_model import (
    EmployeePreferencesModel,
    DayOfWeek
)


class EmployeePreferencesRepository(BaseRepository[EmployeePreferencesModel]):
    """Repository for employee preferences database operations."""
    
    def __init__(self, db: Session):
        """Initialize employee preferences repository."""
        super().__init__(db, EmployeePreferencesModel)
    
    def get_by_user(self, user_id: int) -> List[EmployeePreferencesModel]:
        """Get all preferences for a user."""
        return self.find_by(user_id=user_id)
    
    def get_by_user_and_template(
        self,
        user_id: int,
        template_id: int
    ) -> List[EmployeePreferencesModel]:
        """Get preferences for a user and specific template."""
        return (
            self.db.query(EmployeePreferencesModel)
            .filter(
                EmployeePreferencesModel.user_id == user_id,
                EmployeePreferencesModel.preferred_shift_template_id == template_id
            )
            .all()
        )
    
    def get_by_user_and_day(
        self,
        user_id: int,
        day_of_week: DayOfWeek
    ) -> List[EmployeePreferencesModel]:
        """Get preferences for a user and specific day."""
        return (
            self.db.query(EmployeePreferencesModel)
            .filter(
                EmployeePreferencesModel.user_id == user_id,
                EmployeePreferencesModel.preferred_day_of_week == day_of_week
            )
            .all()
        )
    
    def delete_by_user(self, user_id: int) -> int:
        """Delete all preferences for a user."""
        count = (
            self.db.query(EmployeePreferencesModel)
            .filter(EmployeePreferencesModel.user_id == user_id)
            .delete(synchronize_session=False)
        )
        self.db.flush()
        return count
