"""
Scheduling Service - Main Orchestrator.

This is the main entry point for scheduling optimization. It orchestrates
data building, solving, validation, and persistence.
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.optimization_data_services import OptimizationDataBuilder, OptimizationData
from app.services.constraintService import ConstraintService
from app.db.models.optimizationConfigModel import OptimizationConfigModel
from app.db.models.schedulingRunModel import SchedulingRunModel, SchedulingRunStatus, SolverStatus
from app.services.scheduling.mip_solver import MipSchedulingSolver
from app.services.scheduling.persistence import SchedulingPersistence
from app.services.scheduling.run_status import map_to_solver_status_enum, build_error_message
from app.services.scheduling.types import SchedulingSolution


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
            
        except Exception as e:
            # Update run status to FAILED
            run.status = SchedulingRunStatus.FAILED
            run.completed_at = datetime.now()
            run.error_message = str(e)
            self.db.commit()
            
            print(f"\n❌ Optimization failed: {e}")
            raise
    
    def _execute_optimization_for_run(self, run: SchedulingRunModel):
        """
        Execute optimization for an existing run record (used by async Celery task).
        
        This method does NOT apply assignments to the schedule - it only stores
        solution proposals in SchedulingSolutionModel.
        
        Args:
            run: SchedulingRunModel record (already created with PENDING status)
        """
        try:
            # Execute optimization without applying assignments
            run, solution = self._execute_run(run, apply_assignments=False)
        except Exception as e:
            # Update run status to FAILED
            run.status = SchedulingRunStatus.FAILED
            run.completed_at = datetime.now()
            run.error_message = str(e)
            self.db.commit()
            
            print(f"\n❌ Optimization failed: {e}")
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
        # Update status to RUNNING
        run.status = SchedulingRunStatus.RUNNING
        if not run.started_at:
            run.started_at = datetime.now()
        self.db.commit()
        
        # Load configuration
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
        
        # Build optimization data
        print(f"Building optimization data for weekly schedule {run.weekly_schedule_id}...")
        data = self.data_builder.build(run.weekly_schedule_id)
        
        print(f"Employees: {len(data.employees)}, Shifts: {len(data.shifts)}")
        
        # Build and solve MIP model
        print(f"Building MIP model...")
        solution = self.solver.solve(data, config)
        
        # Check if optimization was infeasible or failed
        if solution.status in ['INFEASIBLE', 'NO_SOLUTION_FOUND']:
            # Optimization failed - no feasible solution exists
            run.status = SchedulingRunStatus.FAILED
            run.completed_at = datetime.now()
            run.runtime_seconds = solution.runtime_seconds
            run.total_assignments = 0
            run.solver_status = map_to_solver_status_enum(solution.status)
            run.error_message = build_error_message(solution.status)
            
            self.db.commit()
            self.db.refresh(run)
            
            print(f"\n❌ Optimization failed: {solution.status}")
            print(f"Error message: {run.error_message}")
            
            return run, solution
        
        # Validate solution against HARD constraints BEFORE persisting
        if solution.status in ['OPTIMAL', 'FEASIBLE']:
            print(f"Validating solution against HARD constraints...")
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
                
                run.status = SchedulingRunStatus.FAILED
                run.solver_status = SolverStatus.INFEASIBLE
                run.error_message = f"HARD constraint violations detected: {error_summary}"
                run.completed_at = datetime.now()
                self.db.commit()
                
                print(f"\n❌ Solution validation failed: {len(validation.errors)} HARD violations")
                raise ValueError(f"HARD constraint violations: {error_summary}")
            
            print(f"✅ Solution validation passed: {len(validation.errors)} HARD violations, {len(validation.warnings)} warnings")
            if validation.warnings:
                print(f"  ⚠️  SOFT constraint warnings: {len(validation.warnings)}")
                for warning in validation.warnings[:5]:
                    print(f"    - {warning.message}")
                if len(validation.warnings) > 5:
                    print(f"    ... and {len(validation.warnings) - 5} more warnings")
        
        # Clear existing assignments if applying new ones
        if apply_assignments:
            print(f"Clearing existing assignments...")
            self.persistence.clear_existing_assignments(run.weekly_schedule_id)
        
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
            print(f"Creating {len(solution.assignments)} shift assignments...")
        else:
            print(f"Storing {len(solution.assignments)} solution records...")
        
        self.persistence.persist_solution_and_apply_assignments(
            run.run_id,
            solution.assignments,
            apply_assignments=apply_assignments,
            commit=False  # Commit together with run update
        )
        
        # Commit all changes (clear + persist + run update) in single transaction
        self.db.commit()
        self.db.refresh(run)
        
        if apply_assignments:
            print(f"\n✅ SchedulingRun {run.run_id} created with {len(solution.assignments)} assignments")
            print(f"✅ Created {len(solution.assignments)} shift assignments in the schedule")
        else:
            print(f"\n✅ SchedulingRun {run.run_id} completed with {len(solution.assignments)} assignments")
        
        return run, solution

