"""
Toy Cases Tests for Constraint Validation.

These tests use simple, predictable scenarios where we know the expected outcome.
Each test creates its own minimal dataset to test specific constraint behaviors.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.models import (
    roleModel, userModel, userRoleModel, shiftTemplateModel,
    shiftRoleRequirementsTabel, weeklyScheduleModel, plannedShiftModel, shiftAssignmentModel,
    timeOffRequestModel, systemConstraintsModel, employeePreferencesModel,
    optimizationConfigModel, schedulingRunModel, schedulingSolutionModel
)

from app.db.session import SessionLocal
from app.services.scheduling.scheduling_service import SchedulingService
from app.services.constraintService import ConstraintService
from app.db.models.systemConstraintsModel import SystemConstraintsModel, SystemConstraintType
from app.db.models.weeklyScheduleModel import WeeklyScheduleModel, ScheduleStatus
from app.db.models.plannedShiftModel import PlannedShiftModel, PlannedShiftStatus
from app.db.models.shiftTemplateModel import ShiftTemplateModel
from app.db.models.userModel import UserModel
from app.db.models.roleModel import RoleModel
from app.db.models.userRoleModel import UserRoleModel
from app.db.models.shiftRoleRequirementsTabel import shift_role_requirements
from app.services.utils.datetime_utils import normalize_shift_datetimes
from datetime import datetime, timedelta, date, time
from werkzeug.security import generate_password_hash
from sqlalchemy import insert


class ToyCaseTestHelper:
    """Helper class to create minimal test data for toy cases."""
    
    def __init__(self, db):
        self.db = db
        self.created_roles = []
        self.created_users = []
        self.created_templates = []
        self.created_schedules = []
        self.created_constraints = []
    
    def create_role(self, role_name: str) -> RoleModel:
        """Create a test role."""
        role = self.db.query(RoleModel).filter(RoleModel.role_name == role_name).first()
        if not role:
            role = RoleModel(role_name=role_name)
            self.db.add(role)
            self.db.commit()
            self.db.refresh(role)
        self.created_roles.append(role)
        return role
    
    def create_employee(self, name: str, email: str, roles: list) -> UserModel:
        """Create a test employee with roles."""
        # Make email unique by adding timestamp
        import time
        unique_email = f"{int(time.time() * 1000000)}_{email}"
        
        user = UserModel(
            user_full_name=name,
            user_email=unique_email,
            hashed_password=generate_password_hash("test123"),
            user_status="ACTIVE",
            is_manager=False
        )
        self.db.add(user)
        self.db.flush()
        
        # Assign roles
        for role_name in roles:
            role = self.create_role(role_name)
            user_role = UserRoleModel(
                user_id=user.user_id,
                role_id=role.role_id
            )
            self.db.add(user_role)
        
        self.db.commit()
        self.db.refresh(user)
        self.created_users.append(user)
        return user
    
    def create_shift_template(self, name: str, start_time: time, end_time: time, 
                             required_roles: list) -> ShiftTemplateModel:
        """Create a shift template with required roles."""
        # Make name unique
        import time as time_module
        unique_name = f"{name}_{int(time_module.time() * 1000000)}"
        
        template = ShiftTemplateModel(
            shift_template_name=unique_name,
            start_time=start_time,
            end_time=end_time,
            location="Test Location"
        )
        self.db.add(template)
        self.db.flush()
        
        # Add required roles
        role_requirements = []
        for role_name, count in required_roles:
            role = self.create_role(role_name)
            role_requirements.append({
                "shift_template_id": template.shift_template_id,
                "role_id": role.role_id,
                "required_count": count
            })
        
        if role_requirements:
            self.db.execute(insert(shift_role_requirements), role_requirements)
        
        self.db.commit()
        self.db.refresh(template)
        self.created_templates.append(template)
        return template
    
    def create_weekly_schedule(self, week_start: date, created_by: UserModel) -> WeeklyScheduleModel:
        """Create a weekly schedule."""
        schedule = WeeklyScheduleModel(
            week_start_date=week_start,
            status=ScheduleStatus.DRAFT,
            created_by_id=created_by.user_id
        )
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        self.created_schedules.append(schedule)
        return schedule
    
    def create_planned_shift(self, schedule: WeeklyScheduleModel, template: ShiftTemplateModel,
                            shift_date: date) -> PlannedShiftModel:
        """Create a planned shift from template."""
        # Get time values from template
        start_time_val: time = template.start_time  # type: ignore
        end_time_val: time = template.end_time  # type: ignore
        start_dt = datetime.combine(shift_date, start_time_val)
        end_dt = datetime.combine(shift_date, end_time_val)
        
        planned = PlannedShiftModel(
            weekly_schedule_id=schedule.weekly_schedule_id,
            shift_template_id=template.shift_template_id,
            date=shift_date,
            start_time=start_dt,
            end_time=end_dt,
            location=template.location,
            status=PlannedShiftStatus.PLANNED
        )
        self.db.add(planned)
        self.db.commit()
        self.db.refresh(planned)
        return planned
    
    def set_constraint(self, constraint_type: SystemConstraintType, value: float, is_hard: bool):
        """Set a system constraint."""
        constraint = self.db.query(SystemConstraintsModel).filter(
            SystemConstraintsModel.constraint_type == constraint_type
        ).first()
        
        if constraint:
            original_value = constraint.constraint_value
            original_hard = constraint.is_hard_constraint
            constraint.constraint_value = value
            constraint.is_hard_constraint = is_hard
            self.created_constraints.append((constraint_type, original_value, original_hard))
        else:
            constraint = SystemConstraintsModel(
                constraint_type=constraint_type,
                constraint_value=value,
                is_hard_constraint=is_hard
            )
            self.db.add(constraint)
            self.created_constraints.append((constraint_type, None, None))
        
        self.db.commit()
    
    def remove_other_constraints(self, keep_constraint: SystemConstraintType):
        """Remove all constraints except the one specified."""
        all_constraints = self.db.query(SystemConstraintsModel).all()
        for constraint in all_constraints:
            if constraint.constraint_type != keep_constraint:
                # Save original if not already saved
                found = False
                for saved_type, _, _ in self.created_constraints:
                    if saved_type == constraint.constraint_type:
                        found = True
                        break
                if not found:
                    self.created_constraints.append((
                        constraint.constraint_type,
                        constraint.constraint_value,
                        constraint.is_hard_constraint
                    ))
                self.db.delete(constraint)
        self.db.commit()
    
    def cleanup(self):
        """Clean up created test data."""
        try:
            # Rollback any pending transactions first
            self.db.rollback()
        except:
            pass
        
        try:
            # Restore original constraints
            for constraint_type, original_value, original_hard in self.created_constraints:
                constraint = self.db.query(SystemConstraintsModel).filter(
                    SystemConstraintsModel.constraint_type == constraint_type
                ).first()
                if constraint:
                    if original_value is not None:
                        constraint.constraint_value = original_value
                        constraint.is_hard_constraint = original_hard
                    else:
                        self.db.delete(constraint)
            
            # Delete created data in reverse order
            for schedule in self.created_schedules:
                # Delete planned shifts
                self.db.query(PlannedShiftModel).filter(
                    PlannedShiftModel.weekly_schedule_id == schedule.weekly_schedule_id
                ).delete(synchronize_session=False)
                self.db.delete(schedule)
            
            for user in self.created_users:
                # Delete user roles
                self.db.query(UserRoleModel).filter(
                    UserRoleModel.user_id == user.user_id
                ).delete(synchronize_session=False)
                self.db.delete(user)
            
            for template in self.created_templates:
                # Delete role requirements
                try:
                    self.db.execute(
                        shift_role_requirements.delete().where(
                            shift_role_requirements.c.shift_template_id == template.shift_template_id
                        )
                    )
                except:
                    pass
                self.db.delete(template)
            
            self.db.commit()
        except Exception as e:
            # If cleanup fails, rollback
            try:
                self.db.rollback()
            except:
                pass


def test_min_rest_hours_pass():
    """Test MIN_REST_HOURS: Should PASS - shifts have enough rest between them."""
    db = SessionLocal()
    helper = ToyCaseTestHelper(db)
    
    try:
        print("=" * 80)
        print("TOY CASE: MIN_REST_HOURS - Should PASS")
        print("=" * 80)
        print("Scenario: Two shifts with 12 hours rest between them")
        print("Expected: Should pass MIN_REST_HOURS=8 (HARD)")
        
        # Create test data
        role = helper.create_role("Waiter")
        employee = helper.create_employee("Test Employee", "test@example.com", ["Waiter"])
        
        # Create shift templates
        morning = helper.create_shift_template(
            "Morning", time(8, 0), time(14, 0), [("Waiter", 1)]
        )
        evening = helper.create_shift_template(
            "Evening", time(20, 0), time(2, 0), [("Waiter", 1)]  # Overnight shift
        )
        
        # Create weekly schedule
        week_start = date.today()
        schedule = helper.create_weekly_schedule(week_start, employee)
        
        # Create planned shifts with 12 hours rest (enough)
        # Day 1: Morning 8:00-14:00
        shift1 = helper.create_planned_shift(schedule, morning, week_start)
        # Day 2: Evening 20:00-02:00 (next day) - 12 hours after shift1 ends
        shift2 = helper.create_planned_shift(schedule, evening, week_start + timedelta(days=1))
        
        # Set constraint and remove others that might interfere
        helper.remove_other_constraints(SystemConstraintType.MIN_REST_HOURS)
        helper.set_constraint(SystemConstraintType.MIN_REST_HOURS, 8.0, True)
        
        # Test assignment
        constraint_service = ConstraintService(db)
        constraint_service.refresh_constraints()  # Refresh to get updated constraints
        
        # Assign employee to both shifts
        assignments = [
            {'user_id': employee.user_id, 'planned_shift_id': shift1.planned_shift_id, 'role_id': role.role_id},
            {'user_id': employee.user_id, 'planned_shift_id': shift2.planned_shift_id, 'role_id': role.role_id}
        ]
        
        schedule_id = int(schedule.weekly_schedule_id)  # type: ignore
        validation = constraint_service.validate_weekly_schedule(
            schedule_id,
            assignments
        )
        
        print(f"\nResults:")
        print(f"  Valid: {validation.is_valid()}")
        print(f"  Errors: {len(validation.errors)}")
        print(f"  Warnings: {len(validation.warnings)}")
        
        if validation.is_valid():
            print(f"\n  ✅ PASS: No violations (as expected)")
        else:
            print(f"\n  ❌ FAIL: Unexpected violations:")
            for error in validation.errors:
                print(f"    - {error.message}")
        
        assert validation.is_valid(), "Expected validation to pass"
        
    finally:
        helper.cleanup()
        db.close()


def test_min_rest_hours_fail():
    """Test MIN_REST_HOURS: Should FAIL - shifts don't have enough rest."""
    db = SessionLocal()
    helper = ToyCaseTestHelper(db)
    
    try:
        print("=" * 80)
        print("TOY CASE: MIN_REST_HOURS - Should FAIL")
        print("=" * 80)
        print("Scenario: Two consecutive shifts with only 2 hours rest")
        print("Expected: Should fail MIN_REST_HOURS=8 (HARD)")
        
        # Create test data
        role = helper.create_role("Waiter")
        employee = helper.create_employee("Test Employee", "test@example.com", ["Waiter"])
        
        # Create shift templates - consecutive shifts
        morning = helper.create_shift_template(
            "Morning", time(8, 0), time(14, 0), [("Waiter", 1)]
        )
        afternoon = helper.create_shift_template(
            "Afternoon", time(16, 0), time(22, 0), [("Waiter", 1)]  # Only 2 hours after morning
        )
        
        # Create weekly schedule
        week_start = date.today()
        schedule = helper.create_weekly_schedule(week_start, employee)
        
        # Create planned shifts - same day, only 2 hours apart
        shift1 = helper.create_planned_shift(schedule, morning, week_start)
        shift2 = helper.create_planned_shift(schedule, afternoon, week_start)
        
        # Set constraint and remove others that might interfere
        helper.remove_other_constraints(SystemConstraintType.MIN_REST_HOURS)
        helper.set_constraint(SystemConstraintType.MIN_REST_HOURS, 8.0, True)
        
        # Test assignment
        constraint_service = ConstraintService(db)
        constraint_service.refresh_constraints()  # Refresh to get updated constraints
        
        assignments = [
            {'user_id': employee.user_id, 'planned_shift_id': shift1.planned_shift_id, 'role_id': role.role_id},
            {'user_id': employee.user_id, 'planned_shift_id': shift2.planned_shift_id, 'role_id': role.role_id}
        ]
        
        schedule_id = int(schedule.weekly_schedule_id)  # type: ignore
        validation = constraint_service.validate_weekly_schedule(
            schedule_id,
            assignments
        )
        
        print(f"\nResults:")
        print(f"  Valid: {validation.is_valid()}")
        print(f"  Errors: {len(validation.errors)}")
        
        rest_errors = [e for e in validation.errors if e.constraint_type == "INSUFFICIENT_REST"]
        print(f"  Rest period errors: {len(rest_errors)}")
        
        if not validation.is_valid() and rest_errors:
            print(f"\n  ✅ PASS: Correctly detected insufficient rest (as expected)")
            for error in rest_errors[:3]:
                print(f"    - {error.message}")
        else:
            print(f"\n  ❌ FAIL: Expected rest period violation but got:")
            print(f"    Valid: {validation.is_valid()}")
            print(f"    Errors: {len(validation.errors)}")
        
        assert not validation.is_valid(), "Expected validation to fail"
        assert len(rest_errors) > 0, "Expected rest period errors"
        
    finally:
        helper.cleanup()
        db.close()


def test_max_hours_per_week_pass():
    """Test MAX_HOURS_PER_WEEK: Should PASS - total hours within limit."""
    db = SessionLocal()
    helper = ToyCaseTestHelper(db)
    
    try:
        print("=" * 80)
        print("TOY CASE: MAX_HOURS_PER_WEEK - Should PASS")
        print("=" * 80)
        print("Scenario: Employee works 35 hours (below MAX_HOURS=40)")
        print("Expected: Should pass MAX_HOURS=40 (HARD)")
        
        role = helper.create_role("Waiter")
        employee = helper.create_employee("Test Employee", "test@example.com", ["Waiter"])
        
        # Create shift template: 7 hours per shift
        shift_template = helper.create_shift_template(
            "Regular", time(9, 0), time(16, 0), [("Waiter", 1)]
        )
        
        week_start = date.today()
        schedule = helper.create_weekly_schedule(week_start, employee)
        
        # Create 5 shifts = 35 hours total (below 40)
        assignments = []
        for day in range(5):
            shift = helper.create_planned_shift(schedule, shift_template, week_start + timedelta(days=day))
            assignments.append({
                'user_id': employee.user_id,
                'planned_shift_id': shift.planned_shift_id,
                'role_id': role.role_id
            })
        
        helper.set_constraint(SystemConstraintType.MAX_HOURS_PER_WEEK, 40.0, True)
        
        constraint_service = ConstraintService(db)
        schedule_id = int(schedule.weekly_schedule_id)  # type: ignore
        validation = constraint_service.validate_weekly_schedule(
            schedule_id,
            assignments
        )
        
        print(f"\nResults:")
        print(f"  Total shifts: 5")
        print(f"  Total hours: 35 (7 hours × 5 shifts)")
        print(f"  Max hours: 40")
        print(f"  Valid: {validation.is_valid()}")
        print(f"  Errors: {len(validation.errors)}")
        
        if validation.is_valid():
            print(f"\n  ✅ PASS: Within hours limit (as expected)")
        else:
            print(f"\n  ❌ FAIL: Unexpected violations")
        
        assert validation.is_valid(), "Expected validation to pass"
        
    finally:
        helper.cleanup()
        db.close()


def test_max_hours_per_week_fail():
    """Test MAX_HOURS_PER_WEEK: Should FAIL - total hours exceed limit."""
    db = SessionLocal()
    helper = ToyCaseTestHelper(db)
    
    try:
        print("=" * 80)
        print("TOY CASE: MAX_HOURS_PER_WEEK - Should FAIL")
        print("=" * 80)
        print("Scenario: Employee works 50 hours (exceeds MAX_HOURS=40)")
        print("Expected: Should fail MAX_HOURS=40 (HARD)")
        
        role = helper.create_role("Waiter")
        employee = helper.create_employee("Test Employee", "test@example.com", ["Waiter"])
        
        # Create shift template: 10 hours per shift
        shift_template = helper.create_shift_template(
            "Long", time(8, 0), time(18, 0), [("Waiter", 1)]
        )
        
        week_start = date.today()
        schedule = helper.create_weekly_schedule(week_start, employee)
        
        # Create 5 shifts = 50 hours total (exceeds 40)
        assignments = []
        for day in range(5):
            shift = helper.create_planned_shift(schedule, shift_template, week_start + timedelta(days=day))
            assignments.append({
                'user_id': employee.user_id,
                'planned_shift_id': shift.planned_shift_id,
                'role_id': role.role_id
            })
        
        helper.set_constraint(SystemConstraintType.MAX_HOURS_PER_WEEK, 40.0, True)
        
        constraint_service = ConstraintService(db)
        schedule_id = int(schedule.weekly_schedule_id)  # type: ignore
        validation = constraint_service.validate_weekly_schedule(
            schedule_id,
            assignments
        )
        
        print(f"\nResults:")
        print(f"  Total shifts: 5")
        print(f"  Total hours: 50 (10 hours × 5 shifts)")
        print(f"  Max hours: 40")
        print(f"  Valid: {validation.is_valid()}")
        print(f"  Errors: {len(validation.errors)}")
        
        max_hours_errors = [e for e in validation.errors if e.constraint_type == "MAX_HOURS_EXCEEDED"]
        
        if not validation.is_valid() and max_hours_errors:
            print(f"\n  ✅ PASS: Correctly detected hours exceeded (as expected)")
            for error in max_hours_errors[:2]:
                print(f"    - {error.message}")
        else:
            print(f"\n  ❌ FAIL: Expected hours violation")
        
        assert not validation.is_valid(), "Expected validation to fail"
        assert len(max_hours_errors) > 0, "Expected max hours errors"
        
    finally:
        helper.cleanup()
        db.close()


def test_min_hours_per_week_pass():
    """Test MIN_HOURS_PER_WEEK: Should PASS - total hours meet minimum."""
    db = SessionLocal()
    helper = ToyCaseTestHelper(db)
    
    try:
        print("=" * 80)
        print("TOY CASE: MIN_HOURS_PER_WEEK - Should PASS")
        print("=" * 80)
        print("Scenario: Employee works 25 hours (meets MIN_HOURS=20)")
        print("Expected: Should pass MIN_HOURS=20 (HARD)")
        
        role = helper.create_role("Waiter")
        employee = helper.create_employee("Test Employee", "test@example.com", ["Waiter"])
        
        shift_template = helper.create_shift_template(
            "Regular", time(9, 0), time(14, 0), [("Waiter", 1)]  # 5 hours
        )
        
        week_start = date.today()
        schedule = helper.create_weekly_schedule(week_start, employee)
        
        # Create 5 shifts = 25 hours total (meets 20)
        assignments = []
        for day in range(5):
            shift = helper.create_planned_shift(schedule, shift_template, week_start + timedelta(days=day))
            assignments.append({
                'user_id': employee.user_id,
                'planned_shift_id': shift.planned_shift_id,
                'role_id': role.role_id
            })
        
        helper.remove_other_constraints(SystemConstraintType.MIN_HOURS_PER_WEEK)
        helper.set_constraint(SystemConstraintType.MIN_HOURS_PER_WEEK, 20.0, True)
        constraint_service = ConstraintService(db)
        constraint_service.refresh_constraints()
        
        constraint_service = ConstraintService(db)
        schedule_id = int(schedule.weekly_schedule_id)  # type: ignore
        validation = constraint_service.validate_weekly_schedule(
            schedule_id,
            assignments
        )
        
        print(f"\nResults:")
        print(f"  Total hours: 25 (5 hours × 5 shifts)")
        print(f"  Min hours: 20")
        print(f"  Valid: {validation.is_valid()}")
        
        if validation.is_valid():
            print(f"\n  ✅ PASS: Meets minimum hours (as expected)")
        else:
            print(f"\n  ❌ FAIL: Unexpected violations")
        
        assert validation.is_valid(), "Expected validation to pass"
        
    finally:
        helper.cleanup()
        db.close()


def test_min_hours_per_week_fail():
    """Test MIN_HOURS_PER_WEEK: Should FAIL - total hours below minimum."""
    db = SessionLocal()
    helper = ToyCaseTestHelper(db)
    
    try:
        print("=" * 80)
        print("TOY CASE: MIN_HOURS_PER_WEEK - Should FAIL")
        print("=" * 80)
        print("Scenario: Employee works 10 hours (below MIN_HOURS=20)")
        print("Expected: Should fail MIN_HOURS=20 (HARD)")
        
        role = helper.create_role("Waiter")
        employee = helper.create_employee("Test Employee", "test@example.com", ["Waiter"])
        
        shift_template = helper.create_shift_template(
            "Short", time(9, 0), time(11, 0), [("Waiter", 1)]  # 2 hours
        )
        
        week_start = date.today()
        schedule = helper.create_weekly_schedule(week_start, employee)
        
        # Create 5 shifts = 10 hours total (below 20)
        assignments = []
        for day in range(5):
            shift = helper.create_planned_shift(schedule, shift_template, week_start + timedelta(days=day))
            assignments.append({
                'user_id': employee.user_id,
                'planned_shift_id': shift.planned_shift_id,
                'role_id': role.role_id
            })
        
        helper.remove_other_constraints(SystemConstraintType.MIN_HOURS_PER_WEEK)
        helper.set_constraint(SystemConstraintType.MIN_HOURS_PER_WEEK, 20.0, True)
        constraint_service = ConstraintService(db)
        constraint_service.refresh_constraints()
        
        constraint_service = ConstraintService(db)
        schedule_id = int(schedule.weekly_schedule_id)  # type: ignore
        validation = constraint_service.validate_weekly_schedule(
            schedule_id,
            assignments
        )
        
        print(f"\nResults:")
        print(f"  Total hours: 10 (2 hours × 5 shifts)")
        print(f"  Min hours: 20")
        print(f"  Valid: {validation.is_valid()}")
        print(f"  Errors: {len(validation.errors)}")
        
        min_hours_errors = [e for e in validation.errors if e.constraint_type == "MIN_HOURS_NOT_MET"]
        
        if not validation.is_valid() and min_hours_errors:
            print(f"\n  ✅ PASS: Correctly detected insufficient hours (as expected)")
        else:
            print(f"\n  ❌ FAIL: Expected min hours violation")
        
        assert not validation.is_valid(), "Expected validation to fail"
        assert len(min_hours_errors) > 0, "Expected min hours errors"
        
    finally:
        helper.cleanup()
        db.close()


def test_max_shifts_per_week_pass():
    """Test MAX_SHIFTS_PER_WEEK: Should PASS - shift count within limit."""
    db = SessionLocal()
    helper = ToyCaseTestHelper(db)
    
    try:
        print("=" * 80)
        print("TOY CASE: MAX_SHIFTS_PER_WEEK - Should PASS")
        print("=" * 80)
        print("Scenario: Employee works 4 shifts (below MAX_SHIFTS=5)")
        print("Expected: Should pass MAX_SHIFTS=5 (HARD)")
        
        role = helper.create_role("Waiter")
        employee = helper.create_employee("Test Employee", "test@example.com", ["Waiter"])
        
        shift_template = helper.create_shift_template(
            "Regular", time(9, 0), time(17, 0), [("Waiter", 1)]
        )
        
        week_start = date.today()
        schedule = helper.create_weekly_schedule(week_start, employee)
        
        # Create 4 shifts (below 5)
        assignments = []
        for day in range(4):
            shift = helper.create_planned_shift(schedule, shift_template, week_start + timedelta(days=day))
            assignments.append({
                'user_id': employee.user_id,
                'planned_shift_id': shift.planned_shift_id,
                'role_id': role.role_id
            })
        
        helper.remove_other_constraints(SystemConstraintType.MAX_SHIFTS_PER_WEEK)
        helper.set_constraint(SystemConstraintType.MAX_SHIFTS_PER_WEEK, 5.0, True)
        constraint_service = ConstraintService(db)
        constraint_service.refresh_constraints()
        
        constraint_service = ConstraintService(db)
        schedule_id = int(schedule.weekly_schedule_id)  # type: ignore
        validation = constraint_service.validate_weekly_schedule(
            schedule_id,
            assignments
        )
        
        print(f"\nResults:")
        print(f"  Total shifts: 4")
        print(f"  Max shifts: 5")
        print(f"  Valid: {validation.is_valid()}")
        
        if validation.is_valid():
            print(f"\n  ✅ PASS: Within shift limit (as expected)")
        else:
            print(f"\n  ❌ FAIL: Unexpected violations")
        
        assert validation.is_valid(), "Expected validation to pass"
        
    finally:
        helper.cleanup()
        db.close()


def test_max_shifts_per_week_fail():
    """Test MAX_SHIFTS_PER_WEEK: Should FAIL - shift count exceeds limit."""
    db = SessionLocal()
    helper = ToyCaseTestHelper(db)
    
    try:
        print("=" * 80)
        print("TOY CASE: MAX_SHIFTS_PER_WEEK - Should FAIL")
        print("=" * 80)
        print("Scenario: Employee works 6 shifts (exceeds MAX_SHIFTS=5)")
        print("Expected: Should fail MAX_SHIFTS=5 (HARD)")
        
        role = helper.create_role("Waiter")
        employee = helper.create_employee("Test Employee", "test@example.com", ["Waiter"])
        
        shift_template = helper.create_shift_template(
            "Regular", time(9, 0), time(17, 0), [("Waiter", 1)]
        )
        
        week_start = date.today()
        schedule = helper.create_weekly_schedule(week_start, employee)
        
        # Create 6 shifts (exceeds 5)
        assignments = []
        for day in range(6):
            shift = helper.create_planned_shift(schedule, shift_template, week_start + timedelta(days=day))
            assignments.append({
                'user_id': employee.user_id,
                'planned_shift_id': shift.planned_shift_id,
                'role_id': role.role_id
            })
        
        helper.remove_other_constraints(SystemConstraintType.MAX_SHIFTS_PER_WEEK)
        helper.set_constraint(SystemConstraintType.MAX_SHIFTS_PER_WEEK, 5.0, True)
        constraint_service = ConstraintService(db)
        constraint_service.refresh_constraints()
        
        constraint_service = ConstraintService(db)
        schedule_id = int(schedule.weekly_schedule_id)  # type: ignore
        validation = constraint_service.validate_weekly_schedule(
            schedule_id,
            assignments
        )
        
        print(f"\nResults:")
        print(f"  Total shifts: 6")
        print(f"  Max shifts: 5")
        print(f"  Valid: {validation.is_valid()}")
        print(f"  Errors: {len(validation.errors)}")
        
        max_shifts_errors = [e for e in validation.errors if e.constraint_type == "MAX_SHIFTS_EXCEEDED"]
        
        if not validation.is_valid() and max_shifts_errors:
            print(f"\n  ✅ PASS: Correctly detected shifts exceeded (as expected)")
        else:
            print(f"\n  ❌ FAIL: Expected shifts violation")
        
        assert not validation.is_valid(), "Expected validation to fail"
        assert len(max_shifts_errors) > 0, "Expected max shifts errors"
        
    finally:
        helper.cleanup()
        db.close()


def test_min_shifts_per_week_pass():
    """Test MIN_SHIFTS_PER_WEEK: Should PASS - shift count meets minimum."""
    db = SessionLocal()
    helper = ToyCaseTestHelper(db)
    
    try:
        print("=" * 80)
        print("TOY CASE: MIN_SHIFTS_PER_WEEK - Should PASS")
        print("=" * 80)
        print("Scenario: Employee works 3 shifts (meets MIN_SHIFTS=2)")
        print("Expected: Should pass MIN_SHIFTS=2 (HARD)")
        
        role = helper.create_role("Waiter")
        employee = helper.create_employee("Test Employee", "test@example.com", ["Waiter"])
        
        shift_template = helper.create_shift_template(
            "Regular", time(9, 0), time(17, 0), [("Waiter", 1)]
        )
        
        week_start = date.today()
        schedule = helper.create_weekly_schedule(week_start, employee)
        
        # Create 3 shifts (meets 2)
        assignments = []
        for day in range(3):
            shift = helper.create_planned_shift(schedule, shift_template, week_start + timedelta(days=day))
            assignments.append({
                'user_id': employee.user_id,
                'planned_shift_id': shift.planned_shift_id,
                'role_id': role.role_id
            })
        
        helper.remove_other_constraints(SystemConstraintType.MIN_SHIFTS_PER_WEEK)
        helper.set_constraint(SystemConstraintType.MIN_SHIFTS_PER_WEEK, 2.0, True)
        constraint_service = ConstraintService(db)
        constraint_service.refresh_constraints()
        
        constraint_service = ConstraintService(db)
        schedule_id = int(schedule.weekly_schedule_id)  # type: ignore
        validation = constraint_service.validate_weekly_schedule(
            schedule_id,
            assignments
        )
        
        print(f"\nResults:")
        print(f"  Total shifts: 3")
        print(f"  Min shifts: 2")
        print(f"  Valid: {validation.is_valid()}")
        
        if validation.is_valid():
            print(f"\n  ✅ PASS: Meets minimum shifts (as expected)")
        else:
            print(f"\n  ❌ FAIL: Unexpected violations")
        
        assert validation.is_valid(), "Expected validation to pass"
        
    finally:
        helper.cleanup()
        db.close()


def test_min_shifts_per_week_fail():
    """Test MIN_SHIFTS_PER_WEEK: Should FAIL - shift count below minimum."""
    db = SessionLocal()
    helper = ToyCaseTestHelper(db)
    
    try:
        print("=" * 80)
        print("TOY CASE: MIN_SHIFTS_PER_WEEK - Should FAIL")
        print("=" * 80)
        print("Scenario: Employee works 1 shift (below MIN_SHIFTS=2)")
        print("Expected: Should fail MIN_SHIFTS=2 (HARD)")
        
        role = helper.create_role("Waiter")
        employee = helper.create_employee("Test Employee", "test@example.com", ["Waiter"])
        
        shift_template = helper.create_shift_template(
            "Regular", time(9, 0), time(17, 0), [("Waiter", 1)]
        )
        
        week_start = date.today()
        schedule = helper.create_weekly_schedule(week_start, employee)
        
        # Create only 1 shift (below 2)
        shift = helper.create_planned_shift(schedule, shift_template, week_start)
        assignments = [{
            'user_id': employee.user_id,
            'planned_shift_id': shift.planned_shift_id,
            'role_id': role.role_id
        }]
        
        helper.remove_other_constraints(SystemConstraintType.MIN_SHIFTS_PER_WEEK)
        helper.set_constraint(SystemConstraintType.MIN_SHIFTS_PER_WEEK, 2.0, True)
        constraint_service = ConstraintService(db)
        constraint_service.refresh_constraints()
        
        constraint_service = ConstraintService(db)
        schedule_id = int(schedule.weekly_schedule_id)  # type: ignore
        validation = constraint_service.validate_weekly_schedule(
            schedule_id,
            assignments
        )
        
        print(f"\nResults:")
        print(f"  Total shifts: 1")
        print(f"  Min shifts: 2")
        print(f"  Valid: {validation.is_valid()}")
        print(f"  Errors: {len(validation.errors)}")
        
        min_shifts_errors = [e for e in validation.errors if e.constraint_type == "MIN_SHIFTS_NOT_MET"]
        
        if not validation.is_valid() and min_shifts_errors:
            print(f"\n  ✅ PASS: Correctly detected insufficient shifts (as expected)")
        else:
            print(f"\n  ❌ FAIL: Expected min shifts violation")
        
        assert not validation.is_valid(), "Expected validation to fail"
        assert len(min_shifts_errors) > 0, "Expected min shifts errors"
        
    finally:
        helper.cleanup()
        db.close()


def test_max_consecutive_days_pass():
    """Test MAX_CONSECUTIVE_DAYS: Should PASS - no more than max consecutive days."""
    db = SessionLocal()
    helper = ToyCaseTestHelper(db)
    
    try:
        print("=" * 80)
        print("TOY CASE: MAX_CONSECUTIVE_DAYS - Should PASS")
        print("=" * 80)
        print("Scenario: Employee works 3 consecutive days (within MAX=5)")
        print("Expected: Should pass MAX_CONSECUTIVE_DAYS=5 (HARD)")
        
        role = helper.create_role("Waiter")
        employee = helper.create_employee("Test Employee", "test@example.com", ["Waiter"])
        
        shift_template = helper.create_shift_template(
            "Regular", time(9, 0), time(17, 0), [("Waiter", 1)]
        )
        
        week_start = date.today()
        schedule = helper.create_weekly_schedule(week_start, employee)
        
        # Create 3 consecutive days (within 5)
        assignments = []
        for day in range(3):
            shift = helper.create_planned_shift(schedule, shift_template, week_start + timedelta(days=day))
            assignments.append({
                'user_id': employee.user_id,
                'planned_shift_id': shift.planned_shift_id,
                'role_id': role.role_id
            })
        
        helper.remove_other_constraints(SystemConstraintType.MAX_CONSECUTIVE_DAYS)
        helper.set_constraint(SystemConstraintType.MAX_CONSECUTIVE_DAYS, 5.0, True)
        constraint_service = ConstraintService(db)
        constraint_service.refresh_constraints()
        
        constraint_service = ConstraintService(db)
        schedule_id = int(schedule.weekly_schedule_id)  # type: ignore
        validation = constraint_service.validate_weekly_schedule(
            schedule_id,
            assignments
        )
        
        print(f"\nResults:")
        print(f"  Consecutive days: 3")
        print(f"  Max consecutive: 5")
        print(f"  Valid: {validation.is_valid()}")
        
        if validation.is_valid():
            print(f"\n  ✅ PASS: Within consecutive days limit (as expected)")
        else:
            print(f"\n  ❌ FAIL: Unexpected violations")
        
        assert validation.is_valid(), "Expected validation to pass"
        
    finally:
        helper.cleanup()
        db.close()


def test_max_consecutive_days_fail():
    """Test MAX_CONSECUTIVE_DAYS: Should FAIL - exceeds max consecutive days."""
    db = SessionLocal()
    helper = ToyCaseTestHelper(db)
    
    try:
        print("=" * 80)
        print("TOY CASE: MAX_CONSECUTIVE_DAYS - Should FAIL")
        print("=" * 80)
        print("Scenario: Employee works 6 consecutive days (exceeds MAX=5)")
        print("Expected: Should fail MAX_CONSECUTIVE_DAYS=5 (HARD)")
        
        role = helper.create_role("Waiter")
        employee = helper.create_employee("Test Employee", "test@example.com", ["Waiter"])
        
        shift_template = helper.create_shift_template(
            "Regular", time(9, 0), time(17, 0), [("Waiter", 1)]
        )
        
        week_start = date.today()
        schedule = helper.create_weekly_schedule(week_start, employee)
        
        # Create 6 consecutive days (exceeds 5)
        assignments = []
        for day in range(6):
            shift = helper.create_planned_shift(schedule, shift_template, week_start + timedelta(days=day))
            assignments.append({
                'user_id': employee.user_id,
                'planned_shift_id': shift.planned_shift_id,
                'role_id': role.role_id
            })
        
        helper.remove_other_constraints(SystemConstraintType.MAX_CONSECUTIVE_DAYS)
        helper.set_constraint(SystemConstraintType.MAX_CONSECUTIVE_DAYS, 5.0, True)
        constraint_service = ConstraintService(db)
        constraint_service.refresh_constraints()
        
        constraint_service = ConstraintService(db)
        schedule_id = int(schedule.weekly_schedule_id)  # type: ignore
        validation = constraint_service.validate_weekly_schedule(
            schedule_id,
            assignments
        )
        
        print(f"\nResults:")
        print(f"  Consecutive days: 6")
        print(f"  Max consecutive: 5")
        print(f"  Valid: {validation.is_valid()}")
        print(f"  Errors: {len(validation.errors)}")
        
        consecutive_errors = [e for e in validation.errors if e.constraint_type == "MAX_CONSECUTIVE_DAYS_EXCEEDED"]
        
        if not validation.is_valid() and consecutive_errors:
            print(f"\n  ✅ PASS: Correctly detected consecutive days exceeded (as expected)")
        else:
            print(f"\n  ❌ FAIL: Expected consecutive days violation")
        
        assert not validation.is_valid(), "Expected validation to fail"
        assert len(consecutive_errors) > 0, "Expected consecutive days errors"
        
    finally:
        helper.cleanup()
        db.close()


def test_max_hours_per_week_soft_pass():
    """Test MAX_HOURS_PER_WEEK SOFT: Should PASS with warnings - exceeds limit but SOFT allows it."""
    db = SessionLocal()
    helper = ToyCaseTestHelper(db)
    
    try:
        print("=" * 80)
        print("TOY CASE: MAX_HOURS_PER_WEEK SOFT - Should PASS with Warnings")
        print("=" * 80)
        print("Scenario: Employee works 50 hours (exceeds MAX_HOURS=40)")
        print("Expected: Should pass because SOFT, but with warnings")
        
        role = helper.create_role("Waiter")
        employee = helper.create_employee("Test Employee", "test@example.com", ["Waiter"])
        
        shift_template = helper.create_shift_template(
            "Long", time(8, 0), time(18, 0), [("Waiter", 1)]  # 10 hours
        )
        
        week_start = date.today()
        schedule = helper.create_weekly_schedule(week_start, employee)
        
        # Create 5 shifts = 50 hours total (exceeds 40)
        assignments = []
        for day in range(5):
            shift = helper.create_planned_shift(schedule, shift_template, week_start + timedelta(days=day))
            assignments.append({
                'user_id': employee.user_id,
                'planned_shift_id': shift.planned_shift_id,
                'role_id': role.role_id
            })
        
        helper.remove_other_constraints(SystemConstraintType.MAX_HOURS_PER_WEEK)
        helper.set_constraint(SystemConstraintType.MAX_HOURS_PER_WEEK, 40.0, False)  # SOFT
        constraint_service = ConstraintService(db)
        constraint_service.refresh_constraints()
        
        validation = constraint_service.validate_weekly_schedule(
            int(schedule.weekly_schedule_id),  # type: ignore
            assignments
        )
        
        print(f"\nResults:")
        print(f"  Total hours: 50 (10 hours × 5 shifts)")
        print(f"  Max hours: 40 (SOFT)")
        print(f"  Valid: {validation.is_valid()}")
        print(f"  Errors: {len(validation.errors)}")
        print(f"  Warnings: {len(validation.warnings)}")
        
        max_hours_warnings = [w for w in validation.warnings if w.constraint_type == "MAX_HOURS_EXCEEDED"]
        
        if validation.is_valid() and max_hours_warnings:
            print(f"\n  ✅ PASS: Valid with warnings (as expected for SOFT constraint)")
            for warning in max_hours_warnings[:2]:
                print(f"    - {warning.message}")
        else:
            print(f"\n  ❌ FAIL: Expected valid with warnings")
            if not validation.is_valid():
                print(f"    Got errors instead of warnings")
            if not max_hours_warnings:
                print(f"    No MAX_HOURS warnings found")
        
        assert validation.is_valid(), "Expected validation to pass (SOFT constraint)"
        assert len(max_hours_warnings) > 0, "Expected warnings for SOFT constraint violation"
        
    finally:
        helper.cleanup()
        db.close()


def test_min_hours_per_week_soft_pass():
    """Test MIN_HOURS_PER_WEEK SOFT: Should PASS with warnings - below minimum but SOFT allows it."""
    db = SessionLocal()
    helper = ToyCaseTestHelper(db)
    
    try:
        print("=" * 80)
        print("TOY CASE: MIN_HOURS_PER_WEEK SOFT - Should PASS with Warnings")
        print("=" * 80)
        print("Scenario: Employee works 10 hours (below MIN_HOURS=20)")
        print("Expected: Should pass because SOFT, but with warnings")
        
        role = helper.create_role("Waiter")
        employee = helper.create_employee("Test Employee", "test@example.com", ["Waiter"])
        
        shift_template = helper.create_shift_template(
            "Short", time(9, 0), time(11, 0), [("Waiter", 1)]  # 2 hours
        )
        
        week_start = date.today()
        schedule = helper.create_weekly_schedule(week_start, employee)
        
        # Create 5 shifts = 10 hours total (below 20)
        assignments = []
        for day in range(5):
            shift = helper.create_planned_shift(schedule, shift_template, week_start + timedelta(days=day))
            assignments.append({
                'user_id': employee.user_id,
                'planned_shift_id': shift.planned_shift_id,
                'role_id': role.role_id
            })
        
        helper.remove_other_constraints(SystemConstraintType.MIN_HOURS_PER_WEEK)
        helper.set_constraint(SystemConstraintType.MIN_HOURS_PER_WEEK, 20.0, False)  # SOFT
        constraint_service = ConstraintService(db)
        constraint_service.refresh_constraints()
        
        validation = constraint_service.validate_weekly_schedule(
            int(schedule.weekly_schedule_id),  # type: ignore
            assignments
        )
        
        print(f"\nResults:")
        print(f"  Total hours: 10 (2 hours × 5 shifts)")
        print(f"  Min hours: 20 (SOFT)")
        print(f"  Valid: {validation.is_valid()}")
        print(f"  Warnings: {len(validation.warnings)}")
        
        min_hours_warnings = [w for w in validation.warnings if w.constraint_type == "MIN_HOURS_NOT_MET"]
        
        if validation.is_valid() and min_hours_warnings:
            print(f"\n  ✅ PASS: Valid with warnings (as expected for SOFT constraint)")
        else:
            print(f"\n  ❌ FAIL: Expected valid with warnings")
        
        assert validation.is_valid(), "Expected validation to pass (SOFT constraint)"
        assert len(min_hours_warnings) > 0, "Expected warnings for SOFT constraint violation"
        
    finally:
        helper.cleanup()
        db.close()


def test_max_shifts_per_week_soft_pass():
    """Test MAX_SHIFTS_PER_WEEK SOFT: Should PASS with warnings - exceeds limit but SOFT allows it."""
    db = SessionLocal()
    helper = ToyCaseTestHelper(db)
    
    try:
        print("=" * 80)
        print("TOY CASE: MAX_SHIFTS_PER_WEEK SOFT - Should PASS with Warnings")
        print("=" * 80)
        print("Scenario: Employee works 6 shifts (exceeds MAX_SHIFTS=5)")
        print("Expected: Should pass because SOFT, but with warnings")
        
        role = helper.create_role("Waiter")
        employee = helper.create_employee("Test Employee", "test@example.com", ["Waiter"])
        
        shift_template = helper.create_shift_template(
            "Regular", time(9, 0), time(17, 0), [("Waiter", 1)]
        )
        
        week_start = date.today()
        schedule = helper.create_weekly_schedule(week_start, employee)
        
        # Create 6 shifts (exceeds 5)
        assignments = []
        for day in range(6):
            shift = helper.create_planned_shift(schedule, shift_template, week_start + timedelta(days=day))
            assignments.append({
                'user_id': employee.user_id,
                'planned_shift_id': shift.planned_shift_id,
                'role_id': role.role_id
            })
        
        helper.remove_other_constraints(SystemConstraintType.MAX_SHIFTS_PER_WEEK)
        helper.set_constraint(SystemConstraintType.MAX_SHIFTS_PER_WEEK, 5.0, False)  # SOFT
        constraint_service = ConstraintService(db)
        constraint_service.refresh_constraints()
        
        validation = constraint_service.validate_weekly_schedule(
            int(schedule.weekly_schedule_id),  # type: ignore
            assignments
        )
        
        print(f"\nResults:")
        print(f"  Total shifts: 6")
        print(f"  Max shifts: 5 (SOFT)")
        print(f"  Valid: {validation.is_valid()}")
        print(f"  Warnings: {len(validation.warnings)}")
        
        max_shifts_warnings = [w for w in validation.warnings if w.constraint_type == "MAX_SHIFTS_EXCEEDED"]
        
        if validation.is_valid() and max_shifts_warnings:
            print(f"\n  ✅ PASS: Valid with warnings (as expected for SOFT constraint)")
        else:
            print(f"\n  ❌ FAIL: Expected valid with warnings")
        
        assert validation.is_valid(), "Expected validation to pass (SOFT constraint)"
        assert len(max_shifts_warnings) > 0, "Expected warnings for SOFT constraint violation"
        
    finally:
        helper.cleanup()
        db.close()


def test_min_shifts_per_week_soft_pass():
    """Test MIN_SHIFTS_PER_WEEK SOFT: Should PASS with warnings - below minimum but SOFT allows it."""
    db = SessionLocal()
    helper = ToyCaseTestHelper(db)
    
    try:
        print("=" * 80)
        print("TOY CASE: MIN_SHIFTS_PER_WEEK SOFT - Should PASS with Warnings")
        print("=" * 80)
        print("Scenario: Employee works 1 shift (below MIN_SHIFTS=2)")
        print("Expected: Should pass because SOFT, but with warnings")
        
        role = helper.create_role("Waiter")
        employee = helper.create_employee("Test Employee", "test@example.com", ["Waiter"])
        
        shift_template = helper.create_shift_template(
            "Regular", time(9, 0), time(17, 0), [("Waiter", 1)]
        )
        
        week_start = date.today()
        schedule = helper.create_weekly_schedule(week_start, employee)
        
        # Create only 1 shift (below 2)
        shift = helper.create_planned_shift(schedule, shift_template, week_start)
        assignments = [{
            'user_id': employee.user_id,
            'planned_shift_id': shift.planned_shift_id,
            'role_id': role.role_id
        }]
        
        helper.remove_other_constraints(SystemConstraintType.MIN_SHIFTS_PER_WEEK)
        helper.set_constraint(SystemConstraintType.MIN_SHIFTS_PER_WEEK, 2.0, False)  # SOFT
        constraint_service = ConstraintService(db)
        constraint_service.refresh_constraints()
        
        validation = constraint_service.validate_weekly_schedule(
            int(schedule.weekly_schedule_id),  # type: ignore
            assignments
        )
        
        print(f"\nResults:")
        print(f"  Total shifts: 1")
        print(f"  Min shifts: 2 (SOFT)")
        print(f"  Valid: {validation.is_valid()}")
        print(f"  Warnings: {len(validation.warnings)}")
        
        min_shifts_warnings = [w for w in validation.warnings if w.constraint_type == "MIN_SHIFTS_NOT_MET"]
        
        if validation.is_valid() and min_shifts_warnings:
            print(f"\n  ✅ PASS: Valid with warnings (as expected for SOFT constraint)")
        else:
            print(f"\n  ❌ FAIL: Expected valid with warnings")
        
        assert validation.is_valid(), "Expected validation to pass (SOFT constraint)"
        assert len(min_shifts_warnings) > 0, "Expected warnings for SOFT constraint violation"
        
    finally:
        helper.cleanup()
        db.close()


def test_min_rest_hours_soft_pass():
    """Test MIN_REST_HOURS SOFT: Should PASS with warnings - insufficient rest but SOFT allows it."""
    db = SessionLocal()
    helper = ToyCaseTestHelper(db)
    
    try:
        print("=" * 80)
        print("TOY CASE: MIN_REST_HOURS SOFT - Should PASS with Warnings")
        print("=" * 80)
        print("Scenario: Two consecutive shifts with only 2 hours rest")
        print("Expected: Should pass because SOFT, but with warnings")
        
        role = helper.create_role("Waiter")
        employee = helper.create_employee("Test Employee", "test@example.com", ["Waiter"])
        
        morning = helper.create_shift_template(
            "Morning", time(8, 0), time(14, 0), [("Waiter", 1)]
        )
        afternoon = helper.create_shift_template(
            "Afternoon", time(16, 0), time(22, 0), [("Waiter", 1)]  # Only 2 hours after morning
        )
        
        week_start = date.today()
        schedule = helper.create_weekly_schedule(week_start, employee)
        
        shift1 = helper.create_planned_shift(schedule, morning, week_start)
        shift2 = helper.create_planned_shift(schedule, afternoon, week_start)
        
        helper.remove_other_constraints(SystemConstraintType.MIN_REST_HOURS)
        helper.set_constraint(SystemConstraintType.MIN_REST_HOURS, 8.0, False)  # SOFT
        constraint_service = ConstraintService(db)
        constraint_service.refresh_constraints()
        
        assignments = [
            {'user_id': employee.user_id, 'planned_shift_id': shift1.planned_shift_id, 'role_id': role.role_id},
            {'user_id': employee.user_id, 'planned_shift_id': shift2.planned_shift_id, 'role_id': role.role_id}
        ]
        
        validation = constraint_service.validate_weekly_schedule(
            int(schedule.weekly_schedule_id),  # type: ignore
            assignments
        )
        
        print(f"\nResults:")
        print(f"  Rest hours: 2 (between shifts)")
        print(f"  Min rest: 8 (SOFT)")
        print(f"  Valid: {validation.is_valid()}")
        print(f"  Warnings: {len(validation.warnings)}")
        
        rest_warnings = [w for w in validation.warnings if w.constraint_type == "INSUFFICIENT_REST"]
        
        if validation.is_valid() and rest_warnings:
            print(f"\n  ✅ PASS: Valid with warnings (as expected for SOFT constraint)")
            for warning in rest_warnings[:2]:
                print(f"    - {warning.message}")
        else:
            print(f"\n  ❌ FAIL: Expected valid with warnings")
        
        assert validation.is_valid(), "Expected validation to pass (SOFT constraint)"
        assert len(rest_warnings) > 0, "Expected warnings for SOFT constraint violation"
        
    finally:
        helper.cleanup()
        db.close()


def test_max_consecutive_days_soft_pass():
    """Test MAX_CONSECUTIVE_DAYS SOFT: Should PASS with warnings - exceeds limit but SOFT allows it."""
    db = SessionLocal()
    helper = ToyCaseTestHelper(db)
    
    try:
        print("=" * 80)
        print("TOY CASE: MAX_CONSECUTIVE_DAYS SOFT - Should PASS with Warnings")
        print("=" * 80)
        print("Scenario: Employee works 6 consecutive days (exceeds MAX=5)")
        print("Expected: Should pass because SOFT, but with warnings")
        
        role = helper.create_role("Waiter")
        employee = helper.create_employee("Test Employee", "test@example.com", ["Waiter"])
        
        shift_template = helper.create_shift_template(
            "Regular", time(9, 0), time(17, 0), [("Waiter", 1)]
        )
        
        week_start = date.today()
        schedule = helper.create_weekly_schedule(week_start, employee)
        
        # Create 6 consecutive days (exceeds 5)
        assignments = []
        for day in range(6):
            shift = helper.create_planned_shift(schedule, shift_template, week_start + timedelta(days=day))
            assignments.append({
                'user_id': employee.user_id,
                'planned_shift_id': shift.planned_shift_id,
                'role_id': role.role_id
            })
        
        helper.remove_other_constraints(SystemConstraintType.MAX_CONSECUTIVE_DAYS)
        helper.set_constraint(SystemConstraintType.MAX_CONSECUTIVE_DAYS, 5.0, False)  # SOFT
        constraint_service = ConstraintService(db)
        constraint_service.refresh_constraints()
        
        validation = constraint_service.validate_weekly_schedule(
            int(schedule.weekly_schedule_id),  # type: ignore
            assignments
        )
        
        print(f"\nResults:")
        print(f"  Consecutive days: 6")
        print(f"  Max consecutive: 5 (SOFT)")
        print(f"  Valid: {validation.is_valid()}")
        print(f"  Warnings: {len(validation.warnings)}")
        
        consecutive_warnings = [w for w in validation.warnings if w.constraint_type == "MAX_CONSECUTIVE_DAYS_EXCEEDED"]
        
        if validation.is_valid() and consecutive_warnings:
            print(f"\n  ✅ PASS: Valid with warnings (as expected for SOFT constraint)")
        else:
            print(f"\n  ❌ FAIL: Expected valid with warnings")
        
        assert validation.is_valid(), "Expected validation to pass (SOFT constraint)"
        assert len(consecutive_warnings) > 0, "Expected warnings for SOFT constraint violation"
        
    finally:
        helper.cleanup()
        db.close()


def run_all_toy_tests():
    """Run all toy case tests."""
    print("\n" + "=" * 80)
    print("TOY CASES TEST SUITE - Simple Predictable Scenarios")
    print("=" * 80)
    
    tests = [
        # HARD constraint tests - PASS
        ("MIN_REST_HOURS - PASS (HARD)", test_min_rest_hours_pass),
        ("MAX_HOURS_PER_WEEK - PASS (HARD)", test_max_hours_per_week_pass),
        ("MIN_HOURS_PER_WEEK - PASS (HARD)", test_min_hours_per_week_pass),
        ("MAX_SHIFTS_PER_WEEK - PASS (HARD)", test_max_shifts_per_week_pass),
        ("MIN_SHIFTS_PER_WEEK - PASS (HARD)", test_min_shifts_per_week_pass),
        ("MAX_CONSECUTIVE_DAYS - PASS (HARD)", test_max_consecutive_days_pass),
        
        # HARD constraint tests - FAIL
        ("MIN_REST_HOURS - FAIL (HARD)", test_min_rest_hours_fail),
        ("MAX_HOURS_PER_WEEK - FAIL (HARD)", test_max_hours_per_week_fail),
        ("MIN_HOURS_PER_WEEK - FAIL (HARD)", test_min_hours_per_week_fail),
        ("MAX_SHIFTS_PER_WEEK - FAIL (HARD)", test_max_shifts_per_week_fail),
        ("MIN_SHIFTS_PER_WEEK - FAIL (HARD)", test_min_shifts_per_week_fail),
        ("MAX_CONSECUTIVE_DAYS - FAIL (HARD)", test_max_consecutive_days_fail),
        
        # SOFT constraint tests - PASS with warnings
        ("MAX_HOURS_PER_WEEK - PASS with Warnings (SOFT)", test_max_hours_per_week_soft_pass),
        ("MIN_HOURS_PER_WEEK - PASS with Warnings (SOFT)", test_min_hours_per_week_soft_pass),
        ("MAX_SHIFTS_PER_WEEK - PASS with Warnings (SOFT)", test_max_shifts_per_week_soft_pass),
        ("MIN_SHIFTS_PER_WEEK - PASS with Warnings (SOFT)", test_min_shifts_per_week_soft_pass),
        ("MIN_REST_HOURS - PASS with Warnings (SOFT)", test_min_rest_hours_soft_pass),
        ("MAX_CONSECUTIVE_DAYS - PASS with Warnings (SOFT)", test_max_consecutive_days_soft_pass),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n\n{'#' * 80}")
        print(f"# Running: {test_name}")
        print(f"{'#' * 80}\n")
        try:
            test_func()
            passed += 1
            print(f"\n✅ Test '{test_name}' PASSED")
        except AssertionError as e:
            failed += 1
            print(f"\n❌ Test '{test_name}' FAILED: {e}")
        except Exception as e:
            failed += 1
            print(f"\n❌ Test '{test_name}' ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("TOY CASES TEST SUITE SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("=" * 80)


if __name__ == "__main__":
    run_all_toy_tests()

