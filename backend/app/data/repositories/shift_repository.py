"""
Shift repository for database operations on shifts and assignments.

This repository handles all database access for PlannedShiftModel and
ShiftAssignmentModel. It should be the only place where these models
are queried or modified directly.
"""

from typing import List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session, joinedload

from app.repositories.base import BaseRepository
from app.data.models.planned_shift_model import PlannedShiftModel, PlannedShiftStatus
from app.data.models.shift_assignment_model import ShiftAssignmentModel
from app.exceptions.repository import NotFoundError, ConflictError


class ShiftRepository(BaseRepository[PlannedShiftModel]):
    """
    Repository for planned shift database operations.
    
    Provides methods for shift CRUD operations and domain-specific queries.
    """
    
    def __init__(self, db: Session):
        """Initialize shift repository."""
        super().__init__(db, PlannedShiftModel)
    
    def get_by_schedule(self, schedule_id: int) -> List[PlannedShiftModel]:
        """
        Get all shifts for a weekly schedule.
        
        Args:
            schedule_id: Weekly schedule ID
            
        Returns:
            List of planned shifts
        """
        return self.find_by(weekly_schedule_id=schedule_id)
    
    def get_by_date_range(
        self,
        start_date: date,
        end_date: date,
        schedule_id: Optional[int] = None
    ) -> List[PlannedShiftModel]:
        """
        Get shifts within a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            schedule_id: Optional schedule ID to filter by
            
        Returns:
            List of planned shifts
        """
        query = self.db.query(PlannedShiftModel).filter(
            PlannedShiftModel.date >= start_date,
            PlannedShiftModel.date <= end_date
        )
        
        if schedule_id is not None:
            query = query.filter(PlannedShiftModel.weekly_schedule_id == schedule_id)
        
        return query.all()
    
    def get_with_assignments(self, shift_id: int) -> Optional[PlannedShiftModel]:
        """
        Get a shift with its assignments eagerly loaded.
        
        Args:
            shift_id: Shift ID
            
        Returns:
            Shift with assignments loaded, or None if not found
        """
        return (
            self.db.query(PlannedShiftModel)
            .options(joinedload(PlannedShiftModel.assignments))
            .filter(PlannedShiftModel.planned_shift_id == shift_id)
            .first()
        )
    
    def get_with_template_and_assignments(self, shift_id: int) -> Optional[PlannedShiftModel]:
        """
        Get a shift with template and assignments eagerly loaded.
        
        Args:
            shift_id: Shift ID
            
        Returns:
            Shift with template and assignments loaded, or None if not found
        """
        return (
            self.db.query(PlannedShiftModel)
            .options(
                joinedload(PlannedShiftModel.shift_template),
                joinedload(PlannedShiftModel.assignments).joinedload(ShiftAssignmentModel.user),
                joinedload(PlannedShiftModel.assignments).joinedload(ShiftAssignmentModel.role)
            )
            .filter(PlannedShiftModel.planned_shift_id == shift_id)
            .first()
        )
    
    def get_all_with_template_and_assignments(self) -> List[PlannedShiftModel]:
        """
        Get all shifts with template and assignments eagerly loaded.
        
        Returns:
            List of shifts with template and assignments loaded
        """
        return (
            self.db.query(PlannedShiftModel)
            .options(
                joinedload(PlannedShiftModel.shift_template),
                joinedload(PlannedShiftModel.assignments).joinedload(ShiftAssignmentModel.user),
                joinedload(PlannedShiftModel.assignments).joinedload(ShiftAssignmentModel.role)
            )
            .all()
        )


class ShiftAssignmentRepository(BaseRepository[ShiftAssignmentModel]):
    """
    Repository for shift assignment database operations.
    
    Provides methods for assignment CRUD operations and domain-specific queries.
    """
    
    def __init__(self, db: Session):
        """Initialize shift assignment repository."""
        super().__init__(db, ShiftAssignmentModel)
    
    def get_by_shift(self, shift_id: int) -> List[ShiftAssignmentModel]:
        """
        Get all assignments for a planned shift.
        
        Args:
            shift_id: Planned shift ID
            
        Returns:
            List of shift assignments
        """
        return self.find_by(planned_shift_id=shift_id)
    
    def get_by_user(self, user_id: int) -> List[ShiftAssignmentModel]:
        """
        Get all assignments for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of shift assignments
        """
        return self.find_by(user_id=user_id)
    
    def get_by_user_and_date_range(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> List[ShiftAssignmentModel]:
        """
        Get assignments for a user within a date range.
        
        Args:
            user_id: User ID
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            List of shift assignments
        """
        return (
            self.db.query(ShiftAssignmentModel)
            .join(PlannedShiftModel)
            .filter(
                ShiftAssignmentModel.user_id == user_id,
                PlannedShiftModel.date >= start_date,
                PlannedShiftModel.date <= end_date
            )
            .all()
        )
    
    def create_assignment(
        self,
        planned_shift_id: int,
        user_id: int,
        role_id: int
    ) -> ShiftAssignmentModel:
        """
        Create a new shift assignment.
        
        Args:
            planned_shift_id: Planned shift ID
            user_id: User ID
            role_id: Role ID
            
        Returns:
            Created assignment
            
        Raises:
            ConflictError: If assignment already exists (unique constraint)
        """
        try:
            return self.create(
                planned_shift_id=planned_shift_id,
                user_id=user_id,
                role_id=role_id
            )
        except ConflictError as e:
            # Provide more context for unique constraint violations
            if "uq_shift_user" in str(e) or "unique" in str(e).lower():
                raise ConflictError(
                    f"User {user_id} is already assigned to shift {planned_shift_id}"
                ) from e
            raise
    
    def delete_by_shift(self, shift_id: int) -> int:
        """
        Delete all assignments for a planned shift.
        
        Args:
            shift_id: Planned shift ID
            
        Returns:
            Number of deleted assignments
        """
        count = (
            self.db.query(ShiftAssignmentModel)
            .filter(ShiftAssignmentModel.planned_shift_id == shift_id)
            .delete(synchronize_session=False)
        )
        self.db.flush()
        return count
    
    def delete_by_schedule(self, schedule_id: int) -> int:
        """
        Delete all assignments for shifts in a weekly schedule.
        
        Args:
            schedule_id: Weekly schedule ID
            
        Returns:
            Number of deleted assignments
        """
        # Get all shift IDs for this schedule
        shift_ids = [
            ps.planned_shift_id
            for ps in self.db.query(PlannedShiftModel)
            .filter(PlannedShiftModel.weekly_schedule_id == schedule_id)
            .all()
        ]
        
        if not shift_ids:
            return 0
        
        count = (
            self.db.query(ShiftAssignmentModel)
            .filter(ShiftAssignmentModel.planned_shift_id.in_(shift_ids))
            .delete(synchronize_session=False)
        )
        self.db.flush()
        return count
