"""
Async optimization tasks using Celery.

This module contains Celery tasks for running long-running optimization jobs
in the background to prevent request timeouts.
"""

from typing import Optional
from datetime import datetime

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models.schedulingRunModel import SchedulingRunModel, SchedulingRunStatus
from app.services.scheduling.scheduling_service import SchedulingService


@celery_app.task(bind=True, name='app.tasks.optimization_tasks.run_optimization')
def run_optimization_task(
    self,
    run_id: int
):
    """
    Celery task to run schedule optimization asynchronously.
    
    This task updates the SchedulingRun record with RUNNING status,
    calls the SchedulingService to perform optimization, and updates
    the record with results.
    
    Args:
        self: Celery task instance (for updating state)
        run_id: ID of the SchedulingRun record (already created with PENDING status)
    
    Returns:
        Dict with run_id, status, and metrics
    """
    db = SessionLocal()
    
    try:
        # Get the run record
        run = db.query(SchedulingRunModel).filter(
            SchedulingRunModel.run_id == run_id
        ).first()
        
        if not run:
            raise ValueError(f"SchedulingRun {run_id} not found")
        
        # Update state for monitoring
        self.update_state(
            state='RUNNING',
            meta={'status': 'Building optimization model', 'run_id': run_id}
        )
        
        # Create service and run optimization
        # The service handles all the logic: data building, solving, storing results
        scheduling_service = SchedulingService(db)
        
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
        
    except Exception as e:
        # Update run record with error
        try:
            run = db.query(SchedulingRunModel).filter(
                SchedulingRunModel.run_id == run_id
            ).first()
            
            if run:
                run.status = SchedulingRunStatus.FAILED
                run.completed_at = datetime.now()
                run.error_message = str(e)
                db.commit()
        except:
            pass
        
        # Re-raise the exception so Celery marks the task as failed
        raise
        
    finally:
        db.close()
