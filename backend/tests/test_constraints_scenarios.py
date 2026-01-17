"""
Test different constraint scenarios for scheduling optimization.

This test suite validates how the system behaves with different constraint
configurations (HARD vs SOFT) and various constraint values.
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
from app.db.models.optimizationConfigModel import OptimizationConfigModel
from app.db.models.userModel import UserModel
from app.services.utils.datetime_utils import normalize_shift_datetimes
from datetime import datetime, timedelta, date, time


def create_planned_shifts_for_weekly_schedule(
    db,
    weekly_schedule_id: int,
    week_start_date: date = None,  # type: ignore
    templates_to_use: list = None  # type: ignore
) -> int:
    """
    Create planned shifts for a weekly schedule from shift templates.
    
    Args:
        db: Database session
        weekly_schedule_id: ID of the weekly schedule
        week_start_date: Start date of the week (if None, uses schedule's week_start_date)
        templates_to_use: List of template names to use (if None, uses all templates)
    
    Returns:
        Number of planned shifts created
    """
    # Get weekly schedule
    weekly_schedule = db.query(WeeklyScheduleModel).filter(
        WeeklyScheduleModel.weekly_schedule_id == weekly_schedule_id
    ).first()
    
    if not weekly_schedule:
        raise ValueError(f"Weekly schedule {weekly_schedule_id} not found")
    
    # Use schedule's week_start_date if not provided
    if week_start_date is None:
        week_start_date = weekly_schedule.week_start_date
    
    # Get all shift templates
    all_templates = db.query(ShiftTemplateModel).all()
    
    if not all_templates:
        raise ValueError("No shift templates found in database")
    
    # Filter templates if specific ones requested
    if templates_to_use:
        templates = {
            t.shift_template_name: t 
            for t in all_templates 
            if t.shift_template_name in templates_to_use
        }
        missing = set(templates_to_use) - set(templates.keys())
        if missing:
            raise ValueError(f"Templates not found: {missing}")
    else:
        templates = {t.shift_template_name: t for t in all_templates}
    
    # Check if shifts already exist for this schedule
    existing_count = db.query(PlannedShiftModel).filter(
        PlannedShiftModel.weekly_schedule_id == weekly_schedule_id
    ).count()
    
    if existing_count > 0:
        print(f"  ℹ️  Weekly schedule {weekly_schedule_id} already has {existing_count} planned shifts")
        return existing_count
    
    # Create planned shifts for each day of the week (7 days)
    created_count = 0
    for day_offset in range(7):
        shift_date = week_start_date + timedelta(days=day_offset)
        
        for template_name, template in templates.items():
            # Combine date with template times
            if template.start_time and template.end_time:
                start_dt = datetime.combine(shift_date, template.start_time)
                end_dt = datetime.combine(shift_date, template.end_time)
            else:
                # If template doesn't have times, use default
                start_dt = datetime.combine(shift_date, time(9, 0))
                end_dt = datetime.combine(shift_date, time(17, 0))
            
            planned_shift = PlannedShiftModel(
                weekly_schedule_id=weekly_schedule_id,
                shift_template_id=template.shift_template_id,
                date=shift_date,
                start_time=start_dt,
                end_time=end_dt,
                location=template.location or "Main Restaurant",
                status=PlannedShiftStatus.PLANNED,
            )
            db.add(planned_shift)
            created_count += 1
    
    db.commit()
    print(f"  ✅ Created {created_count} planned shifts for weekly schedule {weekly_schedule_id}")
    
    return created_count


def ensure_weekly_schedule_with_shifts(
    db,
    week_start_date: date = None,  # type: ignore
    templates_to_use: list = None  # type: ignore
) -> WeeklyScheduleModel:
    """
    Ensure a weekly schedule exists with planned shifts.
    Creates a new schedule if needed, or uses existing one.
    
    Args:
        db: Database session
        week_start_date: Start date of the week (defaults to next Monday)
        templates_to_use: List of template names to use (if None, uses all templates)
    
    Returns:
        WeeklyScheduleModel instance
    """
    # Default to next Monday if not provided
    if week_start_date is None:
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7  # If today is Monday, use next Monday
        week_start_date = today + timedelta(days=days_until_monday)
    
    # Check if schedule already exists for this week
    existing_schedule = db.query(WeeklyScheduleModel).filter(
        WeeklyScheduleModel.week_start_date == week_start_date
    ).first()
    
    if existing_schedule:
        # Check if it has planned shifts
        shift_count = db.query(PlannedShiftModel).filter(
            PlannedShiftModel.weekly_schedule_id == existing_schedule.weekly_schedule_id
        ).count()
        
        if shift_count == 0:
            print(f"  ℹ️  Found existing schedule {existing_schedule.weekly_schedule_id} without shifts, creating shifts...")
            create_planned_shifts_for_weekly_schedule(
                db,
                existing_schedule.weekly_schedule_id,
                week_start_date,
                templates_to_use
            )
        else:
            print(f"  ℹ️  Using existing schedule {existing_schedule.weekly_schedule_id} with {shift_count} shifts")
        
        return existing_schedule
    
    # Create new weekly schedule
    # Find a manager or any employee to be the creator
    managers = db.query(UserModel).filter(UserModel.is_manager == True).all()
    employees = db.query(UserModel).filter(UserModel.user_status.in_(["ACTIVE", "active"])).all()
    
    created_by = managers[0] if managers else (employees[0] if employees else None)
    
    if not created_by:
        raise RuntimeError("No employees found to act as schedule creator")
    
    weekly_schedule = WeeklyScheduleModel(
        week_start_date=week_start_date,
        status=ScheduleStatus.DRAFT,
        created_by_id=created_by.user_id,
    )
    db.add(weekly_schedule)
    db.commit()
    db.refresh(weekly_schedule)
    
    print(f"  ✅ Created new weekly schedule {weekly_schedule.weekly_schedule_id} for week starting {week_start_date}")
    
    # Create planned shifts
    schedule_id = int(weekly_schedule.weekly_schedule_id)  # type: ignore
    create_planned_shifts_for_weekly_schedule(
        db,
        schedule_id,
        week_start_date,
        templates_to_use
    )
    
    return weekly_schedule


class ConstraintTestScenario:
    """Helper class to manage constraint test scenarios."""
    
    def __init__(self, db, name: str):
        self.db = db
        self.name = name
        self.original_constraints = {}
        self.test_constraints = {}
    
    def setup_constraints(self, constraints: dict):
        """
        Setup test constraints.
        
        Args:
            constraints: Dict of {constraint_type: {'value': float, 'is_hard': bool}}
        """
        self.test_constraints = constraints
        
        # Save original constraints
        for constraint_type in constraints.keys():
            original = self.db.query(SystemConstraintsModel).filter(
                SystemConstraintsModel.constraint_type == constraint_type
            ).first()
            if original:
                self.original_constraints[constraint_type] = {
                    'value': original.constraint_value,
                    'is_hard': original.is_hard_constraint
                }
        
        # Update constraints
        for constraint_type, config in constraints.items():
            constraint = self.db.query(SystemConstraintsModel).filter(
                SystemConstraintsModel.constraint_type == constraint_type
            ).first()
            
            if constraint:
                constraint.constraint_value = config['value']
                constraint.is_hard_constraint = config['is_hard']
            else:
                # Create new constraint
                constraint = SystemConstraintsModel(
                    constraint_type=constraint_type,
                    constraint_value=config['value'],
                    is_hard_constraint=config['is_hard']
                )
                self.db.add(constraint)
        
        self.db.commit()
    
    def restore_constraints(self):
        """Restore original constraints."""
        for constraint_type, config in self.original_constraints.items():
            constraint = self.db.query(SystemConstraintsModel).filter(
                SystemConstraintsModel.constraint_type == constraint_type
            ).first()
            if constraint:
                constraint.constraint_value = config['value']
                constraint.is_hard_constraint = config['is_hard']
        
        self.db.commit()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore_constraints()


def test_max_hours_hard_vs_soft():
    """Test MAX_HOURS_PER_WEEK as HARD vs SOFT constraint."""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("TEST: MAX_HOURS_PER_WEEK - HARD vs SOFT")
        print("=" * 80)
        
        # Ensure we have a weekly schedule with planned shifts
        print("\n📅 Setting up weekly schedule with planned shifts...")
        weekly_schedule = ensure_weekly_schedule_with_shifts(db)
        
        service = SchedulingService(db)
        constraint_service = ConstraintService(db)
        
        # Test 1: MAX_HOURS as HARD constraint (strict)
        print(f"\n{'='*80}")
        print("SCENARIO 1: MAX_HOURS_PER_WEEK = 40 (HARD)")
        print('='*80)
        
        with ConstraintTestScenario(db, "max_hours_hard") as scenario:
            scenario.setup_constraints({
                SystemConstraintType.MAX_HOURS_PER_WEEK: {
                    'value': 40.0,
                    'is_hard': True
                }
            })
            
            print(f"Running optimization with MAX_HOURS=40 (HARD)...")
            schedule_id = int(weekly_schedule.weekly_schedule_id)  # type: ignore
            run1, solution1 = service.optimize_schedule(schedule_id)
            
            print(f"\nResults:")
            print(f"  Status: {run1.status.value}")
            print(f"  Solver Status: {run1.solver_status.value}")
            print(f"  Total Assignments: {run1.total_assignments}")
            print(f"  Objective Value: {run1.objective_value:.3f}")
            
            # Validate solution
            schedule_id = int(weekly_schedule.weekly_schedule_id)  # type: ignore
            validation1 = constraint_service.validate_weekly_schedule(
                schedule_id,
                solution1.assignments
            )
            
            print(f"\nValidation:")
            print(f"  Valid: {validation1.is_valid()}")
            print(f"  Errors: {len(validation1.errors)}")
            print(f"  Warnings: {len(validation1.warnings)}")
            
            # Check hours per employee
            from collections import defaultdict
            hours_per_employee = defaultdict(float)
            for assignment in solution1.assignments:
                shift = db.query(PlannedShiftModel).filter(
                    PlannedShiftModel.planned_shift_id == assignment['planned_shift_id']
                ).first()
                if shift:
                    start_dt, end_dt = normalize_shift_datetimes(shift)
                    hours = (end_dt - start_dt).total_seconds() / 3600.0
                    hours_per_employee[assignment['user_id']] += hours
            
            print(f"\nHours per employee (sample):")
            for user_id, hours in list(hours_per_employee.items())[:5]:
                from app.db.models.userModel import UserModel
                user = db.query(UserModel).filter(
                    UserModel.user_id == user_id
                ).first()
                name = user.user_full_name if user else f"User {user_id}"
                print(f"  {name}: {hours:.1f} hours")
                if hours > 40.0:
                    print(f"    ⚠️  EXCEEDS MAX_HOURS!")
        
        # Test 2: MAX_HOURS as SOFT constraint (flexible)
        print(f"\n{'='*80}")
        print("SCENARIO 2: MAX_HOURS_PER_WEEK = 40 (SOFT)")
        print('='*80)
        
        with ConstraintTestScenario(db, "max_hours_soft") as scenario:
            scenario.setup_constraints({
                SystemConstraintType.MAX_HOURS_PER_WEEK: {
                    'value': 40.0,
                    'is_hard': False
                }
            })
            
            print(f"Running optimization with MAX_HOURS=40 (SOFT)...")
            schedule_id = int(weekly_schedule.weekly_schedule_id)  # type: ignore
            run2, solution2 = service.optimize_schedule(schedule_id)
            
            print(f"\nResults:")
            print(f"  Status: {run2.status.value}")
            print(f"  Solver Status: {run2.solver_status.value}")
            print(f"  Total Assignments: {run2.total_assignments}")
            print(f"  Objective Value: {run2.objective_value:.3f}")
            
            # Validate solution
            schedule_id = int(weekly_schedule.weekly_schedule_id)  # type: ignore
            validation2 = constraint_service.validate_weekly_schedule(
                schedule_id,
                solution2.assignments
            )
            
            print(f"\nValidation:")
            print(f"  Valid: {validation2.is_valid()}")
            print(f"  Errors: {len(validation2.errors)}")
            print(f"  Warnings: {len(validation2.warnings)}")
            
            if validation2.warnings:
                max_hours_warnings = [w for w in validation2.warnings 
                                    if w.constraint_type == "MAX_HOURS_EXCEEDED"]
                print(f"  MAX_HOURS warnings: {len(max_hours_warnings)}")
        
        # Compare results
        print(f"\n{'='*80}")
        print("COMPARISON: HARD vs SOFT")
        print('='*80)
        print(f"HARD constraint:")
        print(f"  Status: {run1.status.value}")
        print(f"  Assignments: {run1.total_assignments}")
        print(f"  Objective: {run1.objective_value:.3f}")
        print(f"  Valid: {validation1.is_valid()}")
        
        print(f"\nSOFT constraint:")
        print(f"  Status: {run2.status.value}")
        print(f"  Assignments: {run2.total_assignments}")
        print(f"  Objective: {run2.objective_value:.3f}")
        print(f"  Valid: {validation2.is_valid()}")
        print(f"  Warnings: {len(validation2.warnings)}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_min_hours_hard_vs_soft():
    """Test MIN_HOURS_PER_WEEK as HARD vs SOFT constraint."""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("TEST: MIN_HOURS_PER_WEEK - HARD vs SOFT")
        print("=" * 80)
        
        # Ensure we have a weekly schedule with planned shifts
        print("\n📅 Setting up weekly schedule with planned shifts...")
        weekly_schedule = ensure_weekly_schedule_with_shifts(db)
        
        service = SchedulingService(db)
        constraint_service = ConstraintService(db)
        
        # Test 1: MIN_HOURS as HARD constraint
        print(f"\n{'='*80}")
        print("SCENARIO 1: MIN_HOURS_PER_WEEK = 20 (HARD)")
        print('='*80)
        
        with ConstraintTestScenario(db, "min_hours_hard") as scenario:
            scenario.setup_constraints({
                SystemConstraintType.MIN_HOURS_PER_WEEK: {
                    'value': 20.0,
                    'is_hard': True
                }
            })
            
            print(f"Running optimization with MIN_HOURS=20 (HARD)...")
            schedule_id = int(weekly_schedule.weekly_schedule_id)  # type: ignore
            run1, solution1 = service.optimize_schedule(schedule_id)
            
            print(f"\nResults:")
            print(f"  Status: {run1.status.value}")
            print(f"  Total Assignments: {run1.total_assignments}")
            
            schedule_id = int(weekly_schedule.weekly_schedule_id)  # type: ignore
            validation1 = constraint_service.validate_weekly_schedule(
                schedule_id,
                solution1.assignments
            )
            
            print(f"  Valid: {validation1.is_valid()}")
            print(f"  Errors: {len(validation1.errors)}")
        
        # Test 2: MIN_HOURS as SOFT constraint
        print(f"\n{'='*80}")
        print("SCENARIO 2: MIN_HOURS_PER_WEEK = 20 (SOFT)")
        print('='*80)
        
        with ConstraintTestScenario(db, "min_hours_soft") as scenario:
            scenario.setup_constraints({
                SystemConstraintType.MIN_HOURS_PER_WEEK: {
                    'value': 20.0,
                    'is_hard': False
                }
            })
            
            print(f"Running optimization with MIN_HOURS=20 (SOFT)...")
            schedule_id = int(weekly_schedule.weekly_schedule_id)  # type: ignore
            run2, solution2 = service.optimize_schedule(schedule_id)
            
            print(f"\nResults:")
            print(f"  Status: {run2.status.value}")
            print(f"  Total Assignments: {run2.total_assignments}")
            
            schedule_id = int(weekly_schedule.weekly_schedule_id)  # type: ignore
            validation2 = constraint_service.validate_weekly_schedule(
                schedule_id,
                solution2.assignments
            )
            
            print(f"  Valid: {validation2.is_valid()}")
            print(f"  Warnings: {len(validation2.warnings)}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_max_consecutive_days():
    """Test MAX_CONSECUTIVE_DAYS constraint with different values."""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("TEST: MAX_CONSECUTIVE_DAYS - Different Values")
        print("=" * 80)
        
        # Ensure we have a weekly schedule with planned shifts
        print("\n📅 Setting up weekly schedule with planned shifts...")
        weekly_schedule = ensure_weekly_schedule_with_shifts(db)
        
        service = SchedulingService(db)
        constraint_service = ConstraintService(db)
        
        test_values = [3, 5, 7]
        
        results = {}
        for max_days in test_values:
            print(f"\n{'='*80}")
            print(f"SCENARIO: MAX_CONSECUTIVE_DAYS = {max_days} (HARD)")
            print('='*80)
            
            with ConstraintTestScenario(db, f"max_consecutive_{max_days}") as scenario:
                scenario.setup_constraints({
                    SystemConstraintType.MAX_CONSECUTIVE_DAYS: {
                        'value': float(max_days),
                        'is_hard': True
                    }
                })
                
                print(f"Running optimization...")
                schedule_id = int(weekly_schedule.weekly_schedule_id)  # type: ignore
                run, solution = service.optimize_schedule(schedule_id)
                
                print(f"\nResults:")
                print(f"  Status: {run.status.value}")
                print(f"  Total Assignments: {run.total_assignments}")
                if run.objective_value is not None:
                    print(f"  Objective Value: {run.objective_value:.3f}")
                else:
                    print(f"  Objective Value: None (infeasible or failed)")
                
                schedule_id = int(weekly_schedule.weekly_schedule_id)  # type: ignore
                validation = constraint_service.validate_weekly_schedule(
                    schedule_id,
                    solution.assignments
                )
                
                print(f"  Valid: {validation.is_valid()}")
                print(f"  Errors: {len(validation.errors)}")
                
                results[max_days] = {
                    'status': run.status.value,
                    'assignments': run.total_assignments,
                    'objective': run.objective_value,
                    'valid': validation.is_valid(),
                    'errors': len(validation.errors)
                }
        
        # Compare results
        print(f"\n{'='*80}")
        print("COMPARISON: Different MAX_CONSECUTIVE_DAYS Values")
        print('='*80)
        for max_days, result in results.items():
            print(f"\nMAX_CONSECUTIVE_DAYS = {max_days}:")
            print(f"  Status: {result['status']}")
            print(f"  Assignments: {result['assignments']}")
            print(f"  Objective: {result['objective']:.3f}")
            print(f"  Valid: {result['valid']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_min_rest_hours():
    """Test MIN_REST_HOURS constraint with different values."""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("TEST: MIN_REST_HOURS - Different Values")
        print("=" * 80)
        
        # Ensure we have a weekly schedule with planned shifts
        print("\n📅 Setting up weekly schedule with planned shifts...")
        weekly_schedule = ensure_weekly_schedule_with_shifts(db)
        
        service = SchedulingService(db)
        constraint_service = ConstraintService(db)
        
        test_values = [8.0, 11.0, 12.0]  # 8, 11, 12 hours rest
        
        results = {}
        for rest_hours in test_values:
            print(f"\n{'='*80}")
            print(f"SCENARIO: MIN_REST_HOURS = {rest_hours} (HARD)")
            print('='*80)
            
            with ConstraintTestScenario(db, f"min_rest_{rest_hours}") as scenario:
                scenario.setup_constraints({
                    SystemConstraintType.MIN_REST_HOURS: {
                        'value': rest_hours,
                        'is_hard': True
                    }
                })
                
                print(f"Running optimization...")
                schedule_id = int(weekly_schedule.weekly_schedule_id)  # type: ignore
                run, solution = service.optimize_schedule(schedule_id)
                
                print(f"\nResults:")
                print(f"  Status: {run.status.value}")
                print(f"  Total Assignments: {run.total_assignments}")
                
                schedule_id = int(weekly_schedule.weekly_schedule_id)  # type: ignore
                validation = constraint_service.validate_weekly_schedule(
                    schedule_id,
                    solution.assignments
                )
                
                print(f"  Valid: {validation.is_valid()}")
                print(f"  Errors: {len(validation.errors)}")
                
                rest_errors = [e for e in validation.errors 
                             if e.constraint_type == "INSUFFICIENT_REST"]
                print(f"  Rest period errors: {len(rest_errors)}")
                
                results[rest_hours] = {
                    'status': run.status.value,
                    'assignments': run.total_assignments,
                    'valid': validation.is_valid(),
                    'rest_errors': len(rest_errors)
                }
        
        # Compare results
        print(f"\n{'='*80}")
        print("COMPARISON: Different MIN_REST_HOURS Values")
        print('='*80)
        for rest_hours, result in results.items():
            print(f"\nMIN_REST_HOURS = {rest_hours}:")
            print(f"  Status: {result['status']}")
            print(f"  Assignments: {result['assignments']}")
            print(f"  Valid: {result['valid']}")
            print(f"  Rest errors: {result['rest_errors']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_multiple_constraints_combination():
    """Test multiple constraints together."""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("TEST: Multiple Constraints Combination")
        print("=" * 80)
        
        # Ensure we have a weekly schedule with planned shifts
        print("\n📅 Setting up weekly schedule with planned shifts...")
        weekly_schedule = ensure_weekly_schedule_with_shifts(db)
        
        service = SchedulingService(db)
        constraint_service = ConstraintService(db)
        
        # Scenario 1: All HARD constraints
        print(f"\n{'='*80}")
        print("SCENARIO 1: All Constraints HARD")
        print('='*80)
        
        with ConstraintTestScenario(db, "all_hard") as scenario:
            scenario.setup_constraints({
                SystemConstraintType.MAX_HOURS_PER_WEEK: {'value': 40.0, 'is_hard': True},
                SystemConstraintType.MIN_HOURS_PER_WEEK: {'value': 20.0, 'is_hard': True},
                SystemConstraintType.MAX_SHIFTS_PER_WEEK: {'value': 5.0, 'is_hard': True},
                SystemConstraintType.MIN_SHIFTS_PER_WEEK: {'value': 2.0, 'is_hard': True},
                SystemConstraintType.MAX_CONSECUTIVE_DAYS: {'value': 5.0, 'is_hard': True},
                SystemConstraintType.MIN_REST_HOURS: {'value': 11.0, 'is_hard': True},
            })
            
            print(f"Running optimization with all HARD constraints...")
            schedule_id = int(weekly_schedule.weekly_schedule_id)  # type: ignore
            run1, solution1 = service.optimize_schedule(schedule_id)
            
            schedule_id_val = int(weekly_schedule.weekly_schedule_id)  # type: ignore
            validation1 = constraint_service.validate_weekly_schedule(
                schedule_id_val,
                solution1.assignments
            )
            
            print(f"\nResults:")
            print(f"  Status: {run1.status.value}")
            print(f"  Assignments: {run1.total_assignments}")
            print(f"  Valid: {validation1.is_valid()}")
            print(f"  Errors: {len(validation1.errors)}")
        
        # Scenario 2: All SOFT constraints
        print(f"\n{'='*80}")
        print("SCENARIO 2: All Constraints SOFT")
        print('='*80)
        
        with ConstraintTestScenario(db, "all_soft") as scenario:
            scenario.setup_constraints({
                SystemConstraintType.MAX_HOURS_PER_WEEK: {'value': 40.0, 'is_hard': False},
                SystemConstraintType.MIN_HOURS_PER_WEEK: {'value': 20.0, 'is_hard': False},
                SystemConstraintType.MAX_SHIFTS_PER_WEEK: {'value': 5.0, 'is_hard': False},
                SystemConstraintType.MIN_SHIFTS_PER_WEEK: {'value': 2.0, 'is_hard': False},
                SystemConstraintType.MAX_CONSECUTIVE_DAYS: {'value': 5.0, 'is_hard': False},
                SystemConstraintType.MIN_REST_HOURS: {'value': 11.0, 'is_hard': False},
            })
            
            print(f"Running optimization with all SOFT constraints...")
            schedule_id = int(weekly_schedule.weekly_schedule_id)  # type: ignore
            run2, solution2 = service.optimize_schedule(schedule_id)
            
            schedule_id = int(weekly_schedule.weekly_schedule_id)  # type: ignore
            validation2 = constraint_service.validate_weekly_schedule(
                schedule_id,
                solution2.assignments
            )
            
            print(f"\nResults:")
            print(f"  Status: {run2.status.value}")
            print(f"  Assignments: {run2.total_assignments}")
            print(f"  Valid: {validation2.is_valid()}")
            print(f"  Warnings: {len(validation2.warnings)}")
        
        # Compare
        print(f"\n{'='*80}")
        print("COMPARISON: All HARD vs All SOFT")
        print('='*80)
        print(f"HARD: Status={run1.status.value}, Assignments={run1.total_assignments}, "
              f"Valid={validation1.is_valid()}, Errors={len(validation1.errors)}")
        print(f"SOFT: Status={run2.status.value}, Assignments={run2.total_assignments}, "
              f"Valid={validation2.is_valid()}, Warnings={len(validation2.warnings)}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_infeasible_scenario():
    """Test infeasible constraint scenario."""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("TEST: Infeasible Constraint Scenario")
        print("=" * 80)
        
        # Ensure we have a weekly schedule with planned shifts
        print("\n📅 Setting up weekly schedule with planned shifts...")
        weekly_schedule = ensure_weekly_schedule_with_shifts(db)
        
        service = SchedulingService(db)
        
        # Set very restrictive constraints that might be infeasible
        print(f"\n{'='*80}")
        print("SCENARIO: Very Restrictive Constraints (Potentially Infeasible)")
        print('='*80)
        print("Setting:")
        print("  MAX_HOURS_PER_WEEK = 10 (HARD)")
        print("  MIN_HOURS_PER_WEEK = 30 (HARD)")
        print("  MAX_CONSECUTIVE_DAYS = 1 (HARD)")
        
        with ConstraintTestScenario(db, "infeasible") as scenario:
            scenario.setup_constraints({
                SystemConstraintType.MAX_HOURS_PER_WEEK: {'value': 10.0, 'is_hard': True},
                SystemConstraintType.MIN_HOURS_PER_WEEK: {'value': 30.0, 'is_hard': True},
                SystemConstraintType.MAX_CONSECUTIVE_DAYS: {'value': 1.0, 'is_hard': True},
            })
            
            print(f"\nRunning optimization...")
            schedule_id = int(weekly_schedule.weekly_schedule_id)  # type: ignore
            run, solution = service.optimize_schedule(schedule_id)
            
            print(f"\nResults:")
            print(f"  Status: {run.status.value}")
            print(f"  Solver Status: {run.solver_status.value}")
            print(f"  Total Assignments: {run.total_assignments}")
            
            if run.status.value == "FAILED" or run.solver_status.value == "INFEASIBLE":
                print(f"\n  ✅ Correctly detected infeasible scenario!")
                error_msg_str = str(run.error_message) if run.error_message is not None else ""
                if error_msg_str:
                    print(f"  Error message: {error_msg_str[:200]}")
            else:
                print(f"\n  ⚠️  Solution found (might be feasible or solver didn't detect infeasibility)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def run_all_tests():
    """Run all constraint scenario tests."""
    print("\n" + "=" * 80)
    print("CONSTRAINT SCENARIOS TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("MAX_HOURS HARD vs SOFT", test_max_hours_hard_vs_soft),
        ("MIN_HOURS HARD vs SOFT", test_min_hours_hard_vs_soft),
        ("MAX_CONSECUTIVE_DAYS Different Values", test_max_consecutive_days),
        ("MIN_REST_HOURS Different Values", test_min_rest_hours),
        ("Multiple Constraints Combination", test_multiple_constraints_combination),
        ("Infeasible Scenario", test_infeasible_scenario),
    ]
    
    for test_name, test_func in tests:
        print(f"\n\n{'#' * 80}")
        print(f"# Running: {test_name}")
        print(f"{'#' * 80}\n")
        try:
            test_func()
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    # Run specific test or all tests
    import sys
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "max_hours":
            test_max_hours_hard_vs_soft()
        elif test_name == "min_hours":
            test_min_hours_hard_vs_soft()
        elif test_name == "consecutive":
            test_max_consecutive_days()
        elif test_name == "rest":
            test_min_rest_hours()
        elif test_name == "multiple":
            test_multiple_constraints_combination()
        elif test_name == "infeasible":
            test_infeasible_scenario()
        else:
            print(f"Unknown test: {test_name}")
            print("Available tests: max_hours, min_hours, consecutive, rest, multiple, infeasible")
    else:
        run_all_tests()

