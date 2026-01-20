"""
Metrics API Routes
Provides endpoints for fetching dashboard metrics and statistics
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.data.session import get_db
from app.api.dependencies.auth import get_current_user
from app.data.models.user_model import UserModel
from app.api.controllers.metrics_controller import get_dashboard_metrics

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/")
async def get_metrics(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get dashboard metrics
    
    Returns key metrics including:
    - Total employees
    - Upcoming shifts (next 7 days)
    - Coverage rate
    - Total and published schedules
    - Pending time-off requests
    
    Requires authentication.
    """
    metrics = await get_dashboard_metrics(db)
    return metrics
