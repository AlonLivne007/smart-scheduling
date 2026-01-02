"""
Scheduling optimization API routes.

This module provides endpoints for triggering and managing schedule optimization.
Corresponds to US-10: Optimization API Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime

from app.db.session import get_db
from app.db.models.weeklyScheduleModel import WeeklyScheduleModel
from app.db.models.schedulingRunModel import SchedulingRunModel, SchedulingRunStatus
from app.db.models.optimizationConfigModel import OptimizationConfigModel
from app.api.dependencies.auth import require_manager
from app.db.models.shiftRoleRequirementsTabel import shift_role_requirements
from sqlalchemy import func
from app.tasks.optimization_tasks import run_optimization_task


def _compute_total_required_positions(schedule: WeeklyScheduleModel, db: Session) -> int:
    if not schedule.planned_shifts:
        return 0

    template_ids = [ps.shift_template_id for ps in schedule.planned_shifts if ps.shift_template_id]
    if not template_ids:
        return 0

    # required per template_id
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

router = APIRouter(prefix="/scheduling", tags=["Scheduling Optimization"])


@router.post("/optimize/{weekly_schedule_id}", dependencies=[Depends(require_manager)])
async def optimize_schedule(
    weekly_schedule_id: int,
    config_id: Optional[int] = Query(None, description="Optimization configuration ID (uses default if not specified)"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Trigger async optimization for a specific weekly schedule.
    
    Creates a SchedulingRun record with PENDING status and dispatches
    an async Celery task to perform the optimization. The client should
    poll the run status endpoint to check for completion.
    
    Args:
        weekly_schedule_id: ID of the weekly schedule to optimize
        config_id: Optional optimization configuration ID (uses default if not specified)
        db: Database session
        
    Returns:
        Dictionary containing:
        - run_id: ID of the scheduling run record
        - status: Initial status (PENDING)
        - message: Instructions for polling
        - task_id: Celery task ID for tracking
        
    Raises:
        404: If weekly schedule or config not found
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


@router.get("/optimize/{weekly_schedule_id}", deprecated=True, dependencies=[Depends(require_manager)])
async def optimize_schedule_sync(
    weekly_schedule_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    DEPRECATED: Synchronous optimization endpoint.
    
    This endpoint runs optimization synchronously and may timeout on large schedules.
    Use POST /scheduling/optimize/{weekly_schedule_id} instead for async execution.
    
    Args:
        weekly_schedule_id: ID of the weekly schedule to optimize
        db: Database session
        
    Returns:
        Dictionary containing optimization results
        
    Raises:
        404: If weekly schedule not found
        400: If optimization fails
    """
    from app.services.schedulingService import SchedulingService
    
    # Verify schedule exists
    schedule = db.query(WeeklyScheduleModel).filter(
        WeeklyScheduleModel.weekly_schedule_id == weekly_schedule_id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weekly schedule {weekly_schedule_id} not found"
        )
    
    # Run optimization synchronously
    service = SchedulingService(db)
    
    try:
        run, solution = service.optimize_schedule(weekly_schedule_id)
        
        # Calculate metrics from solution
        coverage_pct = 0.0
        avg_pref_score = 0.0
        employees_used = 0
        
        if solution.assignments:
            # Count unique employees
            employees_used = len(set(a['user_id'] for a in solution.assignments))
            
            # Calculate average preference score
            scores = [a.get('preference_score', 0) for a in solution.assignments if a.get('preference_score') is not None]
            avg_pref_score = sum(scores) / len(scores) if scores else 0.0
            
            # Calculate coverage (assignments vs total REQUIRED positions)
            total_required = _compute_total_required_positions(schedule, db)
            if total_required > 0:
                coverage_pct = (len(solution.assignments) / total_required) * 100
        
        return {
            "run_id": run.run_id,
            "weekly_schedule_id": weekly_schedule_id,
            "status": run.solver_status.value if run.solver_status else run.status.value,
            "runtime_seconds": run.runtime_seconds,
            "objective_value": run.objective_value,
            "total_assignments": run.total_assignments,
            "metrics": {
                "coverage_percentage": round(coverage_pct, 1),
                "average_preference_score": round(avg_pref_score, 2),
                "employees_used": employees_used
            },
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Optimization failed: {str(e)}"
        )


@router.get("/runs/{run_id}")
async def get_scheduling_run(
    run_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get details of a specific scheduling run.
    
    Args:
        run_id: ID of the scheduling run
        db: Database session
        
    Returns:
        Scheduling run details and metrics
        
    Raises:
        404: If run not found
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
            total_required = _compute_total_required_positions(run.weekly_schedule, db)
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


@router.get("/runs/schedule/{weekly_schedule_id}")
async def get_schedule_runs(
    weekly_schedule_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all optimization runs for a specific weekly schedule.
    
    Args:
        weekly_schedule_id: ID of the weekly schedule
        db: Database session
        
    Returns:
        List of scheduling runs ordered by completion time (newest first)
    """
    runs = db.query(SchedulingRunModel).filter(
        SchedulingRunModel.weekly_schedule_id == weekly_schedule_id
    ).order_by(SchedulingRunModel.completed_at.desc()).all()
    
    result = []
    for run in runs:
        # Calculate coverage for each run
        coverage_pct = 0.0
        if run.solutions and run.weekly_schedule:
            total_required = _compute_total_required_positions(run.weekly_schedule, db)
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
