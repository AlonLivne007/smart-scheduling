"""
Database persistence operations for scheduling solutions.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.schedulingSolutionModel import SchedulingSolutionModel
from app.db.models.shiftAssignmentModel import ShiftAssignmentModel
from app.db.models.plannedShiftModel import PlannedShiftModel


class SchedulingPersistence:
    """Handles database persistence of scheduling solutions and assignments."""
    
    def __init__(self, db: Session):
        """
        Initialize persistence handler.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def clear_existing_assignments(self, weekly_schedule_id: int, commit: bool = False) -> None:
        """
        Clear existing shift assignments for a weekly schedule.
        
        This method is designed to be part of a larger transaction. By default,
        it does NOT commit, allowing the caller to combine it with other operations.
        
        Args:
            weekly_schedule_id: ID of the weekly schedule
            commit: If True, commit the transaction. If False (default), caller is responsible for commit.
        
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Get all shift IDs for this schedule
            shift_ids = [
                ps.planned_shift_id 
                for ps in self.db.query(PlannedShiftModel).filter(
                    PlannedShiftModel.weekly_schedule_id == weekly_schedule_id
                ).all()
            ]
            
            if shift_ids:
                self.db.query(ShiftAssignmentModel).filter(
                    ShiftAssignmentModel.planned_shift_id.in_(shift_ids)
                ).delete(synchronize_session=False)
            
            # Commit if requested (caller may want to combine with other operations)
            if commit:
                self.db.commit()
        except SQLAlchemyError as e:
            # Rollback on error
            self.db.rollback()
            raise
    
    def persist_solution_and_apply_assignments(
        self,
        run_id: int,
        assignments: List[Dict[str, Any]],
        apply_assignments: bool = True,
        commit: bool = True
    ) -> None:
        """
        Persist solution records and optionally create shift assignments in a single transaction.
        
        Args:
            run_id: ID of the scheduling run
            assignments: List of assignment dictionaries with keys:
                - user_id
                - planned_shift_id
                - role_id
                - preference_score (optional)
            apply_assignments: If True, also create ShiftAssignmentModel records
            commit: If True, commit the transaction. If False, caller is responsible for commit.
        
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Create solution records
            for assignment in assignments:
                solution_record = SchedulingSolutionModel(
                    run_id=run_id,
                    planned_shift_id=assignment['planned_shift_id'],
                    user_id=assignment['user_id'],
                    role_id=assignment['role_id'],
                    is_selected=True,
                    assignment_score=assignment.get('preference_score')
                )
                self.db.add(solution_record)
                
                # Optionally create actual shift assignment
                if apply_assignments:
                    shift_assignment = ShiftAssignmentModel(
                        planned_shift_id=assignment['planned_shift_id'],
                        user_id=assignment['user_id'],
                        role_id=assignment['role_id']
                    )
                    self.db.add(shift_assignment)
            
            # Commit if requested (caller may want to combine with other operations)
            if commit:
                self.db.commit()
            
        except SQLAlchemyError as e:
            # Rollback on error
            self.db.rollback()
            raise

