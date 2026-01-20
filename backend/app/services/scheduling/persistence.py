"""
Database persistence operations for scheduling solutions.

This service uses repositories for database access - no direct ORM access.
"""

from typing import List, Dict, Any

from app.repositories.shift_repository import ShiftRepository, ShiftAssignmentRepository
from app.repositories.scheduling_solution_repository import SchedulingSolutionRepository
from app.exceptions.repository import DatabaseError


class SchedulingPersistence:
    """
    Handles database persistence of scheduling solutions and assignments.
    
    Uses repositories for all database operations.
    """
    
    def __init__(
        self,
        shift_repository: ShiftRepository,
        assignment_repository: ShiftAssignmentRepository,
        solution_repository: SchedulingSolutionRepository
    ):
        """
        Initialize persistence handler.
        
        Args:
            shift_repository: ShiftRepository instance
            assignment_repository: ShiftAssignmentRepository instance
            solution_repository: SchedulingSolutionRepository instance
        """
        self.shift_repository = shift_repository
        self.assignment_repository = assignment_repository
        self.solution_repository = solution_repository
    
    def clear_existing_assignments(self, weekly_schedule_id: int) -> None:
        """
        Clear existing shift assignments for a weekly schedule.
        
        This method is designed to be part of a larger transaction. It does NOT commit,
        allowing the caller to combine it with other operations.
        
        Args:
            weekly_schedule_id: ID of the weekly schedule
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            self.assignment_repository.delete_by_schedule(weekly_schedule_id)
        except Exception as e:
            raise DatabaseError(f"Failed to clear assignments: {str(e)}") from e
    
    def persist_solution_and_apply_assignments(
        self,
        run_id: int,
        assignments: List[Dict[str, Any]],
        apply_assignments: bool = True
    ) -> None:
        """
        Persist solution records and optionally create shift assignments.
        
        This method does NOT commit, allowing the caller to combine it with other operations.
        
        Args:
            run_id: ID of the scheduling run
            assignments: List of assignment dictionaries with keys:
                - user_id
                - planned_shift_id
                - role_id
                - preference_score (optional)
            apply_assignments: If True, also create ShiftAssignmentModel records
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Create solution records
            for assignment in assignments:
                self.solution_repository.create_solution(
                    run_id=run_id,
                    planned_shift_id=assignment['planned_shift_id'],
                    user_id=assignment['user_id'],
                    role_id=assignment['role_id'],
                    is_selected=True,
                    assignment_score=assignment.get('preference_score')
                )
                
                # Optionally create actual shift assignment
                if apply_assignments:
                    self.assignment_repository.create_assignment(
                        planned_shift_id=assignment['planned_shift_id'],
                        user_id=assignment['user_id'],
                        role_id=assignment['role_id']
                    )
            
        except Exception as e:
            raise DatabaseError(f"Failed to persist solution: {str(e)}") from e
