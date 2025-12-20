"""
Utility to seed the database with simple test data for local development.

Creates:
    - 10 users
    - 3–4 roles
    - Several shift templates
    - 1 basic weekly schedule
    - Planned shifts linked to that schedule

Does NOT create:
    - Shift assignments
    - Time-off requests

Usage (from backend directory):
    python -m app.db.seed_test_data
"""

from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models.userModel import UserModel
from app.db.models.roleModel import RoleModel
from app.db.models.shiftTemplateModel import ShiftTemplateModel
from app.db.models.weeklyScheduleModel import WeeklyScheduleModel
from app.db.models.plannedShiftModel import PlannedShiftModel, PlannedShiftStatus


def seed_test_data(db: Session) -> dict:
    """
    Seed the database with basic test data for local development.

    Creates:
        - 10 users
        - 3–4 roles
        - Several shift templates
        - 1 weekly schedule
        - A set of planned shifts linked to that schedule

    Does NOT create:
        - Shift assignments
        - Time-off requests

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
        }

    # --- Roles ---
    role_names = ["Waiter", "Bartender", "Host", "Manager"]
    roles = [RoleModel(role_name=name) for name in role_names]
    db.add_all(roles)
    db.flush()  # Ensure role IDs are available

    # --- Users ---
    users = []
    for i in range(1, 11):
        user = UserModel(
            user_full_name=f"Test User {i}",
            user_email=f"user{i}@example.com",
            user_status="ACTIVE",
            # Simple/fake hash; for local dev only
            hashed_password="hashedpassword123",
            is_manager=(i <= 2),  # first two are managers
        )
        users.append(user)
    db.add_all(users)
    db.flush()  # Ensure user IDs are available

    # Attach some roles to users (simple pattern)
    # - Managers get "Manager" + one front-of-house role
    # - Others get one primary role
    role_by_name = {r.role_name: r for r in roles}
    for idx, user in enumerate(users, start=1):
        if user.is_manager:
            user.roles.append(role_by_name["Manager"])
            if idx % 2 == 0:
                user.roles.append(role_by_name["Waiter"])
            else:
                user.roles.append(role_by_name["Host"])
        else:
            if idx % 3 == 0:
                user.roles.append(role_by_name["Bartender"])
            elif idx % 3 == 1:
                user.roles.append(role_by_name["Waiter"])
            else:
                user.roles.append(role_by_name["Host"])

    # --- Shift templates ---
    shift_templates_data = [
        {
            "name": "Morning Shift",
            "start": time(8, 0),
            "end": time(12, 0),
            "location": "Main Floor",
            "required_roles": ["Waiter", "Host"],
        },
        {
            "name": "Afternoon Shift",
            "start": time(12, 0),
            "end": time(16, 0),
            "location": "Main Floor",
            "required_roles": ["Waiter", "Bartender"],
        },
        {
            "name": "Evening Shift",
            "start": time(16, 0),
            "end": time(22, 0),
            "location": "Main Floor",
            "required_roles": ["Waiter", "Bartender", "Host"],
        },
    ]

    shift_templates: list[ShiftTemplateModel] = []
    for tpl in shift_templates_data:
        st = ShiftTemplateModel(
            shift_template_name=tpl["name"],
            start_time=tpl["start"],
            end_time=tpl["end"],
            location=tpl["location"],
        )
        # link required roles
        st.required_roles = [role_by_name[rn] for rn in tpl["required_roles"]]
        shift_templates.append(st)

    db.add_all(shift_templates)
    db.flush()  # Ensure template IDs are available

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

    # --- Planned shifts (no assignments) ---
    planned_shifts: list[PlannedShiftModel] = []

    # Simple pattern: create shifts for each template for each day in the week
    for day_offset in range(7):  # 7 days in the week
        shift_date = week_start + timedelta(days=day_offset)
        for tpl in shift_templates:
            # Template times are time-only; combine with date to get datetimes
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

    # Commit all changes at once
    db.commit()

    summary = {
        "users": len(users),
        "roles": len(roles),
        "shift_templates": len(shift_templates),
        "weekly_schedules": 1,
        "planned_shifts": len(planned_shifts),
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
            print("✅ Seeded test data:", summary)
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
        python -m app.db.seed_test_data
    """
    init_test_data()


