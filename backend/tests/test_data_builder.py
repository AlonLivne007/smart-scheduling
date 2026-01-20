"""Test the OptimizationDataBuilder service."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import all models to ensure relationships are properly initialized
from app.db.models import (
    roleModel, userModel, userRoleModel, shiftTemplateModel,
    shiftRoleRequirementsTable, weeklyScheduleModel, plannedShiftModel, shiftAssignmentModel,
    timeOffRequestModel, systemConstraintsModel, employeePreferencesModel,
    optimizationConfigModel, schedulingRunModel, schedulingSolutionModel
)

from app.db.session import SessionLocal
from app.services.optimization_data_services import OptimizationDataBuilder, OptimizationData

def test_data_builder():
    """Test the data builder with a real weekly schedule."""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("TESTING OPTIMIZATION DATA BUILDER")
        print("=" * 60)
        
        # Get first available weekly schedule
        from app.db.models.weeklyScheduleModel import WeeklyScheduleModel
        weekly_schedule = db.query(WeeklyScheduleModel).first()
        
        if not weekly_schedule:
            print("❌ No weekly schedules found in database")
            return
        
        print(f"\n✅ Found weekly schedule ID: {weekly_schedule.weekly_schedule_id}")
        print(f"   Week starting: {weekly_schedule.week_start_date}")
        
        # Initialize data builder
        builder = OptimizationDataBuilder(db)
        
        print(f"\n{'='*60}")
        print("BUILDING OPTIMIZATION DATA...")
        print('='*60)
        
        # Build data
        data = builder.build(weekly_schedule.weekly_schedule_id)
        
        # Print results
        print(f"\n{'='*60}")
        print("EMPLOYEES")
        print('='*60)
        print(f"Total eligible employees: {len(data.employees)}")
        for emp in data.employees[:5]:  # Show first 5
            role_names = ', '.join([f"Role {rid}" for rid in emp['roles']])
            print(f"  • {emp['user_full_name']} (ID: {emp['user_id']})")
            print(f"    Email: {emp['user_email']}")
            print(f"    Roles: {role_names}")
        if len(data.employees) > 5:
            print(f"  ... and {len(data.employees) - 5} more employees")
        
        print(f"\n{'='*60}")
        print("SHIFTS")
        print('='*60)
        print(f"Total planned shifts: {len(data.shifts)}")
        for shift in data.shifts[:5]:  # Show first 5
            print(f"  • Shift ID: {shift['planned_shift_id']}")
            print(f"    Date: {shift['date']}, Time: {shift['start_time'].strftime('%H:%M') if hasattr(shift['start_time'], 'strftime') else shift['start_time']} - {shift['end_time'].strftime('%H:%M') if hasattr(shift['end_time'], 'strftime') else shift['end_time']}")
            print(f"    Location: {shift['location']}")
            print(f"    Required roles: {len(shift['required_roles'])} role(s)")
            for req in shift['required_roles']:
                print(f"      - Role {req['role_id']}: {req['required_count']} employee(s)")
        if len(data.shifts) > 5:
            print(f"  ... and {len(data.shifts) - 5} more shifts")
        
        print(f"\n{'='*60}")
        print("ROLES")
        print('='*60)
        print(f"Total roles: {len(data.roles)}")
        for role in data.roles:
            print(f"  • {role['role_name']} (ID: {role['role_id']})")
        
        print(f"\n{'='*60}")
        print("AVAILABILITY MATRIX")
        print('='*60)
        print(f"Matrix shape: {data.availability_matrix.shape} (employees × shifts)")
        total_cells = data.availability_matrix.size
        available_cells = data.availability_matrix.sum()
        unavailable_cells = total_cells - available_cells
        print(f"Available assignments: {available_cells}/{total_cells} ({100*available_cells/total_cells:.1f}%)")
        print(f"Unavailable assignments: {unavailable_cells}/{total_cells} ({100*unavailable_cells/total_cells:.1f}%)")
        
        # Show sample availability
        if len(data.employees) > 0 and len(data.shifts) > 0:
            print(f"\nSample availability (first 5 employees × first 5 shifts):")
            sample_employees = min(5, len(data.employees))
            sample_shifts = min(5, len(data.shifts))
            
            # Header
            print(f"\n{'Employee':<25}", end="")
            for i in range(sample_shifts):
                print(f"Shift {i+1:<3}", end="")
            print()
            print("-" * (25 + sample_shifts * 9))
            
            # Rows
            for i in range(sample_employees):
                emp_name = data.employees[i]['user_full_name'][:23]
                print(f"{emp_name:<25}", end="")
                for j in range(sample_shifts):
                    avail = "✓" if data.availability_matrix[i, j] == 1 else "✗"
                    print(f"{avail:<9}", end="")
                print()
        
        print(f"\n{'='*60}")
        print("PREFERENCE SCORES MATRIX")
        print('='*60)
        print(f"Matrix shape: {data.preference_scores.shape} (employees × shifts)")
        avg_score = data.preference_scores.mean()
        min_score = data.preference_scores.min()
        max_score = data.preference_scores.max()
        print(f"Average preference score: {avg_score:.3f}")
        print(f"Min score: {min_score:.3f}, Max score: {max_score:.3f}")
        
        # Count by preference level
        high_pref = (data.preference_scores >= 0.7).sum()
        medium_pref = ((data.preference_scores >= 0.4) & (data.preference_scores < 0.7)).sum()
        low_pref = (data.preference_scores < 0.4).sum()
        print(f"High preference (≥0.7): {high_pref} assignments")
        print(f"Medium preference (0.4-0.7): {medium_pref} assignments")
        print(f"Low preference (<0.4): {low_pref} assignments")
        
        # Show sample preferences
        if len(data.employees) > 0 and len(data.shifts) > 0:
            print(f"\nSample preference scores (first 5 employees × first 5 shifts):")
            sample_employees = min(5, len(data.employees))
            sample_shifts = min(5, len(data.shifts))
            
            # Header
            print(f"\n{'Employee':<25}", end="")
            for i in range(sample_shifts):
                print(f"Shift {i+1:<9}", end="")
            print()
            print("-" * (25 + sample_shifts * 9))
            
            # Rows
            for i in range(sample_employees):
                emp_name = data.employees[i]['user_full_name'][:23]
                print(f"{emp_name:<25}", end="")
                for j in range(sample_shifts):
                    score = data.preference_scores[i, j]
                    print(f"{score:<9.3f}", end="")
                print()
        
        print(f"\n{'='*60}")
        print("SHIFT OVERLAPS")
        print('='*60)
        total_overlaps = sum(len(overlaps) for overlaps in data.shift_overlaps.values())
        print(f"Total overlap pairs detected: {total_overlaps // 2}")  # Divide by 2 since each pair counted twice
        
        # Show shifts with overlaps
        shifts_with_overlaps = [sid for sid, overlaps in data.shift_overlaps.items() if overlaps]
        if shifts_with_overlaps:
            print(f"Shifts with overlaps: {len(shifts_with_overlaps)}/{len(data.shifts)}")
            for shift_id in shifts_with_overlaps[:3]:  # Show first 3
                overlapping_ids = data.shift_overlaps[shift_id]
                print(f"  • Shift {shift_id} overlaps with: {overlapping_ids}")
            if len(shifts_with_overlaps) > 3:
                print(f"  ... and {len(shifts_with_overlaps) - 3} more shifts with overlaps")
        else:
            print("No overlapping shifts detected")
        
        print(f"\n{'='*60}")
        print("ROLE REQUIREMENTS")
        print('='*60)
        print(f"Total shifts with role requirements: {len(data.role_requirements)}")
        shifts_with_reqs = [sid for sid, roles in data.role_requirements.items() if roles]
        print(f"Shifts requiring specific roles: {len(shifts_with_reqs)}/{len(data.shifts)}")
        
        print(f"\n{'='*60}")
        print("EMPLOYEE ROLES")
        print('='*60)
        print(f"Total employees: {len(data.employee_roles)}")
        avg_roles = sum(len(roles) for roles in data.employee_roles.values()) / len(data.employee_roles) if data.employee_roles else 0
        print(f"Average roles per employee: {avg_roles:.2f}")
        
        print(f"\n{'='*60}")
        print("DATA INTEGRITY CHECKS")
        print('='*60)
        
        # Check 1: Index mappings
        assert len(data.employee_index) == len(data.employees), "Employee index mismatch"
        assert len(data.shift_index) == len(data.shifts), "Shift index mismatch"
        print("✅ Index mappings are correct")
        
        # Check 2: Matrix dimensions
        assert data.availability_matrix.shape == (len(data.employees), len(data.shifts)), "Availability matrix shape mismatch"
        assert data.preference_scores.shape == (len(data.employees), len(data.shifts)), "Preference scores shape mismatch"
        print("✅ Matrix dimensions are correct")
        
        # Check 3: Matrix values in valid range
        assert ((data.availability_matrix == 0) | (data.availability_matrix == 1)).all(), "Availability matrix has invalid values"
        assert ((data.preference_scores >= 0.0) & (data.preference_scores <= 1.0)).all(), "Preference scores out of range"
        print("✅ Matrix values are in valid ranges")
        
        # Check 4: Role requirements match shifts
        assert all(sid in [s['planned_shift_id'] for s in data.shifts] for sid in data.role_requirements.keys()), "Role requirements contain invalid shift IDs"
        print("✅ Role requirements are valid")
        
        # Check 5: Employee roles match employees
        assert all(uid in [e['user_id'] for e in data.employees] for uid in data.employee_roles.keys()), "Employee roles contain invalid user IDs"
        print("✅ Employee roles are valid")
        
        print(f"\n{'='*60}")
        print("✅ ALL TESTS PASSED")
        print('='*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    test_data_builder()
