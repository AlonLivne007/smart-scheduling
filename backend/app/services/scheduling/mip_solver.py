"""
MIP solver for scheduling optimization.

This module contains the MipSchedulingSolver class that builds and solves
the Mixed Integer Programming model for shift assignment optimization.
"""

from typing import Dict, List, Tuple
from datetime import datetime
import mip
import numpy as np

from app.services.optimization_data_services import OptimizationData
from app.db.models.optimizationConfigModel import OptimizationConfigModel
from app.db.models.systemConstraintsModel import SystemConstraintType
from app.services.scheduling.types import SchedulingSolution
from app.services.scheduling.metrics import calculate_metrics
from app.services.scheduling.run_status import map_solver_status


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
        
        # Log system constraints
        print("\n📋 System Constraints:")
        for constraint_type, (value, is_hard) in data.system_constraints.items():
            constraint_type_str = constraint_type.value if hasattr(constraint_type, 'value') else str(constraint_type)
            hard_soft = "HARD" if is_hard else "SOFT"
            print(f"  {constraint_type_str}: {value} ({hard_soft})")
        
        # Build decision variables and index
        print(f"Creating decision variables ({n_employees} employees × {n_shifts} shifts × roles)...")
        x, vars_by_emp_shift = self._build_decision_variables(model, data, n_employees, n_shifts)
        print(f"Created {len(x)} decision variables")
        
        # Add constraints
        self._add_coverage_constraints(model, data, x, n_employees, n_shifts)
        single_role_count = self._add_single_role_constraints(model, x, vars_by_emp_shift, n_employees, n_shifts)
        overlap_count = self._add_overlap_constraints(model, data, x, vars_by_emp_shift, n_employees)
        
        # Log constraint counts before HARD constraints
        print(f"\n📊 Constraint Summary (before HARD constraints):")
        print(f"  Decision variables: {len(x)}")
        print(f"  Coverage constraints: {sum(len(shift.get('required_roles', [])) for shift in data.shifts)}")
        print(f"  Single-role constraints: {single_role_count}")
        print(f"  Overlap constraints: {overlap_count}")
        
        hard_constraint_counts = self._add_hard_constraints(model, data, x, vars_by_emp_shift, n_employees)
        
        total_hard_constraints = sum(hard_constraint_counts.values())
        print(f"\n📊 Total HARD constraints added: {total_hard_constraints}")
        print(f"  - MAX_SHIFTS_PER_WEEK: {hard_constraint_counts['max_shifts']}")
        print(f"  - MAX_HOURS_PER_WEEK: {hard_constraint_counts['max_hours']}")
        print(f"  - MIN_REST_HOURS: {hard_constraint_counts['min_rest']}")
        
        # Build objective function
        assignments_per_employee = self._add_fairness_terms(model, data, x, vars_by_emp_shift, n_employees)
        soft_penalty_component = self._add_soft_penalties(model, data, x, vars_by_emp_shift, n_employees)
        objective = self._build_objective(
            model, data, x, config, assignments_per_employee, soft_penalty_component
        )
        model.objective = objective
        
        print(f"\nSolving MIP model...")
        print(f"  Max runtime: {config.max_runtime_seconds}s")
        print(f"  MIP gap: {config.mip_gap}")
        print(f"  Weights: preferences={config.weight_preferences}, fairness={config.weight_fairness}, coverage={config.weight_coverage}")
        
        # Solve the model
        status = model.optimize()
        
        # Record results
        end_time = datetime.now()
        solution.runtime_seconds = (end_time - start_time).total_seconds()
        solution.status = map_solver_status(status)
        
        print(f"\nSolver finished: {solution.status}")
        print(f"Runtime: {solution.runtime_seconds:.2f}s")
        
        if status in [mip.OptimizationStatus.OPTIMAL, mip.OptimizationStatus.FEASIBLE]:
            solution.objective_value = model.objective_value
            solution.mip_gap = model.gap
            
            print(f"\n✅ Solver found {solution.status} solution")
            print(f"Objective value: {solution.objective_value:.3f}")
            print(f"MIP gap: {solution.mip_gap:.4f}")
            
            # Extract assignments
            solution.assignments = self._extract_assignments(x, data)
            solution.metrics = calculate_metrics(data, solution.assignments)
            
            print(f"Total assignments: {len(solution.assignments)}")
            print(f"Average preference score: {solution.metrics.get('avg_preference_score', 0):.3f}")
            print(f"Assignments per employee: min={solution.metrics.get('min_assignments', 0)}, max={solution.metrics.get('max_assignments', 0)}, avg={solution.metrics.get('avg_assignments', 0):.1f}")
        
        return solution
    
    def _build_decision_variables(
        self,
        model: mip.Model,
        data: OptimizationData,
        n_employees: int,
        n_shifts: int
    ) -> Tuple[Dict, Dict]:
        """
        Build decision variables and index for efficient access.
        
        Returns:
            Tuple of (x dict, vars_by_emp_shift dict)
            - x: {(i, j, role_id): var} mapping
            - vars_by_emp_shift: {(i, j): [var1, var2, ...]} mapping for performance
        """
        x = {}
        vars_by_emp_shift = {}
        
        for i, emp in enumerate(data.employees):
            for j, shift in enumerate(data.shifts):
                if data.availability_matrix[i, j] != 1:
                    continue

                required_roles = shift.get('required_roles') or []
                if not required_roles:
                    continue

                emp_role_ids = set(emp.get('roles') or [])
                
                # Create variable for each role that employee has and shift requires
                for role_req in required_roles:
                    role_id = role_req['role_id']
                    if role_id in emp_role_ids:
                        var = model.add_var(var_type=mip.BINARY, name=f'x_{i}_{j}_{role_id}')
                        x[i, j, role_id] = var
                        
                        # Build index for performance
                        if (i, j) not in vars_by_emp_shift:
                            vars_by_emp_shift[(i, j)] = []
                        vars_by_emp_shift[(i, j)].append(var)
        
        return x, vars_by_emp_shift
    
    def _add_coverage_constraints(
        self,
        model: mip.Model,
        data: OptimizationData,
        x: Dict,
        n_employees: int,
        n_shifts: int
    ) -> None:
        """Add coverage constraints: each shift must be assigned exactly the required employees for each role."""
        print("Adding coverage constraints...")
        for j, shift in enumerate(data.shifts):
            required_roles = shift.get('required_roles') or []
            if not required_roles:
                continue

            for role_req in required_roles:
                role_id = role_req['role_id']
                required_count = int(role_req['required_count'])

                eligible_vars = [x[i, j, role_id] for i in range(n_employees) if (i, j, role_id) in x]

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
        x: Dict,
        vars_by_emp_shift: Dict,
        n_employees: int,
        n_shifts: int
    ) -> int:
        """
        Add single-role-per-shift constraints: sum_r x[i,j,r] <= 1.
        
        Returns:
            Number of constraints added
        """
        print("Adding single-role-per-shift constraints...")
        count = 0
        for i in range(n_employees):
            for j in range(n_shifts):
                # Use index for performance
                if (i, j) in vars_by_emp_shift:
                    role_vars = vars_by_emp_shift[(i, j)]
                    if len(role_vars) > 1:
                        model += mip.xsum(role_vars) <= 1, f'single_role_emp_{i}_shift_{j}'
                        count += 1
        
        print(f"Added {count} single-role-per-shift constraints")
        return count
    
    def _add_overlap_constraints(
        self,
        model: mip.Model,
        data: OptimizationData,
        x: Dict,
        vars_by_emp_shift: Dict,
        n_employees: int
    ) -> int:
        """
        Add no-overlap constraints: employees can't be assigned to overlapping shifts.
        
        Returns:
            Number of constraints added
        """
        print("Adding no-overlap constraints...")
        count = 0
        
        for shift_id, overlapping_ids in data.shift_overlaps.items():
            if not overlapping_ids:
                continue
            
            shift_idx = data.shift_index[shift_id]
            
            for overlapping_id in overlapping_ids:
                overlapping_idx = data.shift_index[overlapping_id]
                
                # For each employee, they can't be assigned to both overlapping shifts
                for i in range(n_employees):
                    # Use index for performance - FIXED: removed dead code with set()
                    vars_shift = vars_by_emp_shift.get((i, shift_idx), [])
                    vars_overlap = vars_by_emp_shift.get((i, overlapping_idx), [])
                    
                    if vars_shift and vars_overlap:
                        # Sum of all assignments to shift_idx + sum of all assignments to overlapping_idx <= 1
                        model += mip.xsum(vars_shift) + mip.xsum(vars_overlap) <= 1, f'no_overlap_emp_{i}_shift_{shift_idx}_{overlapping_idx}'
                        count += 1
        
        print(f"Added {count} no-overlap constraints")
        return count
    
    def _add_hard_constraints(
        self,
        model: mip.Model,
        data: OptimizationData,
        x: Dict,
        vars_by_emp_shift: Dict,
        n_employees: int
    ) -> Dict[str, int]:
        """
        Add HARD system constraints.
        
        Returns:
            Dict with counts: {'max_shifts': int, 'max_hours': int, 'min_rest': int}
        """
        print("\nAdding HARD system constraints...")
        counts = {'max_shifts': 0, 'max_hours': 0, 'min_rest': 0}
        
        # MAX_SHIFTS_PER_WEEK (hard)
        max_shifts_constraint = data.system_constraints.get(SystemConstraintType.MAX_SHIFTS_PER_WEEK)
        if max_shifts_constraint and max_shifts_constraint[1]:  # is_hard
            max_shifts = int(max_shifts_constraint[0])
            for i in range(n_employees):
                # Use index for performance
                emp_vars = []
                for (ei, ej) in vars_by_emp_shift.keys():
                    if ei == i:
                        emp_vars.extend(vars_by_emp_shift[(ei, ej)])
                
                if emp_vars:
                    model += mip.xsum(emp_vars) <= max_shifts, f'max_shifts_emp_{i}'
                    counts['max_shifts'] += 1
            print(f"  Added {counts['max_shifts']} MAX_SHIFTS_PER_WEEK constraints (max={max_shifts})")
        
        # MAX_HOURS_PER_WEEK (hard)
        max_hours_constraint = data.system_constraints.get(SystemConstraintType.MAX_HOURS_PER_WEEK)
        if max_hours_constraint and max_hours_constraint[1]:  # is_hard
            max_hours = max_hours_constraint[0]
            for i in range(n_employees):
                # Sum of (x[i,j,r] * shift_duration_hours(j)) for all j, r
                emp_hours_vars = []
                for (ei, ej) in vars_by_emp_shift.keys():
                    if ei == i:
                        shift = data.shifts[ej]
                        shift_id = shift['planned_shift_id']
                        shift_duration = data.shift_durations.get(shift_id, 0.0)
                        if shift_duration > 0:
                            for var in vars_by_emp_shift[(ei, ej)]:
                                emp_hours_vars.append(shift_duration * var)
                
                if emp_hours_vars:
                    model += mip.xsum(emp_hours_vars) <= max_hours, f'max_hours_emp_{i}'
                    counts['max_hours'] += 1
            print(f"  Added {counts['max_hours']} MAX_HOURS_PER_WEEK constraints (max={max_hours})")
        
        # MIN_REST_HOURS (hard) - using rest conflicts
        min_rest_constraint = data.system_constraints.get(SystemConstraintType.MIN_REST_HOURS)
        if min_rest_constraint and min_rest_constraint[1]:  # is_hard
            for shift_id, conflicting_ids in data.shift_rest_conflicts.items():
                if not conflicting_ids:
                    continue
                
                shift_idx = data.shift_index[shift_id]
                
                for conflicting_id in conflicting_ids:
                    conflicting_idx = data.shift_index[conflicting_id]
                    
                    # For each employee, they can't be assigned to both conflicting shifts
                    for i in range(n_employees):
                        # Use index for performance
                        vars_shift = vars_by_emp_shift.get((i, shift_idx), [])
                        vars_conflict = vars_by_emp_shift.get((i, conflicting_idx), [])
                        
                        if vars_shift and vars_conflict:
                            model += mip.xsum(vars_shift) + mip.xsum(vars_conflict) <= 1, f'min_rest_emp_{i}_shift_{shift_idx}_{conflicting_idx}'
                            counts['min_rest'] += 1
            print(f"  Added {counts['min_rest']} MIN_REST_HOURS constraints (min={min_rest_constraint[0]})")
        
        return counts
    
    def _add_fairness_terms(
        self,
        model: mip.Model,
        data: OptimizationData,
        x: Dict,
        vars_by_emp_shift: Dict,
        n_employees: int
    ) -> List:
        """
        Add fairness terms (constraints and auxiliary variables).
        
        Returns:
            List of emp_total expressions for use in objective
        """
        print("\nAdding fairness constraints...")
        
        # Calculate average assignments per employee
        total_required_assignments = sum(
            sum(req['required_count'] for req in shift['required_roles'])
            for shift in data.shifts
            if shift['required_roles']
        )
        
        avg_assignments = total_required_assignments / n_employees if n_employees > 0 else 0
        
        # Build emp_total for every employee (even if they have no variables)
        assignments_per_employee = []
        for i in range(n_employees):
            # Use index for performance
            emp_vars = []
            for (ei, ej) in vars_by_emp_shift.keys():
                if ei == i:
                    emp_vars.extend(vars_by_emp_shift[(ei, ej)])
            
            emp_total = mip.xsum(emp_vars) if emp_vars else 0
            assignments_per_employee.append(emp_total)
        
        return assignments_per_employee
    
    def _add_soft_penalties(
        self,
        model: mip.Model,
        data: OptimizationData,
        x: Dict,
        vars_by_emp_shift: Dict,
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
            for i in range(n_employees):
                # Calculate total hours for this employee using index
                emp_hours_vars = []
                for (ei, ej) in vars_by_emp_shift.keys():
                    if ei == i:
                        shift = data.shifts[ej]
                        shift_id = shift['planned_shift_id']
                        shift_duration = data.shift_durations.get(shift_id, 0.0)
                        if shift_duration > 0:
                            for var in vars_by_emp_shift[(ei, ej)]:
                                emp_hours_vars.append(shift_duration * var)
                
                if emp_hours_vars:
                    total_hours = mip.xsum(emp_hours_vars)
                    # Penalty = max(0, min_hours - total_hours)
                    deficit = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'min_hours_deficit_{i}')
                    model += deficit >= min_hours - total_hours
                    soft_penalty_component += deficit
        
        # MIN_SHIFTS_PER_WEEK (soft) - penalty for shifts below minimum
        min_shifts_constraint = data.system_constraints.get(SystemConstraintType.MIN_SHIFTS_PER_WEEK)
        if min_shifts_constraint and not min_shifts_constraint[1]:  # is_soft
            min_shifts = int(min_shifts_constraint[0])
            for i in range(n_employees):
                # Use index for performance
                emp_vars = []
                for (ei, ej) in vars_by_emp_shift.keys():
                    if ei == i:
                        emp_vars.extend(vars_by_emp_shift[(ei, ej)])
                
                if emp_vars:
                    total_shifts = mip.xsum(emp_vars)
                    # Penalty = max(0, min_shifts - total_shifts)
                    deficit = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'min_shifts_deficit_{i}')
                    model += deficit >= min_shifts - total_shifts
                    soft_penalty_component += deficit
        
        return soft_penalty_component
    
    def _build_objective(
        self,
        model: mip.Model,
        data: OptimizationData,
        x: Dict,
        config: OptimizationConfigModel,
        assignments_per_employee: List,
        soft_penalty_component: mip.LinExpr
    ) -> mip.LinExpr:
        """
        Build objective function.
        
        Returns:
            LinExpr for the objective
        """
        print("Building objective function...")
        
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
        avg_assignments = sum(
            sum(req['required_count'] for req in shift['required_roles'])
            for shift in data.shifts
            if shift['required_roles']
        ) / len(data.employees) if len(data.employees) > 0 else 0
        
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
        soft_penalty_weight = 100.0  # Large weight to strongly discourage violations
        
        # Combine objectives with weights
        # Note: fairness is minimized, so we subtract it
        # Soft penalties are minimized, so we subtract them
        objective = (
            config.weight_preferences * preference_component +
            config.weight_coverage * coverage_component -
            config.weight_fairness * fairness_component -
            soft_penalty_weight * soft_penalty_component
        )
        
        return objective
    
    def _extract_assignments(self, x: Dict, data: OptimizationData) -> List[Dict]:
        """
        Extract assignments from solved model.
        
        Returns:
            List of assignment dictionaries
        """
        print("\nExtracting assignments...")
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

