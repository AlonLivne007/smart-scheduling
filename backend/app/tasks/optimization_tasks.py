"""
Async optimization tasks using Celery.

This module contains Celery tasks for running long-running optimization jobs
in the background to prevent request timeouts.

Tasks use repositories for database access - no direct ORM access.
"""

from typing import Optional
from datetime import datetime

from app.celery_app import celery_app
from app.db.session_manager import get_db_session, transaction
from app.repositories.scheduling_run_repository import SchedulingRunRepository
from app.repositories.optimization_config_repository import OptimizationConfigRepository
from app.repositories.shift_repository import ShiftRepository, ShiftAssignmentRepository
from app.repositories.scheduling_solution_repository import SchedulingSolutionRepository
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.shift_template_repository import ShiftTemplateRepository
from app.repositories.weekly_schedule_repository import WeeklyScheduleRepository
from app.repositories.time_off_request_repository import TimeOffRequestRepository
from app.repositories.system_constraints_repository import SystemConstraintsRepository
from app.repositories.employee_preferences_repository import EmployeePreferencesRepository
from app.db.models.schedulingRunModel import SchedulingRunModel, SchedulingRunStatus
from app.services.optimization_data_services.optimization_data_builder import OptimizationDataBuilder
from app.services.scheduling.scheduling_service import SchedulingService
from app.services.scheduling.persistence import SchedulingPersistence
from app.exceptions.repository import NotFoundError


@celery_app.task(bind=True, name='app.tasks.optimization_tasks.run_optimization')
def run_optimization_task(
    self,
    run_id: int
):
    """
    Celery task to run schedule optimization asynchronously.
    
    This task:
    1. Creates its own database session
    2. Creates repositories and services
    3. Uses repositories/services for all database operations
    4. Manages transactions properly
    
    Args:
        self: Celery task instance (for updating state)
        run_id: ID of the SchedulingRun record (already created with PENDING status)
    
    Returns:
        Dict with run_id, status, and metrics
    """
    with get_db_session() as db:
        try:
            # Create repositories
            run_repository = SchedulingRunRepository(db)
            config_repository = OptimizationConfigRepository(db)
            shift_repository = ShiftRepository(db)
            assignment_repository = ShiftAssignmentRepository(db)
            solution_repository = SchedulingSolutionRepository(db)
            user_repository = UserRepository(db)
            role_repository = RoleRepository(db)
            template_repository = ShiftTemplateRepository(db)
            schedule_repository = WeeklyScheduleRepository(db)
            time_off_repository = TimeOffRequestRepository(db)
            constraints_repository = SystemConstraintsRepository(db)
            preferences_repository = EmployeePreferencesRepository(db)
            
            # Get the run record
            run = run_repository.get_by_id(run_id)
            
            if not run:
                raise ValueError(f"SchedulingRun {run_id} not found")
            
            # Update state for monitoring
            self.update_state(
                state='RUNNING',
                meta={'status': 'Building optimization model', 'run_id': run_id}
            )
            
            # Create data builder with repositories
            data_builder = OptimizationDataBuilder(
                user_repository=user_repository,
                shift_repository=shift_repository,
                assignment_repository=assignment_repository,
                role_repository=role_repository,
                template_repository=template_repository,
                schedule_repository=schedule_repository,
                time_off_repository=time_off_repository,
                constraints_repository=constraints_repository,
                preferences_repository=preferences_repository
            )
            
            # Create persistence with repositories
            persistence = SchedulingPersistence(
                shift_repository=shift_repository,
                assignment_repository=assignment_repository,
                solution_repository=solution_repository
            )
            
            # Create service with repositories
            scheduling_service = SchedulingService(
                run_repository=run_repository,
                config_repository=config_repository,
                data_builder=data_builder,
                persistence=persistence
            )
            
            # Execute optimization within a transaction
            with transaction(db):
                # This will update the run record internally
                run, solution = scheduling_service._execute_optimization_for_run(run)
            
            return {
                'run_id': run.run_id,
                'status': run.status.value,
                'solver_status': run.solver_status.value if run.solver_status else None,
                'objective_value': float(run.objective_value) if run.objective_value else None,
                'runtime_seconds': float(run.runtime_seconds) if run.runtime_seconds else None,
                'solutions_count': run.total_assignments or 0,
                'message': 'Optimization completed successfully'
            }
            
        except NotFoundError as e:
            # Update run record with error
            try:
                run_repository = SchedulingRunRepository(db)
                run = run_repository.get_by_id(run_id)
                
                if run:
                    with transaction(db):
                        run_repository.update_status(
                            run_id,
                            SchedulingRunStatus.FAILED,
                            error_message=str(e)
                        )
            except:
                pass
            
            # Re-raise the exception so Celery marks the task as failed
            raise ValueError(f"Optimization failed: {str(e)}")
            
        except Exception as e:
            # Update run record with error
            try:
                run_repository = SchedulingRunRepository(db)
                run = run_repository.get_by_id(run_id)
                
                if run:
                    with transaction(db):
                        run_repository.update_status(
                            run_id,
                            SchedulingRunStatus.FAILED,
                            error_message=str(e)
                        )
            except:
                pass
            
            # Re-raise the exception so Celery marks the task as failed
            raise
