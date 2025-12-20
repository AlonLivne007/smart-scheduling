"""
Test function for Optimization Data Builder.

This module contains a test function that validates the Optimization Data Builder
by running it on seeded test data and printing the results.

Usage (from backend directory):
    python -m app.dev.test_optimization_data_builder
"""

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, Base
# Import all models to ensure SQLAlchemy can resolve relationships
from app.db.models import (
    roleModel, userModel, userRoleModel, shiftTemplateModel,
    shiftRoleRequirementsTabel, weeklyScheduleModel, plannedShiftModel, shiftAssignmentModel,
    timeOffRequestModel, systemConstraintsModel
)
from app.db.models.weeklyScheduleModel import WeeklyScheduleModel
from app.services.optimization_data_services.optimization_data_builder import OptimizationDataBuilder


def test_optimization_data_builder() -> None:
    """
    Test the Optimization Data Builder with seeded test data.
    
    This function:
    1. Finds the first weekly schedule in the database
    2. Runs the Optimization Data Builder on it
    3. Prints comprehensive results to verify correctness
    """
    db: Session = SessionLocal()
    try:
        # Find the first weekly schedule
        weekly_schedule = db.query(WeeklyScheduleModel).first()
        
        if not weekly_schedule:
            print("⚠️  No weekly schedule found. Please seed test data first.")
            return
        
        print(f"\n🧪 Testing Optimization Data Builder")
        print(f"   Weekly Schedule ID: {weekly_schedule.weekly_schedule_id}")
        print(f"   Week Start Date: {weekly_schedule.week_start_date}")
        print(f"   Created By: {weekly_schedule.created_by.user_full_name if weekly_schedule.created_by else 'N/A'}")
        
        # Initialize the data builder
        builder = OptimizationDataBuilder(db)
        
        # Prepare optimization data
        print("\n📊 Building optimization data...")
        data = builder.prepare_optimization_data(weekly_schedule.weekly_schedule_id)
        
        # Print results
        print("\n✅ Optimization Data Builder Results:")
        print(f"\n👥 Employees ({len(data.employees)}):")
        for emp in data.employees:
            print(f"   - {emp['name']} (ID: {emp['user_id']}) - Roles: {emp['role_ids']}")
        
        print(f"\n📅 Shifts ({len(data.shifts)}):")
        for shift in data.shifts[:10]:  # Show first 10 shifts
            print(f"   - Shift {shift['shift_id']}: {shift['date']} {shift['start_time'].strftime('%H:%M')}-{shift['end_time'].strftime('%H:%M')} ({shift['status']})")
        if len(data.shifts) > 10:
            print(f"   ... and {len(data.shifts) - 10} more shifts")
        
        print(f"\n🎭 Role Requirements ({len(data.role_requirements)} shifts):")
        for shift_id, roles in list(data.role_requirements.items())[:5]:  # Show first 5
            role_str = ", ".join([f"Role {r}: {c}" for r, c in roles.items()])
            print(f"   - Shift {shift_id}: {role_str}")
        if len(data.role_requirements) > 5:
            print(f"   ... and {len(data.role_requirements) - 5} more shifts with requirements")
        
        print(f"\n✅ Available Pairs ({len(data.available_pairs)} available pairs):")
        # Show sample of available pairs
        sample_pairs = list(data.available_pairs)[:10]
        for emp_id, shift_id in sample_pairs:
            emp_name = next((e['name'] for e in data.employees if e['user_id'] == emp_id), f"User {emp_id}")
            shift_info = next((s for s in data.shifts if s['shift_id'] == shift_id), None)
            if shift_info:
                print(f"   - {emp_name} available for Shift {shift_id} ({shift_info['date']})")
        if len(data.available_pairs) > 10:
            print(f"   ... and {len(data.available_pairs) - 10} more available pairs")
        
        print(f"\n🔄 Shift Overlaps ({len(data.shift_overlaps)} shifts with overlaps):")
        overlap_count = sum(len(overlaps) for overlaps in data.shift_overlaps.values()) // 2  # Divide by 2 since each overlap is counted twice
        print(f"   Total overlapping pairs: {overlap_count}")
        # Show first few overlaps
        shown = 0
        for shift_id, overlapping in data.shift_overlaps.items():
            if overlapping and shown < 5:
                print(f"   - Shift {shift_id} overlaps with: {list(overlapping)[:3]}")
                shown += 1
        
        print(f"\n🚫 Time-Off Conflicts ({len(data.time_off_conflicts)} employees):")
        for emp_id, conflicting_shifts in data.time_off_conflicts.items():
            emp_name = next((e['name'] for e in data.employees if e['user_id'] == emp_id), f"User {emp_id}")
            print(f"   - {emp_name} (ID: {emp_id}): {len(conflicting_shifts)} conflicting shifts")
        
        print(f"\n📋 Existing Assignments ({len(data.existing_assignments)}):")
        for emp_id, shift_id, role_id in list(data.existing_assignments)[:10]:
            emp_name = next((e['name'] for e in data.employees if e['user_id'] == emp_id), f"User {emp_id}")
            shift_info = next((s for s in data.shifts if s['shift_id'] == shift_id), None)
            if shift_info:
                print(f"   - {emp_name} assigned to Shift {shift_id} ({shift_info['date']}) in Role {role_id}")
        if len(data.existing_assignments) > 10:
            print(f"   ... and {len(data.existing_assignments) - 10} more assignments")
        
        # Summary statistics
        print(f"\n📈 Summary Statistics:")
        print(f"   - Total employees: {len(data.employees)}")
        print(f"   - Total shifts: {len(data.shifts)}")
        print(f"   - Shifts with role requirements: {len(data.role_requirements)}")
        print(f"   - Available assignment pairs: {len(data.available_pairs)}")
        print(f"   - Shifts with overlaps: {len([s for s in data.shift_overlaps.values() if s])}")
        print(f"   - Employees with time-off conflicts: {len(data.time_off_conflicts)}")
        print(f"   - Existing assignments: {len(data.existing_assignments)}")
        
        print("\n✅ Optimization Data Builder test completed successfully!")
        
    except Exception as exc:
        print(f"❌ Error testing Optimization Data Builder: {exc}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    """
    CLI entrypoint to run the test manually.
    
    Usage (from backend directory):
        python -m app.dev.test_optimization_data_builder
    """
    test_optimization_data_builder()

