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
            
            # Check if optimization was infeasible or failed
            if solution.status in ['INFEASIBLE', 'NO_SOLUTION_FOUND']:
                # Optimization failed - no feasible solution exists
                run.status = SchedulingRunStatus.FAILED
                run.completed_at = datetime.now()
                run.runtime_seconds = solution.runtime_seconds
                run.total_assignments = 0
                
                # Map solver status
                status_map = {
                    'INFEASIBLE': SolverStatus.INFEASIBLE,
                    'NO_SOLUTION_FOUND': SolverStatus.NO_SOLUTION_FOUND
                }
                run.solver_status = status_map.get(solution.status, SolverStatus.ERROR)
                
                # Set descriptive error message
                if solution.status == 'INFEASIBLE':
                    run.error_message = (
                        "The optimization problem is infeasible. This means no solution exists that satisfies all constraints. "
                        "Possible reasons: insufficient employees, conflicting constraints, or too many required shifts. "
                        "Try adjusting constraints, adding more employees, or reducing shift requirements."
                    )
                else:
                    run.error_message = (
                        "No solution found within the time limit. The problem may be too complex or infeasible. "
                        "Try increasing the maximum runtime or simplifying the constraints."
                    )
                
                self.db.commit()
                self.db.refresh(run)
                
                print(f"\n❌ Optimization failed: {solution.status}")
                print(f"Error message: {run.error_message}")
                
                return run, solution
            
            # Validate solution against HARD constraints BEFORE persisting
            if solution.status in ['OPTIMAL', 'FEASIBLE']:
                print(f"Validating solution against HARD constraints...")
                validation = self.constraint_service.validate_weekly_schedule(
                    weekly_schedule_id,
                    solution.assignments
                )
                
                if not validation.is_valid():
                    # HARD constraints violated - fail the run
                    error_summary = "; ".join([
                        err.message for err in validation.errors[:10]
                    ])
                    if len(validation.errors) > 10:
                        error_summary += f" ... and {len(validation.errors) - 10} more violations"
                    
                    run.status = SchedulingRunStatus.FAILED
                    run.solver_status = SolverStatus.INFEASIBLE
                    run.error_message = f"HARD constraint violations detected: {error_summary}"
                    run.completed_at = datetime.now()
                    self.db.commit()
                    
                    print(f"\n❌ Solution validation failed: {len(validation.errors)} HARD violations")
                    raise ValueError(f"HARD constraint violations: {error_summary}")
                
                print(f"✅ Solution validation passed: {len(validation.errors)} HARD violations, {len(validation.warnings)} warnings")
                if validation.warnings:
                    print(f"  ⚠️  SOFT constraint warnings: {len(validation.warnings)}")
                    for warning in validation.warnings[:5]:
                        print(f"    - {warning.message}")
                    if len(validation.warnings) > 5:
                        print(f"    ... and {len(validation.warnings) - 5} more warnings")
            
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
            
            # Check if optimization was infeasible or failed
            if solution.status in ['INFEASIBLE', 'NO_SOLUTION_FOUND']:
                # Optimization failed - no feasible solution exists
                run.status = SchedulingRunStatus.FAILED
                run.completed_at = datetime.now()
                run.runtime_seconds = solution.runtime_seconds
                run.total_assignments = 0
                run.solutions_count = 0
                
                # Map solver status
                status_map = {
                    'INFEASIBLE': SolverStatus.INFEASIBLE,
                    'NO_SOLUTION_FOUND': SolverStatus.NO_SOLUTION_FOUND
                }
                run.solver_status = status_map.get(solution.status, SolverStatus.ERROR)
                
                # Set descriptive error message
                if solution.status == 'INFEASIBLE':
                    run.error_message = (
                        "The optimization problem is infeasible. This means no solution exists that satisfies all constraints. "
                        "Possible reasons: insufficient employees, conflicting constraints, or too many required shifts. "
                        "Try adjusting constraints, adding more employees, or reducing shift requirements."
                    )
                else:
                    run.error_message = (
                        "No solution found within the time limit. The problem may be too complex or infeasible. "
                        "Try increasing the maximum runtime or simplifying the constraints."
                    )
                
                self.db.commit()
                
                print(f"\n❌ Optimization failed: {solution.status}")
                print(f"Error message: {run.error_message}")
                
                return
            
            # Validate solution against HARD constraints BEFORE persisting
            if solution.status in ['OPTIMAL', 'FEASIBLE']:
                print(f"Validating solution against HARD constraints...")
                validation = self.constraint_service.validate_weekly_schedule(
                    run.weekly_schedule_id,
                    solution.assignments
                )
                
                if not validation.is_valid():
                    # HARD constraints violated - fail the run
                    error_summary = "; ".join([
                        err.message for err in validation.errors[:10]
                    ])
                    if len(validation.errors) > 10:
                        error_summary += f" ... and {len(validation.errors) - 10} more violations"
                    
                    run.status = SchedulingRunStatus.FAILED
                    run.solver_status = SolverStatus.INFEASIBLE
                    run.error_message = f"HARD constraint violations detected: {error_summary}"
                    run.completed_at = datetime.now()
                    self.db.commit()
                    
                    print(f"\n❌ Solution validation failed: {len(validation.errors)} HARD violations")
                    raise ValueError(f"HARD constraint violations: {error_summary}")
                
                print(f"✅ Solution validation passed: {len(validation.errors)} HARD violations, {len(validation.warnings)} warnings")
                if validation.warnings:
                    print(f"  ⚠️  SOFT constraint warnings: {len(validation.warnings)}")
                    for warning in validation.warnings[:5]:
                        print(f"    - {warning.message}")
                    if len(validation.warnings) > 5:
                        print(f"    ... and {len(validation.warnings) - 5} more warnings")
            
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
        
        # Log system constraints
        print("\n📋 System Constraints:")
        for constraint_type, (value, is_hard) in data.system_constraints.items():
            constraint_type_str = constraint_type.value if hasattr(constraint_type, 'value') else str(constraint_type)
            hard_soft = "HARD" if is_hard else "SOFT"
            print(f"  {constraint_type_str}: {value} ({hard_soft})")
        
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
        
        # Log constraint counts before adding HARD constraints
        print(f"\n📊 Constraint Summary (before HARD constraints):")
        print(f"  Decision variables: {len(x)}")
        print(f"  Coverage constraints: {sum(len(shift.get('required_roles', [])) for shift in data.shifts)}")
        print(f"  Single-role constraints: {single_role_count}")
        print(f"  Overlap constraints: {overlap_count}")
        
        # CONSTRAINT 4: HARD system constraints
        print("\nAdding HARD system constraints...")
        
        # 4a. MAX_SHIFTS_PER_WEEK (hard)
        max_shifts_constraint = data.system_constraints.get(SystemConstraintType.MAX_SHIFTS_PER_WEEK)
        max_shifts_count = 0
        if max_shifts_constraint and max_shifts_constraint[1]:  # is_hard
            max_shifts = int(max_shifts_constraint[0])
            for i in range(n_employees):
                emp_vars = [x[ei, ej, r] for (ei, ej, r) in x.keys() if ei == i]
                if emp_vars:
                    model += mip.xsum(emp_vars) <= max_shifts, f'max_shifts_emp_{i}'
                    max_shifts_count += 1
            print(f"  Added {max_shifts_count} MAX_SHIFTS_PER_WEEK constraints (max={max_shifts})")
        
        # 4b. MAX_HOURS_PER_WEEK (hard)
        max_hours_constraint = data.system_constraints.get(SystemConstraintType.MAX_HOURS_PER_WEEK)
        max_hours_count = 0
        if max_hours_constraint and max_hours_constraint[1]:  # is_hard
            max_hours = max_hours_constraint[0]
            for i in range(n_employees):
                # Sum of (x[i,j,r] * shift_duration_hours(j)) for all j, r
                emp_hours_vars = []
                for (ei, ej, r) in x.keys():
                    if ei == i:
                        shift = data.shifts[ej]
                        shift_id = shift['planned_shift_id']
                        shift_duration = data.shift_durations.get(shift_id, 0.0)
                        if shift_duration > 0:
                            emp_hours_vars.append(shift_duration * x[ei, ej, r])
                
                if emp_hours_vars:
                    model += mip.xsum(emp_hours_vars) <= max_hours, f'max_hours_emp_{i}'
                    max_hours_count += 1
            print(f"  Added {max_hours_count} MAX_HOURS_PER_WEEK constraints (max={max_hours})")
        
        # 4c. MIN_REST_HOURS (hard) - using rest conflicts
        min_rest_constraint = data.system_constraints.get(SystemConstraintType.MIN_REST_HOURS)
        rest_conflict_count = 0
        if min_rest_constraint and min_rest_constraint[1]:  # is_hard
            for shift_id, conflicting_ids in data.shift_rest_conflicts.items():
                if not conflicting_ids:
                    continue
                
                shift_idx = data.shift_index[shift_id]
                
                for conflicting_id in conflicting_ids:
                    conflicting_idx = data.shift_index[conflicting_id]
                    
                    # For each employee, they can't be assigned to both conflicting shifts
                    for i in range(n_employees):
                        role_ids_shift = {r for (ei, ej, r) in x.keys() if ei == i and ej == shift_idx}
                        role_ids_conflict = {r for (ei, ej, r) in x.keys() if ei == i and ej == conflicting_idx}
                        
                        if role_ids_shift and role_ids_conflict:
                            vars_shift = [x[i, shift_idx, r] for r in role_ids_shift]
                            vars_conflict = [x[i, conflicting_idx, r] for r in role_ids_conflict]
                            model += mip.xsum(vars_shift) + mip.xsum(vars_conflict) <= 1, f'min_rest_emp_{i}_shift_{shift_idx}_{conflicting_idx}'
                            rest_conflict_count += 1
            print(f"  Added {rest_conflict_count} MIN_REST_HOURS constraints (min={min_rest_constraint[0]})")
        
        # Log final constraint counts
        total_hard_constraints = max_shifts_count + max_hours_count + rest_conflict_count
        print(f"\n📊 Total HARD constraints added: {total_hard_constraints}")
        print(f"  - MAX_SHIFTS_PER_WEEK: {max_shifts_count}")
        print(f"  - MAX_HOURS_PER_WEEK: {max_hours_count}")
        print(f"  - MIN_REST_HOURS: {rest_conflict_count}")
        
        # CONSTRAINT 5: Fairness - try to distribute shifts evenly
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
            # Get all variables for this employee across all shifts and roles
            emp_vars = [x[ei, ej, r] for (ei, ej, r) in x.keys() if ei == i]
            emp_total = mip.xsum(emp_vars) if emp_vars else 0
            assignments_per_employee.append(emp_total)
        
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
        
        # Component 4: SOFT constraint penalties
        # Penalize violations of soft MIN_HOURS_PER_WEEK and MIN_SHIFTS_PER_WEEK
        soft_penalty_component = 0
        soft_penalty_weight = 100.0  # Large weight to strongly discourage violations
        
        # MIN_HOURS_PER_WEEK (soft) - penalty for hours below minimum
        min_hours_constraint = data.system_constraints.get(SystemConstraintType.MIN_HOURS_PER_WEEK)
        if min_hours_constraint and not min_hours_constraint[1]:  # is_soft
            min_hours = min_hours_constraint[0]
            for i in range(n_employees):
                # Calculate total hours for this employee
                emp_hours_vars = []
                for (ei, ej, r) in x.keys():
                    if ei == i:
                        shift = data.shifts[ej]
                        shift_id = shift['planned_shift_id']
                        shift_duration = data.shift_durations.get(shift_id, 0.0)
                        if shift_duration > 0:
                            emp_hours_vars.append(shift_duration * x[ei, ej, r])
                
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
                emp_vars = [x[ei, ej, r] for (ei, ej, r) in x.keys() if ei == i]
                if emp_vars:
                    total_shifts = mip.xsum(emp_vars)
                    # Penalty = max(0, min_shifts - total_shifts)
                    deficit = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'min_shifts_deficit_{i}')
                    model += deficit >= min_shifts - total_shifts
                    soft_penalty_component += deficit
        
        # Combine objectives with weights
        # Note: fairness is minimized, so we subtract it
        # Soft penalties are minimized, so we subtract them
        objective = (
            config.weight_preferences * preference_component +
            config.weight_coverage * coverage_component -
            config.weight_fairness * fairness_component -
            soft_penalty_weight * soft_penalty_component
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
            
            print(f"\n✅ Solver found {solution.status} solution")
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
