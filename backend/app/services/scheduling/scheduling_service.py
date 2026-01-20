"""
Scheduling Service - Main Orchestrator.

This is the main entry point for scheduling optimization. It orchestrates
data building, solving, and persistence.

The service is designed to be used by Celery workers for async optimization.
The main entry point is `_execute_optimization_for_run()` which executes
optimization for an existing SchedulingRun record.

This service uses repositories for database access - no direct ORM access.

Note: Solution validation is handled by the MIP solver itself. If the MIP
returns OPTIMAL or FEASIBLE, the solution is guaranteed to satisfy all hard
constraints as they are encoded directly in the MIP model.
"""

from typing import Tuple
from datetime import datetime
import logging

from app.services.optimization_data_services import OptimizationDataBuilder, OptimizationData
from app.db.models.optimizationConfigModel import OptimizationConfigModel
from app.db.models.schedulingRunModel import SchedulingRunModel, SchedulingRunStatus, SolverStatus
from app.services.scheduling.mip_solver import MipSchedulingSolver
from app.services.scheduling.persistence import SchedulingPersistence
from app.services.scheduling.run_status import map_to_solver_status_enum, build_error_message
from app.services.scheduling.types import SchedulingSolution
from app.repositories.scheduling_run_repository import SchedulingRunRepository
from app.repositories.optimization_config_repository import OptimizationConfigRepository
from app.repositories.shift_repository import ShiftRepository, ShiftAssignmentRepository
from app.repositories.scheduling_solution_repository import SchedulingSolutionRepository
from app.exceptions.repository import NotFoundError, DatabaseError

logger = logging.getLogger(__name__)


class SchedulingService:
    """
    Service for solving scheduling optimization problems.
    
    Uses repositories for all database operations.
    """
    
    def __init__(
        self,
        run_repository: SchedulingRunRepository,
        config_repository: OptimizationConfigRepository,
        data_builder: OptimizationDataBuilder,
        persistence: SchedulingPersistence
    ):
        """
        Initialize the scheduling service.
        
        Args:
            run_repository: SchedulingRunRepository instance
            config_repository: OptimizationConfigRepository instance
            data_builder: OptimizationDataBuilder instance (uses repositories internally)
            persistence: SchedulingPersistence instance (uses repositories internally)
        """
        self.run_repository = run_repository
        self.config_repository = config_repository
        self.data_builder = data_builder
        self.solver = MipSchedulingSolver()
        self.persistence = persistence
    
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
            DatabaseError: If database operations fail
        """
        try:
            # Execute optimization without applying assignments
            run, solution = self._execute_run(run, apply_assignments=False)
            return run, solution
        except Exception as e:
            # Update run status to FAILED with proper error handling
            self._mark_run_as_failed(run, e)
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
        data = self.data_builder.build(run.weekly_schedule_id)
        
        # Solve MIP model
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
        
        Uses repository to update status.
        
        Args:
            run: SchedulingRunModel record
        
        Returns:
            Updated run record
        
        Raises:
            ValueError: If run not found or already started
        """
        # Get fresh copy and check status
        current_run = self.run_repository.get_by_id(run.run_id)
        if not current_run:
            raise ValueError(f"Run {run.run_id} not found")
        
        # Check if run was already started by another process
        if current_run.status != SchedulingRunStatus.PENDING:
            raise ValueError(
                f"Run {run.run_id} is already in status {current_run.status}, "
                f"cannot start again"
            )
        
        # Update to RUNNING status
        updated_run = self.run_repository.update_status(
            run.run_id,
            SchedulingRunStatus.RUNNING
        )
        
        return updated_run
    
    def _mark_run_as_failed(
        self,
        run: SchedulingRunModel,
        error: Exception
    ) -> None:
        """
        Mark a run as failed and update error information.
        
        Args:
            run: SchedulingRunModel record
            error: Exception that caused the failure
        """
        error_message = str(error) if str(error) else f"Unexpected error: {type(error).__name__}"
        
        try:
            self.run_repository.update_status(
                run.run_id,
                SchedulingRunStatus.FAILED,
                error_message=error_message
            )
        except Exception as commit_error:
            logger.error(
                f"Failed to update run status for run_id={run.run_id}, "
                f"original_error={error}, commit_error={commit_error}",
                exc_info=True
            )
        
        if isinstance(error, (ValueError, DatabaseError)):
            logger.error(
                f"Optimization failed for run_id={run.run_id}, error={error}",
                exc_info=True
            )
        else:
            logger.exception(
                f"Unexpected error during optimization for run_id={run.run_id}"
            )
    
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
            config = self.config_repository.get_by_id(run.config_id)
            if not config:
                raise ValueError(f"Optimization config {run.config_id} not found")
        else:
            config = self.config_repository.get_default()
            if not config:
                raise ValueError("No default optimization configuration found")
        
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
        updated_run = self.run_repository.update_with_results(
            run.run_id,
            solver_status=map_to_solver_status_enum(solution.status),
            objective_value=None,
            runtime_seconds=solution.runtime_seconds,
            mip_gap=None,
            total_assignments=0
        )
        
        # Update status to FAILED separately
        updated_run = self.run_repository.update(
            updated_run.run_id,
            status=SchedulingRunStatus.FAILED,
            error_message=build_error_message(solution.status)
        )
        
        logger.warning(f"Optimization failed: {solution.status}, error_message: {updated_run.error_message}")
        
        return updated_run, solution
    
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
            DatabaseError: If persistence fails
        """
        # Clear existing assignments if applying new ones
        if apply_assignments:
            logger.info(f"Clearing existing assignments for weekly_schedule_id={run.weekly_schedule_id}...")
            self.persistence.clear_existing_assignments(run.weekly_schedule_id)
        
        # Persist solution and optionally apply assignments
        if apply_assignments:
            logger.info(f"Creating {len(solution.assignments)} shift assignments...")
        else:
            logger.info(f"Storing {len(solution.assignments)} solution records...")
        
        try:
            self.persistence.persist_solution_and_apply_assignments(
                run.run_id,
                solution.assignments,
                apply_assignments=apply_assignments
            )
            
            # Update run with results
            updated_run = self.run_repository.update_with_results(
                run.run_id,
                solver_status=map_to_solver_status_enum(solution.status),
                objective_value=solution.objective_value,
                runtime_seconds=solution.runtime_seconds,
                mip_gap=solution.mip_gap,
                total_assignments=len(solution.assignments)
            )
            
        except Exception as e:
            logger.error(
                f"Failed to persist solution for run_id={run.run_id}, error={e}",
                exc_info=True
            )
            raise DatabaseError(f"Failed to persist solution: {str(e)}") from e
        
        if apply_assignments:
            logger.info(
                f"SchedulingRun {updated_run.run_id} completed with {len(solution.assignments)} assignments"
            )
        else:
            logger.info(
                f"SchedulingRun {updated_run.run_id} completed with {len(solution.assignments)} solution records"
            )
        
        return updated_run
