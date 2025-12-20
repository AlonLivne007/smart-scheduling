"""
Optimization data structure.

This module contains the OptimizationData data structure (DTO/dataclass style)
that holds all the structured data needed to build a MIP model.
No SQLAlchemy, no business logic.
"""

from typing import Dict, List, Set, Tuple
from app.db.models.systemConstraintsModel import SystemConstraintType


class OptimizationData:
    """
    Data structure for optimization input.
    
    This class holds all the structured data needed to build a MIP model.
    """
    
    def __init__(self):
        # List of eligible employees with their roles
        self.employees: List[Dict] = []  # [{user_id, name, role_ids: [1, 2, ...]}]
        
        # List of planned shifts
        self.shifts: List[Dict] = []  # [{shift_id, date, start_time, end_time, template_id, location}]
        
        # Role requirements per shift: {shift_id: {role_id: required_count}}
        self.role_requirements: Dict[int, Dict[int, int]] = {}
        
        # Available pairs: {(employee_id, shift_id)} - only stores available assignments
        self.available_pairs: Set[Tuple[int, int]] = set()
        
        # Eligible roles per employee-shift pair: {(employee_id, shift_id): {role_id, ...}}
        # Contains roles that employee is qualified for AND are required by the shift
        # Only includes available pairs (for optimization variables)
        self.eligible_roles: Dict[Tuple[int, int], Set[int]] = {}
        
        # Shift durations in hours: {shift_id: duration_hours}
        self.shift_durations: Dict[int, float] = {}
        
        # Shift overlaps: {shift_id: {overlapping_shift_ids}}
        self.shift_overlaps: Dict[int, Set[int]] = {}
        
        # Time-off conflicts: {employee_id: [shift_ids]}
        self.time_off_conflicts: Dict[int, List[int]] = {}
        
        # Existing assignments: {(employee_id, shift_id, role_id): bool}
        self.existing_assignments: Set[Tuple[int, int, int]] = set()
        
        # Fixed assignments mapping: {(employee_id, shift_id): role_id}
        # Used by MIP builder to fix x[i,j,k_assigned] = 1 and prevent other roles
        self.fixed_assignments: Dict[Tuple[int, int], int] = {}
        
        # System constraints: {SystemConstraintType: (value, is_hard)}
        # Loaded once to keep MIP builder clean (no DB queries)
        self.system_constraints: Dict[SystemConstraintType, Tuple[float, bool]] = {}

