"""
Comprehensive seed data script for smart-scheduling.

Small mode:
- Minimal realistic dataset for basic functionality.

BIG mode (--big):
- Large, realistic stress-test dataset for the MIP solver (≈100 employees, high coverage, preferences, time off, weekly schedule).
"""

import sys
import os
import random
from collections import defaultdict
from datetime import datetime, date, time, timedelta
from werkzeug.security import generate_password_hash

from sqlalchemy import select, func as sa_func, delete, insert

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.session import SessionLocal
from app.db.models.userModel import UserModel
from app.db.models.roleModel import RoleModel
from app.db.models.userRoleModel import UserRoleModel
from app.db.models.shiftTemplateModel import ShiftTemplateModel
from app.db.models.employeePreferencesModel import EmployeePreferencesModel, DayOfWeek
from app.db.models.weeklyScheduleModel import WeeklyScheduleModel, ScheduleStatus
from app.db.models.plannedShiftModel import PlannedShiftModel, PlannedShiftStatus
from app.db.models.shiftAssignmentModel import ShiftAssignmentModel  # noqa: F401 - ensure mapper registration
from app.db.models.systemConstraintsModel import SystemConstraintsModel, SystemConstraintType
from app.db.models.timeOffRequestModel import TimeOffRequestModel, TimeOffRequestStatus, TimeOffRequestType
from app.db.models.optimizationConfigModel import OptimizationConfigModel
from app.db.models.schedulingRunModel import SchedulingRunModel  # noqa: F401 - ensure mapper registration
from app.db.models.schedulingSolutionModel import SchedulingSolutionModel  # noqa: F401 - ensure mapper registration
from app.db.models.shiftRoleRequirementsTabel import shift_role_requirements


RANDOM_SEED = 42


def is_big_mode() -> bool:
    """Detect if the script should run in BIG mode based on CLI args."""
    return "--big" in sys.argv


def clear_existing_data(db):
    """Clear all existing data."""
    print("🗑️  Clearing existing data...")
    
    # Delete in correct order (respecting foreign keys)
    db.query(EmployeePreferencesModel).delete()
    db.query(SystemConstraintsModel).delete()
    db.query(TimeOffRequestModel).delete()
    db.query(PlannedShiftModel).delete()
    db.query(WeeklyScheduleModel).delete()
    db.query(UserRoleModel).delete()
    db.query(UserModel).delete()
    
    # Delete shift role requirements (association table)
    db.execute(delete(shift_role_requirements))
    
    # Delete shift templates and roles that are not in our current required list
    required_roles = ["Waiter", "Bartender", "Host", "Manager"]
    required_templates = ["Morning Shift", "Afternoon Shift", "Evening Shift"]
    
    # Delete templates not in required list
    db.query(ShiftTemplateModel).filter(
        ~ShiftTemplateModel.shift_template_name.in_(required_templates)
    ).delete(synchronize_session=False)
    
    # Delete roles not in required list
    db.query(RoleModel).filter(
        ~RoleModel.role_name.in_(required_roles)
    ).delete(synchronize_session=False)
    
    db.commit()
    print("✅ Data cleared")


def create_roles(db):
    """Create roles if they don't exist."""
    print("\n👔 Creating roles...")
    
    required_roles = ["Waiter", "Bartender", "Host", "Manager"]
    existing_roles = {role.role_name: role for role in db.query(RoleModel).all()}
    
    created_count = 0
    for role_name in required_roles:
        if role_name not in existing_roles:
            role = RoleModel(role_name=role_name)
            db.add(role)
            created_count += 1
            print(f"   ✅ Created role: {role_name}")
        else:
            print(f"   ℹ️  Role already exists: {role_name}")
    
    db.commit()
    if created_count > 0:
        print(f"✅ Created {created_count} new role(s)")
    else:
        print("✅ All roles already exist")
    
    # Return all roles (existing + newly created)
    return {role.role_name: role for role in db.query(RoleModel).all()}


def create_shift_templates(db, roles):
    """Create shift templates if they don't exist."""
    print("\n⏰ Creating shift templates...")
    
    templates_data = [
        ("Morning Shift", time(8, 0), time(14, 0), ["Waiter", "Bartender", "Host"]),
        ("Afternoon Shift", time(14, 0), time(20, 0), ["Waiter", "Bartender", "Host"]),
        ("Evening Shift", time(18, 0), time(23, 0), ["Waiter", "Bartender", "Host"]),
    ]
    
    existing_templates = {t.shift_template_name: t for t in db.query(ShiftTemplateModel).all()}
    
    created_count = 0
    for template_name, start_time, end_time, required_role_names in templates_data:
        if template_name not in existing_templates:
            template = ShiftTemplateModel(
                shift_template_name=template_name,
                start_time=start_time,
                end_time=end_time,
                location="Main Restaurant"
            )
            db.add(template)
            db.flush()
            
            # Add required roles
            role_requirements = []
            for role_name in required_role_names:
                if role_name in roles:
                    role_requirements.append({
                        "shift_template_id": template.shift_template_id,
                        "role_id": roles[role_name].role_id,
                        "required_count": 1
                    })
            
            if role_requirements:
                db.execute(insert(shift_role_requirements), role_requirements)
            
            created_count += 1
            print(f"   ✅ Created template: {template_name} ({start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')})")
        else:
            print(f"   ℹ️  Template already exists: {template_name}")
    
    db.commit()
    if created_count > 0:
        print(f"✅ Created {created_count} new template(s)")
    else:
        print("✅ All templates already exist")


def create_employees(db, roles):
    """Create employees with multiple roles."""
    print("\n👥 Creating employees...")
    
    # Roles should be passed in (created by create_roles)
    
    employees_data = [
        # Waiters (8 employees - expanded from 4)
        {"name": "Alice Johnson", "email": "alice@restaurant.com", "roles": ["Waiter"]},
        {"name": "Bob Smith", "email": "bob@restaurant.com", "roles": ["Waiter"]},
        {"name": "Charlie Brown", "email": "charlie@restaurant.com", "roles": ["Waiter"]},
        {"name": "Diana Prince", "email": "diana@restaurant.com", "roles": ["Waiter"]},
        {"name": "Ethan Hunt", "email": "ethan@restaurant.com", "roles": ["Waiter"]},
        {"name": "Fiona Apple", "email": "fiona@restaurant.com", "roles": ["Waiter"]},
        {"name": "George Clooney", "email": "george@restaurant.com", "roles": ["Waiter"]},
        {"name": "Hannah Montana", "email": "hannah@restaurant.com", "roles": ["Waiter"]},
        
        # Bartenders (6 employees - expanded from 4)
        {"name": "Ian McKellen", "email": "ian@restaurant.com", "roles": ["Bartender"]},
        {"name": "Julia Roberts", "email": "julia@restaurant.com", "roles": ["Bartender"]},
        {"name": "Kevin Hart", "email": "kevin@restaurant.com", "roles": ["Bartender"]},
        {"name": "Laura Dern", "email": "laura@restaurant.com", "roles": ["Bartender"]},
        {"name": "Morgan Freeman", "email": "morgan@restaurant.com", "roles": ["Bartender"]},
        {"name": "Natalie Portman", "email": "natalie@restaurant.com", "roles": ["Bartender"]},
        
        # Hosts (5 employees - expanded from 3)
        {"name": "Oliver Twist", "email": "oliver@restaurant.com", "roles": ["Host"]},
        {"name": "Penny Lane", "email": "penny@restaurant.com", "roles": ["Host"]},
        {"name": "Quinn Fabray", "email": "quinn@restaurant.com", "roles": ["Host"]},
        {"name": "Rachel Green", "email": "rachel@restaurant.com", "roles": ["Host"]},
        {"name": "Sarah Connor", "email": "sarah@restaurant.com", "roles": ["Host"]},
        
        # Multi-role employees (6 employees - expanded from 3)
        {"name": "Taylor Swift", "email": "taylor@restaurant.com", "roles": ["Waiter", "Bartender"]},
        {"name": "Uma Thurman", "email": "uma@restaurant.com", "roles": ["Waiter", "Host"]},
        {"name": "Vincent Vega", "email": "vincent@restaurant.com", "roles": ["Bartender", "Host"]},
        {"name": "Will Smith", "email": "will@restaurant.com", "roles": ["Waiter", "Bartender"]},
        {"name": "Xena Warrior", "email": "xena@restaurant.com", "roles": ["Waiter", "Host"]},
        {"name": "Yoda Master", "email": "yoda@restaurant.com", "roles": ["Bartender", "Host"]},
        
        # Managers (3 employees)
        {"name": "Zack Morris", "email": "zack@restaurant.com", "roles": ["Manager"], "password": "password123", "is_manager": True},
        {"name": "Amy Adams", "email": "amy@restaurant.com", "roles": ["Manager"], "password": "password123", "is_manager": True},
        {"name": "Daniel Gusakov", "email": "daniel.gusakov@gmail.com", "roles": ["Manager"], "password": "Daniel124", "is_manager": True},
        {"name": "Alon", "email": "alon.livne@gmail.com", "roles": ["Manager"], "password": "Alon123", "is_manager": True},
    ]
    
    created_employees = []
    for emp_data in employees_data:
        # Create user with properly hashed password
        # Default password: "password123" (or custom if specified)
        password = emp_data.get("password", "password123")
        is_manager = emp_data.get("is_manager", False)
        user = UserModel(
            user_full_name=emp_data["name"],
            user_email=emp_data["email"],
            hashed_password=generate_password_hash(password),
            user_status="ACTIVE",
            is_manager=is_manager
        )
        db.add(user)
        db.flush()
        
        # Assign roles
        for role_name in emp_data["roles"]:
            if role_name in roles:
                user_role = UserRoleModel(
                    user_id=user.user_id,
                    role_id=roles[role_name].role_id
                )
                db.add(user_role)
            else:
                print(f"   ⚠️  Warning: Role '{role_name}' not found for {emp_data['name']}")
        
        created_employees.append(user)
        print(f"   ✅ {emp_data['name']} ({', '.join(emp_data['roles'])})")
    
    db.commit()
    print(f"\n✅ Created {len(created_employees)} employees")
    return created_employees


def create_employees_big(db, roles):
    """
    Create ~100 employees with a realistic role distribution and some multi-role employees.
    
    Distribution:
    - 55 Waiters
    - 25 Bartenders
    - 15 Hosts
    - 3 Managers from the numeric pool
    - Plus 2 named manager logins (Daniel, Alon)
    """
    print("\n👥 Creating BIG MODE employees...")

    role_distribution = (
        ("Waiter", 55),
        ("Bartender", 25),
        ("Host", 15),
        ("Manager", 3),
    )

    created_employees = []
    current_index = 1

    # Primary role assignment
    for role_name, count in role_distribution:
        for _ in range(count):
            user_index = current_index
            current_index += 1

            email = f"user{user_index:03d}@restaurant.com"
            name = f"Employee {user_index:03d}"
            is_manager = role_name == "Manager"

            user = UserModel(
                user_full_name=name,
                user_email=email,
                hashed_password=generate_password_hash("password123"),
                user_status="ACTIVE",
                is_manager=is_manager,
            )
            db.add(user)
            db.flush()

            if role_name in roles:
                db.add(
                    UserRoleModel(
                        user_id=user.user_id,
                        role_id=roles[role_name].role_id,
                    )
                )
            else:
                print(f"   ⚠️  Warning: Role '{role_name}' not found for BIG employees")

            created_employees.append(user)

    # Ensure our two known manager login users also exist in BIG mode
    manager_role = roles.get("Manager")
    if manager_role is not None:
        special_managers = [
            {
                "name": "Daniel Gusakov",
                "email": "daniel.gusakov@gmail.com",
                "password": "Daniel124",
            },
            {
                "name": "Alon",
                "email": "alon.livne@gmail.com",
                "password": "Alon123",
            },
        ]
        existing_emails = {u.user_email for u in created_employees}
        for sm in special_managers:
            if sm["email"] in existing_emails:
                continue
            user = UserModel(
                user_full_name=sm["name"],
                user_email=sm["email"],
                hashed_password=generate_password_hash(sm["password"]),
                user_status="ACTIVE",
                is_manager=True,
            )
            db.add(user)
            db.flush()
            db.add(
                UserRoleModel(
                    user_id=user.user_id,
                    role_id=manager_role.role_id,
                )
            )
            created_employees.append(user)

    db.commit()

    # Assign multi-roles (15–25 employees) – exclude managers as much as possible
    print("   🔁 Assigning multi-role employees...")
    non_manager_emps = [u for u in created_employees if not u.is_manager]
    random.shuffle(non_manager_emps)
    multi_role_target = random.randint(15, 25)
    multi_role_selected = non_manager_emps[:multi_role_target]

    # Map primary roles via user-role table
    role_by_id = {r.role_id: r for r in db.query(RoleModel).all()}
    user_roles = db.query(UserRoleModel).all()
    roles_for_user = defaultdict(list)
    for ur in user_roles:
        roles_for_user[ur.user_id].append(role_by_id.get(ur.role_id))

    multi_role_count = 0
    for user in multi_role_selected:
        primary_roles = roles_for_user.get(user.user_id, [])
        if not primary_roles:
            continue

        primary_name = primary_roles[0].role_name
        possible_second_roles = []
        if primary_name == "Waiter":
            possible_second_roles = ["Bartender", "Host"]
        elif primary_name == "Bartender":
            possible_second_roles = ["Waiter", "Host"]
        elif primary_name == "Host":
            possible_second_roles = ["Waiter", "Bartender"]

        if not possible_second_roles:
            continue

        second_role_name = random.choice(possible_second_roles)
        if second_role_name not in roles:
            continue

        existing_names = {r.role_name for r in primary_roles}
        if second_role_name in existing_names:
            continue

        db.add(
            UserRoleModel(
                user_id=user.user_id,
                role_id=roles[second_role_name].role_id,
            )
        )
        multi_role_count += 1

    db.commit()

    print(f"✅ Created {len(created_employees)} BIG employees ({multi_role_count} multi-role)")
    return created_employees


def create_employee_preferences(db, employees):
    """Create varied preferences for each employee."""
    print("\n⭐ Creating employee preferences...")
    
    # Get shift templates
    templates = {t.shift_template_name: t for t in db.query(ShiftTemplateModel).all()}
    
    # Preference patterns
    preferences_data = [
        # Morning lovers
        ("Alice Johnson", "Morning Shift", [DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY, DayOfWeek.FRIDAY], 0.9),
        ("Bob Smith", "Morning Shift", [DayOfWeek.TUESDAY, DayOfWeek.THURSDAY], 0.8),
        ("Ethan Hunt", "Morning Shift", [DayOfWeek.SATURDAY, DayOfWeek.SUNDAY], 0.85),
        ("Fiona Apple", "Morning Shift", [DayOfWeek.MONDAY, DayOfWeek.FRIDAY], 0.9),
        
        # Evening lovers
        ("Charlie Brown", "Evening Shift", [DayOfWeek.FRIDAY, DayOfWeek.SATURDAY, DayOfWeek.SUNDAY], 1.0),
        ("Diana Prince", "Evening Shift", [DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY], 0.85),
        ("George Clooney", "Evening Shift", [DayOfWeek.THURSDAY, DayOfWeek.FRIDAY], 0.9),
        ("Hannah Montana", "Evening Shift", [DayOfWeek.SATURDAY, DayOfWeek.SUNDAY], 0.95),
        
        # Afternoon preferences (bartenders)
        ("Ian McKellen", "Afternoon Shift", [DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY], 0.9),
        ("Julia Roberts", "Afternoon Shift", [DayOfWeek.THURSDAY, DayOfWeek.FRIDAY], 0.8),
        ("Kevin Hart", "Evening Shift", [DayOfWeek.FRIDAY, DayOfWeek.SATURDAY], 0.95),
        ("Laura Dern", "Morning Shift", [DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY], 0.85),
        ("Morgan Freeman", "Afternoon Shift", [DayOfWeek.TUESDAY, DayOfWeek.THURSDAY], 0.9),
        ("Natalie Portman", "Evening Shift", [DayOfWeek.SATURDAY, DayOfWeek.SUNDAY], 1.0),
        
        # Host preferences
        ("Oliver Twist", "Morning Shift", [DayOfWeek.MONDAY, DayOfWeek.FRIDAY], 0.9),
        ("Penny Lane", "Afternoon Shift", [DayOfWeek.WEDNESDAY, DayOfWeek.SATURDAY], 0.8),
        ("Quinn Fabray", "Evening Shift", [DayOfWeek.FRIDAY, DayOfWeek.SUNDAY], 0.95),
        ("Rachel Green", "Morning Shift", [DayOfWeek.TUESDAY, DayOfWeek.THURSDAY], 0.85),
        ("Sarah Connor", "Afternoon Shift", [DayOfWeek.MONDAY, DayOfWeek.SATURDAY], 0.9),
        
        # Multi-role preferences
        ("Taylor Swift", "Afternoon Shift", [DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY, DayOfWeek.FRIDAY], 0.9),
        ("Uma Thurman", "Morning Shift", [DayOfWeek.TUESDAY, DayOfWeek.THURSDAY], 0.85),
        ("Vincent Vega", "Evening Shift", [DayOfWeek.SATURDAY, DayOfWeek.SUNDAY], 1.0),
        ("Will Smith", "Afternoon Shift", [DayOfWeek.WEDNESDAY, DayOfWeek.FRIDAY], 0.9),
        ("Xena Warrior", "Morning Shift", [DayOfWeek.MONDAY, DayOfWeek.SATURDAY], 0.85),
        ("Yoda Master", "Evening Shift", [DayOfWeek.THURSDAY, DayOfWeek.SUNDAY], 0.9),
    ]
    
    user_map = {user.user_full_name: user for user in employees}
    
    for user_name, template_name, days, weight in preferences_data:
        if user_name in user_map and template_name in templates:
            user = user_map[user_name]
            template = templates[template_name]
            
            for day in days:
                pref = EmployeePreferencesModel(
                    user_id=user.user_id,
                    preferred_shift_template_id=template.shift_template_id,
                    preferred_day_of_week=day,
                    preferred_start_time=template.start_time,
                    preferred_end_time=template.end_time,
                    preference_weight=weight
                )
                db.add(pref)
    
    db.commit()
    count = db.query(EmployeePreferencesModel).count()
    print(f"✅ Created {count} preference records")


def create_employee_preferences_big(db, employees, templates_by_name):
    """
    Create 2–4 preferences per employee, biased by role and shift type.
    
    - Bartenders: prefer Evening/Afternoon
    - Hosts: prefer Morning/Afternoon
    - Waiters: mixed
    - Managers: lighter, earlier shifts
    """
    print("\n⭐ Creating BIG MODE employee preferences...")

    # Helper: choose template name biased by role
    def choose_template_for_role(role_name: str) -> str:
        if role_name == "Bartender":
            return random.choices(
                ["Evening Shift", "Afternoon Shift"], weights=[0.7, 0.3], k=1
            )[0]
        if role_name == "Host":
            return random.choices(
                ["Morning Shift", "Afternoon Shift"], weights=[0.6, 0.4], k=1
            )[0]
        if role_name == "Manager":
            return random.choices(
                ["Morning Shift", "Afternoon Shift"], weights=[0.7, 0.3], k=1
            )[0]
        # Waiter or others: mixed
        return random.choice(["Morning Shift", "Afternoon Shift", "Evening Shift"])

    day_enum_order = [
        DayOfWeek.MONDAY,
        DayOfWeek.TUESDAY,
        DayOfWeek.WEDNESDAY,
        DayOfWeek.THURSDAY,
        DayOfWeek.FRIDAY,
        DayOfWeek.SATURDAY,
        DayOfWeek.SUNDAY,
    ]

    created_count = 0

    # Preload roles for each user
    role_by_id = {r.role_id: r for r in db.query(RoleModel).all()}
    all_user_roles = db.query(UserRoleModel).all()
    roles_for_user = defaultdict(list)
    for ur in all_user_roles:
        roles_for_user[ur.user_id].append(role_by_id.get(ur.role_id))

    for user in employees:
        user_roles = [r for r in roles_for_user.get(user.user_id, []) if r is not None]
        if user_roles:
            primary_role_name = sorted([r.role_name for r in user_roles])[0]
        else:
            primary_role_name = "Waiter"

        # 2–4 preferences each, skewed toward 2–3 overall
        base = random.choice([2, 2, 3, 3, 4])
        num_prefs = base

        chosen_days = random.sample(day_enum_order, k=min(4, len(day_enum_order)))

        for _ in range(num_prefs):
            template_name = choose_template_for_role(primary_role_name)
            template = templates_by_name.get(template_name)
            if not template:
                continue

            day = random.choice(chosen_days)
            weight = round(random.uniform(0.6, 1.0), 2)

            pref = EmployeePreferencesModel(
                user_id=user.user_id,
                preferred_shift_template_id=template.shift_template_id,
                preferred_day_of_week=day,
                preferred_start_time=template.start_time,
                preferred_end_time=template.end_time,
                preference_weight=weight,
            )
            db.add(pref)
            created_count += 1

    db.commit()
    total = db.query(EmployeePreferencesModel).count()
    print(f"✅ Created {created_count} BIG preferences (total in DB: {total})")


def create_system_constraints(db, employees):
    """Create system-wide constraints (these apply to ALL employees)."""
    print("\n⚙️  Creating system constraints...")
    
    # System-wide constraints (apply to everyone)
    constraints_data = [
        (SystemConstraintType.MAX_HOURS_PER_WEEK, 50.0, True),  # Increased from 40
        (SystemConstraintType.MIN_HOURS_PER_WEEK, 15.0, False),  # Reduced from 20
        (SystemConstraintType.MAX_CONSECUTIVE_DAYS, 6, True),  # Increased from 5
        (SystemConstraintType.MIN_REST_HOURS, 8.0, True),  # Reduced from 10
        (SystemConstraintType.MAX_SHIFTS_PER_WEEK, 7, True),  # Increased from 6
        (SystemConstraintType.MIN_SHIFTS_PER_WEEK, 2, False),  # Reduced from 3
    ]
    
    for constraint_type, value, is_hard in constraints_data:
        constraint = SystemConstraintsModel(
            constraint_type=constraint_type,
            constraint_value=value,
            is_hard_constraint=is_hard
        )
        db.add(constraint)
    
    db.commit()
    count = db.query(SystemConstraintsModel).count()
    print(f"✅ Created {count} system-wide constraint records")


def create_system_constraints_big(db):
    """
    Create system-wide constraints tuned for BIG MODE feasibility.
    
    - MAX_HOURS_PER_WEEK: 50 (hard)
    - MIN_HOURS_PER_WEEK: 5 (soft)
    - MIN_REST_HOURS: 8 (hard)
    - MAX_SHIFTS_PER_WEEK: 7 (hard)
    - MIN_SHIFTS_PER_WEEK: 1 (soft)
    - MAX_CONSECUTIVE_DAYS: 6 (hard)
    """
    print("\n⚙️  Creating BIG MODE system constraints...")

    constraints_data = [
        (SystemConstraintType.MAX_HOURS_PER_WEEK, 50.0, True),
        (SystemConstraintType.MIN_HOURS_PER_WEEK, 5.0, False),
        (SystemConstraintType.MAX_CONSECUTIVE_DAYS, 6.0, True),
        (SystemConstraintType.MIN_REST_HOURS, 8.0, True),
        (SystemConstraintType.MAX_SHIFTS_PER_WEEK, 7.0, True),
        (SystemConstraintType.MIN_SHIFTS_PER_WEEK, 1.0, False),
    ]

    for constraint_type, value, is_hard in constraints_data:
        constraint = SystemConstraintsModel(
            constraint_type=constraint_type,
            constraint_value=value,
            is_hard_constraint=is_hard,
        )
        db.add(constraint)

    db.commit()
    count = db.query(SystemConstraintsModel).count()
    print(f"✅ Created {count} BIG MODE system-wide constraint records")


def create_time_off_requests(db, employees):
    """Create 3+ time-off requests for current week (Dec 23-29, 2025)."""
    print("\n📅 Creating time-off requests...")
    
    # Current week: Dec 23-29, 2025
    week_start = date(2025, 12, 23)
    
    time_off_data = [
        # Only 3 employees with time off for variety
        ("Alice Johnson", date(2025, 12, 24), date(2025, 12, 24), TimeOffRequestType.PERSONAL, TimeOffRequestStatus.APPROVED),
        ("Kevin Hart", date(2025, 12, 26), date(2025, 12, 26), TimeOffRequestType.PERSONAL, TimeOffRequestStatus.APPROVED),
        ("Quinn Fabray", date(2025, 12, 27), date(2025, 12, 27), TimeOffRequestType.SICK, TimeOffRequestStatus.APPROVED),
        
        # Pending requests (should not affect optimization)
        ("Bob Smith", date(2025, 12, 30), date(2025, 12, 31), TimeOffRequestType.VACATION, TimeOffRequestStatus.PENDING),
        ("Diana Prince", date(2026, 1, 2), date(2026, 1, 3), TimeOffRequestType.PERSONAL, TimeOffRequestStatus.PENDING),
    ]
    
    user_map = {user.user_full_name: user for user in employees}
    manager = next((u for u in employees if u.user_full_name == "Zack Morris"), employees[0])
    
    for user_name, start, end, req_type, status in time_off_data:
        if user_name in user_map:
            user = user_map[user_name]
            req = TimeOffRequestModel(
                user_id=user.user_id,
                start_date=start,
                end_date=end,
                request_type=req_type,
                status=status,
                approved_by_id=manager.user_id if status == TimeOffRequestStatus.APPROVED else None,
                requested_at=datetime.now()
            )
            db.add(req)
    
    db.commit()
    approved_count = db.query(TimeOffRequestModel).filter(
        TimeOffRequestModel.status == TimeOffRequestStatus.APPROVED
    ).count()
    print(f"✅ Created {approved_count} approved time-off requests")


def create_time_off_requests_big(db, employees, week_start: date):
    """
    Create ~12 approved one-day time-off requests within the given week,
    plus a few pending requests outside the week.
    """
    print("\n📅 Creating BIG MODE time-off requests...")

    week_dates = [week_start + timedelta(days=i) for i in range(7)]

    # Choose managers for approvals
    managers = [u for u in employees if u.is_manager]
    approved_by = managers[0] if managers else (employees[0] if employees else None)

    # Build role mapping
    role_by_id = {r.role_id: r for r in db.query(RoleModel).all()}
    all_user_roles = db.query(UserRoleModel).all()
    roles_for_user = defaultdict(list)
    for ur in all_user_roles:
        roles_for_user[ur.user_id].append(role_by_id.get(ur.role_id))

    # Approved requests inside the week
    approved_requests_target = 12
    approved_created = 0
    day_role_counts = defaultdict(lambda: defaultdict(int))

    shuffled_emps = list(employees)
    random.shuffle(shuffled_emps)

    base_requested_at = datetime(2025, 12, 1, 9, 0, 0)

    for user in shuffled_emps:
        if approved_created >= approved_requests_target:
            break

        user_roles = [r for r in roles_for_user.get(user.user_id, []) if r is not None]
        if not user_roles:
            continue

        primary_role_name = sorted([r.role_name for r in user_roles])[0]
        # Avoid removing too many employees of same role on same day
        random.shuffle(week_dates)
        for d in week_dates:
            if day_role_counts[d][primary_role_name] >= 2:
                continue

            req = TimeOffRequestModel(
                user_id=user.user_id,
                start_date=d,
                end_date=d,
                request_type=TimeOffRequestType.PERSONAL,
                status=TimeOffRequestStatus.APPROVED,
                requested_at=base_requested_at + timedelta(minutes=approved_created),
                approved_by_id=approved_by.user_id if approved_by else None,
                approved_at=base_requested_at + timedelta(minutes=approved_created + 5),
            )
            db.add(req)
            day_role_counts[d][primary_role_name] += 1
            approved_created += 1
            break

    # A few pending requests outside the week (do not affect optimization)
    pending_dates = [
        (week_start + timedelta(days=7), week_start + timedelta(days=8)),
        (week_start - timedelta(days=3), week_start - timedelta(days=2)),
        (week_start + timedelta(days=10), week_start + timedelta(days=11)),
    ]
    for idx, (start, end) in enumerate(pending_dates):
        if idx >= len(employees):
            break
        user = employees[idx]
        req = TimeOffRequestModel(
            user_id=user.user_id,
            start_date=start,
            end_date=end,
            request_type=TimeOffRequestType.VACATION,
            status=TimeOffRequestStatus.PENDING,
            requested_at=base_requested_at + timedelta(days=idx + 30),
            approved_by_id=None,
            approved_at=None,
        )
        db.add(req)

    db.commit()

    approved_count = db.query(TimeOffRequestModel).filter(
        TimeOffRequestModel.status == TimeOffRequestStatus.APPROVED
    ).count()
    pending_count = db.query(TimeOffRequestModel).filter(
        TimeOffRequestModel.status == TimeOffRequestStatus.PENDING
    ).count()
    print(f"✅ Created {approved_created} BIG MODE approved time-off requests (total approved={approved_count}, pending={pending_count})")


def create_default_optimization_config(db):
    """Create a default optimization configuration if one doesn't exist."""
    print("\n⚙️  Creating default optimization configuration...")
    
    # Check if a default config already exists
    existing_default = db.query(OptimizationConfigModel).filter(
        OptimizationConfigModel.is_default == True
    ).first()
    
    if existing_default:
        print(f"   ℹ️  Default config already exists: {existing_default.config_name} (ID: {existing_default.config_id})")
        return existing_default
    
    # Create default configuration
    default_config = OptimizationConfigModel(
        config_name="Default Balanced",
        weight_fairness=0.3,
        weight_preferences=0.4,
        weight_cost=0.1,
        weight_coverage=0.2,
        max_runtime_seconds=600 if is_big_mode() else 300,
        mip_gap=0.01,
        is_default=True
    )
    
    db.add(default_config)
    db.commit()
    db.refresh(default_config)
    
    print(f"   ✅ Created default optimization config: {default_config.config_name} (ID: {default_config.config_id})")
    print(f"      Weights: Fairness={default_config.weight_fairness}, Preferences={default_config.weight_preferences}, Cost={default_config.weight_cost}, Coverage={default_config.weight_coverage}")
    print(f"      Runtime limit: {default_config.max_runtime_seconds}s, MIP gap: {default_config.mip_gap}")
    
    return default_config



def ensure_shift_templates_with_requirements_big(db, roles):
    """
    Ensure Morning/Afternoon/Evening templates exist with high coverage role requirements.
    
    Each template gets required_count totals in the 22–30 range.
    """
    print("\n⏰ Ensuring BIG MODE shift templates with high coverage requirements...")

    # Ensure templates exist (with base requirements)
    create_shift_templates(db, roles)

    # High-coverage requirements per template
    # Totals: 14 + 6 + 2 + 1 = 23 per template
    template_role_counts = {
        "Morning Shift": {"Waiter": 14, "Bartender": 6, "Host": 2, "Manager": 1},
        "Afternoon Shift": {"Waiter": 14, "Bartender": 6, "Host": 2, "Manager": 1},
        "Evening Shift": {"Waiter": 14, "Bartender": 6, "Host": 2, "Manager": 1},
    }

    templates_by_name = {
        t.shift_template_name: t for t in db.query(ShiftTemplateModel).all()
    }

    for template_name, role_counts in template_role_counts.items():
        template = templates_by_name.get(template_name)
        if not template:
            print(f"   ⚠️  Missing template '{template_name}' in BIG MODE setup")
            continue

        # Clear existing requirements for this template
        db.execute(
            delete(shift_role_requirements).where(
                shift_role_requirements.c.shift_template_id == template.shift_template_id
            )
        )

        records = []
        for role_name, required_count in role_counts.items():
            role = roles.get(role_name)
            if not role:
                print(f"   ⚠️  Role '{role_name}' not found when configuring '{template_name}'")
                continue
            records.append(
                {
                    "shift_template_id": template.shift_template_id,
                    "role_id": role.role_id,
                    "required_count": required_count,
                }
            )

        if records:
            db.execute(insert(shift_role_requirements), records)

    db.commit()

    # Sanity log
    for template_name, template in templates_by_name.items():
        if template_name not in template_role_counts:
            continue
        rows = db.execute(
            select(
                shift_role_requirements.c.role_id,
                shift_role_requirements.c.required_count,
            ).where(
                shift_role_requirements.c.shift_template_id
                == template.shift_template_id
            )
        ).all()
        total_required = sum(r.required_count for r in rows)
        print(f"   ✅ Template '{template_name}' total required_count={total_required}")


def create_weekly_schedule_and_planned_shifts_big(
    db, week_start: date, location: str = "Main Restaurant"
) -> WeeklyScheduleModel:
    """
    Create a WeeklyScheduleModel and 7 days × 3 templates = 21 planned shifts.
    """
    print("\n📆 Creating BIG MODE weekly schedule and planned shifts...")

    employees = db.query(UserModel).all()
    managers = [u for u in employees if u.is_manager]
    created_by = managers[0] if managers else (employees[0] if employees else None)
    if not created_by:
        raise RuntimeError("No employees found to act as schedule creator")

    weekly_schedule = WeeklyScheduleModel(
        week_start_date=week_start,
        status=ScheduleStatus.DRAFT,
        created_by_id=created_by.user_id,
    )
    db.add(weekly_schedule)
    db.flush()

    templates = {
        t.shift_template_name: t for t in db.query(ShiftTemplateModel).all()
    }
    required_templates = ["Morning Shift", "Afternoon Shift", "Evening Shift"]
    for name in required_templates:
        if name not in templates:
            raise RuntimeError(f"Required shift template '{name}' not found for BIG MODE")

    for day_offset in range(7):
        shift_date = week_start + timedelta(days=day_offset)
        for template_name in required_templates:
            template = templates[template_name]
            start_dt = datetime.combine(shift_date, template.start_time)
            end_dt = datetime.combine(shift_date, template.end_time)

            planned = PlannedShiftModel(
                weekly_schedule_id=weekly_schedule.weekly_schedule_id,
                shift_template_id=template.shift_template_id,
                date=shift_date,
                start_time=start_dt,
                end_time=end_dt,
                location=template.location or location,
                status=PlannedShiftStatus.PLANNED,
            )
            db.add(planned)

    db.commit()
    db.refresh(weekly_schedule)

    total_shifts = db.query(PlannedShiftModel).filter(
        PlannedShiftModel.weekly_schedule_id == weekly_schedule.weekly_schedule_id
    ).count()
    print(f"✅ Created BIG MODE weekly schedule {weekly_schedule.weekly_schedule_id} with {total_shifts} planned shifts")

    return weekly_schedule


def sanity_validate_big_dataset(db, week_start: date):
    """
    Print sanity checks for BIG MODE dataset:
    - Employees per role
    - Number of shifts
    - Per template required totals
    - Basic coverage feasibility vs. available employees (per role per template)
    """
    print("\n🔎 BIG MODE SANITY VALIDATION")

    # Employees per role
    roles = db.query(RoleModel).all()
    role_counts = {}
    for role in roles:
        count = (
            db.query(UserRoleModel)
            .filter(UserRoleModel.role_id == role.role_id)
            .count()
        )
        role_counts[role.role_name] = count
    print("   Employees per role:")
    for role_name, count in sorted(role_counts.items()):
        print(f"     - {role_name}: {count}")

    # Number of planned shifts
    total_shifts = db.query(PlannedShiftModel).count()
    print(f"   Total planned shifts: {total_shifts}")

    # Per template required totals
    templates = db.query(ShiftTemplateModel).all()
    print("   Shift template role requirements (total per template):")
    max_required_per_role = defaultdict(int)
    for template in templates:
        rows = db.execute(
            select(
                shift_role_requirements.c.role_id,
                shift_role_requirements.c.required_count,
            ).where(
                shift_role_requirements.c.shift_template_id
                == template.shift_template_id
            )
        ).all()
        total_required = sum(r.required_count for r in rows)
        print(
            f"     - {template.shift_template_name}: total_required={total_required}"
        )
        for r in rows:
            role_name = next(
                (ro.role_name for ro in roles if ro.role_id == r.role_id), None
            )
            if role_name:
                if r.required_count > max_required_per_role[role_name]:
                    max_required_per_role[role_name] = r.required_count

    print("   Max required per shift by role vs available employees:")
    for role_name, max_req in sorted(max_required_per_role.items()):
        available = role_counts.get(role_name, 0)
        status = "OK" if available >= max_req else "INSUFFICIENT"
        print(
            f"     - {role_name}: required_max={max_req}, available={available} -> {status}"
        )

    # Optional basic coverage check: for each shift, ensure enough employees per role (ignoring hours/rest)
    print("   Basic coverage check per template (ignoring hours/rest)...")

    # Precompute role -> users
    all_user_roles = db.query(UserRoleModel).all()
    users = db.query(UserModel).all()
    users_by_id = {u.user_id: u for u in users}
    users_for_role = defaultdict(list)
    for ur in all_user_roles:
        role = next((ro for ro in roles if ro.role_id == ur.role_id), None)
        if role:
            users_for_role[role.role_name].append(users_by_id[ur.user_id])

    # Precompute approved time off per user/date
    approved_time_off = db.query(TimeOffRequestModel).filter(
        TimeOffRequestModel.status == TimeOffRequestStatus.APPROVED
    ).all()
    time_off_by_user_date = set(
        (t.user_id, t.start_date) for t in approved_time_off if t.start_date == t.end_date
    )

    problems = 0
    for template in templates:
        rows = db.execute(
            select(
                shift_role_requirements.c.role_id,
                shift_role_requirements.c.required_count,
            ).where(
                shift_role_requirements.c.shift_template_id
                == template.shift_template_id
            )
        ).all()
        if not rows:
            continue

        for day_offset in range(7):
            shift_date = week_start + timedelta(days=day_offset)
            for r in rows:
                role_name = next(
                    (ro.role_name for ro in roles if ro.role_id == r.role_id), None
                )
                if not role_name:
                    continue
                available = [
                    u
                    for u in users_for_role.get(role_name, [])
                    if (u.user_id, shift_date) not in time_off_by_user_date
                ]
                if len(available) < r.required_count:
                    problems += 1

    if problems == 0:
        print("   ✅ Basic per-shift coverage appears FEASIBLE (ignoring hours/rest).")
    else:
        print(
            f"   ⚠️  Found {problems} potential coverage shortfalls in basic check (investigate if needed)."
        )


def main():
    """Main execution function."""
    big_mode = is_big_mode()

    print("="*60)
    print("COMPREHENSIVE DATA SEEDING")
    print("="*60)
    print(f"Mode: {'BIG' if big_mode else 'SMALL'}")

    if big_mode:
        random.seed(RANDOM_SEED)

    db = SessionLocal()

    try:
        # Clear existing data
        clear_existing_data(db)

        # Create roles (must be done before employees)
        roles = create_roles(db)

        if not big_mode:
            # SMALL MODE: original behavior
            create_shift_templates(db, roles)
            employees = create_employees(db, roles)
            create_employee_preferences(db, employees)
            create_system_constraints(db, employees)
            create_time_off_requests(db, employees)
            create_default_optimization_config(db)
        else:
            # BIG MODE: high-coverage, large dataset
            week_start = date(2025, 12, 22)  # Monday of the week

            ensure_shift_templates_with_requirements_big(db, roles)
            employees = create_employees_big(db, roles)
            create_system_constraints_big(db)
            weekly_schedule = create_weekly_schedule_and_planned_shifts_big(
                db, week_start, location="Main Restaurant"
            )

            templates_by_name = {
                t.shift_template_name: t
                for t in db.query(ShiftTemplateModel).all()
            }
            create_employee_preferences_big(db, employees, templates_by_name)
            create_time_off_requests_big(db, employees, week_start)
            create_default_optimization_config(db)
            sanity_validate_big_dataset(db, week_start)

        print("\n" + "="*60)
        print("✅ DATA SEEDING COMPLETE!")
        print("="*60)

        # Summary
        print("\n📊 SUMMARY:")
        print(f"   Employees: {db.query(UserModel).count()}")
        print(f"   Planned shifts: {db.query(PlannedShiftModel).count()}")
        print(f"   Preferences: {db.query(EmployeePreferencesModel).count()}")
        print(f"   Constraints: {db.query(SystemConstraintsModel).count()}")
        print(f"   Time-off requests (approved): {db.query(TimeOffRequestModel).filter(TimeOffRequestModel.status == TimeOffRequestStatus.APPROVED).count()}")
        print(f"   Optimization configs: {db.query(OptimizationConfigModel).count()}")

        print("\n✨ Ready for optimization!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
