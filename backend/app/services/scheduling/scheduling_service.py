"""
Scheduling Service - Main Orchestrator.

This is the main entry point for scheduling optimization. It orchestrates
data building, solving, validation, and persistence.
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.services.optimization_data_services import OptimizationDataBuilder, OptimizationData
from app.services.constraintService import ConstraintService
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
        self.constraint_service = ConstraintService(db)
        self.solver = MipSchedulingSolver()
        self.persistence = SchedulingPersistence(db)
    
    def optimize_schedule(
        self,
        weekly_schedule_id: int,
        config_id: Optional[int] = None
    ) -> Tuple[SchedulingRunModel, SchedulingSolution]:
        """
        Optimize shift assignments for a weekly schedule.
        
        Creates a SchedulingRun record to track the optimization execution,
        runs the MIP solver, and stores the results in the database.
        
        Args:
            weekly_schedule_id: ID of the weekly schedule to optimize
            config_id: Optional ID of optimization configuration to use
        
        Returns:
            Tuple of (SchedulingRunModel, SchedulingSolution)
        """
        # Create SchedulingRun record
        run = SchedulingRunModel(
            weekly_schedule_id=weekly_schedule_id,
            config_id=config_id,
            status=SchedulingRunStatus.PENDING,
            started_at=datetime.now()
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        
        try:
            # Execute optimization
            run, solution = self._execute_run(run, apply_assignments=True)
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
                f"Optimization failed for run_id={run.run_id}, "
                f"weekly_schedule_id={weekly_schedule_id}, error={e}",
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
                f"Unexpected error during optimization for run_id={run.run_id}, "
                f"weekly_schedule_id={weekly_schedule_id}"
            )
            raise
    
    def _execute_optimization_for_run(
        self,
        run: SchedulingRunModel
    ) -> Tuple[SchedulingRunModel, SchedulingSolution]:
        """
        Execute optimization for an existing run record (used by async Celery task).
        
        This method does NOT apply assignments to the schedule - it only stores
        solution proposals in SchedulingSolutionModel.
        
        Args:
            run: SchedulingRunModel record (already created with PENDING status)
        
        Returns:
            Tuple of (updated run, solution)
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
        
        # Build and solve
        solution = self._build_and_solve(run, config)
        
        # Check if optimization was infeasible or failed
        if solution.status in ['INFEASIBLE', 'NO_SOLUTION_FOUND']:
            return self._handle_infeasible_solution(run, solution)
        
        # Validate solution against HARD constraints BEFORE persisting
        if solution.status in ['OPTIMAL', 'FEASIBLE']:
            self._validate_solution(run, solution)
        
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
    
    def _build_and_solve(
        self,
        run: SchedulingRunModel,
        config: OptimizationConfigModel
    ) -> SchedulingSolution:
        """
        Build optimization data and solve MIP model.
        
        Args:
            run: SchedulingRunModel record
            config: OptimizationConfigModel
        
        Returns:
            SchedulingSolution
        """
        # Build optimization data
        logger.info(f"Building optimization data for weekly schedule {run.weekly_schedule_id}...")
        data = self.data_builder.build(run.weekly_schedule_id)
        
        logger.info(f"Employees: {len(data.employees)}, Shifts: {len(data.shifts)}")
        
        # Build and solve MIP model
        logger.info(f"Building MIP model...")
        solution = self.solver.solve(data, config)
        
        return solution
    
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
    
    def _validate_solution(
        self,
        run: SchedulingRunModel,
        solution: SchedulingSolution
    ) -> None:
        """
        Validate solution against HARD constraints.
        
        Args:
            run: SchedulingRunModel record
            solution: SchedulingSolution to validate
        
        Raises:
            ValueError: If HARD constraints are violated
        """
        logger.info(f"Validating solution against HARD constraints...")
        validation = self.constraint_service.validate_weekly_schedule(
            run.weekly_schedule_id,
            solution.assignments
        )
        
        if not validation.is_valid():
            # HARD constraints violated - fail the run
            error_summary = "; ".join([
                err.message for err in validation.errors[:10]
            ])
            if len(validation.errors) > 10:
                error_summary += f" ... and {len(validation.errors) - 10} more violations"
            
            try:
                run.status = SchedulingRunStatus.FAILED
                run.solver_status = SolverStatus.INFEASIBLE
                run.error_message = f"HARD constraint violations detected: {error_summary}"
                run.completed_at = datetime.now()
                self.db.commit()
            except SQLAlchemyError as commit_error:
                self.db.rollback()
                logger.error(
                    f"Failed to update run status after validation failure, "
                    f"run_id={run.run_id}, commit_error={commit_error}",
                    exc_info=True
                )
                raise
            
            logger.error(
                f"Solution validation failed: {len(validation.errors)} HARD violations, "
                f"run_id={run.run_id}, weekly_schedule_id={run.weekly_schedule_id}"
            )
            raise ValueError(f"HARD constraint violations: {error_summary}")
        
        logger.info(
            f"Solution validation passed: {len(validation.errors)} HARD violations, "
            f"{len(validation.warnings)} warnings, run_id={run.run_id}"
        )
        if validation.warnings:
            logger.warning(
                f"SOFT constraint warnings: {len(validation.warnings)}, run_id={run.run_id}"
            )
            for warning in validation.warnings[:5]:
                logger.debug(f"  - {warning.message}")
    
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

