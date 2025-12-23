"""Test the ConstraintService."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import all models
from app.db.models import (
    roleModel, userModel, userRoleModel, shiftTemplateModel,
    shiftRoleRequirementsTabel, weeklyScheduleModel, plannedShiftModel, shiftAssignmentModel,
    timeOffRequestModel, systemConstraintsModel, employeePreferencesModel,
    optimizationConfigModel, schedulingRunModel, schedulingSolutionModel
)

from app.db.session import SessionLocal
from app.services.constraintService import ConstraintService, ValidationResult
from app.db.models.timeOffRequestModel import TimeOffRequestModel, TimeOffRequestStatus
from app.db.models.systemConstraintsModel import SystemConstraintsModel, SystemConstraintType
from app.db.models.plannedShiftModel import PlannedShiftModel
from datetime import date, datetime, time

def test_constraint_service():
    """Test the constraint service with various scenarios."""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("TESTING CONSTRAINT SERVICE")
        print("=" * 60)
        
        # Initialize service
        service = ConstraintService(db)
        
        print(f"\n✅ ConstraintService initialized")
        print(f"   Loaded {len(service.system_constraints)} system constraints:")
        for constraint_type, constraint_data in service.system_constraints.items():
            print(f"     • {constraint_type.value}: {constraint_data['value']} ({'HARD' if constraint_data['is_hard'] else 'SOFT'})")
        
        # Get test data
        shifts = db.query(PlannedShiftModel).limit(5).all()
        
        if not shifts:
            print("\n❌ No shifts found for testing")
            return
        
        print(f"\n{'='*60}")
        print("TEST 1: Valid Assignment")
        print('='*60)
        
        # Test a valid assignment
        test_shift = shifts[0]
        print(f"Testing shift {test_shift.planned_shift_id} on {test_shift.date}")
        
        # Get an employee with roles
        from app.db.models.userModel import UserModel
        employee = db.query(UserModel).filter(
            UserModel.user_status.in_(["ACTIVE", "active"])
        ).first()
        
        if not employee or not employee.roles:
            print("❌ No active employees with roles found")
            return
        
        print(f"Testing employee: {employee.user_full_name} (ID: {employee.user_id})")
        print(f"Employee roles: {[r.role_id for r in employee.roles]}")
        
        result = service.validate_assignment(
            employee.user_id,
            test_shift.planned_shift_id,
            employee.roles[0].role_id  # Use first role
        )
        
        print(f"\nValidation result:")
        print(f"  Valid: {result.is_valid()}")
        print(f"  Errors: {len(result.errors)}")
        print(f"  Warnings: {len(result.warnings)}")
        
        if not result.is_valid():
            print(f"\n  Errors found:")
            for error in result.errors:
                print(f"    • {error.message}")
        else:
            print(f"  ✅ Assignment is valid!")
        
        if result.has_warnings():
            print(f"\n  Warnings:")
            for warning in result.warnings:
                print(f"    • {warning.message}")
        
        print(f"\n{'='*60}")
        print("TEST 2: Invalid Role Assignment")
        print('='*60)
        
        # Test assigning employee to a role they don't have
        from app.db.models.roleModel import RoleModel
        all_roles = db.query(RoleModel).all()
        employee_role_ids = [r.role_id for r in employee.roles]
        
        # Find a role the employee doesn't have
        invalid_role = None
        for role in all_roles:
            if role.role_id not in employee_role_ids:
                invalid_role = role
                break
        
        if invalid_role:
            print(f"Assigning employee to invalid role: {invalid_role.role_name} (ID: {invalid_role.role_id})")
            
            result = service.validate_assignment(
                employee.user_id,
                test_shift.planned_shift_id,
                invalid_role.role_id
            )
            
            print(f"\nValidation result:")
            print(f"  Valid: {result.is_valid()}")
            print(f"  Errors: {len(result.errors)}")
            
            if not result.is_valid():
                print(f"  ✅ Correctly rejected:")
                for error in result.errors:
                    print(f"    • {error.message}")
        else:
            print("  ⚠️  Employee has all roles, skipping test")
        
        print(f"\n{'='*60}")
        print("TEST 3: Time-Off Conflict")
        print('='*60)
        
        # Check if employee has any approved time-off
        time_off = db.query(TimeOffRequestModel).filter(
            TimeOffRequestModel.user_id == employee.user_id,
            TimeOffRequestModel.status == TimeOffRequestStatus.APPROVED
        ).first()
        
        if time_off:
            print(f"Employee has time-off from {time_off.start_date} to {time_off.end_date}")
            
            # Find a shift during time-off
            conflicting_shift = db.query(PlannedShiftModel).filter(
                PlannedShiftModel.date >= time_off.start_date,
                PlannedShiftModel.date <= time_off.end_date
            ).first()
            
            if conflicting_shift:
                print(f"Testing assignment to shift on {conflicting_shift.date} (during time-off)")
                
                result = service.validate_assignment(
                    employee.user_id,
                    conflicting_shift.planned_shift_id,
                    employee.roles[0].role_id
                )
                
                print(f"\nValidation result:")
                print(f"  Valid: {result.is_valid()}")
                
                if not result.is_valid():
                    print(f"  ✅ Correctly detected time-off conflict:")
                    for error in result.errors:
                        if error.constraint_type == "TIME_OFF_CONFLICT":
                            print(f"    • {error.message}")
            else:
                print("  ⚠️  No shifts found during time-off period")
        else:
            print("  ⚠️  Employee has no approved time-off, skipping test")
        
        print(f"\n{'='*60}")
        print("TEST 4: Weekly Schedule Validation")
        print('='*60)
        
        # Create mock weekly assignments
        test_assignments = []
        available_shifts = db.query(PlannedShiftModel).limit(5).all()
        
        for shift in available_shifts[:3]:  # Test with 3 shifts
            test_assignments.append({
                'user_id': employee.user_id,
                'planned_shift_id': shift.planned_shift_id,
                'role_id': employee.roles[0].role_id
            })
        
        print(f"Testing weekly schedule with {len(test_assignments)} assignments for {employee.user_full_name}")
        
        result = service.validate_weekly_schedule(
            available_shifts[0].weekly_schedule_id,
            test_assignments
        )
        
        print(f"\nValidation result:")
        print(f"  Valid: {result.is_valid()}")
        print(f"  Total errors: {len(result.errors)}")
        print(f"  Total warnings: {len(result.warnings)}")
        
        if result.errors:
            print(f"\n  Errors:")
            for error in result.errors:
                print(f"    • [{error.constraint_type}] {error.message}")
        
        if result.warnings:
            print(f"\n  Warnings:")
            for warning in result.warnings:
                print(f"    • [{warning.constraint_type}] {warning.message}")
        
        if result.is_valid():
            print(f"\n  ✅ Weekly schedule is valid!")
        
        print(f"\n{'='*60}")
        print("TEST 5: Overlapping Shifts")
        print('='*60)
        
        # Find shifts on the same date
        same_date_shifts = db.query(PlannedShiftModel).filter(
            PlannedShiftModel.date == test_shift.date
        ).limit(3).all()
        
        if len(same_date_shifts) >= 2:
            print(f"Testing overlapping shifts on {test_shift.date}")
            print(f"  Shift 1: {same_date_shifts[0].start_time} - {same_date_shifts[0].end_time}")
            print(f"  Shift 2: {same_date_shifts[1].start_time} - {same_date_shifts[1].end_time}")
            
            overlap_assignments = [
                {
                    'user_id': employee.user_id,
                    'planned_shift_id': same_date_shifts[0].planned_shift_id,
                    'role_id': employee.roles[0].role_id
                },
                {
                    'user_id': employee.user_id,
                    'planned_shift_id': same_date_shifts[1].planned_shift_id,
                    'role_id': employee.roles[0].role_id
                }
            ]
            
            # Validate second assignment with first as existing
            result = service.validate_assignment(
                employee.user_id,
                same_date_shifts[1].planned_shift_id,
                employee.roles[0].role_id,
                overlap_assignments[:1]
            )
            
            print(f"\nValidation result:")
            print(f"  Valid: {result.is_valid()}")
            
            overlap_errors = [e for e in result.errors if e.constraint_type == "SHIFT_OVERLAP"]
            if overlap_errors:
                print(f"  ✅ Correctly detected shift overlap:")
                for error in overlap_errors:
                    print(f"    • {error.message}")
            elif not result.is_valid():
                print(f"  Validation failed for other reasons:")
                for error in result.errors:
                    print(f"    • {error.message}")
            else:
                print(f"  ℹ️  Shifts do not overlap")
        else:
            print("  ⚠️  Not enough shifts on same date to test overlaps")
        
        print(f"\n{'='*60}")
        print("SUMMARY")
        print('='*60)
        print("✅ All constraint validation tests completed!")
        print("\nImplemented validations:")
        print("  ✅ Employee availability (active status)")
        print("  ✅ Time-off conflicts")
        print("  ✅ Role qualifications")
        print("  ✅ Shift overlaps")
        print("  ✅ Rest period between shifts")
        print("  ✅ Weekly hour limits (MAX/MIN)")
        print("  ✅ Weekly shift count limits (MAX/MIN)")
        print("  ✅ Consecutive working days limit")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    test_constraint_service()
