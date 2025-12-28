"""
Enhanced seed script to add next week's schedule with some assignments.

This supplements the existing seed_test_data.py by:
- Creating a weekly schedule for NEXT week (for the dashboard widget)
- Adding planned shifts for next week
- Creating some shift assignments to show coverage
- Adding some time-off requests

Run from backend directory:
    python -m app.db.seed_next_week
"""

from datetime import date, datetime, time, timedelta
import random

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models.userModel import UserModel
from app.db.models.roleModel import RoleModel
from app.db.models.shiftTemplateModel import ShiftTemplateModel
from app.db.models.weeklyScheduleModel import WeeklyScheduleModel
from app.db.models.plannedShiftModel import PlannedShiftModel, PlannedShiftStatus
from app.db.models.shiftAssignmentModel import ShiftAssignmentModel
from app.db.models.timeOffRequestModel import TimeOffRequestModel, TimeOffRequestType, TimeOffRequestStatus


def seed_next_week_data(db: Session) -> dict:
    """
    Create next week's schedule with assignments for demo purposes.
    """
    
    # Get existing data
    users = db.query(UserModel).all()
    roles = db.query(RoleModel).all()
    templates = db.query(ShiftTemplateModel).all()
    
    if not users or not roles or not templates:
        print("⚠️ No base data found. Run seed_test_data.py first.")
        return {}
    
    # Calculate next week's Monday
    today = date.today()
    current_weekday = today.weekday()  # 0 = Monday
    days_until_next_monday = 7 - current_weekday if current_weekday != 0 else 7
    next_monday = today + timedelta(days=days_until_next_monday)
    
    print(f"📅 Creating schedule for week starting: {next_monday}")
    
    # Check if schedule already exists for next week
    existing_schedule = db.query(WeeklyScheduleModel).filter(
        WeeklyScheduleModel.week_start_date == next_monday
    ).first()
    
    if existing_schedule:
        print(f"✅ Schedule for {next_monday} already exists. Skipping.")
        return {"message": "Next week already seeded"}
    
    # Use admin user as creator (check for admin@example.com)
    manager = db.query(UserModel).filter(UserModel.user_email == "admin@example.com").first()
    if not manager:
        # Fallback to any manager
        manager = next((u for u in users if u.is_manager), users[0])
    
    # Create next week's schedule
    weekly_schedule = WeeklyScheduleModel(
        week_start_date=next_monday,
        created_by_id=manager.user_id,
    )
    db.add(weekly_schedule)
    db.flush()
    
    # Create planned shifts for next week
    planned_shifts = []
    role_by_name = {r.role_name: r for r in roles}
    
    # Pattern: 3 shifts per day (morning, afternoon, evening)
    for day_offset in range(7):  # Monday to Sunday
        shift_date = next_monday + timedelta(days=day_offset)
        
        for template in templates:
            start_dt = datetime.combine(shift_date, template.start_time) if template.start_time else datetime(
                shift_date.year, shift_date.month, shift_date.day, 0, 0
            )
            end_dt = datetime.combine(shift_date, template.end_time) if template.end_time else datetime(
                shift_date.year, shift_date.month, shift_date.day, 23, 59
            )
            
            planned_shift = PlannedShiftModel(
                weekly_schedule_id=weekly_schedule.weekly_schedule_id,
                shift_template_id=template.shift_template_id,
                date=shift_date,
                start_time=start_dt,
                end_time=end_dt,
                location=template.location or "Main Floor",
                status=PlannedShiftStatus.PLANNED,
            )
            planned_shifts.append(planned_shift)
    
    db.add_all(planned_shifts)
    db.flush()
    
    # Create shift assignments (some shifts fully covered, some partial, some empty)
    assignments = []
    non_manager_users = [u for u in users if not u.is_manager]
    
    for idx, shift in enumerate(planned_shifts):
        # Get template to know required roles
        template = next((t for t in templates if t.shift_template_id == shift.shift_template_id), None)
        if not template or not template.required_roles:
            continue
        
        # Assign coverage based on pattern:
        # - 60% fully covered
        # - 25% partially covered
        # - 15% empty
        coverage_type = idx % 100
        
        if coverage_type < 60:  # Fully covered
            for required_role in template.required_roles:
                # Find a user with this role
                eligible_users = [u for u in non_manager_users if required_role in u.roles]
                if eligible_users:
                    assigned_user = random.choice(eligible_users)
                    assignment = ShiftAssignmentModel(
                        planned_shift_id=shift.planned_shift_id,
                        user_id=assigned_user.user_id,
                        role_id=required_role.role_id,
                    )
                    assignments.append(assignment)
        
        elif coverage_type < 85:  # Partially covered
            # Assign only some of the required roles
            roles_to_assign = template.required_roles[:len(template.required_roles)//2 + 1]
            for required_role in roles_to_assign:
                eligible_users = [u for u in non_manager_users if required_role in u.roles]
                if eligible_users:
                    assigned_user = random.choice(eligible_users)
                    assignment = ShiftAssignmentModel(
                        planned_shift_id=shift.planned_shift_id,
                        user_id=assigned_user.user_id,
                        role_id=required_role.role_id,
                    )
                    assignments.append(assignment)
        
        # else: Leave empty (no assignments)
    
    db.add_all(assignments)
    
    # Create some time-off requests
    time_off_requests = []
    request_types = [TimeOffRequestType.VACATION, TimeOffRequestType.SICK, TimeOffRequestType.PERSONAL]
    statuses = [TimeOffRequestStatus.PENDING, TimeOffRequestStatus.APPROVED, TimeOffRequestStatus.REJECTED]
    
    # Create 5-8 requests
    for i in range(random.randint(5, 8)):
        user = random.choice(users)
        request_type = random.choice(request_types)
        status = random.choice(statuses)
        
        # Random date in next 2 weeks
        start_offset = random.randint(0, 14)
        duration = random.randint(1, 3)
        
        request_start = next_monday + timedelta(days=start_offset)
        request_end = request_start + timedelta(days=duration)
        
        time_off = TimeOffRequestModel(
            user_id=user.user_id,
            request_type=request_type,
            start_date=request_start,
            end_date=request_end,
            status=status,
            requested_at=datetime.now() - timedelta(days=random.randint(1, 7)),
        )
        
        # If approved/rejected, set approver and date
        if status != TimeOffRequestStatus.PENDING:
            time_off.approved_by_id = manager.user_id
            time_off.approved_at = datetime.now() - timedelta(days=random.randint(1, 5))
        
        time_off_requests.append(time_off)
    
    db.add_all(time_off_requests)
    
    # Commit everything
    db.commit()
    
    summary = {
        "weekly_schedule": 1,
        "planned_shifts": len(planned_shifts),
        "shift_assignments": len(assignments),
        "time_off_requests": len(time_off_requests),
        "week_start": str(next_monday),
    }
    
    print(f"✅ Created next week's data:")
    print(f"   - Planned shifts: {len(planned_shifts)}")
    print(f"   - Assignments: {len(assignments)}")
    print(f"   - Time-off requests: {len(time_off_requests)}")
    
    return summary


def init_next_week_data() -> None:
    """Run the seeding"""
    db: Session = SessionLocal()
    try:
        summary = seed_next_week_data(db)
        if summary.get("weekly_schedule"):
            print("✅ Next week's schedule created successfully!")
        else:
            print("ℹ️ Next week's data already exists or base data missing.")
    except Exception as exc:
        db.rollback()
        print(f"⚠️ Error seeding next week: {exc}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    init_next_week_data()
