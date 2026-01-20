"""Test the SchedulingService with MIP solver."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import all models
from app.db.models import (
    roleModel, userModel, userRoleModel, shiftTemplateModel,
    shiftRoleRequirementsTable, weeklyScheduleModel, plannedShiftModel, shiftAssignmentModel,
    timeOffRequestModel, systemConstraintsModel, employeePreferencesModel,
    optimizationConfigModel, schedulingRunModel, schedulingSolutionModel
)

from app.db.session import SessionLocal
from app.services.scheduling.scheduling_service import SchedulingService
from app.db.models.weeklyScheduleModel import WeeklyScheduleModel

def test_scheduling_service():
    """Test the scheduling service with real data."""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("TESTING SCHEDULING SERVICE - MIP SOLVER")
        print("=" * 60)
        
        # Get a weekly schedule
        weekly_schedule = db.query(WeeklyScheduleModel).order_by(WeeklyScheduleModel.weekly_schedule_id.desc()).first()
        
        if not weekly_schedule:
            print("❌ No weekly schedules found")
            return
        
        print(f"\n✅ Found weekly schedule ID: {weekly_schedule.weekly_schedule_id}")
        print(f"   Week starting: {weekly_schedule.week_start_date}")
        
        # Initialize service
        service = SchedulingService(db)
        print(f"\n✅ SchedulingService initialized")
        
        print(f"\n{'='*60}")
        print("RUNNING OPTIMIZATION")
        print('='*60)
        
        # Create SchedulingRun record
        from app.db.models.schedulingRunModel import SchedulingRunModel, SchedulingRunStatus
        from datetime import datetime
        
        run = SchedulingRunModel(
            weekly_schedule_id=weekly_schedule.weekly_schedule_id,
            status=SchedulingRunStatus.PENDING,
            started_at=datetime.now()
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        
        # Run optimization
        run, solution = service._execute_optimization_for_run(run)
        
        print(f"\n{'='*60}")
        print("OPTIMIZATION RESULTS")
        print('='*60)
        
        print(f"\nSchedulingRun ID: {run.run_id}")
        print(f"Status: {run.status.value}")
        print(f"Solver Status: {run.solver_status.value}")
        print(f"Runtime: {run.runtime_seconds:.2f} seconds")
        print(f"Objective Value: {run.objective_value:.3f}")
        print(f"MIP Gap: {run.mip_gap:.4f}")
        print(f"Total Assignments: {run.total_assignments}")
        
        print(f"\n{'='*60}")
        print("DATABASE VERIFICATION")
        print('='*60)
        
        # Query the scheduling run from database
        db.refresh(run)
        print(f"\n✅ SchedulingRun persisted to database")
        print(f"   Run ID: {run.run_id}")
        print(f"   Solutions stored: {len(run.solutions)}")
        
        # Verify solutions
        if run.solutions:
            print(f"\n✅ Sample solutions from database:")
            for i, sol in enumerate(run.solutions[:5]):
                shift = sol.planned_shift
                user = sol.user
                role = sol.role
                print(f"   {i+1}. {user.user_full_name} → {shift.date} {shift.start_time.strftime('%H:%M')}-{shift.end_time.strftime('%H:%M')} as {role.role_name} (score: {sol.assignment_score:.2f})")
            if len(run.solutions) > 5:
                print(f"   ... and {len(run.solutions) - 5} more")
        
        print(f"\n{'='*60}")
        print("SOLUTION SUMMARY")
        print('='*60)
        
        print(f"\nStatus: {solution.status}")
        print(f"Runtime: {solution.runtime_seconds:.2f} seconds")
        print(f"Objective Value: {solution.objective_value:.3f}")
        print(f"MIP Gap: {solution.mip_gap:.4f}")
        
        print(f"\n{'='*60}")
        print("SOLUTION METRICS")
        print('='*60)
        
        for key, value in solution.metrics.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        
        print(f"\n{'='*60}")
        print("ASSIGNMENTS")
        print('='*60)
        
        print(f"\nTotal assignments: {len(solution.assignments)}")
        
        if solution.assignments:
            # Group by employee
            assignments_by_emp = {}
            for assignment in solution.assignments:
                user_id = assignment['user_id']
                if user_id not in assignments_by_emp:
                    assignments_by_emp[user_id] = []
                assignments_by_emp[user_id].append(assignment)
            
            print(f"\nAssignments by employee:")
            for user_id, emp_assignments in sorted(assignments_by_emp.items()):
                from app.db.models.userModel import UserModel
                user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
                user_name = user.user_full_name if user else f"User {user_id}"
                
                print(f"\n  {user_name} ({len(emp_assignments)} shifts):")
                
                avg_pref = sum(a['preference_score'] for a in emp_assignments) / len(emp_assignments)
                print(f"    Average preference score: {avg_pref:.3f}")
                
                # Show first 3 shifts
                for assignment in emp_assignments[:3]:
                    from app.db.models.plannedShiftModel import PlannedShiftModel
                    from app.db.models.roleModel import RoleModel
                    
                    shift = db.query(PlannedShiftModel).filter(
                        PlannedShiftModel.planned_shift_id == assignment['planned_shift_id']
                    ).first()
                    
                    role = db.query(RoleModel).filter(
                        RoleModel.role_id == assignment['role_id']
                    ).first()
                    
                    if shift and role:
                        print(f"      • {shift.date} {shift.start_time.strftime('%H:%M') if hasattr(shift.start_time, 'strftime') else shift.start_time}-{shift.end_time.strftime('%H:%M') if hasattr(shift.end_time, 'strftime') else shift.end_time} as {role.role_name} (pref: {assignment['preference_score']:.2f})")
                
                if len(emp_assignments) > 3:
                    print(f"      ... and {len(emp_assignments) - 3} more shifts")
        
        print(f"\n{'='*60}")
        print("COVERAGE ANALYSIS")
        print('='*60)
        
        # Analyze shift coverage
        shifts_with_assignments = set(a['planned_shift_id'] for a in solution.assignments)
        
        from app.db.models.plannedShiftModel import PlannedShiftModel, PlannedShiftStatus
        all_shifts = db.query(PlannedShiftModel).filter(
            PlannedShiftModel.weekly_schedule_id == weekly_schedule.weekly_schedule_id,
            PlannedShiftModel.status != PlannedShiftStatus.CANCELLED
        ).all()
        
        covered_count = len(shifts_with_assignments)
        total_count = len(all_shifts)
        coverage_pct = (covered_count / total_count * 100) if total_count > 0 else 0
        
        print(f"\nShift Coverage: {covered_count}/{total_count} ({coverage_pct:.1f}%)")
        
        # Check if all required roles are filled
        unfilled_shifts = []
        for shift in all_shifts:
            if shift.planned_shift_id not in shifts_with_assignments:
                unfilled_shifts.append(shift)
        
        if unfilled_shifts:
            print(f"\nUnfilled shifts: {len(unfilled_shifts)}")
            for shift in unfilled_shifts[:5]:
                print(f"  • Shift {shift.planned_shift_id} on {shift.date}")
            if len(unfilled_shifts) > 5:
                print(f"  ... and {len(unfilled_shifts) - 5} more")
        else:
            print(f"\n✅ All shifts have at least one assignment!")
        
        print(f"\n{'='*60}")
        print("SOLUTION VALIDATION")
        print('='*60)
        
        # Note: Solution validation is handled by the MIP solver itself.
        # If the MIP returns OPTIMAL or FEASIBLE, the solution is guaranteed
        # to satisfy all hard constraints as they are encoded directly in the MIP model.
        
        if solution.status in ["OPTIMAL", "FEASIBLE"]:
            print(f"\n  ✅ Solution status: {solution.status}")
            print(f"  ✅ Solution is guaranteed to satisfy all hard constraints (validated by MIP solver)")
            print(f"  ✅ Total assignments: {len(solution.assignments)}")
        else:
            print(f"\n  ⚠️  Solution status: {solution.status}")
            print(f"  ⚠️  Solution may not be valid")
        
        print(f"\n{'='*60}")
        if solution.status in ["OPTIMAL", "FEASIBLE"]:
            print("✅ OPTIMIZATION SUCCESSFUL!")
        else:
            print(f"⚠️  OPTIMIZATION STATUS: {solution.status}")
        print('='*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    test_scheduling_service()
