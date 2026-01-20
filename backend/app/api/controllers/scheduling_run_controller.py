"""
Scheduling run controller module.

This module contains business logic for scheduling run management operations including
creation, retrieval, updating, and deletion of optimization runs and their solutions.
Controllers use repositories for database access - no direct ORM access.
"""

from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session  # Only for type hints

from app.data.repositories.scheduling_run_repository import SchedulingRunRepository
from app.data.repositories import SchedulingSolutionRepository
from app.data.repositories.weekly_schedule_repository import WeeklyScheduleRepository
from app.data.repositories.user_repository import UserRepository
from app.data.models.scheduling_run_model import SchedulingRunStatus
from app.schemas.scheduling_run_schema import (
    SchedulingRunCreate,
    SchedulingRunUpdate,
    SchedulingRunRead,
)
from app.schemas.scheduling_solution_schema import (
    SchedulingSolutionRead,
)
from app.core.exceptions.repository import NotFoundError
from app.data.session_manager import transaction


def _serialize_scheduling_run(run) -> SchedulingRunRead:
    """
    Convert ORM object to Pydantic schema.
    """
    solution_count = len(run.solutions) if run.solutions else 0
    
    return SchedulingRunRead(
        run_id=run.run_id,
        weekly_schedule_id=run.weekly_schedule_id,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        solver_name=None,  # Field doesn't exist in model
        objective_value=run.objective_value,
        solver_status=run.solver_status,
        runtime_seconds=run.runtime_seconds,
        created_by_id=None,
        created_by_name=None,
        solution_count=solution_count,
        error_message=run.error_message,
    )


def _serialize_scheduling_solution(solution) -> SchedulingSolutionRead:
    """
    Convert ORM object to Pydantic schema.
    """
    user_full_name = solution.user.user_full_name if solution.user else None
    role_name = solution.role.role_name if solution.role else None
    shift_date = solution.planned_shift.start_time.date() if solution.planned_shift and solution.planned_shift.start_time else None
    
    return SchedulingSolutionRead(
        solution_id=solution.solution_id,
        run_id=solution.run_id,
        planned_shift_id=solution.planned_shift_id,
        user_id=solution.user_id,
        role_id=solution.role_id,
        assignment_score=solution.assignment_score,
        created_at=solution.created_at,
        user_full_name=user_full_name,
        role_name=role_name,
        shift_date=shift_date,
    )


async def create_scheduling_run(
    run_data: SchedulingRunCreate,
    user_id: int,
    run_repository: SchedulingRunRepository,
    schedule_repository: WeeklyScheduleRepository,
    user_repository: UserRepository,
    db: Session  # For transaction management
) -> SchedulingRunRead:
    """
    Create a new scheduling run.
    
    Business logic:
    - Verify weekly schedule exists
    - Verify user exists
    - Create run with PENDING status
    """
    # Business rule: Verify weekly schedule exists
    schedule_repository.get_or_raise(run_data.weekly_schedule_id)
    
    # Business rule: Verify user exists
    user_repository.get_or_raise(user_id)
    
    with transaction(db):
        run = run_repository.create(
            weekly_schedule_id=run_data.weekly_schedule_id,
            status=SchedulingRunStatus.PENDING,
        )
        
        # Get run with relationships for serialization
        run = run_repository.get_with_solutions(run.run_id)
        return _serialize_scheduling_run(run)


async def list_scheduling_runs(
    run_repository: SchedulingRunRepository,
    weekly_schedule_id: Optional[int] = None,
    status_filter: Optional[SchedulingRunStatus] = None
) -> List[SchedulingRunRead]:
    """
    Retrieve all scheduling runs, optionally filtered by schedule or status.
    """
    if weekly_schedule_id:
        runs = run_repository.get_by_schedule(weekly_schedule_id)
    elif status_filter:
        runs = run_repository.get_by_status(status_filter)
    else:
        runs = run_repository.get_all()
    
    # Load solutions for each run
    runs_with_solutions = []
    for run in runs:
        run = run_repository.get_with_solutions(run.run_id)
        runs_with_solutions.append(run)
    
    # Sort by started_at descending
    runs_with_solutions.sort(key=lambda r: r.started_at if r.started_at else r.run_id, reverse=True)
    
    return [_serialize_scheduling_run(r) for r in runs_with_solutions]


async def get_scheduling_run(
    run_id: int,
    run_repository: SchedulingRunRepository
) -> SchedulingRunRead:
    """
    Retrieve a single scheduling run by ID.
    """
    run = run_repository.get_with_solutions(run_id)
    if not run:
        raise NotFoundError(f"Scheduling run {run_id} not found")
    return _serialize_scheduling_run(run)


async def update_scheduling_run(
    run_id: int,
    run_data: SchedulingRunUpdate,
    run_repository: SchedulingRunRepository,
    db: Session  # For transaction management
) -> SchedulingRunRead:
    """
    Update a scheduling run. Used internally to update run status and solver results.
    
    Business logic:
    - Update fields if provided
    """
    run_repository.get_or_raise(run_id)  # Verify exists
    
    with transaction(db):
        # Update fields
        update_data = {}
        if run_data.status is not None:
            update_data["status"] = run_data.status
        if run_data.objective_value is not None:
            update_data["objective_value"] = run_data.objective_value
        if run_data.solver_status is not None:
            update_data["solver_status"] = run_data.solver_status
        if run_data.runtime_seconds is not None:
            update_data["runtime_seconds"] = run_data.runtime_seconds
        if run_data.completed_at is not None:
            update_data["completed_at"] = run_data.completed_at
        
        if update_data:
            run_repository.update(run_id, **update_data)
        
        # Get updated run with relationships
        run = run_repository.get_with_solutions(run_id)
        return _serialize_scheduling_run(run)


async def delete_scheduling_run(
    run_id: int,
    run_repository: SchedulingRunRepository,
    db: Session  # For transaction management
) -> None:
    """
    Delete a scheduling run and all its solutions.
    
    Business logic:
    - Verify run exists
    - Delete run (solutions cascade)
    """
    run_repository.get_or_raise(run_id)  # Verify exists
    
    with transaction(db):
        run_repository.delete(run_id)


async def get_solutions_for_run(
    run_id: int,
    solution_repository: SchedulingSolutionRepository,
    run_repository: SchedulingRunRepository
) -> List[SchedulingSolutionRead]:
    """
    Get all solutions for a scheduling run.
    
    Business logic:
    - Verify run exists
    - Get solutions with relationships
    """
    run_repository.get_or_raise(run_id)  # Verify run exists
    
    solutions = solution_repository.get_all_with_relationships_by_run(run_id)
    return [_serialize_scheduling_solution(s) for s in solutions]


async def apply_solution_to_schedule(
    run_id: int,
    solution_repository: SchedulingSolutionRepository,
    assignment_repository,
    run_repository: SchedulingRunRepository,
    db: Session  # For transaction management
) -> dict:
    """
    Apply a scheduling solution to create actual shift assignments.
    
    Business logic:
    - Verify run exists and is completed
    - Get selected solutions
    - Create shift assignments
    - Clear existing assignments for the schedule
    """
    run = run_repository.get_with_relations(run_id)
    if not run:
        raise NotFoundError(f"Scheduling run {run_id} not found")
    
    # Business rule: Only completed runs can be applied
    if run.status != SchedulingRunStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot apply solution: run status is {run.status.value}, must be COMPLETED"
        )
    
    # Get selected solutions
    selected_solutions = solution_repository.get_selected_by_run(run_id)
    
    if not selected_solutions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No selected solutions found for this run"
        )
    
    with transaction(db):
        # Clear existing assignments for the schedule
        assignment_repository.delete_by_schedule(run.weekly_schedule_id)
        
        # Create assignments from solutions
        for solution in selected_solutions:
            assignment_repository.create_assignment(
                planned_shift_id=solution.planned_shift_id,
                user_id=solution.user_id,
                role_id=solution.role_id
            )
        
        return {
            "message": f"Applied {len(selected_solutions)} assignments from solution",
            "run_id": run_id,
            "assignments_created": len(selected_solutions)
        }
