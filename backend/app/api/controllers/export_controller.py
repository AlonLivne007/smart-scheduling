"""
Export Controller
Handles exporting schedules to PDF and Excel formats
Controllers use repositories for database access - no direct ORM access.
"""

from datetime import timedelta
from typing import Dict, List, Tuple, Literal

from app.data.repositories.weekly_schedule_repository import WeeklyScheduleRepository
from app.data.repositories.shift_repository import ShiftRepository
from app.data.repositories.shift_repository import ShiftAssignmentRepository
from app.data.repositories.user_repository import UserRepository
from app.data.repositories import ShiftTemplateRepository
from app.core.exceptions.repository import NotFoundError


def _fetch_schedule_export_data(
    schedule_id: int,
    schedule_repository: WeeklyScheduleRepository,
    shift_repository: ShiftRepository,
    template_repository: ShiftTemplateRepository,
    assignment_repository: ShiftAssignmentRepository,
    user_repository: UserRepository
) -> Tuple:
    """
    Fetch all data needed for schedule export.
    
    Uses repositories to get all data.
    
    Returns:
        Tuple of (schedule, planned_shifts, templates_dict, assignments_dict)
    """
    # Get schedule
    schedule = schedule_repository.get_with_relations(schedule_id)
    if not schedule:
        raise NotFoundError(f"Schedule with ID {schedule_id} not found")
    
    # Get all planned shifts for this schedule
    all_shifts = shift_repository.get_all()
    planned_shifts = [s for s in all_shifts if s.weekly_schedule_id == schedule_id]
    
    # Get all unique template IDs
    template_ids = list(set(shift.shift_template_id for shift in planned_shifts if shift.shift_template_id))
    
    # Fetch all templates using repository
    templates_dict = {}
    for template_id in template_ids:
        template = template_repository.get_by_id(template_id)
        if template:
            templates_dict[template_id] = template
    
    # Get all shift IDs
    shift_ids = [shift.planned_shift_id for shift in planned_shifts]
    
    # Fetch all assignments using repository
    assignments_dict: Dict[int, List] = {}
    for shift_id in shift_ids:
        assignments = assignment_repository.get_by_shift(shift_id)
        if assignments:
            assignments_dict[shift_id] = assignments
    
    return schedule, planned_shifts, templates_dict, assignments_dict


async def _export_schedule_pdf(
    schedule_id: int,
    schedule_repository: WeeklyScheduleRepository,
    shift_repository: ShiftRepository,
    template_repository: ShiftTemplateRepository,
    assignment_repository: ShiftAssignmentRepository,
    user_repository: UserRepository
) -> bytes:
    """
    Export a weekly schedule to PDF format
    
    Uses repositories to get all data.
    """
    # Fetch all data needed
    schedule, planned_shifts, templates_dict, assignments_dict = _fetch_schedule_export_data(
        schedule_id,
        schedule_repository,
        shift_repository,
        template_repository,
        assignment_repository,
        user_repository
    )
    
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
            template = templates_dict.get(shift.shift_template_id) if shift.shift_template_id else None
            
            # Get assignments
            assignments = assignments_dict.get(shift.planned_shift_id, [])
            
            # Get employee names using repository
            employee_names = []
            for assignment in assignments:
                if assignment.user_id:
                    employee = user_repository.get_by_id(assignment.user_id)
                    employee_names.append(employee.user_full_name if employee else "Unassigned")
            
            shift_data = {
                'time': f"{template.start_time} - {template.end_time}" if template else "N/A",
                'template_name': template.shift_template_name if template else "Unnamed",
                'location': shift.location or (template.location if template else ""),
                'assignments': [
                    {
                        'employee': employee_names[i] if i < len(employee_names) else "Unassigned",
                        'role': assignment.role_id
                    }
                    for i, assignment in enumerate(assignments)
                ]
            }
            shifts_by_day[shift_date].append(shift_data)
    
    # Generate PDF
    pdf_content = generate_simple_pdf(schedule, shifts_by_day)
    
    return pdf_content


async def _export_schedule_excel(
    schedule_id: int,
    schedule_repository: WeeklyScheduleRepository,
    shift_repository: ShiftRepository,
    template_repository: ShiftTemplateRepository,
    assignment_repository: ShiftAssignmentRepository,
    user_repository: UserRepository
) -> bytes:
    """
    Export a weekly schedule to Excel format
    
    Uses repositories to get all data.
    """
    # Fetch all data needed
    schedule, planned_shifts, templates_dict, assignments_dict = _fetch_schedule_export_data(
        schedule_id,
        schedule_repository,
        shift_repository,
        template_repository,
        assignment_repository,
        user_repository
    )
    
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
        template = templates_dict.get(shift.shift_template_id) if shift.shift_template_id else None
        
        # Get assignments
        assignments = assignments_dict.get(shift.planned_shift_id, [])
        
        shift_date = shift.date.strftime('%Y-%m-%d')
        day_name = shift.date.strftime('%A')
        template_name = template.shift_template_name if template else "Unnamed"
        time_range = f"{template.start_time} - {template.end_time}" if template else "N/A"
        location = shift.location or (template.location if template else "")
        
        if assignments:
            for assignment in assignments:
                employee = user_repository.get_by_id(assignment.user_id)
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
    
    # Generate CSV format
    csv_content = generate_csv(rows)
    
    return csv_content


def generate_simple_pdf(schedule, shifts_by_day: Dict[str, List]) -> bytes:
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


async def export_schedule(
    schedule_id: int,
    format: Literal["pdf", "excel"],
    schedule_repository: WeeklyScheduleRepository,
    shift_repository: ShiftRepository,
    template_repository: ShiftTemplateRepository,
    assignment_repository: ShiftAssignmentRepository,
    user_repository: UserRepository
) -> Tuple[bytes, str, str]:
    """
    Export schedule in requested format.
    
    Uses repositories to get all data.
    
    Returns:
        Tuple of (content, media_type, filename)
    """
    if format == "pdf":
        content = await _export_schedule_pdf(
            schedule_id,
            schedule_repository,
            shift_repository,
            template_repository,
            assignment_repository,
            user_repository
        )
        return content, "application/pdf", f"schedule_{schedule_id}.pdf"
    elif format == "excel":
        content = await _export_schedule_excel(
            schedule_id,
            schedule_repository,
            shift_repository,
            template_repository,
            assignment_repository,
            user_repository
        )
        return content, "text/csv", f"schedule_{schedule_id}.csv"
    else:
        raise ValueError("Invalid format. Use 'pdf' or 'excel'")
