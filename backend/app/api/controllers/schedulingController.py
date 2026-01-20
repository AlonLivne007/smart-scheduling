"""
Scheduling optimization controller.

This module contains business logic for scheduling optimization operations
including triggering optimization, retrieving run details with metrics, and
calculating required positions.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.db.models.weeklyScheduleModel import WeeklyScheduleModel
from app.db.models.schedulingRunModel import SchedulingRunModel, SchedulingRunStatus
from app.db.models.optimizationConfigModel import OptimizationConfigModel
from app.db.models.shiftRoleRequirementsTabel import shift_role_requirements
from app.tasks.optimization_tasks import run_optimization_task


def compute_total_required_positions(
    schedule: WeeklyScheduleModel,
    db: Session
) -> int:
    """
    Calculate total required positions for a weekly schedule.
    
    Args:
        schedule: WeeklyScheduleModel instance
        db: Database session
        
    Returns:
        Total number of required positions across all shifts
    """
    if not schedule.planned_shifts:
        return 0

    template_ids = [ps.shift_template_id for ps in schedule.planned_shifts if ps.shift_template_id]
    if not template_ids:
        return 0

    # Required per template_id
    rows = (
        db.query(
            shift_role_requirements.c.shift_template_id,
            func.sum(shift_role_requirements.c.required_count).label("required_total"),
        )
        .filter(shift_role_requirements.c.shift_template_id.in_(template_ids))
        .group_by(shift_role_requirements.c.shift_template_id)
        .all()
    )
    required_by_template = {r.shift_template_id: int(r.required_total or 0) for r in rows}

    return sum(required_by_template.get(ps.shift_template_id, 0) for ps in schedule.planned_shifts)


async def trigger_optimization(
    db: Session,
    weekly_schedule_id: int,
    config_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Trigger async optimization for a weekly schedule.
    
    Creates a SchedulingRun record with PENDING status and dispatches
    an async Celery task to perform the optimization.
    
    Args:
        db: Database session
        weekly_schedule_id: ID of the weekly schedule to optimize
        config_id: Optional optimization configuration ID (uses default if not specified)
        
    Returns:
        Dictionary containing:
        - run_id: ID of the scheduling run record
        - status: Initial status (PENDING)
        - message: Instructions for polling
        - task_id: Celery task ID for tracking
        
    Raises:
        HTTPException: If weekly schedule or config not found
    """
    # Verify schedule exists
    schedule = db.query(WeeklyScheduleModel).filter(
        WeeklyScheduleModel.weekly_schedule_id == weekly_schedule_id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weekly schedule {weekly_schedule_id} not found"
        )
    
    # Verify config if provided
    if config_id:
        config = db.query(OptimizationConfigModel).filter(
            OptimizationConfigModel.config_id == config_id
        ).first()
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Optimization config {config_id} not found"
            )
    
    # Create SchedulingRun record with PENDING status
    run = SchedulingRunModel(
        weekly_schedule_id=weekly_schedule_id,
        config_id=config_id,
        status=SchedulingRunStatus.PENDING
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    
    # Dispatch async Celery task
    task = run_optimization_task.delay(run.run_id)
    
    return {
        "run_id": run.run_id,
        "status": run.status.value,
        "task_id": task.id,
        "message": f"Optimization task dispatched. Poll GET /scheduling/runs/{run.run_id} for status."
    }


async def get_scheduling_run_with_metrics(
    db: Session,
    run_id: int
) -> Dict[str, Any]:
    """
    Get details of a specific scheduling run with calculated metrics.
    
    Args:
        db: Database session
        run_id: ID of the scheduling run
        
    Returns:
        Dictionary containing scheduling run details and metrics
        
    Raises:
        HTTPException: If run not found
    """
    run = db.query(SchedulingRunModel).filter(
        SchedulingRunModel.run_id == run_id
    ).first()
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduling run {run_id} not found"
        )
    
    # Calculate metrics from solutions
    coverage_pct = 0.0
    avg_pref_score = 0.0
    employees_used = 0

    if run.solutions:
        employees_used = len(set(s.user_id for s in run.solutions))
        scores = [s.assignment_score for s in run.solutions if s.assignment_score is not None]
        avg_pref_score = sum(scores) / len(scores) if scores else 0.0

        if run.weekly_schedule:
            total_required = compute_total_required_positions(run.weekly_schedule, db)
            if total_required > 0:
                coverage_pct = (len(run.solutions) / total_required) * 100
    
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


async def get_schedule_runs_with_metrics(
    db: Session,
    weekly_schedule_id: int
) -> List[Dict[str, Any]]:
    """
    Get all optimization runs for a specific weekly schedule with metrics.
    
    Args:
        db: Database session
        weekly_schedule_id: ID of the weekly schedule
        
    Returns:
        List of scheduling runs with metrics, ordered by completion time (newest first)
    """
    runs = db.query(SchedulingRunModel).filter(
        SchedulingRunModel.weekly_schedule_id == weekly_schedule_id
    ).order_by(SchedulingRunModel.completed_at.desc()).all()
    
    result = []
    for run in runs:
        # Calculate coverage for each run
        coverage_pct = 0.0
        if run.solutions and run.weekly_schedule:
            total_required = compute_total_required_positions(run.weekly_schedule, db)
            if total_required > 0:
                coverage_pct = (len(run.solutions) / total_required) * 100
        
        result.append({
            "run_id": run.run_id,
            "status": run.solver_status.value if run.solver_status else run.status.value,
            "runtime_seconds": run.runtime_seconds,
            "total_assignments": run.total_assignments,
            "coverage_percentage": round(coverage_pct, 1),
            "completed_at": run.completed_at.isoformat() if run.completed_at else None
        })
    
    return result
