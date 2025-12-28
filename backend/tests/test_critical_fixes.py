"""
Simple test functions for critical fixes:
- Overnight shift handling
- Role-aware MIP model
- Cross-midnight overlap detection
"""

from datetime import datetime, date, time, timedelta
from app.services.optimization_data_services.optimization_precompute import (
    normalize_shift_datetimes,
    _shifts_overlap,
    build_shift_durations
)
from app.services.optimization_data_services.optimization_data import OptimizationData
from app.services.schedulingService import SchedulingService
import numpy as np

class MockDB:
    """Minimal mock database session for testing."""
    def query(self, model):
        return MockQuery()

class MockQuery:
    """Minimal mock query that returns empty results."""
    def all(self):
        return []
    def filter(self, *args, **kwargs):
        return self
    def first(self):
        return None

def test_mip_requires_distinct_employees_for_two_roles():
    # Build minimal OptimizationData directly (don't use builder which requires DB)
    data = OptimizationData()
    data.employees = [
        {"user_id": 1, "roles": [10, 20]},   # multi-role
        {"user_id": 2, "roles": [10]},       # role 10 only
        {"user_id": 3, "roles": [20]},       # role 20 only
    ]
    data.shifts = [{
        "planned_shift_id": 100,
        "date": date(2024, 1, 1),
        "start_time": time(9, 0),
        "end_time": time(17, 0),
        "required_roles": [{"role_id": 10, "required_count": 1},
                           {"role_id": 20, "required_count": 1}],
    }]
    data.employee_index = {e["user_id"]: i for i, e in enumerate(data.employees)}
    data.shift_index = {100: 0}
    data.availability_matrix = np.ones((3, 1), dtype=int)
    data.preference_scores = np.ones((3, 1), dtype=float) * 0.5
    data.shift_overlaps = {100: []}
    data.employee_roles = {1: [10, 20], 2: [10], 3: [20]}  # Set up employee_roles mapping

    # Minimal config stub (whatever your OptimizationConfigModel expects)
    class Cfg:
        max_runtime_seconds = 5
        mip_gap = 0.0
        weight_preferences = 1.0
        weight_coverage = 1.0
        weight_fairness = 0.0

    service = SchedulingService(db=MockDB())  # Use mock DB for testing
    solution = service._build_and_solve_mip(data, Cfg())

    assert solution.status in ("OPTIMAL", "FEASIBLE"), f"Solution status was {solution.status}"
    # Must assign exactly 2 employees to cover 2 roles
    assert len(solution.assignments) == 2, f"Expected 2 assignments, got {len(solution.assignments)}"
    # Roles covered exactly once each
    roles = sorted(a["role_id"] for a in solution.assignments)
    assert roles == [10, 20], f"Expected roles [10, 20], got {roles}"
    # Verify assignments have correct structure
    for assignment in solution.assignments:
        assert "user_id" in assignment, "Assignment missing user_id"
        assert "planned_shift_id" in assignment, "Assignment missing planned_shift_id"
        assert "role_id" in assignment, "Assignment missing role_id"
        assert assignment["planned_shift_id"] == 100, "All assignments should be for shift 100"
    # Verify we have 2 distinct employees (not one employee covering both roles)
    user_ids = [a["user_id"] for a in solution.assignments]
    assert len(set(user_ids)) == 2, f"Expected 2 distinct employees, got {user_ids}"


if __name__ == "__main__":
    print("Running critical fixes tests...\n")
    
    try:
        test_mip_requires_distinct_employees_for_two_roles()
        
        print("\n✅ All critical fixes tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise

