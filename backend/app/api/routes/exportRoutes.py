"""
Export API Routes
Provides endpoints for exporting schedules to PDF and Excel
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Literal

from app.db.session import get_db
from app.api.dependencies.auth import get_current_user
from app.db.models.userModel import UserModel
from app.api.controllers.exportController import export_schedule_pdf, export_schedule_excel

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/schedule/{schedule_id}")
async def export_schedule(
    schedule_id: int,
    format: Literal["pdf", "excel"] = "pdf",
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Export a weekly schedule to PDF or Excel format
    
    Args:
        schedule_id: ID of the schedule to export
        format: Export format - either "pdf" or "excel"
        
    Returns:
        File download with appropriate content type
        
    Requires authentication.
    """
    try:
        if format == "pdf":
            content = await export_schedule_pdf(db, schedule_id)
            media_type = "application/pdf"
            filename = f"schedule_{schedule_id}.pdf"
        elif format == "excel":
            content = await export_schedule_excel(db, schedule_id)
            media_type = "text/csv"  # Using CSV for now
            filename = f"schedule_{schedule_id}.csv"
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'pdf' or 'excel'")
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
