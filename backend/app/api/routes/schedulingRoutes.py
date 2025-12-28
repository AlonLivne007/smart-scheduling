"""
Scheduling optimization API routes.

This module provides endpoints for triggering and managing schedule optimization.
Corresponds to US-10: Optimization API Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime

from app.db.session import get_db
from app.db.models.weeklyScheduleModel import WeeklyScheduleModel
from app.db.models.schedulingRunModel import SchedulingRunModel
from app.services.schedulingService import SchedulingService
from app.api.dependencies.auth import require_manager
from app.db.models.shiftRoleRequirementsTabel import shift_role_requirements
from sqlalchemy import func


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
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Trigger optimization for a specific weekly schedule.
    
    This endpoint initiates the MIP solver to generate optimal shift assignments
    for all planned shifts in the specified weekly schedule.
    
    Args:
        weekly_schedule_id: ID of the weekly schedule to optimize
        db: Database session
        
    Returns:
        Dictionary containing:
        - run_id: ID of the scheduling run record
        - status: Optimization status (OPTIMAL, INFEASIBLE, etc.)
        - runtime_seconds: Time taken to solve
        - objective_value: Objective function value
        - total_assignments: Number of shift assignments created
        - metrics: Additional optimization metrics
        
    Raises:
        404: If weekly schedule not found
        400: If optimization fails
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
    
    # Run optimization
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
