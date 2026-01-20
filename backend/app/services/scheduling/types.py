"""
Shared types for scheduling service.
"""

from typing import Dict, List, Any


class SchedulingSolution:
    """Result of scheduling optimization."""
    
    def __init__(self):
        self.status: str = "UNKNOWN"  # OPTIMAL, FEASIBLE, INFEASIBLE, NO_SOLUTION_FOUND
        self.objective_value: float = 0.0
        self.runtime_seconds: float = 0.0
        self.mip_gap: float = 0.0
        self.assignments: List[Dict[str, Any]] = []  # List of {user_id, planned_shift_id, role_id}
        self.metrics: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'status': self.status,
            'objective_value': self.objective_value,
            'runtime_seconds': self.runtime_seconds,
            'mip_gap': self.mip_gap,
            'assignments': self.assignments,
            'metrics': self.metrics
        }

