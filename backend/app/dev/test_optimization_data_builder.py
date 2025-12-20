"""
Smoke test for OptimizationDataBuilder (manual runner, not pytest).

Usage (from backend container):
    python -m app.dev.smoke_optimization_data_builder
    python -m app.dev.smoke_optimization_data_builder --schedule-id 1
"""

from __future__ import annotations

import argparse
import sys
from typing import Dict, Any

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models.weeklyScheduleModel import WeeklyScheduleModel
from app.services.optimization_data_services.optimization_data_builder import (
    OptimizationDataBuilder,
)
# Import all models to ensure SQLAlchemy can resolve relationships
from app.db.models import (
    roleModel, userModel, userRoleModel, shiftTemplateModel,
    shiftRoleRequirementsTabel, weeklyScheduleModel, plannedShiftModel, shiftAssignmentModel,
    timeOffRequestModel, systemConstraintsModel
)


REQUIRED_SYSTEM_CONSTRAINTS = [
    # keep in sync with what your MIP expects to always exist
    "MAX_HOURS_PER_WEEK",
    "MIN_HOURS_PER_WEEK",
    "MAX_CONSECUTIVE_DAYS",
    "MIN_REST_HOURS",
    "MAX_SHIFTS_PER_WEEK",
    "MIN_SHIFTS_PER_WEEK",
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test OptimizationDataBuilder")
    parser.add_argument(
        "--schedule-id",
        type=int,
        default=None,
        help="Weekly schedule id to test. If omitted, uses the latest by week_start_date.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=10,
        help="How many sample items to print in each section.",
    )
    return parser.parse_args()


def _pick_weekly_schedule(db: Session, schedule_id: int | None) -> WeeklyScheduleModel | None:
    if schedule_id is not None:
        return (
            db.query(WeeklyScheduleModel)
            .filter(WeeklyScheduleModel.weekly_schedule_id == schedule_id)
            .first()
        )

    # default: latest schedule by week_start_date
    return (
        db.query(WeeklyScheduleModel)
        .order_by(WeeklyScheduleModel.week_start_date.desc())
        .first()
    )


def _assert_basic_invariants(data: Any) -> None:
    # 1) Core objects exist
    assert data.employees is not None, "employees is None"
    assert data.shifts is not None, "shifts is None"
    assert len(data.employees) > 0, "No employees returned"
    assert len(data.shifts) > 0, "No shifts returned"

    # 2) Role requirements cover shifts (if your model expects every shift to have requirements)
    assert isinstance(data.role_requirements, dict), "role_requirements should be dict"
    missing_rr = [s["shift_id"] for s in data.shifts if s["shift_id"] not in data.role_requirements]
    assert not missing_rr, f"Missing role requirements for shifts: {missing_rr[:10]}"

    # 3) available_pairs consistent type
    assert isinstance(data.available_pairs, set), "available_pairs should be a set"
    assert all(isinstance(p, tuple) and len(p) == 2 for p in data.available_pairs), "bad tuple in available_pairs"

    # 4) eligible_roles subset of available_pairs
    assert isinstance(data.eligible_roles, dict), "eligible_roles should be dict"
    bad_keys = [k for k in data.eligible_roles.keys() if k not in data.available_pairs]
    assert not bad_keys, f"eligible_roles contains keys not in available_pairs. Example: {bad_keys[:5]}"

    # 5) shift_durations positive if present
    if hasattr(data, "shift_durations") and data.shift_durations:
        non_pos = [sid for sid, d in data.shift_durations.items() if d <= 0]
        assert not non_pos, f"Non-positive shift durations for shift_ids: {non_pos[:10]}"

    # 6) fixed_assignments consistent with existing_assignments
    if hasattr(data, "fixed_assignments") and data.fixed_assignments:
        for (emp_id, shift_id), role_id in data.fixed_assignments.items():
            assert (emp_id, shift_id, role_id) in data.existing_assignments, (
                f"fixed_assignments has ({emp_id},{shift_id})->{role_id} "
                f"but it's missing from existing_assignments"
            )

    # 7) existing assignments must not appear as available pairs (by your builder logic)
    existing_pairs = {(e, s) for (e, s, _) in data.existing_assignments}
    overlap = existing_pairs & data.available_pairs
    assert not overlap, f"Some existing (emp,shift) are also in available_pairs: {list(overlap)[:10]}"

    # 8) system constraints presence (if builder loads them)
    if hasattr(data, "system_constraints") and data.system_constraints is not None:
        # system_constraints keys might be Enum values, so compare by .value when possible
        keys = []
        for k in data.system_constraints.keys():
            keys.append(getattr(k, "value", str(k)))

        missing = [c for c in REQUIRED_SYSTEM_CONSTRAINTS if c not in keys]
        assert not missing, f"Missing required system constraints: {missing}"


def _build_fast_lookups(data: Any) -> tuple[Dict[int, str], Dict[int, Dict[str, Any]]]:
    emp_name_by_id = {e["user_id"]: e["name"] for e in data.employees}
    shift_by_id = {s["shift_id"]: s for s in data.shifts}
    return emp_name_by_id, shift_by_id


def main() -> int:
    args = _parse_args()
    db: Session = SessionLocal()

    try:
        weekly_schedule = _pick_weekly_schedule(db, args.schedule_id)
        if not weekly_schedule:
            print("⚠️  No weekly schedule found. Please seed test data first.")
            return 1

        print("\n🧪 Smoke Testing OptimizationDataBuilder")
        print(f"   Weekly Schedule ID: {weekly_schedule.weekly_schedule_id}")
        print(f"   Week Start Date: {weekly_schedule.week_start_date}")
        print(f"   Created By: {weekly_schedule.created_by.user_full_name if weekly_schedule.created_by else 'N/A'}")

        builder = OptimizationDataBuilder(db)

        print("\n📊 Building optimization data...")
        data = builder.prepare_optimization_data(weekly_schedule.weekly_schedule_id)

        # Assertions (fast fail)
        _assert_basic_invariants(data)

        emp_name_by_id, shift_by_id = _build_fast_lookups(data)

        # ---- Print summary ----
        print("\n✅ OptimizationDataBuilder Smoke Test Results")

        print(f"\n👥 Employees: {len(data.employees)}")
        for e in data.employees[: args.max_samples]:
            print(f"   - {e['name']} (ID: {e['user_id']}), roles={e['role_ids']}")
        if len(data.employees) > args.max_samples:
            print(f"   ... and {len(data.employees) - args.max_samples} more")

        print(f"\n📅 Shifts: {len(data.shifts)}")
        for s in data.shifts[: args.max_samples]:
            st = s["start_time"].strftime("%H:%M")
            et = s["end_time"].strftime("%H:%M")
            print(f"   - Shift {s['shift_id']}: {s['date']} {st}-{et} ({s['status']})")
        if len(data.shifts) > args.max_samples:
            print(f"   ... and {len(data.shifts) - args.max_samples} more")

        print(f"\n🎭 Role Requirements: {len(data.role_requirements)} shifts")
        for shift_id, roles in list(data.role_requirements.items())[: args.max_samples]:
            role_str = ", ".join([f"Role {r}: {c}" for r, c in roles.items()])
            print(f"   - Shift {shift_id}: {role_str}")
        if len(data.role_requirements) > args.max_samples:
            print(f"   ... and {len(data.role_requirements) - args.max_samples} more")

        print(f"\n✅ Available Pairs: {len(data.available_pairs)}")
        for (emp_id, shift_id) in list(data.available_pairs)[: args.max_samples]:
            emp_name = emp_name_by_id.get(emp_id, f"User {emp_id}")
            s = shift_by_id.get(shift_id)
            if s:
                print(f"   - {emp_name} available for Shift {shift_id} ({s['date']})")
        if len(data.available_pairs) > args.max_samples:
            print(f"   ... and {len(data.available_pairs) - args.max_samples} more")

        print(f"\n🧩 Eligible Roles entries: {len(data.eligible_roles)}")
        for (emp_id, shift_id), roles in list(data.eligible_roles.items())[: args.max_samples]:
            emp_name = emp_name_by_id.get(emp_id, f"User {emp_id}")
            print(f"   - ({emp_name}, Shift {shift_id}) -> roles={sorted(list(roles))}")
        if len(data.eligible_roles) > args.max_samples:
            print(f"   ... and {len(data.eligible_roles) - args.max_samples} more")

        if hasattr(data, "shift_durations") and data.shift_durations:
            print(f"\n⏱️ Shift Durations: {len(data.shift_durations)}")
            for shift_id, dur in list(data.shift_durations.items())[: args.max_samples]:
                print(f"   - Shift {shift_id}: {dur:.2f} hours")

        print(f"\n🔄 Shift Overlaps: {len(data.shift_overlaps)} shift-keys")
        overlap_pairs = sum(len(v) for v in data.shift_overlaps.values()) // 2
        print(f"   Total overlapping pairs: {overlap_pairs}")
        shown = 0
        for shift_id, overlaps in data.shift_overlaps.items():
            if overlaps and shown < args.max_samples:
                print(f"   - Shift {shift_id} overlaps with: {sorted(list(overlaps))[:5]}")
                shown += 1

        print(f"\n🚫 Time-Off Conflicts: {len(data.time_off_conflicts)} employees")
        for emp_id, conflicting in list(data.time_off_conflicts.items())[: args.max_samples]:
            emp_name = emp_name_by_id.get(emp_id, f"User {emp_id}")
            print(f"   - {emp_name} (ID: {emp_id}): {len(conflicting)} conflicting shifts")

        print(f"\n📋 Existing Assignments: {len(data.existing_assignments)}")
        for emp_id, shift_id, role_id in list(data.existing_assignments)[: args.max_samples]:
            emp_name = emp_name_by_id.get(emp_id, f"User {emp_id}")
            s = shift_by_id.get(shift_id)
            if s:
                print(f"   - {emp_name} assigned to Shift {shift_id} ({s['date']}) role={role_id}")
        if len(data.existing_assignments) > args.max_samples:
            print(f"   ... and {len(data.existing_assignments) - args.max_samples} more")

        if hasattr(data, "fixed_assignments") and data.fixed_assignments:
            print(f"\n📌 Fixed Assignments: {len(data.fixed_assignments)}")
            for (emp_id, shift_id), role_id in list(data.fixed_assignments.items())[: args.max_samples]:
                emp_name = emp_name_by_id.get(emp_id, f"User {emp_id}")
                print(f"   - ({emp_name}, Shift {shift_id}) fixed role={role_id}")

        if hasattr(data, "system_constraints") and data.system_constraints:
            print(f"\n⚙️ System Constraints: {len(data.system_constraints)}")
            for k, (val, is_hard) in data.system_constraints.items():
                k_name = getattr(k, "value", str(k))
                print(f"   - {k_name}: value={val}, hard={is_hard}")

        print("\n✅ Smoke test completed successfully!")
        return 0

    except AssertionError as e:
        print(f"\n❌ Smoke test FAILED (assertion): {e}")
        return 1
    except Exception as exc:
        print(f"\n❌ Smoke test FAILED (exception): {exc}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
