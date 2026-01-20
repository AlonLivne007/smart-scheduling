"""
Optimization data structure.

This module contains the OptimizationData data structure (DTO/dataclass style)
that holds all the structured data needed to build a MIP model.
No SQLAlchemy, no business logic.
"""

from typing import Dict, List, Set, Tuple, Any
import numpy as np
from app.data.models.system_constraints_model import SystemConstraintType


class OptimizationData:
    """
    Data class to hold all extracted optimization data.
    
    Attributes:
        employees: List of eligible employee dictionaries
        shifts: List of planned shift dictionaries
        roles: List of role dictionaries
        availability_matrix: 2D numpy array (employees × shifts) - 1 if available, 0 if not
        preference_scores: 2D numpy array (employees × shifts) - preference score 0.0-1.0
        role_requirements: Dictionary mapping shift_id -> List of required role_ids
        employee_roles: Dictionary mapping user_id -> List of role_ids
        shift_overlaps: Dictionary mapping shift_id -> List of overlapping shift_ids
        employee_index: Dictionary mapping user_id -> array index
        shift_index: Dictionary mapping planned_shift_id -> array index
        existing_assignments: Set of (employee_id, shift_id, role_id) tuples (to be added)
        shift_durations: Dictionary mapping shift_id -> duration_hours (to be added)
        system_constraints: Dictionary mapping SystemConstraintType -> (value, is_hard) (to be added)
        time_off_conflicts: Dictionary mapping employee_id -> list of conflicting shift_ids (to be added)
    """
    
    def __init__(self):
        # Basic sets (from CURRENT)
        self.employees: List[Dict[str, Any]] = []
        self.shifts: List[Dict[str, Any]] = []
        self.roles: List[Dict[str, Any]] = []
        
        # Numpy matrices (from CURRENT - required for MIP solver)
        self.availability_matrix: np.ndarray = None
        self.preference_scores: np.ndarray = None
        
        # Index mappings (from CURRENT - required for MIP solver)
        self.employee_index: Dict[int, int] = {}
        self.shift_index: Dict[int, int] = {}
        
        # Role mappings (from CURRENT)
        self.role_requirements: Dict[int, List[int]] = {}  # Keep CURRENT format
        self.employee_roles: Dict[int, List[int]] = {}
        self.shift_overlaps: Dict[int, List[int]] = {}
        
        # New fields from MY branch (to be populated in later phases)
        self.existing_assignments: Set[Tuple[int, int, int]] = set()  # {(emp_id, shift_id, role_id)}
        self.shift_durations: Dict[int, float] = {}  # {shift_id: duration_hours}
        self.system_constraints: Dict[SystemConstraintType, Tuple[float, bool]] = {}  # {type: (value, is_hard)}
        self.time_off_conflicts: Dict[int, List[int]] = {}  # {emp_id: [conflicting_shift_ids]}
        self.shift_rest_conflicts: Dict[int, Set[int]] = {}  # {shift_id: {conflicting_shift_ids}} for MIN_REST_HOURS

