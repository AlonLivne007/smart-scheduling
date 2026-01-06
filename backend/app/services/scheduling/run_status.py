"""
Status mapping and error message generation for scheduling runs.
"""

import mip
from app.db.models.schedulingRunModel import SolverStatus


def map_solver_status(mip_status: mip.OptimizationStatus) -> str:
    """
    Map MIP solver status to internal string status.
    
    Args:
        mip_status: MIP OptimizationStatus enum
        
    Returns:
        String status: OPTIMAL, FEASIBLE, INFEASIBLE, NO_SOLUTION_FOUND, or UNKNOWN
    """
    if mip_status == mip.OptimizationStatus.OPTIMAL:
        return "OPTIMAL"
    elif mip_status == mip.OptimizationStatus.FEASIBLE:
        return "FEASIBLE"
    elif mip_status == mip.OptimizationStatus.INFEASIBLE:
        return "INFEASIBLE"
    elif mip_status == mip.OptimizationStatus.NO_SOLUTION_FOUND:
        return "NO_SOLUTION_FOUND"
    else:
        return "UNKNOWN"


def map_to_solver_status_enum(status: str) -> SolverStatus:
    """
    Map internal string status to SolverStatus enum.
    
    Args:
        status: Internal string status
        
    Returns:
        SolverStatus enum value
    """
    status_map = {
        'OPTIMAL': SolverStatus.OPTIMAL,
        'FEASIBLE': SolverStatus.FEASIBLE,
        'INFEASIBLE': SolverStatus.INFEASIBLE,
        'NO_SOLUTION_FOUND': SolverStatus.NO_SOLUTION_FOUND
    }
    return status_map.get(status, SolverStatus.ERROR)


def build_error_message(status: str) -> str:
    """
    Build descriptive error message for failed optimization.
    
    Args:
        status: Internal string status (INFEASIBLE or NO_SOLUTION_FOUND)
        
    Returns:
        Descriptive error message
    """
    if status == 'INFEASIBLE':
        return (
            "The optimization problem is infeasible. This means no solution exists that satisfies all constraints. "
            "Possible reasons: insufficient employees, conflicting constraints, or too many required shifts. "
            "Try adjusting constraints, adding more employees, or reducing shift requirements."
        )
    elif status == 'NO_SOLUTION_FOUND':
        return (
            "No solution found within the time limit. The problem may be too complex or infeasible. "
            "Try increasing the maximum runtime or simplifying the constraints."
        )
    else:
        return f"Optimization failed with status: {status}"

