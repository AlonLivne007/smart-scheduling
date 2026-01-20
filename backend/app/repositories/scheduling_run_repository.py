"""
Scheduling run repository for database operations on scheduling runs.

This repository handles all database access for SchedulingRunModel.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from app.repositories.base import BaseRepository
from app.db.models.schedulingRunModel import (
    SchedulingRunModel,
    SchedulingRunStatus,
    SolverStatus
)
from app.db.models.schedulingSolutionModel import SchedulingSolutionModel


class SchedulingRunRepository(BaseRepository[SchedulingRunModel]):
    """Repository for scheduling run database operations."""
    
    def __init__(self, db: Session):
        """Initialize scheduling run repository."""
        super().__init__(db, SchedulingRunModel)
    
    def get_by_schedule(self, schedule_id: int) -> List[SchedulingRunModel]:
        """Get all runs for a weekly schedule."""
        return self.find_by(weekly_schedule_id=schedule_id)
    
    def get_by_status(self, status: SchedulingRunStatus) -> List[SchedulingRunModel]:
        """Get all runs with a specific status."""
        return self.find_by(status=status)
    
    def get_pending_runs(self) -> List[SchedulingRunModel]:
        """Get all pending runs."""
        return self.find_by(status=SchedulingRunStatus.PENDING)
    
    def get_with_solutions(self, run_id: int) -> Optional[SchedulingRunModel]:
        """Get a run with its solutions eagerly loaded."""
        return (
            self.db.query(SchedulingRunModel)
            .options(joinedload(SchedulingRunModel.solutions))
            .filter(SchedulingRunModel.run_id == run_id)
            .first()
        )
    
    def get_with_relations(self, run_id: int) -> Optional[SchedulingRunModel]:
        """Get a run with all relationships eagerly loaded."""
        return (
            self.db.query(SchedulingRunModel)
            .options(
                joinedload(SchedulingRunModel.weekly_schedule),
                joinedload(SchedulingRunModel.config),
                joinedload(SchedulingRunModel.solutions).joinedload(SchedulingSolutionModel.user),
                joinedload(SchedulingRunModel.solutions).joinedload(SchedulingSolutionModel.role),
                joinedload(SchedulingRunModel.solutions).joinedload(SchedulingSolutionModel.planned_shift)
            )
            .filter(SchedulingRunModel.run_id == run_id)
            .first()
        )
    
    def update_status(
        self,
        run_id: int,
        status: SchedulingRunStatus,
        error_message: Optional[str] = None
    ) -> SchedulingRunModel:
        """
        Update run status.
        
        Args:
            run_id: Run ID
            status: New status
            error_message: Error message if status is FAILED
            
        Returns:
            Updated run
        """
        update_data = {"status": status}
        
        if status == SchedulingRunStatus.RUNNING:
            update_data["started_at"] = datetime.now()
        elif status in (SchedulingRunStatus.COMPLETED, SchedulingRunStatus.FAILED, SchedulingRunStatus.CANCELLED):
            update_data["completed_at"] = datetime.now()
        
        if error_message:
            update_data["error_message"] = error_message
        
        return self.update(run_id, **update_data)
    
    def update_with_results(
        self,
        run_id: int,
        solver_status: SolverStatus,
        objective_value: Optional[float] = None,
        runtime_seconds: Optional[float] = None,
        mip_gap: Optional[float] = None,
        total_assignments: Optional[int] = None
    ) -> SchedulingRunModel:
        """
        Update run with optimization results.
        
        Args:
            run_id: Run ID
            solver_status: Solver status
            objective_value: Objective function value
            runtime_seconds: Runtime in seconds
            mip_gap: Final MIP gap
            total_assignments: Number of assignments
            
        Returns:
            Updated run
        """
        return self.update(
            run_id,
            status=SchedulingRunStatus.COMPLETED,
            solver_status=solver_status,
            objective_value=objective_value,
            runtime_seconds=runtime_seconds,
            mip_gap=mip_gap,
            total_assignments=total_assignments,
            completed_at=datetime.now()
        )
