"""
Export Controller
Handles exporting schedules to PDF and Excel formats
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any, List
from io import BytesIO
import json

from app.db.models.weeklyScheduleModel import WeeklyScheduleModel
from app.db.models.plannedShiftModel import PlannedShiftModel
from app.db.models.shiftAssignmentModel import ShiftAssignmentModel
from app.db.models.userModel import UserModel
from app.db.models.shiftTemplateModel import ShiftTemplateModel


async def export_schedule_pdf(db: Session, schedule_id: int) -> bytes:
    """
    Export a weekly schedule to PDF format
    
    Args:
        db: Database session
        schedule_id: ID of the weekly schedule to export
        
    Returns:
        PDF file as bytes
        
    Raises:
        ValueError: If schedule not found
    """
    # Get schedule with all data
    schedule = db.query(WeeklyScheduleModel).filter(
        WeeklyScheduleModel.weekly_schedule_id == schedule_id
    ).first()
    
    if not schedule:
        raise ValueError(f"Schedule with ID {schedule_id} not found")
    
    # Get all planned shifts for this schedule
    planned_shifts = db.query(PlannedShiftModel).filter(
        PlannedShiftModel.weekly_schedule_id == schedule_id
    ).all()
    
    # Organize shifts by day
    shifts_by_day = {}
    week_start = schedule.week_start_date
    
    for i in range(7):
        day_date = week_start + timedelta(days=i)
        day_str = day_date.strftime('%Y-%m-%d')
        shifts_by_day[day_str] = []
    
    # Add shifts to their respective days
    for shift in planned_shifts:
        shift_date = shift.date.strftime('%Y-%m-%d')
        if shift_date in shifts_by_day:
            # Get template info
            template = db.query(ShiftTemplateModel).filter(
                ShiftTemplateModel.shift_template_id == shift.shift_template_id
            ).first()
            
            # Get assignments
            assignments = db.query(ShiftAssignmentModel).filter(
                ShiftAssignmentModel.planned_shift_id == shift.planned_shift_id
            ).all()
            
            shift_data = {
                'time': f"{template.start_time} - {template.end_time}" if template else "N/A",
                'template_name': template.shift_template_name if template else "Unnamed",
                'location': shift.location or template.location if template else "",
                'assignments': [
                    {
                        'employee': db.query(UserModel).filter(
                            UserModel.user_id == assignment.user_id
                        ).first().user_full_name if assignment.user_id else "Unassigned",
                        'role': assignment.role_id
                    }
                    for assignment in assignments
                ]
            }
            shifts_by_day[shift_date].append(shift_data)
    
    # For now, return a simple text representation as bytes
    # In production, you would use a library like reportlab or weasyprint
    pdf_content = generate_simple_pdf(schedule, shifts_by_day)
    
    return pdf_content


async def export_schedule_excel(db: Session, schedule_id: int) -> bytes:
    """
    Export a weekly schedule to Excel format
    
    Args:
        db: Database session
        schedule_id: ID of the weekly schedule to export
        
    Returns:
        Excel file as bytes
        
    Raises:
        ValueError: If schedule not found
    """
    # Get schedule with all data
    schedule = db.query(WeeklyScheduleModel).filter(
        WeeklyScheduleModel.weekly_schedule_id == schedule_id
    ).first()
    
    if not schedule:
        raise ValueError(f"Schedule with ID {schedule_id} not found")
    
    # Get all planned shifts for this schedule
    planned_shifts = db.query(PlannedShiftModel).filter(
        PlannedShiftModel.weekly_schedule_id == schedule_id
    ).all()
    
    # Prepare data for Excel
    rows = []
    rows.append(['Weekly Schedule Export'])
    rows.append(['Week Starting:', schedule.week_start_date.strftime('%Y-%m-%d')])
    rows.append(['Status:', schedule.status.value])
    rows.append([])  # Empty row
    rows.append(['Date', 'Day', 'Shift', 'Time', 'Location', 'Assigned Employee', 'Role'])
    
    # Add shift data
    for shift in planned_shifts:
        # Get template info
        template = db.query(ShiftTemplateModel).filter(
            ShiftTemplateModel.shift_template_id == shift.shift_template_id
        ).first()
        
        # Get assignments
        assignments = db.query(ShiftAssignmentModel).filter(
            ShiftAssignmentModel.planned_shift_id == shift.planned_shift_id
        ).all()
        
        shift_date = shift.date.strftime('%Y-%m-%d')
        day_name = shift.date.strftime('%A')
        template_name = template.shift_template_name if template else "Unnamed"
        time_range = f"{template.start_time} - {template.end_time}" if template else "N/A"
        location = shift.location or (template.location if template else "")
        
        if assignments:
            for assignment in assignments:
                employee = db.query(UserModel).filter(
                    UserModel.user_id == assignment.user_id
                ).first()
                employee_name = employee.user_full_name if employee else "Unassigned"
                
                rows.append([
                    shift_date,
                    day_name,
                    template_name,
                    time_range,
                    location,
                    employee_name,
                    assignment.role_id or ""
                ])
        else:
            # No assignments
            rows.append([
                shift_date,
                day_name,
                template_name,
                time_range,
                location,
                "UNASSIGNED",
                ""
            ])
    
    # Generate CSV format (simple export without external dependencies)
    # In production, use openpyxl or xlsxwriter for proper Excel files
    csv_content = generate_csv(rows)
    
    return csv_content


def generate_simple_pdf(schedule: WeeklyScheduleModel, shifts_by_day: Dict[str, List]) -> bytes:
    """
    Generate a simple PDF representation
    For production, use reportlab or weasyprint
    """
    # Simple text-based PDF placeholder
    content = f"Weekly Schedule - Week of {schedule.week_start_date}\n"
    content += f"Status: {schedule.status.value}\n"
    content += "=" * 80 + "\n\n"
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    week_start = schedule.week_start_date
    
    for i, day_name in enumerate(days):
        day_date = week_start + timedelta(days=i)
        day_str = day_date.strftime('%Y-%m-%d')
        content += f"\n{day_name}, {day_date.strftime('%B %d, %Y')}\n"
        content += "-" * 80 + "\n"
        
        shifts = shifts_by_day.get(day_str, [])
        if not shifts:
            content += "  No shifts scheduled\n"
        else:
            for shift in shifts:
                content += f"  {shift['time']} - {shift['template_name']}\n"
                content += f"    Location: {shift['location']}\n"
                if shift['assignments']:
                    content += f"    Assigned: {', '.join([a['employee'] for a in shift['assignments']])}\n"
                else:
                    content += f"    UNASSIGNED\n"
                content += "\n"
    
    return content.encode('utf-8')


def generate_csv(rows: List[List[str]]) -> bytes:
    """
    Generate CSV format from rows
    """
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerows(rows)
    
    return output.getvalue().encode('utf-8')
