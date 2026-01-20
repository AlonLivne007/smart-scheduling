"""
Scheduling optimization controller.

This module contains business logic for scheduling optimization operations
including triggering optimization, retrieving run details with metrics, and
calculating required positions.
Controllers use repositories for database access - no direct ORM access.
"""

from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session  # Only for type hints

from app.repositories.weekly_schedule_repository import WeeklyScheduleRepository
from app.repositories.scheduling_run_repository import SchedulingRunRepository
from app.repositories.optimization_config_repository import OptimizationConfigRepository
from app.repositories.shift_template_repository import ShiftTemplateRepository
from app.tasks.optimization_tasks import run_optimization_task
from app.exceptions.repository import NotFoundError, ConflictError
from app.db.session_manager import transaction


def _calculate_coverage_percentage(
    run,
    schedule,
    template_repository: ShiftTemplateRepository
) -> float:
    """
    Calculate coverage percentage for a scheduling run.
    
    Uses repository to get role requirements.
    """
    if not run.solutions or not schedule:
        return 0.0
    
    total_required = _compute_total_required_positions(schedule, template_repository)
    if total_required == 0:
        return 0.0
    
    return (len(run.solutions) / total_required) * 100


def _compute_total_required_positions(
    schedule,
    template_repository: ShiftTemplateRepository
) -> int:
    """
    Calculate total required positions for a weekly schedule.
    
    Uses repository to get role requirements.
    """
    if not schedule.planned_shifts:
        return 0

    template_ids = [ps.shift_template_id for ps in schedule.planned_shifts if ps.shift_template_id]
    if not template_ids:
        return 0

    # Get role requirements using repository
    template_role_map = template_repository.get_role_requirements_with_counts(template_ids)
    
    # Sum required counts per template
    required_by_template = {
        template_id: sum(role_map.values())
        for template_id, role_map in template_role_map.items()
    }

    return sum(required_by_template.get(ps.shift_template_id, 0) for ps in schedule.planned_shifts)


async def trigger_optimization(
    weekly_schedule_id: int,
    config_id: Optional[int],
    schedule_repository: WeeklyScheduleRepository,
    config_repository: OptimizationConfigRepository,
    run_repository: SchedulingRunRepository,
    db: Session  # For transaction management
) -> Dict[str, Any]:
    """
    Trigger async optimization for a weekly schedule.
    
    Creates a SchedulingRun record with PENDING status and dispatches
    an async Celery task to perform the optimization.
    
    Business logic:
    - Verify schedule exists
    - Verify config exists if provided
    - Create run with PENDING status
    - Dispatch Celery task
    """
    try:
        # Business rule: Verify schedule exists
        schedule_repository.get_or_raise(weekly_schedule_id)
        
        # Business rule: Verify config if provided
        if config_id:
            config_repository.get_or_raise(config_id)
        
        with transaction(db):
            # Create SchedulingRun record with PENDING status
            run = run_repository.create(
                weekly_schedule_id=weekly_schedule_id,
                config_id=config_id,
                status="PENDING"  # Will be converted to enum by model
            )
            
            # Dispatch async Celery task
            task = run_optimization_task.delay(run.run_id)
            
            return {
                "run_id": run.run_id,
                "status": run.status.value if hasattr(run.status, 'value') else str(run.status),
                "task_id": task.id,
                "message": f"Optimization task dispatched. Poll GET /scheduling/runs/{run.run_id} for status."
            }
            
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


async def get_scheduling_run_with_metrics(
    run_id: int,
    run_repository: SchedulingRunRepository,
    schedule_repository: WeeklyScheduleRepository,
    template_repository: ShiftTemplateRepository
) -> Dict[str, Any]:
    """
    Get details of a specific scheduling run with calculated metrics.
    
    Business logic:
    - Get run with solutions
    - Get schedule
    - Calculate metrics
    """
    try:
        run = run_repository.get_with_solutions(run_id)
        if not run:
            raise NotFoundError(f"Scheduling run {run_id} not found")
        
        schedule = schedule_repository.get_by_id(run.weekly_schedule_id)
        
        # Calculate metrics from solutions
        coverage_pct = 0.0
        avg_pref_score = 0.0
        employees_used = 0

        if run.solutions:
            employees_used = len(set(s.user_id for s in run.solutions))
            scores = [s.assignment_score for s in run.solutions if s.assignment_score is not None]
            avg_pref_score = sum(scores) / len(scores) if scores else 0.0

            coverage_pct = _calculate_coverage_percentage(run, schedule, template_repository)
        
        return {
            "run_id": run.run_id,
            "weekly_schedule_id": run.weekly_schedule_id,
            "status": run.solver_status.value if run.solver_status else run.status.value,
            "runtime_seconds": run.runtime_seconds,
            "objective_value": run.objective_value,
            "total_assignments": run.total_assignments,
            "coverage_percentage": round(coverage_pct, 1),
            "average_preference_score": round(avg_pref_score, 2),
            "employees_used": employees_used,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "error_message": run.error_message
        }
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduling run {run_id} not found"
        )


async def get_schedule_runs_with_metrics(
    weekly_schedule_id: int,
    run_repository: SchedulingRunRepository,
    schedule_repository: WeeklyScheduleRepository,
    template_repository: ShiftTemplateRepository
) -> List[Dict[str, Any]]:
    """
    Get all optimization runs for a specific weekly schedule with metrics.
    
    Business logic:
    - Get all runs for schedule
    - Calculate metrics for each
    """
    try:
        schedule_repository.get_or_raise(weekly_schedule_id)  # Verify schedule exists
        
        runs = run_repository.get_by_schedule(weekly_schedule_id)
        
        result = []
        for run in runs:
            # Get run with solutions
            run_with_solutions = run_repository.get_with_solutions(run.run_id)
            schedule = schedule_repository.get_by_id(weekly_schedule_id)
            
            # Calculate coverage for each run
            coverage_pct = _calculate_coverage_percentage(run_with_solutions, schedule, template_repository)
            
            result.append({
                "run_id": run.run_id,
                "status": run.solver_status.value if run.solver_status else run.status.value,
                "runtime_seconds": run.runtime_seconds,
                "total_assignments": run.total_assignments,
                "coverage_percentage": round(coverage_pct, 1),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None
            })
        
        # Sort by completed_at descending
        result.sort(key=lambda r: r["completed_at"] or "", reverse=True)
        
        return result
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weekly schedule {weekly_schedule_id} not found"
        )
