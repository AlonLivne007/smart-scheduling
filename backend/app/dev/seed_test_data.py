"""
Utility to seed the database with comprehensive test data for local development.

Creates:
    - 15 users with diverse role assignments
    - 4 roles
    - Multiple shift templates with role requirement counts
    - 1 weekly schedule
    - Planned shifts (including overlapping shifts)
    - Shift assignments (existing assignments)
    - Time-off requests (approved and pending)
    - System constraints

Usage (from backend directory):
    python -m app.dev.seed_test_data
"""

from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import insert

from app.db.session import SessionLocal
from app.db.models.userModel import UserModel
from app.db.models.roleModel import RoleModel
from app.db.models.shiftTemplateModel import ShiftTemplateModel
from app.db.models.weeklyScheduleModel import WeeklyScheduleModel
from app.db.models.plannedShiftModel import PlannedShiftModel, PlannedShiftStatus
from app.db.models.shiftAssignmentModel import ShiftAssignmentModel
from app.db.models.timeOffRequestModel import TimeOffRequestModel, TimeOffRequestStatus, TimeOffRequestType
from app.db.models.systemConstraintsModel import SystemConstraintsModel, SystemConstraintType
from app.db.models.shiftRoleRequirementsTabel import shift_role_requirements


def seed_test_data(db: Session) -> dict:
    """
    Seed the database with comprehensive test data for optimization testing.

    Creates:
        - 15 users with diverse role assignments
        - 4 roles
        - Multiple shift templates with role requirement counts
        - 1 weekly schedule
        - Planned shifts (including overlapping shifts)
        - Shift assignments (existing assignments)
        - Time-off requests (approved and pending)
        - System constraints

    Returns:
        A summary dict with counts of created entities.
    """

    # If roles already exist, assume test data has been seeded and skip
    existing_role = db.query(RoleModel).first()
    if existing_role:
        print("✅ Test data already present, skipping seeding.")
        return {
            "users": 0,
            "roles": 0,
            "shift_templates": 0,
            "weekly_schedules": 0,
            "planned_shifts": 0,
            "shift_assignments": 0,
            "time_off_requests": 0,
            "system_constraints": 0,
        }

    # --- Roles ---
    role_names = ["Waiter", "Bartender", "Host", "Manager"]
    roles = [RoleModel(role_name=name) for name in role_names]
    db.add_all(roles)
    db.flush()  # Ensure role IDs are available
    role_by_name = {r.role_name: r for r in roles}

    # --- Users ---
    # Create 15 users with diverse role assignments for better testing
    users = []
    user_roles_config = [
        # Managers (users 1-3)
        {"name": "Manager Alice", "email": "alice@example.com", "is_manager": True, "roles": ["Manager", "Waiter"]},
        {"name": "Manager Bob", "email": "bob@example.com", "is_manager": True, "roles": ["Manager", "Host"]},
        {"name": "Manager Carol", "email": "carol@example.com", "is_manager": True, "roles": ["Manager", "Bartender"]},
        # Multi-role employees (users 4-8)
        {"name": "Multi-Role Dave", "email": "dave@example.com", "is_manager": False, "roles": ["Waiter", "Bartender"]},
        {"name": "Multi-Role Eve", "email": "eve@example.com", "is_manager": False, "roles": ["Waiter", "Host"]},
        {"name": "Multi-Role Frank", "email": "frank@example.com", "is_manager": False, "roles": ["Bartender", "Host"]},
        {"name": "Multi-Role Grace", "email": "grace@example.com", "is_manager": False, "roles": ["Waiter", "Bartender", "Host"]},
        {"name": "Multi-Role Henry", "email": "henry@example.com", "is_manager": False, "roles": ["Waiter", "Host"]},
        # Single-role employees (users 9-15)
        {"name": "Waiter Ian", "email": "ian@example.com", "is_manager": False, "roles": ["Waiter"]},
        {"name": "Waiter Jane", "email": "jane@example.com", "is_manager": False, "roles": ["Waiter"]},
        {"name": "Bartender Kevin", "email": "kevin@example.com", "is_manager": False, "roles": ["Bartender"]},
        {"name": "Bartender Lisa", "email": "lisa@example.com", "is_manager": False, "roles": ["Bartender"]},
        {"name": "Host Mike", "email": "mike@example.com", "is_manager": False, "roles": ["Host"]},
        {"name": "Host Nancy", "email": "nancy@example.com", "is_manager": False, "roles": ["Host"]},
        {"name": "Waiter Oscar", "email": "oscar@example.com", "is_manager": False, "roles": ["Waiter"]},
    ]

    for user_config in user_roles_config:
        user = UserModel(
            user_full_name=user_config["name"],
            user_email=user_config["email"],
            hashed_password="hashedpassword123",
            is_manager=user_config["is_manager"],
        )
        # Assign roles
        for role_name in user_config["roles"]:
            user.roles.append(role_by_name[role_name])
        users.append(user)

    db.add_all(users)
    db.flush()  # Ensure user IDs are available

    # --- Shift templates with role requirement counts ---
    shift_templates_data = [
        {
            "name": "Morning Shift",
            "start": time(8, 0),
            "end": time(12, 0),
            "location": "Main Floor",
            "required_roles": [
                {"role": "Waiter", "count": 2},
                {"role": "Host", "count": 1},
            ],
        },
        {
            "name": "Afternoon Shift",
            "start": time(12, 0),
            "end": time(16, 0),
            "location": "Main Floor",
            "required_roles": [
                {"role": "Waiter", "count": 2},
                {"role": "Bartender", "count": 1},
            ],
        },
        {
            "name": "Evening Shift",
            "start": time(16, 0),
            "end": time(22, 0),
            "location": "Main Floor",
            "required_roles": [
                {"role": "Waiter", "count": 3},
                {"role": "Bartender", "count": 2},
                {"role": "Host", "count": 1},
            ],
        },
        {
            "name": "Late Night Shift",
            "start": time(22, 0),
            "end": time(2, 0),  # Overnight shift
            "location": "Main Floor",
            "required_roles": [
                {"role": "Waiter", "count": 1},
                {"role": "Bartender", "count": 1},
            ],
        },
    ]

    shift_templates: list[ShiftTemplateModel] = []
    template_role_requirements = []  # Store for later insertion

    for tpl in shift_templates_data:
        st = ShiftTemplateModel(
            shift_template_name=tpl["name"],
            start_time=tpl["start"],
            end_time=tpl["end"],
            location=tpl["location"],
        )
        shift_templates.append(st)

    db.add_all(shift_templates)
    db.flush()  # Ensure template IDs are available

    # Insert role requirements with counts
    for tpl_data, template in zip(shift_templates_data, shift_templates):
        for role_req in tpl_data["required_roles"]:
            template_role_requirements.append({
                "shift_template_id": template.shift_template_id,
                "role_id": role_by_name[role_req["role"]].role_id,
                "required_count": role_req["count"],
            })

    if template_role_requirements:
        db.execute(insert(shift_role_requirements), template_role_requirements)
        db.flush()

    # --- Weekly schedule ---
    today = date.today()
    # Use Monday as the start of the week
    week_start = today - timedelta(days=today.weekday())
    created_by_user = users[0]  # first user as schedule creator

    weekly_schedule = WeeklyScheduleModel(
        week_start_date=week_start,
        created_by_id=created_by_user.user_id,
    )
    db.add(weekly_schedule)
    db.flush()  # Ensure schedule ID is available

    # --- Planned shifts (including overlapping shifts) ---
    planned_shifts: list[PlannedShiftModel] = []

    # Create shifts for each template for each day in the week
    for day_offset in range(7):  # 7 days in the week
        shift_date = week_start + timedelta(days=day_offset)
        for tpl in shift_templates:
            # Handle overnight shifts (end_time < start_time means next day)
            if tpl.end_time < tpl.start_time:
                # Overnight shift: end is next day
                end_date = shift_date + timedelta(days=1)
                start_dt = datetime.combine(shift_date, tpl.start_time)
                end_dt = datetime.combine(end_date, tpl.end_time)
            else:
                start_dt = datetime.combine(shift_date, tpl.start_time) if tpl.start_time else datetime(
                    shift_date.year, shift_date.month, shift_date.day, 0, 0
                )
                end_dt = datetime.combine(shift_date, tpl.end_time) if tpl.end_time else datetime(
                    shift_date.year, shift_date.month, shift_date.day, 23, 59
                )

            planned_shift = PlannedShiftModel(
                weekly_schedule_id=weekly_schedule.weekly_schedule_id,
                shift_template_id=tpl.shift_template_id,
                date=shift_date,
                start_time=start_dt,
                end_time=end_dt,
                location=tpl.location or "Main Floor",
                status=PlannedShiftStatus.PLANNED,
            )
            planned_shifts.append(planned_shift)

    db.add_all(planned_shifts)
    db.flush()  # Ensure shift IDs are available

    # --- Shift assignments (existing assignments) ---
    # Create some existing assignments to test existing_assignments logic
    assignments = []
    
    # Assign some employees to shifts on Monday and Tuesday
    monday_shifts = [s for s in planned_shifts if s.date == week_start]
    tuesday_shifts = [s for s in planned_shifts if s.date == week_start + timedelta(days=1)]
    
    # Monday assignments
    if len(monday_shifts) >= 3:
        # Assign user 4 (Dave - Waiter/Bartender) to Monday morning shift as Waiter
        morning_shift = next((s for s in monday_shifts if s.shift_template_id == shift_templates[0].shift_template_id), None)
        if morning_shift:
            assignments.append(ShiftAssignmentModel(
                planned_shift_id=morning_shift.planned_shift_id,
                user_id=users[3].user_id,  # Dave
                role_id=role_by_name["Waiter"].role_id,
            ))
        
        # Assign user 5 (Eve - Waiter/Host) to Monday afternoon shift as Waiter
        afternoon_shift = next((s for s in monday_shifts if s.shift_template_id == shift_templates[1].shift_template_id), None)
        if afternoon_shift:
            assignments.append(ShiftAssignmentModel(
                planned_shift_id=afternoon_shift.planned_shift_id,
                user_id=users[4].user_id,  # Eve
                role_id=role_by_name["Waiter"].role_id,
            ))
        
        # Assign user 6 (Frank - Bartender/Host) to Monday evening shift as Bartender
        evening_shift = next((s for s in monday_shifts if s.shift_template_id == shift_templates[2].shift_template_id), None)
        if evening_shift:
            assignments.append(ShiftAssignmentModel(
                planned_shift_id=evening_shift.planned_shift_id,
                user_id=users[5].user_id,  # Frank
                role_id=role_by_name["Bartender"].role_id,
            ))
    
    # Tuesday assignments
    if len(tuesday_shifts) >= 2:
        # Assign user 9 (Ian - Waiter) to Tuesday morning shift
        morning_shift = next((s for s in tuesday_shifts if s.shift_template_id == shift_templates[0].shift_template_id), None)
        if morning_shift:
            assignments.append(ShiftAssignmentModel(
                planned_shift_id=morning_shift.planned_shift_id,
                user_id=users[8].user_id,  # Ian
                role_id=role_by_name["Waiter"].role_id,
            ))
        
        # Assign user 11 (Kevin - Bartender) to Tuesday afternoon shift
        afternoon_shift = next((s for s in tuesday_shifts if s.shift_template_id == shift_templates[1].shift_template_id), None)
        if afternoon_shift:
            assignments.append(ShiftAssignmentModel(
                planned_shift_id=afternoon_shift.planned_shift_id,
                user_id=users[10].user_id,  # Kevin
                role_id=role_by_name["Bartender"].role_id,
            ))

    db.add_all(assignments)
    db.flush()

    # --- Time-off requests ---
    time_off_requests = []
    now = datetime.now()

    # Approved time-off requests (these will block assignments)
    # User 7 (Grace) has approved vacation Wednesday-Friday
    time_off_requests.append(TimeOffRequestModel(
        user_id=users[6].user_id,  # Grace
        start_date=week_start + timedelta(days=2),  # Wednesday
        end_date=week_start + timedelta(days=4),  # Friday
        request_type=TimeOffRequestType.VACATION,
        status=TimeOffRequestStatus.APPROVED,
        requested_at=now - timedelta(days=5),
        approved_by_id=users[0].user_id,  # Manager Alice
        approved_at=now - timedelta(days=4),
    ))

    # User 10 (Jane) has approved sick leave on Thursday
    time_off_requests.append(TimeOffRequestModel(
        user_id=users[9].user_id,  # Jane
        start_date=week_start + timedelta(days=3),  # Thursday
        end_date=week_start + timedelta(days=3),  # Thursday
        request_type=TimeOffRequestType.SICK,
        status=TimeOffRequestStatus.APPROVED,
        requested_at=now - timedelta(days=3),
        approved_by_id=users[1].user_id,  # Manager Bob
        approved_at=now - timedelta(days=2),
    ))

    # User 13 (Mike) has approved personal day on Friday
    time_off_requests.append(TimeOffRequestModel(
        user_id=users[12].user_id,  # Mike
        start_date=week_start + timedelta(days=4),  # Friday
        end_date=week_start + timedelta(days=4),  # Friday
        request_type=TimeOffRequestType.PERSONAL,
        status=TimeOffRequestStatus.APPROVED,
        requested_at=now - timedelta(days=2),
        approved_by_id=users[0].user_id,  # Manager Alice
        approved_at=now - timedelta(days=1),
    ))

    # Pending time-off requests (these should NOT block assignments)
    # User 8 (Henry) has pending request for Saturday
    time_off_requests.append(TimeOffRequestModel(
        user_id=users[7].user_id,  # Henry
        start_date=week_start + timedelta(days=5),  # Saturday
        end_date=week_start + timedelta(days=5),  # Saturday
        request_type=TimeOffRequestType.VACATION,
        status=TimeOffRequestStatus.PENDING,
        requested_at=now - timedelta(days=1),
    ))

    db.add_all(time_off_requests)
    db.flush()

    # --- System constraints ---
    system_constraints = [
        SystemConstraintsModel(
            constraint_type=SystemConstraintType.MAX_HOURS_PER_WEEK,
            constraint_value=40.0,
            is_hard_constraint=True,
        ),
        SystemConstraintsModel(
            constraint_type=SystemConstraintType.MIN_HOURS_PER_WEEK,
            constraint_value=20.0,
            is_hard_constraint=False,  # Soft constraint
        ),
        SystemConstraintsModel(
            constraint_type=SystemConstraintType.MAX_CONSECUTIVE_DAYS,
            constraint_value=5.0,
            is_hard_constraint=True,
        ),
        SystemConstraintsModel(
            constraint_type=SystemConstraintType.MIN_REST_HOURS,
            constraint_value=11.0,
            is_hard_constraint=True,
        ),
        SystemConstraintsModel(
            constraint_type=SystemConstraintType.MAX_SHIFTS_PER_WEEK,
            constraint_value=6.0,
            is_hard_constraint=False,  # Soft constraint
        ),
        SystemConstraintsModel(
            constraint_type=SystemConstraintType.MIN_SHIFTS_PER_WEEK,
            constraint_value=3.0,
            is_hard_constraint=False,  # Soft constraint
        ),
    ]

    db.add_all(system_constraints)

    # Commit all changes at once
    db.commit()

    summary = {
        "users": len(users),
        "roles": len(roles),
        "shift_templates": len(shift_templates),
        "weekly_schedules": 1,
        "planned_shifts": len(planned_shifts),
        "shift_assignments": len(assignments),
        "time_off_requests": len(time_off_requests),
        "system_constraints": len(system_constraints),
    }
    return summary


def init_test_data() -> None:
    """
    Convenience wrapper to seed test data using an internal DB session.
    Intended to be called from application startup (similar to init_master_user).
    """
    db: Session = SessionLocal()
    try:
        summary = seed_test_data(db)
        if summary.get("roles", 0) > 0:
            print("✅ Seeded comprehensive test data:")
            print(f"   - {summary.get('users', 0)} users")
            print(f"   - {summary.get('roles', 0)} roles")
            print(f"   - {summary.get('shift_templates', 0)} shift templates")
            print(f"   - {summary.get('weekly_schedules', 0)} weekly schedule(s)")
            print(f"   - {summary.get('planned_shifts', 0)} planned shifts")
            print(f"   - {summary.get('shift_assignments', 0)} shift assignments")
            print(f"   - {summary.get('time_off_requests', 0)} time-off requests")
            print(f"   - {summary.get('system_constraints', 0)} system constraints")
        else:
            print("ℹ️ Test data already present, skipping seeding.")
    except Exception as exc:
        db.rollback()
        print(f"⚠️  Warning: Could not seed test data: {exc}")
    finally:
        db.close()


if __name__ == "__main__":
    """
    Simple CLI entrypoint to seed the database.

    Run from the backend directory:
        python -m app.dev.seed_test_data
    """
    init_test_data()

