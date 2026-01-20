"""
MIP solver for scheduling optimization.

This module contains the MipSchedulingSolver class that builds and solves
the Mixed Integer Programming model for shift assignment optimization.
"""

from typing import Dict, List, Tuple, Any
from datetime import datetime, date
import mip

from app.services.optimization_data_services import OptimizationData
from app.data.models.optimization_config_model import OptimizationConfigModel
from app.data.models.system_constraints_model import SystemConstraintType
from app.services.scheduling.types import SchedulingSolution
from app.services.scheduling.metrics import calculate_metrics
from app.services.scheduling.run_status import map_solver_status


# Constants
SOFT_PENALTY_WEIGHT = 100.0  # Large weight to strongly discourage soft constraint violations


class MipSchedulingSolver:
    """MIP solver for scheduling optimization."""
    
    def solve(
        self,
        data: OptimizationData,
        config: OptimizationConfigModel
    ) -> SchedulingSolution:
        """
        Build and solve the MIP model.
        
        Args:
            data: OptimizationData with employees, shifts, and matrices
            config: OptimizationConfig with weights and solver parameters
        
        Returns:
            SchedulingSolution with results
        """
        solution = SchedulingSolution()
        start_time = datetime.now()
        
        # Create MIP model
        model = mip.Model(sense=mip.MAXIMIZE, solver_name=mip.CBC)
        
        # Set solver parameters
        model.max_seconds = config.max_runtime_seconds
        model.max_mip_gap = config.mip_gap
        
        n_employees = len(data.employees)
        n_shifts = len(data.shifts)
        
        # Validate matrix dimensions
        if data.preference_scores.shape != (n_employees, n_shifts):
            raise ValueError(
                f"Preference scores matrix shape mismatch: expected ({n_employees}, {n_shifts}), "
                f"got {data.preference_scores.shape}"
            )
        if data.availability_matrix.shape != (n_employees, n_shifts):
            raise ValueError(
                f"Availability matrix shape mismatch: expected ({n_employees}, {n_shifts}), "
                f"got {data.availability_matrix.shape}"
            )
        
        # Build decision variables and indexes
        x, vars_by_emp_shift, vars_by_employee = self._build_decision_variables(model, data, n_employees, n_shifts)
        
        # Add constraints
        self._add_coverage_constraints(model, data, x, n_employees, n_shifts)
        self._add_single_role_constraints(model, x, vars_by_emp_shift, n_employees, n_shifts)
        self._add_overlap_constraints(model, data, x, vars_by_emp_shift, n_employees)
        self._add_hard_constraints(model, data, x, vars_by_emp_shift, vars_by_employee, n_employees)
        
        # Build objective function
        assignments_per_employee, avg_assignments = self._add_fairness_terms(model, data, x, vars_by_employee, n_employees)
        soft_penalty_component = self._add_soft_penalties(model, data, x, vars_by_emp_shift, vars_by_employee, n_employees)
        objective = self._build_objective(
            model, data, x, config, assignments_per_employee, soft_penalty_component, avg_assignments
        )
        model.objective = objective
        
        # Solve the model
        status = model.optimize()
        
        # Record results
        end_time = datetime.now()
        solution.runtime_seconds = (end_time - start_time).total_seconds()
        solution.status = map_solver_status(status)
        
        if status in [mip.OptimizationStatus.OPTIMAL, mip.OptimizationStatus.FEASIBLE]:
            solution.objective_value = model.objective_value
            solution.mip_gap = model.gap
            
            # Extract assignments
            solution.assignments = self._extract_assignments(x, data)
            solution.metrics = calculate_metrics(data, solution.assignments)
        
        return solution
    
    def _build_decision_variables(
        self,
        model: mip.Model,
        data: OptimizationData,
        n_employees: int,
        n_shifts: int
    ) -> Tuple[Dict, Dict, Dict]:
        """
        Build decision variables and indexes for efficient access.
        
        Returns:
            Tuple of (x dict, vars_by_emp_shift dict, vars_by_employee dict)
            - x: {(emp_idx, shift_idx, role_id): var} mapping
            - vars_by_emp_shift: {(emp_idx, shift_idx): [var1, var2, ...]} mapping for performance
            - vars_by_employee: {emp_idx: [var1, var2, ...]} mapping for O(1) access
        """
        x: Dict[Tuple[int, int, int], mip.Var] = {}
        vars_by_emp_shift: Dict[Tuple[int, int], List[mip.Var]] = {}
        vars_by_employee: Dict[int, List[mip.Var]] = {}
        
        for emp_idx, emp in enumerate(data.employees):
            for shift_idx, shift in enumerate(data.shifts):
                if data.availability_matrix[emp_idx, shift_idx] != 1:
                    continue

                required_roles = shift.get('required_roles') or []
                if not required_roles:
                    continue

                emp_role_ids = set(emp.get('roles') or [])
                
                # Create variable for each role that employee has and shift requires
                for role_req in required_roles:
                    role_id = role_req['role_id']
                    if role_id in emp_role_ids:
                        var = model.add_var(var_type=mip.BINARY, name=f'x_{emp_idx}_{shift_idx}_{role_id}')
                        x[emp_idx, shift_idx, role_id] = var
                        
                        # Build indexes for performance
                        if (emp_idx, shift_idx) not in vars_by_emp_shift:
                            vars_by_emp_shift[(emp_idx, shift_idx)] = []
                        vars_by_emp_shift[(emp_idx, shift_idx)].append(var)
                        
                        # Build employee index for O(1) access
                        if emp_idx not in vars_by_employee:
                            vars_by_employee[emp_idx] = []
                        vars_by_employee[emp_idx].append(var)
        
        return x, vars_by_emp_shift, vars_by_employee
    
    # Helper methods for common operations
    
    def _get_employee_vars(
        self, emp_idx: int, vars_by_employee: Dict[int, List[mip.Var]]
    ) -> List[mip.Var]:
        """
        Get all variables for a specific employee.
        
        Args:
            emp_idx: Employee index
            vars_by_employee: Index mapping emp_idx -> [vars] for O(1) access
            
        Returns:
            List of all variables for the employee
        """
        return vars_by_employee.get(emp_idx, [])
    
    def _get_employee_hours_vars(
        self, emp_idx: int, vars_by_emp_shift: Dict[Tuple[int, int], List[mip.Var]], data: OptimizationData
    ) -> List[mip.LinExpr]:
        """
        Get list of (duration * var) expressions for a specific employee.
        
        Args:
            emp_idx: Employee index
            vars_by_emp_shift: Index mapping (emp_idx, shift_idx) -> [vars]
            data: OptimizationData with shifts and durations
            
        Returns:
            List of (shift_duration * var) expressions
        """
        emp_hours_vars = []
        for (ei, ej) in vars_by_emp_shift.keys():
            if ei == emp_idx:
                shift = data.shifts[ej]
                shift_id = shift['planned_shift_id']
                shift_duration = data.shift_durations.get(shift_id, 0.0)
                if shift_duration > 0:
                    for var in vars_by_emp_shift[(ei, ej)]:
                        emp_hours_vars.append(shift_duration * var)
        return emp_hours_vars
    
    def _build_date_to_shifts_mapping(
        self, data: OptimizationData
    ) -> Dict[date, List[int]]:
        """
        Build mapping from date to list of shift indices.
        
        Returns:
            Dictionary mapping date -> [shift_indices]
        """
        date_to_shifts: Dict[date, List[int]] = {}
        for j, shift in enumerate(data.shifts):
            shift_date = shift['date']
            if isinstance(shift_date, datetime):
                shift_date = shift_date.date()
            if shift_date not in date_to_shifts:
                date_to_shifts[shift_date] = []
            date_to_shifts[shift_date].append(j)
        return date_to_shifts
    
    def _build_works_on_day_variables(
        self,
        model: mip.Model,
        data: OptimizationData,
        vars_by_emp_shift: Dict[Tuple[int, int], List[mip.Var]],
        n_employees: int,
        date_to_shifts: Dict[date, List[int]],
        var_name_prefix: str = "works_day"
    ) -> Dict[Tuple[int, date], mip.Var]:
        """
        Build binary variables indicating if employee works on each date.
        
        Args:
            model: MIP model
            data: OptimizationData
            vars_by_emp_shift: Index for performance
            n_employees: Number of employees
            date_to_shifts: Mapping from date to shift indices
            var_name_prefix: Prefix for variable names
            
        Returns:
            Dictionary mapping (emp_idx, date) -> works_on_day variable
        """
        works_on_day: Dict[Tuple[int, date], mip.Var] = {}
        sorted_dates = sorted(date_to_shifts.keys())
        
        for emp_idx in range(n_employees):
            for d in sorted_dates:
                var = model.add_var(
                    var_type=mip.BINARY,
                    name=f'{var_name_prefix}_emp_{emp_idx}_date_{d}'
                )
                works_on_day[(emp_idx, d)] = var
                
                shift_indices_for_date = date_to_shifts[d]
                vars_for_date = []
                for shift_idx in shift_indices_for_date:
                    if (emp_idx, shift_idx) in vars_by_emp_shift:
                        vars_for_date.extend(vars_by_emp_shift[(emp_idx, shift_idx)])
                
                if vars_for_date:
                    for var_for_date in vars_for_date:
                        model += works_on_day[(emp_idx, d)] >= var_for_date
                    model += works_on_day[(emp_idx, d)] <= mip.xsum(vars_for_date)
        
        return works_on_day
    
    def _add_coverage_constraints(
        self,
        model: mip.Model,
        data: OptimizationData,
        x: Dict[Tuple[int, int, int], mip.Var],
        n_employees: int,
        n_shifts: int
    ) -> None:
        """Add coverage constraints: each shift must be assigned exactly the required employees for each role."""
        for j, shift in enumerate(data.shifts):
            required_roles = shift.get('required_roles') or []
            if not required_roles:
                continue

            for role_req in required_roles:
                role_id = role_req['role_id']
                required_count = int(role_req['required_count'])

                eligible_vars = [x[emp_idx, j, role_id] for emp_idx in range(n_employees) if (emp_idx, j, role_id) in x]

                if not eligible_vars:
                    if required_count > 0:
                        raise ValueError(
                            f"Infeasible coverage: planned_shift_id={shift['planned_shift_id']} "
                            f"requires role_id={role_id} count={required_count}, but no eligible employees exist "
                            f"(availability_matrix=0 or no matching roles)."
                        )
                    continue

                model += mip.xsum(eligible_vars) == required_count, f'coverage_shift_{j}_role_{role_id}'
    
    def _add_single_role_constraints(
        self,
        model: mip.Model,
        x: Dict[Tuple[int, int, int], mip.Var],
        vars_by_emp_shift: Dict[Tuple[int, int], List[mip.Var]],
        n_employees: int,
        n_shifts: int
    ) -> int:
        """
        Add single-role-per-shift constraints: sum_r x[i,j,r] <= 1.
        
        Returns:
            Number of constraints added
        """
        count = 0
        for emp_idx in range(n_employees):
            for shift_idx in range(n_shifts):
                if (emp_idx, shift_idx) in vars_by_emp_shift:
                    role_vars = vars_by_emp_shift[(emp_idx, shift_idx)]
                    if len(role_vars) > 1:
                        model += mip.xsum(role_vars) <= 1, f'single_role_emp_{emp_idx}_shift_{shift_idx}'
                        count += 1
        
        return count
    
    def _add_overlap_constraints(
        self,
        model: mip.Model,
        data: OptimizationData,
        x: Dict[Tuple[int, int, int], mip.Var],
        vars_by_emp_shift: Dict[Tuple[int, int], List[mip.Var]],
        n_employees: int
    ) -> int:
        """
        Add no-overlap constraints: employees can't be assigned to overlapping shifts.
        
        Returns:
            Number of constraints added
        """
        count = 0
        
        for shift_id, overlapping_ids in data.shift_overlaps.items():
            if not overlapping_ids:
                continue
            
            shift_idx = data.shift_index[shift_id]
            
            for overlapping_id in overlapping_ids:
                overlapping_idx = data.shift_index[overlapping_id]
                
                for emp_idx in range(n_employees):
                    vars_shift = vars_by_emp_shift.get((emp_idx, shift_idx), [])
                    vars_overlap = vars_by_emp_shift.get((emp_idx, overlapping_idx), [])
                    
                    if vars_shift and vars_overlap:
                        model += mip.xsum(vars_shift) + mip.xsum(vars_overlap) <= 1, f'no_overlap_emp_{emp_idx}_shift_{shift_idx}_{overlapping_idx}'
                        count += 1
        
        return count
    
    def _add_hard_constraints(
        self,
        model: mip.Model,
        data: OptimizationData,
        x: Dict[Tuple[int, int, int], mip.Var],
        vars_by_emp_shift: Dict[Tuple[int, int], List[mip.Var]],
        vars_by_employee: Dict[int, List[mip.Var]],
        n_employees: int
    ) -> Dict[str, int]:
        """
        Add HARD system constraints.
        
        Returns:
            Dict with counts: {'max_shifts': int, 'max_hours': int, 'min_rest': int, 'max_consecutive': int, 'min_hours': int, 'min_shifts': int}
        """
        counts = {'max_shifts': 0, 'max_hours': 0, 'min_rest': 0, 'max_consecutive': 0, 'min_hours': 0, 'min_shifts': 0}
        
        # MAX_SHIFTS_PER_WEEK (hard)
        max_shifts_constraint = data.system_constraints.get(SystemConstraintType.MAX_SHIFTS_PER_WEEK)
        if max_shifts_constraint and max_shifts_constraint[1]:  # is_hard
            max_shifts = int(max_shifts_constraint[0])
            for emp_idx in range(n_employees):
                emp_vars = self._get_employee_vars(emp_idx, vars_by_employee)
                if emp_vars:
                    model += mip.xsum(emp_vars) <= max_shifts, f'max_shifts_emp_{emp_idx}'
                    counts['max_shifts'] += 1
        
        # MAX_HOURS_PER_WEEK (hard)
        max_hours_constraint = data.system_constraints.get(SystemConstraintType.MAX_HOURS_PER_WEEK)
        if max_hours_constraint and max_hours_constraint[1]:  # is_hard
            max_hours = max_hours_constraint[0]
            for emp_idx in range(n_employees):
                emp_hours_vars = self._get_employee_hours_vars(emp_idx, vars_by_emp_shift, data)
                if emp_hours_vars:
                    model += mip.xsum(emp_hours_vars) <= max_hours, f'max_hours_emp_{emp_idx}'
                    counts['max_hours'] += 1
        
        # MIN_REST_HOURS (hard) - using rest conflicts
        min_rest_constraint = data.system_constraints.get(SystemConstraintType.MIN_REST_HOURS)
        if min_rest_constraint and min_rest_constraint[1]:  # is_hard
            for shift_id, conflicting_ids in data.shift_rest_conflicts.items():
                if not conflicting_ids:
                    continue
                
                shift_idx = data.shift_index[shift_id]
                
                for conflicting_id in conflicting_ids:
                    conflicting_idx = data.shift_index[conflicting_id]
                    
                    for emp_idx in range(n_employees):
                        vars_shift = vars_by_emp_shift.get((emp_idx, shift_idx), [])
                        vars_conflict = vars_by_emp_shift.get((emp_idx, conflicting_idx), [])
                        
                        if vars_shift and vars_conflict:
                            model += mip.xsum(vars_shift) + mip.xsum(vars_conflict) <= 1, f'min_rest_emp_{emp_idx}_shift_{shift_idx}_{conflicting_idx}'
                            counts['min_rest'] += 1
        
        # MAX_CONSECUTIVE_DAYS (hard)
        max_consecutive_constraint = data.system_constraints.get(SystemConstraintType.MAX_CONSECUTIVE_DAYS)
        if max_consecutive_constraint and max_consecutive_constraint[1]:  # is_hard
            max_consecutive = int(max_consecutive_constraint[0])
            counts['max_consecutive'] = self._add_consecutive_days_constraints(
                model, data, x, vars_by_emp_shift, n_employees, max_consecutive
            )
        
        # MIN_HOURS_PER_WEEK (hard)
        min_hours_constraint = data.system_constraints.get(SystemConstraintType.MIN_HOURS_PER_WEEK)
        if min_hours_constraint and min_hours_constraint[1]:  # is_hard
            min_hours = min_hours_constraint[0]
            for emp_idx in range(n_employees):
                emp_hours_vars = self._get_employee_hours_vars(emp_idx, vars_by_emp_shift, data)
                if emp_hours_vars:
                    model += mip.xsum(emp_hours_vars) >= min_hours, f'min_hours_emp_{emp_idx}'
                    counts['min_hours'] += 1
        
        # MIN_SHIFTS_PER_WEEK (hard)
        min_shifts_constraint = data.system_constraints.get(SystemConstraintType.MIN_SHIFTS_PER_WEEK)
        if min_shifts_constraint and min_shifts_constraint[1]:  # is_hard
            min_shifts = int(min_shifts_constraint[0])
            for emp_idx in range(n_employees):
                emp_vars = self._get_employee_vars(emp_idx, vars_by_employee)
                if emp_vars:
                    model += mip.xsum(emp_vars) >= min_shifts, f'min_shifts_emp_{emp_idx}'
                    counts['min_shifts'] += 1
        
        return counts
    
    def _add_consecutive_days_constraints(
        self,
        model: mip.Model,
        data: OptimizationData,
        x: Dict[Tuple[int, int, int], mip.Var],
        vars_by_emp_shift: Dict[Tuple[int, int], List[mip.Var]],
        n_employees: int,
        max_consecutive: int
    ) -> int:
        """
        Add MAX_CONSECUTIVE_DAYS constraints.
        
        For each employee, we create binary variables indicating if they work on each day.
        Then, for each sequence of (max_consecutive+1) consecutive days, we add constraint:
        sum of day indicators <= max_consecutive.
        
        This ensures no employee works more than max_consecutive consecutive days.
        
        Args:
            model: MIP model
            data: OptimizationData
            x: Decision variables dict
            vars_by_emp_shift: Index for performance
            n_employees: Number of employees
            max_consecutive: Maximum consecutive days allowed
            
        Returns:
            Number of constraints added
        """
        date_to_shifts = self._build_date_to_shifts_mapping(data)
        if not date_to_shifts:
            return 0
        
        sorted_dates = sorted(date_to_shifts.keys())
        works_on_day = self._build_works_on_day_variables(
            model, data, vars_by_emp_shift, n_employees, date_to_shifts
        )
        
        # Find all sequences of (max_consecutive+1) consecutive days
        constraint_count = 0
        for start_idx in range(len(sorted_dates) - max_consecutive):
            # Check if dates[start_idx:start_idx+max_consecutive+1] are consecutive
            sequence_dates = sorted_dates[start_idx:start_idx + max_consecutive + 1]
            is_consecutive = True
            for i in range(len(sequence_dates) - 1):
                if (sequence_dates[i+1] - sequence_dates[i]).days != 1:
                    is_consecutive = False
                    break
            
            if not is_consecutive:
                continue
            
            for emp_idx in range(n_employees):
                day_vars = [works_on_day[(emp_idx, d)] for d in sequence_dates]
                if day_vars:
                    model += mip.xsum(day_vars) <= max_consecutive, \
                            f'max_consecutive_emp_{emp_idx}_days_{start_idx}'
                    constraint_count += 1
        
        return constraint_count
    
    def _add_fairness_terms(
        self,
        model: mip.Model,
        data: OptimizationData,
        x: Dict[Tuple[int, int, int], mip.Var],
        vars_by_employee: Dict[int, List[mip.Var]],
        n_employees: int
    ) -> Tuple[List[mip.LinExpr], float]:
        """
        Add fairness terms (constraints and auxiliary variables).
        
        Returns:
            Tuple of (assignments_per_employee list, avg_assignments float)
        """
        # Calculate average assignments per employee
        total_required_assignments = sum(
            sum(req['required_count'] for req in shift['required_roles'])
            for shift in data.shifts
            if shift['required_roles']
        )
        
        avg_assignments = total_required_assignments / n_employees if n_employees > 0 else 0
        
        # Build emp_total for every employee (even if they have no variables)
        assignments_per_employee = []
        for emp_idx in range(n_employees):
            emp_vars = self._get_employee_vars(emp_idx, vars_by_employee)
            emp_total = mip.xsum(emp_vars) if emp_vars else 0
            assignments_per_employee.append(emp_total)
        
        return assignments_per_employee, avg_assignments
    
    def _add_soft_penalties(
        self,
        model: mip.Model,
        data: OptimizationData,
        x: Dict[Tuple[int, int, int], mip.Var],
        vars_by_emp_shift: Dict[Tuple[int, int], List[mip.Var]],
        vars_by_employee: Dict[int, List[mip.Var]],
        n_employees: int
    ) -> mip.LinExpr:
        """
        Add soft constraint penalties.
        
        Returns:
            LinExpr for soft penalty component
        """
        soft_penalty_component = 0
        
        # MIN_HOURS_PER_WEEK (soft) - penalty for hours below minimum
        min_hours_constraint = data.system_constraints.get(SystemConstraintType.MIN_HOURS_PER_WEEK)
        if min_hours_constraint and not min_hours_constraint[1]:  # is_soft
            min_hours = min_hours_constraint[0]
            for emp_idx in range(n_employees):
                emp_hours_vars = self._get_employee_hours_vars(emp_idx, vars_by_emp_shift, data)
                if emp_hours_vars:
                    total_hours = mip.xsum(emp_hours_vars)
                    deficit = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'min_hours_deficit_{emp_idx}')
                    model += deficit >= min_hours - total_hours
                    soft_penalty_component += deficit
        
        # MIN_SHIFTS_PER_WEEK (soft) - penalty for shifts below minimum
        min_shifts_constraint = data.system_constraints.get(SystemConstraintType.MIN_SHIFTS_PER_WEEK)
        if min_shifts_constraint and not min_shifts_constraint[1]:  # is_soft
            min_shifts = int(min_shifts_constraint[0])
            for emp_idx in range(n_employees):
                emp_vars = self._get_employee_vars(emp_idx, vars_by_employee)
                if emp_vars:
                    total_shifts = mip.xsum(emp_vars)
                    deficit = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'min_shifts_deficit_{emp_idx}')
                    model += deficit >= min_shifts - total_shifts
                    soft_penalty_component += deficit
        
        # MAX_HOURS_PER_WEEK (soft) - penalty for hours above maximum
        max_hours_constraint = data.system_constraints.get(SystemConstraintType.MAX_HOURS_PER_WEEK)
        if max_hours_constraint and not max_hours_constraint[1]:  # is_soft
            max_hours = max_hours_constraint[0]
            for emp_idx in range(n_employees):
                emp_hours_vars = self._get_employee_hours_vars(emp_idx, vars_by_emp_shift, data)
                if emp_hours_vars:
                    total_hours = mip.xsum(emp_hours_vars)
                    excess = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'max_hours_excess_{emp_idx}')
                    model += excess >= total_hours - max_hours
                    soft_penalty_component += excess
        
        # MAX_SHIFTS_PER_WEEK (soft) - penalty for shifts above maximum
        max_shifts_constraint = data.system_constraints.get(SystemConstraintType.MAX_SHIFTS_PER_WEEK)
        if max_shifts_constraint and not max_shifts_constraint[1]:  # is_soft
            max_shifts = int(max_shifts_constraint[0])
            for emp_idx in range(n_employees):
                emp_vars = self._get_employee_vars(emp_idx, vars_by_employee)
                if emp_vars:
                    total_shifts = mip.xsum(emp_vars)
                    excess = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'max_shifts_excess_{emp_idx}')
                    model += excess >= total_shifts - max_shifts
                    soft_penalty_component += excess
        
        # MIN_REST_HOURS (soft) - penalty for insufficient rest between shifts
        min_rest_constraint = data.system_constraints.get(SystemConstraintType.MIN_REST_HOURS)
        if min_rest_constraint and not min_rest_constraint[1]:  # is_soft
            min_rest_hours = min_rest_constraint[0]
            for shift_id, conflicting_ids in data.shift_rest_conflicts.items():
                if not conflicting_ids:
                    continue
                
                shift_idx = data.shift_index[shift_id]
                
                for conflicting_id in conflicting_ids:
                    conflicting_idx = data.shift_index[conflicting_id]
                    
                    for emp_idx in range(n_employees):
                        vars_shift = vars_by_emp_shift.get((emp_idx, shift_idx), [])
                        vars_conflict = vars_by_emp_shift.get((emp_idx, conflicting_idx), [])
                        
                        if vars_shift and vars_conflict:
                            total_assignments = mip.xsum(vars_shift) + mip.xsum(vars_conflict)
                            violation = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'min_rest_violation_emp_{emp_idx}_shift_{shift_idx}_{conflicting_idx}')
                            model += violation >= total_assignments - 1
                            soft_penalty_component += violation
        
        # MAX_CONSECUTIVE_DAYS (soft) - penalty for too many consecutive days
        max_consecutive_constraint = data.system_constraints.get(SystemConstraintType.MAX_CONSECUTIVE_DAYS)
        if max_consecutive_constraint and not max_consecutive_constraint[1]:  # is_soft
            max_consecutive = int(max_consecutive_constraint[0])
            date_to_shifts = self._build_date_to_shifts_mapping(data)
            
            if date_to_shifts:
                sorted_dates = sorted(date_to_shifts.keys())
                works_on_day = self._build_works_on_day_variables(
                    model, data, vars_by_emp_shift, n_employees, date_to_shifts,
                    var_name_prefix="works_day_soft"
                )
                
                # Find all sequences of (max_consecutive+1) consecutive days and add penalties
                for start_idx in range(len(sorted_dates) - max_consecutive):
                    sequence_dates = sorted_dates[start_idx:start_idx + max_consecutive + 1]
                    is_consecutive = True
                    for i in range(len(sequence_dates) - 1):
                        if (sequence_dates[i+1] - sequence_dates[i]).days != 1:
                            is_consecutive = False
                            break
                    
                    if not is_consecutive:
                        continue
                    
                    for emp_idx in range(n_employees):
                        day_vars = [works_on_day[(emp_idx, d)] for d in sequence_dates]
                        if day_vars:
                            total_days = mip.xsum(day_vars)
                            excess_days = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'max_consecutive_excess_emp_{emp_idx}_days_{start_idx}')
                            model += excess_days >= total_days - max_consecutive
                            soft_penalty_component += excess_days
        
        return soft_penalty_component
    
    def _build_objective(
        self,
        model: mip.Model,
        data: OptimizationData,
        x: Dict[Tuple[int, int, int], mip.Var],
        config: OptimizationConfigModel,
        assignments_per_employee: List[mip.LinExpr],
        soft_penalty_component: mip.LinExpr,
        avg_assignments: float
    ) -> mip.LinExpr:
        """
        Build objective function.
        
        Args:
            avg_assignments: Pre-calculated average assignments per employee
            
        Returns:
            LinExpr for the objective
        """
        # Component 1: Maximize preference satisfaction
        try:
            preference_component = mip.xsum(
                data.preference_scores[i, j] * x[i, j, r]
                for (i, j, r) in x
            )
        except (KeyError, IndexError) as e:
            raise ValueError(
                f"Error building preference component: {e}. "
                f"Matrix shape: {data.preference_scores.shape}, "
                f"Employees: {len(data.employees)}, Shifts: {len(data.shifts)}, "
                f"Variables: {len(x)}"
            ) from e
        
        # Component 2: Fairness (minimize deviation from average)
        # We'll use auxiliary variables for absolute deviation
        fairness_vars = []
        for i, emp_total in enumerate(assignments_per_employee):
            # Deviation from average (can be positive or negative)
            deviation_pos = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'dev_pos_{i}')
            deviation_neg = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'dev_neg_{i}')
            
            # emp_total - avg = deviation_pos - deviation_neg
            model += emp_total - avg_assignments == deviation_pos - deviation_neg
            
            fairness_vars.append(deviation_pos + deviation_neg)
        
        fairness_component = mip.xsum(fairness_vars) if fairness_vars else 0
        
        # Component 3: Coverage (maximize filled assignments)
        try:
            coverage_component = mip.xsum(x[i, j, r] for (i, j, r) in x)
        except KeyError as e:
            raise ValueError(
                f"Error building coverage component: KeyError {e}. "
                f"This should not happen as we're iterating over x.keys()"
            ) from e
        
        # Component 4: SOFT constraint penalties
        
        # Combine objectives with weights
        # Note: fairness is minimized, so we subtract it
        # Soft penalties are minimized, so we subtract them
        objective = (
            config.weight_preferences * preference_component +
            config.weight_coverage * coverage_component -
            config.weight_fairness * fairness_component -
            SOFT_PENALTY_WEIGHT * soft_penalty_component
        )
        
        return objective
    
    def _extract_assignments(self, x: Dict, data: OptimizationData) -> List[Dict[str, Any]]:
        """
        Extract assignments from solved model.
        
        Returns:
            List of assignment dictionaries
        """
        assignments = []
        for (i, j, role_id), var in x.items():
            if var.x > 0.5:  # Variable is 1 (assigned)
                emp = data.employees[i]
                shift = data.shifts[j]
                
                assignments.append({
                    'user_id': emp['user_id'],
                    'planned_shift_id': shift['planned_shift_id'],
                    'role_id': role_id,
                    'preference_score': float(data.preference_scores[i, j])
                })
        
        return assignments

