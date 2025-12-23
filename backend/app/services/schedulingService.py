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

from app.services.optimizationDataBuilder import OptimizationDataBuilder, OptimizationData
from app.services.constraintService import ConstraintService
from app.db.models.optimizationConfigModel import OptimizationConfigModel
from app.db.models.schedulingRunModel import SchedulingRunModel, SchedulingRunStatus, SolverStatus
from app.db.models.schedulingSolutionModel import SchedulingSolutionModel
from app.db.models.shiftAssignmentModel import ShiftAssignmentModel


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
        
        print(f"Creating decision variables ({n_employees} employees × {n_shifts} shifts)...")
        
        # Decision variables: x[i,j,k] = 1 if employee i assigned to shift j in role k
        # For simplicity, we create x[i,j] and assign a concrete role post-optimization.
        # IMPORTANT: only create x[i,j] if employee i is eligible for at least one required role of shift j.
        x = {}
        for i, emp in enumerate(data.employees):
            for j, shift in enumerate(data.shifts):
                if data.availability_matrix[i, j] != 1:
                    continue

                required_roles = shift.get('required_roles') or []
                if not required_roles:
                    continue

                required_role_ids = {rr['role_id'] for rr in required_roles if rr.get('role_id') is not None}
                emp_role_ids = set(emp.get('roles') or [])
                if not required_role_ids.intersection(emp_role_ids):
                    continue

                x[i, j] = model.add_var(var_type=mip.BINARY, name=f'x_{i}_{j}')
        
        print(f"Created {len(x)} decision variables")
        
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
                
                # Sum of employees who have this role and are assigned to this shift
                eligible_employees = []
                for i, emp in enumerate(data.employees):
                    if role_id in emp['roles'] and (i, j) in x:
                        eligible_employees.append(x[i, j])
                
                if eligible_employees:
                    # Use == instead of >= to ensure EXACT coverage, not over-assignment
                    model += mip.xsum(eligible_employees) == required_count, f'coverage_shift_{j}_role_{role_id}'
        
        # CONSTRAINT 2: No overlapping shifts for same employee
        print("Adding no-overlap constraints...")
        overlap_count = 0
        for shift_id, overlapping_ids in data.shift_overlaps.items():
            if not overlapping_ids:
                continue
            
            shift_idx = data.shift_index[shift_id]
            
            for overlapping_id in overlapping_ids:
                overlapping_idx = data.shift_index[overlapping_id]
                
                # For each employee, they can't be assigned to both overlapping shifts
                for i in range(n_employees):
                    if (i, shift_idx) in x and (i, overlapping_idx) in x:
                        model += x[i, shift_idx] + x[i, overlapping_idx] <= 1, f'no_overlap_emp_{i}_shift_{shift_idx}_{overlapping_idx}'
                        overlap_count += 1
        
        print(f"Added {overlap_count} no-overlap constraints")
        
        # CONSTRAINT 3: Fairness - try to distribute shifts evenly
        print("Adding fairness constraints...")
        
        # Calculate average assignments per employee
        total_required_assignments = sum(
            sum(req['required_count'] for req in shift['required_roles'])
            for shift in data.shifts
            if shift['required_roles']
        )
        
        avg_assignments = total_required_assignments / n_employees if n_employees > 0 else 0
        
        # Allow some deviation from average (soft constraint via objective)
        assignments_per_employee = []
        for i in range(n_employees):
            emp_vars = [x[i, j] for j in range(n_shifts) if (i, j) in x]
            if emp_vars:
                assignments_per_employee.append(mip.xsum(emp_vars))
        
        # OBJECTIVE FUNCTION
        print("Building objective function...")
        
        # Component 1: Maximize preference satisfaction
        preference_component = mip.xsum(
            data.preference_scores[i, j] * x[i, j]
            for (i, j) in x
        )
        
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
        
        # Component 3: Coverage (maximize filled shifts)
        coverage_component = mip.xsum(x[i, j] for (i, j) in x)
        
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
            for (i, j), var in x.items():
                if var.x > 0.5:  # Variable is 1 (assigned)
                    emp = data.employees[i]
                    shift = data.shifts[j]
                    
                    # Determine which role to assign
                    # Find a role that the employee has and the shift needs
                    emp_roles = set(emp['roles'])
                    shift_role_ids = [req['role_id'] for req in shift['required_roles']]
                    matching_roles = emp_roles.intersection(shift_role_ids)
                    
                    if matching_roles:
                        role_id = list(matching_roles)[0]  # Pick first matching role
                    else:
                        # Fallback to employee's first role
                        role_id = emp['roles'][0] if emp['roles'] else None
                    
                    if role_id:
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
