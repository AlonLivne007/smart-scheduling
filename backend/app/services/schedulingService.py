"""
Scheduling Service - MIP Solver Integration.

This service builds and solves a Mixed Integer Programming (MIP) model
to find optimal shift assignments that maximize employee preferences
and fairness while satisfying all constraints.
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import mip
import numpy as np

from app.services.optimization_data_services import OptimizationDataBuilder, OptimizationData
from app.services.constraintService import ConstraintService
from app.db.models.optimizationConfigModel import OptimizationConfigModel
from app.db.models.schedulingRunModel import SchedulingRunModel, SchedulingRunStatus, SolverStatus
from app.db.models.schedulingSolutionModel import SchedulingSolutionModel
from app.db.models.shiftAssignmentModel import ShiftAssignmentModel
from app.db.models.systemConstraintsModel import SystemConstraintType


class SchedulingSolution:
    """Result of scheduling optimization."""
    
    def __init__(self):
        self.status: str = "UNKNOWN"  # OPTIMAL, FEASIBLE, INFEASIBLE, NO_SOLUTION_FOUND
        self.objective_value: float = 0.0
        self.runtime_seconds: float = 0.0
        self.mip_gap: float = 0.0
        self.assignments: List[Dict] = []  # List of {user_id, planned_shift_id, role_id}
        self.metrics: Dict = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'status': self.status,
            'objective_value': self.objective_value,
            'runtime_seconds': self.runtime_seconds,
            'mip_gap': self.mip_gap,
            'assignments': self.assignments,
            'metrics': self.metrics
        }


class SchedulingService:
    """Service for solving scheduling optimization problems."""
    
    def __init__(self, db: Session):
        """
        Initialize the scheduling service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.data_builder = OptimizationDataBuilder(db)
        self.constraint_service = ConstraintService(db)
    
    def optimize_schedule(
        self,
        weekly_schedule_id: int,
        config_id: Optional[int] = None
    ) -> Tuple[SchedulingRunModel, SchedulingSolution]:
        """
        Optimize shift assignments for a weekly schedule.
        
        Creates a SchedulingRun record to track the optimization execution,
        runs the MIP solver, and stores the results in the database.
        
        Args:
            weekly_schedule_id: ID of the weekly schedule to optimize
            config_id: Optional ID of optimization configuration to use
        
        Returns:
            Tuple of (SchedulingRunModel, SchedulingSolution)
        """
        # Create SchedulingRun record
        run = SchedulingRunModel(
            weekly_schedule_id=weekly_schedule_id,
            config_id=config_id,
            status=SchedulingRunStatus.PENDING,
            started_at=datetime.now()
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        
        try:
            # Update status to RUNNING
            run.status = SchedulingRunStatus.RUNNING
            self.db.commit()
            
            # Load configuration
            if config_id:
                config = self.db.query(OptimizationConfigModel).filter(
                    OptimizationConfigModel.config_id == config_id
                ).first()
            else:
                config = self.db.query(OptimizationConfigModel).filter(
                    OptimizationConfigModel.is_default == True
                ).first()
            
            if not config:
                raise ValueError("No optimization configuration found")
            
            # Build optimization data
            print(f"Building optimization data for weekly schedule {weekly_schedule_id}...")
            data = self.data_builder.build(weekly_schedule_id)
            
            print(f"Employees: {len(data.employees)}, Shifts: {len(data.shifts)}")
            
            # Build and solve MIP model
            print(f"Building MIP model...")
            solution = self._build_and_solve_mip(data, config)
            
            # Clear existing assignments for this schedule before creating new ones
            print(f"Clearing existing assignments...")
            from app.db.models.plannedShiftModel import PlannedShiftModel
            shift_ids = [ps.planned_shift_id for ps in self.db.query(PlannedShiftModel).filter(
                PlannedShiftModel.weekly_schedule_id == weekly_schedule_id
            ).all()]
            
            if shift_ids:
                self.db.query(ShiftAssignmentModel).filter(
                    ShiftAssignmentModel.planned_shift_id.in_(shift_ids)
                ).delete(synchronize_session=False)
                self.db.commit()
            
            # Update run with results
            run.status = SchedulingRunStatus.COMPLETED
            run.completed_at = datetime.now()
            run.runtime_seconds = solution.runtime_seconds
            run.objective_value = solution.objective_value
            run.mip_gap = solution.mip_gap
            run.total_assignments = len(solution.assignments)
            
            # Map solver status
            status_map = {
                'OPTIMAL': SolverStatus.OPTIMAL,
                'FEASIBLE': SolverStatus.FEASIBLE,
                'INFEASIBLE': SolverStatus.INFEASIBLE,
                'NO_SOLUTION_FOUND': SolverStatus.NO_SOLUTION_FOUND
            }
            run.solver_status = status_map.get(solution.status, SolverStatus.ERROR)
            
            # Store solution assignments and create actual shift assignments
            print(f"Creating {len(solution.assignments)} shift assignments...")
            for assignment in solution.assignments:
                # Store in scheduling_solutions (proposals)
                solution_record = SchedulingSolutionModel(
                    run_id=run.run_id,
                    planned_shift_id=assignment['planned_shift_id'],
                    user_id=assignment['user_id'],
                    role_id=assignment['role_id'],
                    is_selected=True,
                    assignment_score=assignment.get('preference_score')
                )
                self.db.add(solution_record)
                
                # Create actual shift assignment
                shift_assignment = ShiftAssignmentModel(
                    planned_shift_id=assignment['planned_shift_id'],
                    user_id=assignment['user_id'],
                    role_id=assignment['role_id']
                )
                self.db.add(shift_assignment)
            
            self.db.commit()
            self.db.refresh(run)
            
            print(f"\n✅ SchedulingRun {run.run_id} created with {len(solution.assignments)} assignments")
            print(f"✅ Created {len(solution.assignments)} shift assignments in the schedule")
            
            return run, solution
            
        except Exception as e:
            # Update run status to FAILED
            run.status = SchedulingRunStatus.FAILED
            run.completed_at = datetime.now()
            run.error_message = str(e)
            self.db.commit()
            
            print(f"\n❌ Optimization failed: {e}")
            raise
    
    def _execute_optimization_for_run(self, run: SchedulingRunModel):
        """
        Execute optimization for an existing run record (used by async Celery task).
        
        Args:
            run: SchedulingRunModel record (already created with PENDING status)
        """
        try:
            # Update status to RUNNING
            run.status = SchedulingRunStatus.RUNNING
            run.started_at = datetime.now()
            self.db.commit()
            
            # Load configuration
            if run.config_id:
                config = self.db.query(OptimizationConfigModel).filter(
                    OptimizationConfigModel.config_id == run.config_id
                ).first()
            else:
                config = self.db.query(OptimizationConfigModel).filter(
                    OptimizationConfigModel.is_default == True
                ).first()
            
            if not config:
                raise ValueError("No optimization configuration found")
            
            # Build optimization data
            print(f"Building optimization data for weekly schedule {run.weekly_schedule_id}...")
            data = self.data_builder.build(run.weekly_schedule_id)
            
            print(f"Employees: {len(data.employees)}, Shifts: {len(data.shifts)}")
            
            # Build and solve MIP model
            print(f"Building MIP model...")
            solution = self._build_and_solve_mip(data, config)
            
            # Update run with results
            run.status = SchedulingRunStatus.COMPLETED
            run.completed_at = datetime.now()
            run.runtime_seconds = solution.runtime_seconds
            run.objective_value = solution.objective_value
            run.mip_gap = solution.mip_gap
            run.total_assignments = len(solution.assignments)
            run.solutions_count = len(solution.assignments)
            
            # Map solver status
            status_map = {
                'OPTIMAL': SolverStatus.OPTIMAL,
                'FEASIBLE': SolverStatus.FEASIBLE,
                'INFEASIBLE': SolverStatus.INFEASIBLE,
                'NO_SOLUTION_FOUND': SolverStatus.NO_SOLUTION_FOUND
            }
            run.solver_status = status_map.get(solution.status, SolverStatus.ERROR)
            
            # Store solution assignments
            print(f"Storing {len(solution.assignments)} solution records...")
            for assignment in solution.assignments:
                solution_record = SchedulingSolutionModel(
                    run_id=run.run_id,
                    planned_shift_id=assignment['planned_shift_id'],
                    user_id=assignment['user_id'],
                    role_id=assignment['role_id'],
                    is_selected=True,
                    assignment_score=assignment.get('preference_score')
                )
                self.db.add(solution_record)
            
            self.db.commit()
            
            print(f"\n✅ SchedulingRun {run.run_id} completed with {len(solution.assignments)} assignments")
            
        except Exception as e:
            # Update run status to FAILED
            run.status = SchedulingRunStatus.FAILED
            run.completed_at = datetime.now()
            run.error_message = str(e)
            self.db.commit()
            
            print(f"\n❌ Optimization failed: {e}")
            raise
    
    def _build_and_solve_mip(
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
        
        print(f"Creating decision variables ({n_employees} employees × {n_shifts} shifts × roles)...")
        
        # Decision variables: x[i,j,r] = 1 if employee i assigned to shift j in role r
        # Only create x[i,j,r] for eligible triples:
        # - availability_matrix[i,j] == 1
        # - shift.required_roles contains role r
        # - employee has role r
        x = {}
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
                        x[i, j, role_id] = model.add_var(var_type=mip.BINARY, name=f'x_{i}_{j}_{role_id}')
        
        print(f"Created {len(x)} decision variables")
        
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
        
        # CONSTRAINT 1: Each shift must be assigned exactly the required employees for each role
        print("Adding coverage constraints...")
        for j, shift in enumerate(data.shifts):
            required_roles = shift['required_roles']
            
            if not required_roles:
                continue
            
            # For each role required by this shift
            for role_req in required_roles:
                role_id = role_req['role_id']
                required_count = role_req['required_count']
                
                # Sum of employees assigned to this shift in this role: sum_i x[i,j,r]
                eligible_vars = [x[i, j, role_id] for i in range(n_employees) if (i, j, role_id) in x]
                
                if eligible_vars:
                    # Use == to ensure EXACT coverage
                    model += mip.xsum(eligible_vars) == required_count, f'coverage_shift_{j}_role_{role_id}'
                else:
                    # No eligible employees: enforce infeasibility if required_count > 0
                    if required_count > 0:
                        model += 0 == required_count, f'infeasible_coverage_shift_{j}_role_{role_id}'
        
        # CONSTRAINT 2: Single role per employee per shift: sum_r x[i,j,r] <= 1
        print("Adding single-role-per-shift constraints...")
        single_role_count = 0
        for i in range(n_employees):
            for j in range(n_shifts):
                # Get all role_ids for this (i,j) pair
                role_ids_for_ij = {r for (ei, ej, r) in x.keys() if ei == i and ej == j}
                if len(role_ids_for_ij) > 1:
                    role_vars = [x[i, j, r] for r in role_ids_for_ij]
                    model += mip.xsum(role_vars) <= 1, f'single_role_emp_{i}_shift_{j}'
                    single_role_count += 1
        
        print(f"Added {single_role_count} single-role-per-shift constraints")
        
        # CONSTRAINT 3: No overlapping shifts for same employee
        print("Adding no-overlap constraints...")
        overlap_count = 0
        for shift_id, overlapping_ids in data.shift_overlaps.items():
            if not overlapping_ids:
                continue
            
            shift_idx = data.shift_index[shift_id]
            
            for overlapping_id in overlapping_ids:
                overlapping_idx = data.shift_index[overlapping_id]
                
                # For each employee, they can't be assigned to both overlapping shifts in any role
                for i in range(n_employees):
                    # Get all role vars for (i, shift_idx) and (i, overlapping_idx)
                    vars_shift = [x[i, shift_idx, r] for r in set() if (i, shift_idx, r) in x]
                    vars_overlap = [x[i, overlapping_idx, r] for r in set() if (i, overlapping_idx, r) in x]
                    
                    role_ids_shift = {r for (ei, ej, r) in x.keys() if ei == i and ej == shift_idx}
                    role_ids_overlap = {r for (ei, ej, r) in x.keys() if ei == i and ej == overlapping_idx}
                    
                    if role_ids_shift and role_ids_overlap:
                        vars_shift = [x[i, shift_idx, r] for r in role_ids_shift]
                        vars_overlap = [x[i, overlapping_idx, r] for r in role_ids_overlap]
                        # Sum of all assignments to shift_idx + sum of all assignments to overlapping_idx <= 1
                        model += mip.xsum(vars_shift) + mip.xsum(vars_overlap) <= 1, f'no_overlap_emp_{i}_shift_{shift_idx}_{overlapping_idx}'
                        overlap_count += 1
        
        print(f"Added {overlap_count} no-overlap constraints")
        
        # CONSTRAINT 4: System-wide constraints (MAX_SHIFTS_PER_WEEK, MAX_HOURS_PER_WEEK, etc.)
        print("Adding system-wide constraints...")
        
        # Get system constraints
        max_shifts_constraint = data.system_constraints.get(SystemConstraintType.MAX_SHIFTS_PER_WEEK)
        min_shifts_constraint = data.system_constraints.get(SystemConstraintType.MIN_SHIFTS_PER_WEEK)
        max_hours_constraint = data.system_constraints.get(SystemConstraintType.MAX_HOURS_PER_WEEK)
        min_hours_constraint = data.system_constraints.get(SystemConstraintType.MIN_HOURS_PER_WEEK)
        
        system_constraint_count = 0
        
        # Build emp_total for every employee (for shift counting and hours)
        assignments_per_employee = []
        for i in range(n_employees):
            # Get all variables for this employee across all shifts and roles
            emp_vars = [x[ei, ej, r] for (ei, ej, r) in x.keys() if ei == i]
            emp_total = mip.xsum(emp_vars) if emp_vars else 0
            assignments_per_employee.append(emp_total)
            
            # CONSTRAINT 4a: MAX_SHIFTS_PER_WEEK (hard constraint)
            if max_shifts_constraint and max_shifts_constraint[1]:  # (value, is_hard)
                max_shifts = int(max_shifts_constraint[0])
                if emp_vars:
                    model += emp_total <= max_shifts, f'max_shifts_emp_{i}'
                    system_constraint_count += 1
            
            # CONSTRAINT 4b: MIN_SHIFTS_PER_WEEK (only if hard constraint)
            if min_shifts_constraint and min_shifts_constraint[1]:  # (value, is_hard)
                min_shifts = int(min_shifts_constraint[0])
                if emp_vars:
                    model += emp_total >= min_shifts, f'min_shifts_emp_{i}'
                    system_constraint_count += 1
            
            # CONSTRAINT 4c: MAX_HOURS_PER_WEEK (hard constraint)
            if max_hours_constraint and max_hours_constraint[1]:  # (value, is_hard)
                max_hours = float(max_hours_constraint[0])
                if emp_vars:
                    # Calculate total hours for this employee
                    hours_total = mip.xsum(
                        data.shift_durations.get(data.shifts[j]['planned_shift_id'], 0) * x[i, j, r]
                        for (ei, ej, r) in x.keys() if ei == i
                        for j in [ej]  # Get shift index from the variable
                    )
                    model += hours_total <= max_hours, f'max_hours_emp_{i}'
                    system_constraint_count += 1
            
            # CONSTRAINT 4d: MIN_HOURS_PER_WEEK (only if hard constraint)
            if min_hours_constraint and min_hours_constraint[1]:  # (value, is_hard)
                min_hours = float(min_hours_constraint[0])
                if emp_vars:
                    # Calculate total hours for this employee
                    hours_total = mip.xsum(
                        data.shift_durations.get(data.shifts[j]['planned_shift_id'], 0) * x[i, j, r]
                        for (ei, ej, r) in x.keys() if ei == i
                        for j in [ej]  # Get shift index from the variable
                    )
                    model += hours_total >= min_hours, f'min_hours_emp_{i}'
                    system_constraint_count += 1
        
        print(f"Added {system_constraint_count} system constraint checks")
        
        # CONSTRAINT 5: Fairness - try to distribute shifts evenly
        print("Adding fairness constraints...")
        
        # Calculate average assignments per employee
        total_required_assignments = sum(
            sum(req['required_count'] for req in shift['required_roles'])
            for shift in data.shifts
            if shift['required_roles']
        )
        
        avg_assignments = total_required_assignments / n_employees if n_employees > 0 else 0
        
        # OBJECTIVE FUNCTION
        print("Building objective function...")
        
        # Component 1: Maximize preference satisfaction
        # Sum over all (i,j,r) triples: preference_scores[i,j] * x[i,j,r]
        try:
            preference_component = mip.xsum(
                data.preference_scores[i, j] * x[i, j, r]
                for (i, j, r) in x
            )
        except (KeyError, IndexError) as e:
            raise ValueError(
                f"Error building preference component: {e}. "
                f"Matrix shape: {data.preference_scores.shape}, "
                f"Employees: {n_employees}, Shifts: {n_shifts}, "
                f"Variables: {len(x)}"
            ) from e
        
        # Component 2: Fairness (minimize deviation from average)
        # We'll use auxiliary variables for absolute deviation
        fairness_vars = []
        for i, emp_total in enumerate(assignments_per_employee):
            # Deviation from average (can be positive or negative)
            # We'll minimize the sum of deviations
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
        
        # Combine objectives with weights
        # Note: fairness is minimized, so we subtract it
        objective = (
            config.weight_preferences * preference_component +
            config.weight_coverage * coverage_component -
            config.weight_fairness * fairness_component
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
        
        # Map solver status
        if status == mip.OptimizationStatus.OPTIMAL:
            solution.status = "OPTIMAL"
        elif status == mip.OptimizationStatus.FEASIBLE:
            solution.status = "FEASIBLE"
        elif status == mip.OptimizationStatus.INFEASIBLE:
            solution.status = "INFEASIBLE"
        elif status == mip.OptimizationStatus.NO_SOLUTION_FOUND:
            solution.status = "NO_SOLUTION_FOUND"
        else:
            solution.status = "UNKNOWN"
        
        print(f"\nSolver finished: {solution.status}")
        print(f"Runtime: {solution.runtime_seconds:.2f}s")
        
        if status in [mip.OptimizationStatus.OPTIMAL, mip.OptimizationStatus.FEASIBLE]:
            solution.objective_value = model.objective_value
            solution.mip_gap = model.gap
            
            print(f"Objective value: {solution.objective_value:.3f}")
            print(f"MIP gap: {solution.mip_gap:.4f}")
            
            # Extract solution
            print("\nExtracting assignments...")
            assignments = []
            for (i, j, role_id), var in x.items():
                if var.x > 0.5:  # Variable is 1 (assigned)
                    emp = data.employees[i]
                    shift = data.shifts[j]
                    
                    # Role ID comes directly from variable key (i, j, role_id)
                    assignments.append({
                        'user_id': emp['user_id'],
                        'planned_shift_id': shift['planned_shift_id'],
                        'role_id': role_id,
                        'preference_score': float(data.preference_scores[i, j])
                    })
            
            solution.assignments = assignments
            
            # Calculate metrics
            solution.metrics = self._calculate_metrics(data, assignments)
            
            print(f"Total assignments: {len(assignments)}")
            print(f"Average preference score: {solution.metrics.get('avg_preference_score', 0):.3f}")
            print(f"Assignments per employee: min={solution.metrics.get('min_assignments', 0)}, max={solution.metrics.get('max_assignments', 0)}, avg={solution.metrics.get('avg_assignments', 0):.1f}")
        
        return solution
    
    def _calculate_metrics(self, data: OptimizationData, assignments: List[Dict]) -> Dict:
        """Calculate solution metrics."""
        if not assignments:
            return {
                'total_assignments': 0,
                'avg_preference_score': 0.0,
                'min_assignments': 0,
                'max_assignments': 0,
                'avg_assignments': 0.0,
                'shifts_filled': 0,
                'shifts_total': len(data.shifts)
            }
        
        # Preference scores
        pref_scores = [a['preference_score'] for a in assignments]
        avg_pref = sum(pref_scores) / len(pref_scores) if pref_scores else 0.0
        
        # Assignments per employee
        assignments_by_emp = {}
        for assignment in assignments:
            user_id = assignment['user_id']
            assignments_by_emp[user_id] = assignments_by_emp.get(user_id, 0) + 1
        
        if assignments_by_emp:
            min_assignments = min(assignments_by_emp.values())
            max_assignments = max(assignments_by_emp.values())
            avg_assignments = sum(assignments_by_emp.values()) / len(assignments_by_emp)
        else:
            min_assignments = max_assignments = avg_assignments = 0
        
        # Shifts filled
        shifts_with_assignments = len(set(a['planned_shift_id'] for a in assignments))
        
        return {
            'total_assignments': len(assignments),
            'avg_preference_score': avg_pref,
            'min_assignments': min_assignments,
            'max_assignments': max_assignments,
            'avg_assignments': avg_assignments,
            'shifts_filled': shifts_with_assignments,
            'shifts_total': len(data.shifts),
            'employees_assigned': len(assignments_by_emp),
            'employees_total': len(data.employees)
        }
