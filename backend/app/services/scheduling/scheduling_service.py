"""
Scheduling Service - Main Orchestrator.

This is the main entry point for scheduling optimization. It orchestrates
data building, solving, and persistence.

The service is designed to be used by Celery workers for async optimization.
The main entry point is `_execute_optimization_for_run()` which executes
optimization for an existing SchedulingRun record.

Note: Solution validation is handled by the MIP solver itself. If the MIP
returns OPTIMAL or FEASIBLE, the solution is guaranteed to satisfy all hard
constraints as they are encoded directly in the MIP model.
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.services.optimization_data_services import OptimizationDataBuilder, OptimizationData
from app.db.models.optimizationConfigModel import OptimizationConfigModel
from app.db.models.schedulingRunModel import SchedulingRunModel, SchedulingRunStatus, SolverStatus
from app.services.scheduling.mip_solver import MipSchedulingSolver
from app.services.scheduling.persistence import SchedulingPersistence
from app.services.scheduling.run_status import map_to_solver_status_enum, build_error_message
from app.services.scheduling.types import SchedulingSolution

logger = logging.getLogger(__name__)


class SchedulingService:
    """Service for solving scheduling optimization problems."""
    
    def __init__(self, db: Session):
        """
        Initialize the scheduling service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.data_builder = OptimizationDataBuilder(db)
        self.solver = MipSchedulingSolver()
        self.persistence = SchedulingPersistence(db)
    
    def _execute_optimization_for_run(
        self,
        run: SchedulingRunModel
    ) -> Tuple[SchedulingRunModel, SchedulingSolution]:
        """
        Main entry point for executing optimization (used by Celery workers).
        
        This is the primary method for running schedule optimization. It executes
        the full optimization pipeline: data building, MIP solving, and persistence.
        
        This method does NOT apply assignments to the schedule - it only stores
        solution proposals in SchedulingSolutionModel. This allows for review
        and approval before assignments are applied.
        
        Args:
            run: SchedulingRunModel record (already created with PENDING status)
        
        Returns:
            Tuple of (updated run, solution)
        
        Raises:
            ValueError: If run not found, already started, or configuration missing
            SQLAlchemyError: If database operations fail
        """
        try:
            # Execute optimization without applying assignments
            run, solution = self._execute_run(run, apply_assignments=False)
            return run, solution
        except (ValueError, SQLAlchemyError) as e:
            # Update run status to FAILED with proper error handling
            try:
                run.status = SchedulingRunStatus.FAILED
                run.completed_at = datetime.now()
                run.error_message = str(e)
                self.db.commit()
            except SQLAlchemyError as commit_error:
                # If commit fails, rollback and log
                self.db.rollback()
                logger.error(
                    f"Failed to update run status for run_id={run.run_id}, "
                    f"original_error={e}, commit_error={commit_error}",
                    exc_info=True
                )
            
            logger.error(
                f"Optimization failed for run_id={run.run_id}, error={e}",
                exc_info=True
            )
            raise
        except Exception as e:
            # Catch-all for unexpected errors (programming errors, etc.)
            try:
                run.status = SchedulingRunStatus.FAILED
                run.completed_at = datetime.now()
                run.error_message = f"Unexpected error: {str(e)}"
                self.db.commit()
            except SQLAlchemyError as commit_error:
                self.db.rollback()
                logger.error(
                    f"Failed to update run status for run_id={run.run_id}, "
                    f"original_error={e}, commit_error={commit_error}",
                    exc_info=True
                )
            
            logger.exception(
                f"Unexpected error during optimization for run_id={run.run_id}"
            )
            raise
    
    def _execute_run(
        self,
        run: SchedulingRunModel,
        apply_assignments: bool = True
    ) -> Tuple[SchedulingRunModel, SchedulingSolution]:
        """
        Shared executor for optimization runs.
        
        Args:
            run: SchedulingRunModel record
            apply_assignments: If True, create ShiftAssignmentModel records. If False, only store solutions.
        
        Returns:
            Tuple of (updated run, solution)
        """
        # Update status to RUNNING with race condition protection
        run = self._start_run(run)
        
        # Load configuration
        config = self._load_optimization_config(run)
        
        # Build optimization data
        logger.info(f"Building optimization data for weekly schedule {run.weekly_schedule_id}...")
        data = self.data_builder.build(run.weekly_schedule_id)
        logger.info(f"Employees: {len(data.employees)}, Shifts: {len(data.shifts)}")
        
        # Solve MIP model
        logger.info(f"Building and solving MIP model...")
        solution = self.solver.solve(data, config)
        
        # Check if optimization was infeasible or failed
        if solution.status in ['INFEASIBLE', 'NO_SOLUTION_FOUND']:
            return self._handle_infeasible_solution(run, solution)
        
        # Note: Solution validation is handled by the MIP solver itself.
        # If the MIP returns OPTIMAL or FEASIBLE, the solution is guaranteed to satisfy
        # all hard constraints. No additional validation needed.
        
        # Persist solution and optionally apply assignments
        run = self._persist_solution(run, solution, apply_assignments)
        
        return run, solution
    
    def _start_run(self, run: SchedulingRunModel) -> SchedulingRunModel:
        """
        Start a run with race condition protection.
        
        Uses SELECT FOR UPDATE to prevent concurrent execution.
        
        Args:
            run: SchedulingRunModel record
        
        Returns:
            Locked and updated run record
        
        Raises:
            ValueError: If run not found or already started
        """
        # Use SELECT FOR UPDATE to prevent race conditions
        locked_run = self.db.query(SchedulingRunModel).filter(
            SchedulingRunModel.run_id == run.run_id
        ).with_for_update().first()
        
        if not locked_run:
            raise ValueError(f"Run {run.run_id} not found")
        
        # Check if run was already started by another process
        if locked_run.status != SchedulingRunStatus.PENDING:
            raise ValueError(
                f"Run {run.run_id} is already in status {locked_run.status}, "
                f"cannot start again"
            )
        
        locked_run.status = SchedulingRunStatus.RUNNING
        if not locked_run.started_at:
            locked_run.started_at = datetime.now()
        self.db.commit()
        self.db.refresh(locked_run)
        
        return locked_run
    
    def _load_optimization_config(self, run: SchedulingRunModel) -> OptimizationConfigModel:
        """
        Load optimization configuration for a run.
        
        Args:
            run: SchedulingRunModel record
        
        Returns:
            OptimizationConfigModel
        
        Raises:
            ValueError: If no configuration found
        """
        if run.config_id:
            config = self.db.query(OptimizationConfigModel).filter(
                OptimizationConfigModel.config_id == run.config_id
            ).first()
        else:
            config = self.db.query(OptimizationConfigModel).filter(
                OptimizationConfigModel.is_default == True
            ).first()
        
        if not config:
            raise ValueError("No optimization configuration found")
        
        return config
    
    def _handle_infeasible_solution(
        self,
        run: SchedulingRunModel,
        solution: SchedulingSolution
    ) -> Tuple[SchedulingRunModel, SchedulingSolution]:
        """
        Handle infeasible or failed solution.
        
        Args:
            run: SchedulingRunModel record
            solution: SchedulingSolution with failed status
        
        Returns:
            Tuple of (updated run, solution)
        """
        run.status = SchedulingRunStatus.FAILED
        run.completed_at = datetime.now()
        run.runtime_seconds = solution.runtime_seconds
        run.total_assignments = 0
        run.solver_status = map_to_solver_status_enum(solution.status)
        run.error_message = build_error_message(solution.status)
        
        self.db.commit()
        self.db.refresh(run)
        
        logger.warning(f"Optimization failed: {solution.status}, error_message: {run.error_message}")
        
        return run, solution
    
    def _persist_solution(
        self,
        run: SchedulingRunModel,
        solution: SchedulingSolution,
        apply_assignments: bool
    ) -> SchedulingRunModel:
        """
        Persist solution and optionally apply assignments.
        
        Args:
            run: SchedulingRunModel record
            solution: SchedulingSolution to persist
            apply_assignments: If True, create ShiftAssignmentModel records
        
        Returns:
            Updated run record
        
        Raises:
            SQLAlchemyError: If persistence fails
        """
        # Clear existing assignments if applying new ones
        if apply_assignments:
            logger.info(f"Clearing existing assignments for weekly_schedule_id={run.weekly_schedule_id}...")
            self.persistence.clear_existing_assignments(run.weekly_schedule_id, commit=False)
        
        # Update run with results
        run.status = SchedulingRunStatus.COMPLETED
        run.completed_at = datetime.now()
        run.runtime_seconds = solution.runtime_seconds
        run.objective_value = solution.objective_value
        run.mip_gap = solution.mip_gap
        run.total_assignments = len(solution.assignments)
        run.solver_status = map_to_solver_status_enum(solution.status)
        
        # Persist solution and optionally apply assignments
        # Use commit=False to combine with run update in single transaction
        if apply_assignments:
            logger.info(f"Creating {len(solution.assignments)} shift assignments...")
        else:
            logger.info(f"Storing {len(solution.assignments)} solution records...")
        
        try:
            self.persistence.persist_solution_and_apply_assignments(
                run.run_id,
                solution.assignments,
                apply_assignments=apply_assignments,
                commit=False  # Commit together with run update
            )
            
            # Commit all changes (clear + persist + run update) in single transaction
            self.db.commit()
            self.db.refresh(run)
        except SQLAlchemyError as e:
            # Rollback on error
            self.db.rollback()
            logger.error(
                f"Failed to persist solution for run_id={run.run_id}, error={e}",
                exc_info=True
            )
            raise
        
        if apply_assignments:
            logger.info(
                f"SchedulingRun {run.run_id} completed with {len(solution.assignments)} assignments"
            )
        else:
            logger.info(
                f"SchedulingRun {run.run_id} completed with {len(solution.assignments)} solution records"
            )
        
        return run

