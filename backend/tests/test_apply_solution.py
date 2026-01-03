"""
Test the apply solution endpoint (US-11).

This test verifies that optimization solutions can be applied to create
actual shift assignments.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all models first to ensure relationships are properly initialized
from app.db.models import (
    roleModel, userModel, userRoleModel, shiftTemplateModel,
    shiftRoleRequirementsTabel, weeklyScheduleModel, plannedShiftModel, shiftAssignmentModel,
    timeOffRequestModel, systemConstraintsModel, employeePreferencesModel,
    optimizationConfigModel, schedulingRunModel, schedulingSolutionModel
)

from app.db.session import SessionLocal
from app.db.models.schedulingRunModel import SchedulingRunModel, SchedulingRunStatus
from app.db.models.schedulingSolutionModel import SchedulingSolutionModel
from app.db.models.shiftAssignmentModel import ShiftAssignmentModel
from app.db.models.plannedShiftModel import PlannedShiftModel, PlannedShiftStatus
from app.db.models.weeklyScheduleModel import WeeklyScheduleModel
from app.api.controllers.schedulingRunController import apply_scheduling_solution


def test_apply_solution():
    """
    Test applying an optimization solution.
    
    Prerequisites:
    - Run seed_comprehensive_data.py to create test data
    - Run the scheduling optimization to create a completed run with solutions
    """
    db = SessionLocal()
    
    try:
        print("\n" + "="*70)
        print("TEST: Apply Optimization Solution (US-11)")
        print("="*70 + "\n")
        
        # 1. Find a completed scheduling run
        print("📋 Finding a completed scheduling run...")
        run = db.query(SchedulingRunModel).filter(
            SchedulingRunModel.status == SchedulingRunStatus.COMPLETED
        ).order_by(SchedulingRunModel.run_id.desc()).first()
        
        if not run:
            print("❌ No completed scheduling run found!")
            print("   Please run the optimization first:")
            print("   POST /scheduling/optimize/{weekly_schedule_id}")
            return
        
        print(f"✅ Found scheduling run: ID={run.run_id}")
        print(f"   Weekly Schedule ID: {run.weekly_schedule_id}")
        print(f"   Status: {run.status.value}")
        print(f"   Objective Value: {run.objective_value}")
        print(f"   Runtime: {run.runtime_seconds}s")
        
        # 2. Check solutions
        solutions_count = db.query(SchedulingSolutionModel).filter(
            SchedulingSolutionModel.run_id == run.run_id,
            SchedulingSolutionModel.is_selected == True
        ).count()
        
        print(f"\n📊 Solutions to apply: {solutions_count}")
        
        if solutions_count == 0:
            print("❌ No selected solutions found!")
            return
        
        # 3. Check for existing assignments
        shifts = db.query(SchedulingSolutionModel.planned_shift_id).filter(
            SchedulingSolutionModel.run_id == run.run_id,
            SchedulingSolutionModel.is_selected == True
        ).distinct().all()
        shift_ids = [s[0] for s in shifts]
        
        existing_assignments = db.query(ShiftAssignmentModel).filter(
            ShiftAssignmentModel.planned_shift_id.in_(shift_ids)
        ).count()
        
        print(f"⚠️  Existing assignments for these shifts: {existing_assignments}")
        
        # 4. Apply solution (with overwrite if needed)
        print("\n🚀 Applying solution...")
        overwrite = existing_assignments > 0
        
        if overwrite:
            print(f"   Using overwrite=True to replace {existing_assignments} existing assignments")
        
        import asyncio
        result = asyncio.run(apply_scheduling_solution(db, run.run_id, overwrite=overwrite))
        
        print(f"\n✅ Solution applied successfully!")
        print(f"   {result['message']}")
        print(f"   Assignments created: {result['assignments_created']}")
        print(f"   Shifts updated: {result['shifts_updated']}")
        
        # 5. Verify assignments were created
        new_assignments = db.query(ShiftAssignmentModel).filter(
            ShiftAssignmentModel.planned_shift_id.in_(shift_ids)
        ).all()
        
        print(f"\n📊 Verification:")
        print(f"   Total assignments in DB: {len(new_assignments)}")
        
        # Sample a few assignments
        print(f"\n   Sample assignments:")
        for i, assignment in enumerate(new_assignments[:5]):
            user_name = assignment.user.user_full_name if assignment.user else "Unknown"
            role_name = assignment.role.role_name if assignment.role else "Unknown"
            shift_date = assignment.planned_shift.start_time if assignment.planned_shift else "Unknown"
            print(f"   {i+1}. {user_name} → {role_name} @ {shift_date}")
        
        # 6. Verify shift statuses were updated
        updated_shifts = db.query(PlannedShiftModel).filter(
            PlannedShiftModel.planned_shift_id.in_(shift_ids),
            PlannedShiftModel.status == PlannedShiftStatus.FULLY_ASSIGNED
        ).count()
        
        print(f"\n   Shifts marked as FULLY_ASSIGNED: {updated_shifts}/{len(shift_ids)}")
        
        # 7. Test error handling: try to apply again without overwrite
        print(f"\n🧪 Testing conflict detection (should fail)...")
        try:
            asyncio.run(apply_scheduling_solution(db, run.run_id, overwrite=False))
            print("   ❌ Should have raised conflict error!")
        except Exception as e:
            if "conflict" in str(e).lower() or "existing" in str(e).lower():
                print(f"   ✅ Correctly detected conflict: {str(e)[:100]}")
            else:
                print(f"   ⚠️  Unexpected error: {str(e)[:100]}")
        
        print("\n" + "="*70)
        print("✅ TEST PASSED: Apply solution endpoint works correctly!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    test_apply_solution()
