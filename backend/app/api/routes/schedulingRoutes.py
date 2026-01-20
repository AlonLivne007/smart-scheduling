"""
Scheduling optimization API routes.

This module provides endpoints for triggering and managing schedule optimization.
Corresponds to US-10: Optimization API Endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.db.session import get_db
from app.api.dependencies.auth import require_manager
from app.api.controllers.schedulingController import trigger_optimization

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
    return await trigger_optimization(db, weekly_schedule_id, config_id)
