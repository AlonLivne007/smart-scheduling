"""
Comprehensive seed data script for smart-scheduling.

Creates:
- 3+ employees per role (Waiter, Bartender, Hostess, Manager)
- 1+ constraint per employee
- 3+ time-off requests for the current week (Dec 23-29, 2025)
- Varied preferences and availability
"""

import sys
import os
from datetime import datetime, date, time, timedelta
from werkzeug.security import generate_password_hash
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import all models to ensure relationships are properly initialized
from app.db.models import (
    roleModel, userModel, userRoleModel, shiftTemplateModel,
    shiftRoleRequirementsTabel, weeklyScheduleModel, plannedShiftModel, shiftAssignmentModel,
    timeOffRequestModel, systemConstraintsModel, employeePreferencesModel,
    optimizationConfigModel, schedulingRunModel, schedulingSolutionModel
)

from app.db.session import SessionLocal
from app.db.models.userModel import UserModel
from app.db.models.roleModel import RoleModel
from app.db.models.userRoleModel import UserRoleModel
from app.db.models.shiftTemplateModel import ShiftTemplateModel
from app.db.models.employeePreferencesModel import EmployeePreferencesModel, DayOfWeek
from app.db.models.weeklyScheduleModel import WeeklyScheduleModel
from app.db.models.plannedShiftModel import PlannedShiftModel, PlannedShiftStatus
from app.db.models.systemConstraintsModel import SystemConstraintsModel, SystemConstraintType
from app.db.models.timeOffRequestModel import TimeOffRequestModel, TimeOffRequestStatus, TimeOffRequestType
from app.db.models.optimizationConfigModel import OptimizationConfigModel


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
    # Keep roles and shift templates
    
    db.commit()
    print("✅ Data cleared")


def create_employees(db):
    """Create employees with multiple roles."""
    print("\n👥 Creating employees...")
    
    # Get roles
    roles = {role.role_name: role for role in db.query(RoleModel).all()}
    
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
        
        # Hostesses (5 employees - expanded from 3)
        {"name": "Oliver Twist", "email": "oliver@restaurant.com", "roles": ["Hostess"]},
        {"name": "Penny Lane", "email": "penny@restaurant.com", "roles": ["Hostess"]},
        {"name": "Quinn Fabray", "email": "quinn@restaurant.com", "roles": ["Hostess"]},
        {"name": "Rachel Green", "email": "rachel@restaurant.com", "roles": ["Hostess"]},
        {"name": "Sarah Connor", "email": "sarah@restaurant.com", "roles": ["Hostess"]},
        
        # Multi-role employees (6 employees - expanded from 3)
        {"name": "Taylor Swift", "email": "taylor@restaurant.com", "roles": ["Waiter", "Bartender"]},
        {"name": "Uma Thurman", "email": "uma@restaurant.com", "roles": ["Waiter", "Hostess"]},
        {"name": "Vincent Vega", "email": "vincent@restaurant.com", "roles": ["Bartender", "Hostess"]},
        {"name": "Will Smith", "email": "will@restaurant.com", "roles": ["Waiter", "Bartender"]},
        {"name": "Xena Warrior", "email": "xena@restaurant.com", "roles": ["Waiter", "Hostess"]},
        {"name": "Yoda Master", "email": "yoda@restaurant.com", "roles": ["Bartender", "Hostess"]},
        
        # Managers (3 employees)
        {"name": "Zack Morris", "email": "zack@restaurant.com", "roles": ["Manager"], "password": "password123", "is_manager": True},
        {"name": "Amy Adams", "email": "amy@restaurant.com", "roles": ["Manager"], "password": "password123", "is_manager": True},
        {"name": "Daniel Gusakov", "email": "daniel.gusakov@gmail.com", "roles": ["Manager"], "password": "Daniel124", "is_manager": True},
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
        
        created_employees.append(user)
        print(f"   ✅ {emp_data['name']} ({', '.join(emp_data['roles'])})")
    
    db.commit()
    print(f"\n✅ Created {len(created_employees)} employees")
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
        
        # Hostess preferences
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
        max_runtime_seconds=300,
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


def create_weekly_schedule(db, employees):
    """Create weekly schedule for current week with comprehensive shifts."""
    print("\n📋 Creating weekly schedule for Dec 23-29, 2025...")
    
    # Get shift templates and roles
    templates = {t.shift_template_name: t for t in db.query(ShiftTemplateModel).all()}
    roles = {r.role_name: r for r in db.query(RoleModel).all()}
    
    # Get first manager or user
    manager = next((u for u in employees if u.user_full_name == "Zack Morris"), employees[0])
    
    # Create weekly schedule
    schedule = WeeklyScheduleModel(
        week_start_date=date(2025, 12, 23),
        created_by_id=manager.user_id
    )
    db.add(schedule)
    db.flush()
    
    # Create shifts for each day
    shift_configs = [
        # Each day needs: Morning (Waiter, Bartender, Hostess), Afternoon (same), Evening (same)
        (DayOfWeek.MONDAY, "Morning Shift", ["Waiter", "Bartender", "Hostess"]),
        (DayOfWeek.MONDAY, "Afternoon Shift", ["Waiter", "Bartender", "Hostess"]),
        (DayOfWeek.MONDAY, "Evening Shift", ["Waiter", "Waiter", "Bartender", "Hostess"]),  # Extra waiter for evening
        
        (DayOfWeek.TUESDAY, "Morning Shift", ["Waiter", "Bartender", "Hostess"]),
        (DayOfWeek.TUESDAY, "Afternoon Shift", ["Waiter", "Bartender", "Hostess"]),
        (DayOfWeek.TUESDAY, "Evening Shift", ["Waiter", "Waiter", "Bartender", "Hostess"]),
        
        (DayOfWeek.WEDNESDAY, "Morning Shift", ["Waiter", "Bartender", "Hostess"]),
        (DayOfWeek.WEDNESDAY, "Afternoon Shift", ["Waiter", "Bartender", "Hostess"]),
        (DayOfWeek.WEDNESDAY, "Evening Shift", ["Waiter", "Waiter", "Bartender", "Hostess"]),
        
        (DayOfWeek.THURSDAY, "Morning Shift", ["Waiter", "Bartender", "Hostess"]),
        (DayOfWeek.THURSDAY, "Afternoon Shift", ["Waiter", "Bartender", "Hostess"]),
        (DayOfWeek.THURSDAY, "Evening Shift", ["Waiter", "Waiter", "Bartender", "Hostess"]),
        
        (DayOfWeek.FRIDAY, "Morning Shift", ["Waiter", "Bartender", "Hostess"]),
        (DayOfWeek.FRIDAY, "Afternoon Shift", ["Waiter", "Waiter", "Bartender", "Hostess"]),  # Busy Friday
        (DayOfWeek.FRIDAY, "Evening Shift", ["Waiter", "Waiter", "Waiter", "Bartender", "Bartender", "Hostess"]),  # Very busy
        
        (DayOfWeek.SATURDAY, "Morning Shift", ["Waiter", "Bartender", "Hostess"]),
        (DayOfWeek.SATURDAY, "Afternoon Shift", ["Waiter", "Waiter", "Bartender", "Hostess"]),
        (DayOfWeek.SATURDAY, "Evening Shift", ["Waiter", "Waiter", "Waiter", "Bartender", "Bartender", "Hostess"]),
        
        (DayOfWeek.SUNDAY, "Morning Shift", ["Waiter", "Bartender", "Hostess"]),
        (DayOfWeek.SUNDAY, "Afternoon Shift", ["Waiter", "Bartender", "Hostess"]),
        (DayOfWeek.SUNDAY, "Evening Shift", ["Waiter", "Waiter", "Bartender", "Hostess"]),
    ]
    
    # Map day of week to date
    day_map = {
        DayOfWeek.MONDAY: 0,    # Dec 23 is Tuesday, so offset
        DayOfWeek.TUESDAY: 1,
        DayOfWeek.WEDNESDAY: 2,
        DayOfWeek.THURSDAY: 3,
        DayOfWeek.FRIDAY: 4,
        DayOfWeek.SATURDAY: 5,
        DayOfWeek.SUNDAY: 6
    }
    
    # Dec 23, 2025 is a Tuesday
    base_date = date(2025, 12, 23)  # Tuesday
    # Adjust day_map: Tuesday=0, Wednesday=1, etc.
    actual_day_map = {
        DayOfWeek.TUESDAY: 0,
        DayOfWeek.WEDNESDAY: 1,
        DayOfWeek.THURSDAY: 2,
        DayOfWeek.FRIDAY: 3,
        DayOfWeek.SATURDAY: 4,
        DayOfWeek.SUNDAY: 5,
        DayOfWeek.MONDAY: 6  # Dec 29 is Monday
    }
    
    shift_count = 0
    for day_of_week, template_name, role_names in shift_configs:
        if template_name not in templates:
            continue
        
        template = templates[template_name]
        shift_date = base_date + timedelta(days=actual_day_map[day_of_week])
        
        # Create one planned shift for each role requirement
        for role_name in role_names:
            if role_name not in roles:
                continue
            
            # Create datetime objects
            start_datetime = datetime.combine(shift_date, template.start_time)
            end_datetime = datetime.combine(shift_date, template.end_time)
            
            # Create planned shift
            planned_shift = PlannedShiftModel(
                weekly_schedule_id=schedule.weekly_schedule_id,
                shift_template_id=template.shift_template_id,
                date=shift_date,
                start_time=start_datetime,
                end_time=end_datetime,
                location="Main Restaurant",
                status=PlannedShiftStatus.PLANNED
            )
            db.add(planned_shift)
            
            shift_count += 1
    
    db.commit()
    db.refresh(schedule)
    
    print(f"✅ Created weekly schedule {schedule.weekly_schedule_id} with {shift_count} shifts")
    return schedule


def main():
    """Main execution function."""
    print("="*60)
    print("COMPREHENSIVE DATA SEEDING")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Clear existing data
        clear_existing_data(db)
        
        # Create employees (3+ per role)
        employees = create_employees(db)
        
        # Create employee preferences
        create_employee_preferences(db, employees)
        
        # Create system constraints (1+ per employee)
        create_system_constraints(db, employees)
        
        # Create time-off requests (3+ for current week)
        create_time_off_requests(db, employees)
        
        # Create default optimization configuration
        create_default_optimization_config(db)
        
        # Create weekly schedule with shifts
        schedule = create_weekly_schedule(db, employees)
        
        print("\n" + "="*60)
        print("✅ DATA SEEDING COMPLETE!")
        print("="*60)
        
        # Summary
        print("\n📊 SUMMARY:")
        print(f"   Employees: {db.query(UserModel).count()}")
        print(f"   Preferences: {db.query(EmployeePreferencesModel).count()}")
        print(f"   Constraints: {db.query(SystemConstraintsModel).count()}")
        print(f"   Time-off requests (approved): {db.query(TimeOffRequestModel).filter(TimeOffRequestModel.status == TimeOffRequestStatus.APPROVED).count()}")
        print(f"   Optimization configs: {db.query(OptimizationConfigModel).count()}")
        print(f"   Weekly schedule: {schedule.weekly_schedule_id}")
        print(f"   Planned shifts: {db.query(PlannedShiftModel).filter(PlannedShiftModel.weekly_schedule_id == schedule.weekly_schedule_id).count()}")
        
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
