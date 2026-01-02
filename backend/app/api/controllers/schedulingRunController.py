"""
Scheduling run controller module.

This module contains business logic for scheduling run management operations including
creation, retrieval, updating, and deletion of optimization runs and their solutions.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List, Optional
from app.db.models.schedulingRunModel import (
    SchedulingRunModel,
    SchedulingRunStatus
)
from app.db.models.schedulingSolutionModel import SchedulingSolutionModel
from app.db.models.weeklyScheduleModel import WeeklyScheduleModel
from app.db.models.userModel import UserModel
from app.db.models.shiftAssignmentModel import ShiftAssignmentModel
from app.db.models.plannedShiftModel import PlannedShiftModel, PlannedShiftStatus
from app.schemas.schedulingRunSchema import (
    SchedulingRunCreate,
    SchedulingRunUpdate,
    SchedulingRunRead,
)
from app.schemas.schedulingSolutionSchema import (
    SchedulingSolutionCreate,
    SchedulingSolutionRead,
)
from app.schemas.shiftAssignmentSchema import ShiftAssignmentRead


# ------------------------
# Helper Functions
# ------------------------

def _serialize_scheduling_run(run: SchedulingRunModel) -> SchedulingRunRead:
    """
    Convert ORM object to Pydantic schema.
    
    Args:
        run: SchedulingRunModel instance
        
    Returns:
        SchedulingRunRead instance
    """
    # Count solutions
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
    )


def _serialize_scheduling_solution(solution: SchedulingSolutionModel) -> SchedulingSolutionRead:
    """
    Convert ORM object to Pydantic schema.
    
    Args:
        solution: SchedulingSolutionModel instance
        
    Returns:
        SchedulingSolutionRead instance
    """
    user_full_name = solution.user.user_full_name if solution.user else None
    role_name = solution.role.role_name if solution.role else None
    # Extract date from datetime (start_time is a datetime, we need just the date)
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


# ------------------------
# CRUD Functions for Scheduling Runs
# ------------------------

async def create_scheduling_run(
    db: Session,
    run_data: SchedulingRunCreate,
    user_id: int
) -> SchedulingRunRead:
    """
    Create a new scheduling run.
    
    Args:
        db: Database session
        run_data: Scheduling run creation data
        user_id: ID of the user creating the run
        
    Returns:
        Created SchedulingRunRead instance
        
    Raises:
        HTTPException: If validation fails or database error occurs
    """
    try:
        # Verify weekly schedule exists
        schedule = db.get(WeeklyScheduleModel, run_data.weekly_schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Weekly schedule not found"
            )
        
        # Verify user exists
        user = db.get(UserModel, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        run = SchedulingRunModel(
            weekly_schedule_id=run_data.weekly_schedule_id,
            status=SchedulingRunStatus.PENDING,
        )
        
        db.add(run)
        db.commit()
        db.refresh(run)
        
        # Ensure relationships are loaded
        _ = run.weekly_schedule
        
        return _serialize_scheduling_run(run)
    
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {error_str}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_all_scheduling_runs(
    db: Session,
    weekly_schedule_id: Optional[int] = None,
    status_filter: Optional[SchedulingRunStatus] = None
) -> List[SchedulingRunRead]:
    """
    Retrieve all scheduling runs, optionally filtered by schedule or status.
    
    Args:
        db: Database session
        weekly_schedule_id: Optional weekly schedule ID to filter by
        status_filter: Optional status to filter by
        
    Returns:
        List of SchedulingRunRead instances
        
    Raises:
        HTTPException: If database error occurs
    """
    try:
        query = db.query(SchedulingRunModel).options(
            joinedload(SchedulingRunModel.solutions)
        )
        
        if weekly_schedule_id:
            query = query.filter(SchedulingRunModel.weekly_schedule_id == weekly_schedule_id)
        
        if status_filter:
            query = query.filter(SchedulingRunModel.status == status_filter)
        
        runs = query.order_by(SchedulingRunModel.started_at.desc()).all()
        return [_serialize_scheduling_run(r) for r in runs]
    
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_scheduling_run(
    db: Session,
    run_id: int
) -> SchedulingRunRead:
    """
    Retrieve a single scheduling run by ID.
    
    Args:
        db: Database session
        run_id: Scheduling run identifier
        
    Returns:
        SchedulingRunRead instance
        
    Raises:
        HTTPException: If run not found or database error occurs
    """
    try:
        run = db.query(SchedulingRunModel).options(
            joinedload(SchedulingRunModel.solutions)
        ).filter(SchedulingRunModel.run_id == run_id).first()
        
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduling run not found"
            )
        
        return _serialize_scheduling_run(run)
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def update_scheduling_run(
    db: Session,
    run_id: int,
    run_data: SchedulingRunUpdate
) -> SchedulingRunRead:
    """
    Update a scheduling run. Used internally to update run status and solver results.
    
    Args:
        db: Database session
        run_id: Scheduling run identifier
        run_data: Update data
        
    Returns:
        Updated SchedulingRunRead instance
        
    Raises:
        HTTPException: If run not found or database error occurs
    """
    try:
        run = db.get(SchedulingRunModel, run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduling run not found"
            )
        
        # Update fields if provided
        if run_data.status is not None:
            run.status = run_data.status
        if run_data.solver_name is not None:
            run.solver_name = run_data.solver_name
        if run_data.objective_value is not None:
            run.objective_value = run_data.objective_value
        if run_data.solver_status is not None:
            run.solver_status = run_data.solver_status
        if run_data.runtime_seconds is not None:
            run.runtime_seconds = run_data.runtime_seconds
        if run_data.completed_at is not None:
            run.completed_at = run_data.completed_at
        
        db.commit()
        db.refresh(run)
        
        # Ensure relationships are loaded
        _ = run.solutions
        
        return _serialize_scheduling_run(run)
    
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {error_str}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def delete_scheduling_run(
    db: Session,
    run_id: int
) -> None:
    """
    Delete a scheduling run and all its solutions.
    
    Args:
        db: Database session
        run_id: Scheduling run identifier
        
    Raises:
        HTTPException: If run not found or database error occurs
    """
    try:
        run = db.get(SchedulingRunModel, run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduling run not found"
            )
        
        db.delete(run)
        db.commit()
    
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {error_str}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


# ------------------------
# Solution Management Functions
# ------------------------

async def create_scheduling_solutions(
    db: Session,
    run_id: int,
    solutions_data: List[SchedulingSolutionCreate]
) -> List[SchedulingSolutionRead]:
    """
    Create multiple scheduling solutions for a run.
    Used internally when storing optimizer results.
    
    Args:
        db: Database session
        run_id: Scheduling run identifier
        solutions_data: List of solution creation data
        
    Returns:
        List of created SchedulingSolutionRead instances
        
    Raises:
        HTTPException: If run not found or database error occurs
    """
    try:
        # Verify run exists
        run = db.get(SchedulingRunModel, run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduling run not found"
            )
        
        solutions = []
        for solution_data in solutions_data:
            solution = SchedulingSolutionModel(
                run_id=run_id,
                planned_shift_id=solution_data.planned_shift_id,
                user_id=solution_data.user_id,
                role_id=solution_data.role_id,
                assignment_score=solution_data.assignment_score,
            )
            db.add(solution)
            solutions.append(solution)
        
        db.commit()
        
        # Refresh all solutions and load relationships
        for solution in solutions:
            db.refresh(solution)
            _ = solution.user
            _ = solution.role
            _ = solution.planned_shift
        
        return [_serialize_scheduling_solution(s) for s in solutions]
    
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {error_str}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_scheduling_solutions(
    db: Session,
    run_id: int
) -> List[SchedulingSolutionRead]:
    """
    Retrieve all solutions for a scheduling run.
    
    Args:
        db: Database session
        run_id: Scheduling run identifier
        
    Returns:
        List of SchedulingSolutionRead instances
        
    Raises:
        HTTPException: If run not found or database error occurs
    """
    try:
        # Verify run exists
        run = db.get(SchedulingRunModel, run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduling run not found"
            )
        
        solutions = db.query(SchedulingSolutionModel).options(
            joinedload(SchedulingSolutionModel.user),
            joinedload(SchedulingSolutionModel.role),
            joinedload(SchedulingSolutionModel.planned_shift)
        ).filter(SchedulingSolutionModel.run_id == run_id).all()
        
        return [_serialize_scheduling_solution(s) for s in solutions]
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def apply_scheduling_solution(
    db: Session,
    run_id: int,
    overwrite: bool = False
) -> dict:
    """
    Apply an optimization solution by converting SchedulingSolution records
    into actual ShiftAssignment records.
    
    Args:
        db: Database session
        run_id: Scheduling run identifier
        overwrite: If True, delete existing assignments for affected shifts before applying.
                  If False, raises error if conflicts exist.
        
    Returns:
        Dictionary with application results:
            - assignments_created: Number of assignments created
            - shifts_updated: Number of shifts marked as fully assigned
            - message: Success message
        
    Raises:
        HTTPException: If run not found, solution invalid, or conflicts exist
    """
    try:
        # 1. Verify run exists and is completed
        run = db.query(SchedulingRunModel).options(
            joinedload(SchedulingRunModel.solutions)
        ).filter(SchedulingRunModel.run_id == run_id).first()
        
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduling run not found"
            )
        
        if run.status != SchedulingRunStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot apply solution. Run status is {run.status.value}, expected COMPLETED"
            )
        
        # 2. Get all selected solutions
        solutions = db.query(SchedulingSolutionModel).filter(
            SchedulingSolutionModel.run_id == run_id,
            SchedulingSolutionModel.is_selected == True
        ).all()
        
        if not solutions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No selected solutions found for this run"
            )
        
        # 3. Check for existing assignments if not overwriting
        if not overwrite:
            shift_ids = list(set([sol.planned_shift_id for sol in solutions]))
            existing = db.query(ShiftAssignmentModel).filter(
                ShiftAssignmentModel.planned_shift_id.in_(shift_ids)
            ).count()
            
            if existing > 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Found {existing} existing assignments. Use overwrite=true to replace them."
                )
        
        # 4. If overwriting, delete existing assignments for affected shifts
        assignments_created = 0
        shifts_updated = set()
        
        if overwrite:
            shift_ids = list(set([sol.planned_shift_id for sol in solutions]))
            deleted = db.query(ShiftAssignmentModel).filter(
                ShiftAssignmentModel.planned_shift_id.in_(shift_ids)
            ).delete(synchronize_session=False)
        
        # 5. Create new shift assignments from solutions
        for solution in solutions:
            # Check if assignment already exists (in case of partial overwrite)
            existing = db.query(ShiftAssignmentModel).filter(
                ShiftAssignmentModel.planned_shift_id == solution.planned_shift_id,
                ShiftAssignmentModel.user_id == solution.user_id,
                ShiftAssignmentModel.role_id == solution.role_id
            ).first()
            
            if not existing:
                assignment = ShiftAssignmentModel(
                    planned_shift_id=solution.planned_shift_id,
                    user_id=solution.user_id,
                    role_id=solution.role_id
                )
                db.add(assignment)
                assignments_created += 1
                shifts_updated.add(solution.planned_shift_id)
        
        # 6. Update PlannedShift status to FULLY_ASSIGNED
        for shift_id in shifts_updated:
            shift = db.get(PlannedShiftModel, shift_id)
            if shift:
                shift.status = PlannedShiftStatus.FULLY_ASSIGNED
        
        # 7. Commit transaction
        db.commit()
        
        return {
            "assignments_created": assignments_created,
            "shifts_updated": len(shifts_updated),
            "message": f"Successfully applied {assignments_created} assignments to {len(shifts_updated)} shifts"
        }
    
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {error_str}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

