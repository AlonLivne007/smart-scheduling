"""
Scheduling solution repository for database operations on scheduling solutions.

This repository handles all database access for SchedulingSolutionModel.
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.repositories.base import BaseRepository
from app.db.models.schedulingSolutionModel import SchedulingSolutionModel


class SchedulingSolutionRepository(BaseRepository[SchedulingSolutionModel]):
    """Repository for scheduling solution database operations."""
    
    def __init__(self, db: Session):
        """Initialize scheduling solution repository."""
        super().__init__(db, SchedulingSolutionModel)
    
    def get_by_run(self, run_id: int) -> List[SchedulingSolutionModel]:
        """Get all solutions for a run."""
        return self.find_by(run_id=run_id)
    
    def get_selected_by_run(self, run_id: int) -> List[SchedulingSolutionModel]:
        """Get all selected solutions for a run."""
        return (
            self.db.query(SchedulingSolutionModel)
            .filter(
                SchedulingSolutionModel.run_id == run_id,
                SchedulingSolutionModel.is_selected == True
            )
            .all()
        )
    
    def get_with_relationships(self, solution_id: int) -> Optional[SchedulingSolutionModel]:
        """Get a solution with relationships loaded."""
        return (
            self.db.query(SchedulingSolutionModel)
            .options(
                joinedload(SchedulingSolutionModel.user),
                joinedload(SchedulingSolutionModel.role),
                joinedload(SchedulingSolutionModel.planned_shift)
            )
            .filter(SchedulingSolutionModel.solution_id == solution_id)
            .first()
        )
    
    def get_all_with_relationships_by_run(self, run_id: int) -> List[SchedulingSolutionModel]:
        """Get all solutions for a run with relationships loaded."""
        return (
            self.db.query(SchedulingSolutionModel)
            .options(
                joinedload(SchedulingSolutionModel.user),
                joinedload(SchedulingSolutionModel.role),
                joinedload(SchedulingSolutionModel.planned_shift)
            )
            .filter(SchedulingSolutionModel.run_id == run_id)
            .all()
        )
    
    def get_by_shift(self, shift_id: int) -> List[SchedulingSolutionModel]:
        """Get all solutions for a planned shift."""
        return self.find_by(planned_shift_id=shift_id)
    
    def create_solution(
        self,
        run_id: int,
        planned_shift_id: int,
        user_id: int,
        role_id: int,
        is_selected: bool = True,
        assignment_score: Optional[float] = None
    ) -> SchedulingSolutionModel:
        """
        Create a new solution record.
        
        Args:
            run_id: Scheduling run ID
            planned_shift_id: Planned shift ID
            user_id: User ID
            role_id: Role ID
            is_selected: Whether this solution is selected
            assignment_score: Assignment score
            
        Returns:
            Created solution
        """
        return self.create(
            run_id=run_id,
            planned_shift_id=planned_shift_id,
            user_id=user_id,
            role_id=role_id,
            is_selected=is_selected,
            assignment_score=assignment_score
        )
    
    def delete_by_run(self, run_id: int) -> int:
        """Delete all solutions for a run."""
        count = (
            self.db.query(SchedulingSolutionModel)
            .filter(SchedulingSolutionModel.run_id == run_id)
            .delete(synchronize_session=False)
        )
        self.db.flush()
        return count
