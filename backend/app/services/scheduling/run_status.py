"""
Status mapping and error message generation for scheduling runs.

This module provides centralized error message generation to ensure:
- Clear, actionable messages for users
- No duplicate messages
- Specific information about failure causes
- Guidance on how to fix issues
"""

import mip
import re
from typing import Optional, Dict, Any
from app.data.models.scheduling_run_model import SolverStatus


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


def _extract_error_details(error_message: str) -> Dict[str, Any]:
    """
    Extract specific error details from exception message.
    
    Args:
        error_message: Exception message string
        
    Returns:
        Dict with extracted details: error_type, shift_id, role_id, etc.
    """
    details = {
        'error_type': 'UNKNOWN',
        'shift_id': None,
        'role_id': None,
        'required_count': None,
        'message': error_message
    }
    
    # Check for coverage/infeasible coverage errors
    if 'Infeasible coverage' in error_message or 'no eligible employees' in error_message.lower():
        details['error_type'] = 'INSUFFICIENT_EMPLOYEES'
        
        # Extract shift_id
        shift_match = re.search(r'planned_shift_id[=:](\d+)', error_message)
        if shift_match:
            details['shift_id'] = int(shift_match.group(1))
        
        # Extract role_id
        role_match = re.search(r'role_id[=:](\d+)', error_message)
        if role_match:
            details['role_id'] = int(role_match.group(1))
        
        # Extract required count
        count_match = re.search(r'count[=:](\d+)', error_message)
        if count_match:
            details['required_count'] = int(count_match.group(1))
    
    # Check for no employees found
    elif 'No eligible employees found' in error_message:
        details['error_type'] = 'NO_EMPLOYEES'
    
    # Check for no shifts found
    elif 'No planned shifts found' in error_message:
        details['error_type'] = 'NO_SHIFTS'
    
    # Check for config errors
    elif 'optimization config' in error_message.lower() or 'configuration' in error_message.lower():
        details['error_type'] = 'CONFIG_ERROR'
    
    return details


def build_error_message(
    status: str,
    original_error: Optional[Exception] = None,
    constraint_info: Optional[Dict[str, Any]] = None
) -> str:
    """
    Build descriptive, actionable error message for failed optimization.
    
    This is the CENTRALIZED error message generator. All error messages
    should go through this function to ensure consistency and avoid duplicates.
    
    Args:
        status: Internal string status (INFEASIBLE, NO_SOLUTION_FOUND, etc.)
        original_error: Optional original exception that caused the failure
        constraint_info: Optional dict with constraint information to identify problematic constraints
        
    Returns:
        Descriptive, actionable error message with specific guidance
    """
    # First, try to extract details from original error if provided
    error_details = None
    if original_error:
        error_details = _extract_error_details(str(original_error))
    
    # Build base message based on status
    if status == 'INFEASIBLE':
        # Check for specific error types
        if error_details and error_details['error_type'] == 'INSUFFICIENT_EMPLOYEES':
            shift_info = f" for shift ID {error_details['shift_id']}" if error_details['shift_id'] else ""
            role_info = f" role ID {error_details['role_id']}" if error_details['role_id'] else ""
            count_info = f" ({error_details['required_count']} required)" if error_details['required_count'] else ""
            
            return (
                f"Optimization failed: Insufficient employees available{shift_info}{role_info}{count_info}.\n\n"
                f"Root cause: No employees with the required role are available for this shift.\n\n"
                f"Recommended actions:\n"
                f"• Add employees with the required role\n"
                f"• Check employee availability for this shift\n"
                f"• Review time-off requests that may block availability\n"
                f"• No need to modify constraints - the issue is insufficient available employees"
            )
        
        elif error_details and error_details['error_type'] == 'NO_EMPLOYEES':
            return (
                f"Optimization failed: No eligible employees found.\n\n"
                f"Root cause: No employees exist in the system or no employees have the required roles.\n\n"
                f"Recommended actions:\n"
                f"• Add employees to the system\n"
                f"• Ensure employees have appropriate roles assigned\n"
                f"• Verify employees are active in the system"
            )
        
        elif error_details and error_details['error_type'] == 'NO_SHIFTS':
            return (
                f"Optimization failed: No planned shifts found.\n\n"
                f"Root cause: No shifts are planned in the weekly schedule.\n\n"
                f"Recommended actions:\n"
                f"• Add shifts to the weekly schedule\n"
                f"• Ensure shifts are configured with required roles"
            )
        
        else:
            # Generic infeasible message - be specific and concise with feasibility analysis
            if constraint_info:
                # Build list of only the hard constraints that exist
                hard_constraints = []
                
                if constraint_info.get('has_hard_max_hours'):
                    value = constraint_info.get('max_hours_value', '?')
                    hard_constraints.append(f"MAX_HOURS_PER_WEEK = {value} hours")
                
                if constraint_info.get('has_hard_max_shifts'):
                    value = constraint_info.get('max_shifts_value', '?')
                    hard_constraints.append(f"MAX_SHIFTS_PER_WEEK = {value}")
                
                if constraint_info.get('has_hard_min_rest'):
                    value = constraint_info.get('min_rest_value', '?')
                    hard_constraints.append(f"MIN_REST_HOURS = {value} hours")
                
                if constraint_info.get('has_hard_max_consecutive'):
                    value = constraint_info.get('max_consecutive_value', '?')
                    hard_constraints.append(f"MAX_CONSECUTIVE_DAYS = {value}")
                
                if constraint_info.get('has_hard_min_hours'):
                    value = constraint_info.get('min_hours_value', '?')
                    hard_constraints.append(f"MIN_HOURS_PER_WEEK = {value} hours")
                
                if constraint_info.get('has_hard_min_shifts'):
                    value = constraint_info.get('min_shifts_value', '?')
                    hard_constraints.append(f"MIN_SHIFTS_PER_WEEK = {value}")
                
                if hard_constraints:
                    # Add feasibility analysis if available
                    feasibility_msg = ""
                    
                    if constraint_info.get('has_hard_max_hours'):
                        required = constraint_info.get('total_required_hours', 0)
                        max_possible = constraint_info.get('max_possible_hours', 0)
                        n_emp = constraint_info.get('n_employees', 0)
                        if max_possible > 0 and required > max_possible:
                            feasibility_msg = (
                                f"\n\nRequired: {required:.1f} hours, "
                                f"Maximum possible: {max_possible:.1f} hours ({n_emp} employees × {constraint_info.get('max_hours_value')} hours)"
                            )
                    
                    if constraint_info.get('has_hard_max_shifts'):
                        required = constraint_info.get('total_required_shifts', 0)
                        max_possible = constraint_info.get('max_possible_shifts', 0)
                        n_emp = constraint_info.get('n_employees', 0)
                        if max_possible > 0 and required > max_possible:
                            if feasibility_msg:
                                feasibility_msg += f"\nRequired: {required} shifts, Maximum possible: {max_possible} shifts ({n_emp} employees × {constraint_info.get('max_shifts_value')} shifts)"
                            else:
                                feasibility_msg = (
                                    f"\n\nRequired: {required} shifts, "
                                    f"Maximum possible: {max_possible} shifts ({n_emp} employees × {constraint_info.get('max_shifts_value')} shifts)"
                                )
                    
                    # If only one constraint, be very specific
                    if len(hard_constraints) == 1:
                        return (
                            f"Optimization failed: Hard constraint is too restrictive.\n\n"
                            f"Constraint: {hard_constraints[0]}{feasibility_msg}\n\n"
                            f"Solution: Convert to soft constraint or increase the limit."
                        )
                    else:
                        # Multiple constraints - list them concisely
                        constraints_list = "\n".join(f"• {c}" for c in hard_constraints)
                        return (
                            f"Optimization failed: Hard constraints are too restrictive.\n\n"
                            f"Constraints:\n{constraints_list}{feasibility_msg}\n\n"
                            f"Solution: Convert to soft constraints or relax the limits."
                        )
            
            # No constraint info available - minimal message
            return (
                f"Optimization failed: Problem is infeasible.\n\n"
                f"Check hard constraints or add more employees."
            )
    
    elif status == 'NO_SOLUTION_FOUND':
        return (
            f"Optimization failed: No solution found within time limit.\n\n"
            f"Root cause: The problem is too complex or potentially infeasible.\n\n"
            f"Recommended actions:\n"
            f"• Increase the maximum runtime in optimization settings\n"
            f"• Simplify constraints (convert hard constraints to soft constraints)\n"
            f"• Reduce the number of shifts or employees\n"
            f"• Check if the problem is actually infeasible (INFEASIBLE) - try relaxing constraints"
        )
    
    else:
        # For other error types, use original error message if available
        if original_error:
            error_str = str(original_error)
            # If it's a specific error we recognize, format it nicely
            if error_details and error_details['error_type'] != 'UNKNOWN':
                return build_error_message(error_details['error_type'], original_error)
            return f"Optimization error: {error_str}"
        
        return f"Optimization failed with status: {status}"


def build_diagnostic_info(
    status: str,
    original_error: Optional[Exception] = None,
    data_summary: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build diagnostic information to help users understand failures.
    
    Args:
        status: Solver status
        original_error: Original exception
        data_summary: Optional summary of optimization data (employee count, shift count, etc.)
        
    Returns:
        Dict with diagnostic information
    """
    diagnostic = {
        'status': status,
        'error_type': 'UNKNOWN',
        'recommendations': []
    }
    
    if original_error:
        error_details = _extract_error_details(str(original_error))
        diagnostic['error_type'] = error_details['error_type']
        diagnostic['original_error'] = str(original_error)
        
        if error_details['shift_id']:
            diagnostic['problematic_shift_id'] = error_details['shift_id']
        if error_details['role_id']:
            diagnostic['problematic_role_id'] = error_details['role_id']
    
    # Add data summary if available
    if data_summary:
        diagnostic['data_summary'] = data_summary
        diagnostic['recommendations'] = _generate_recommendations(status, diagnostic, data_summary)
    
    return diagnostic


def _generate_recommendations(
    status: str,
    diagnostic: Dict[str, Any],
    data_summary: Dict[str, Any]
) -> list:
    """Generate specific recommendations based on diagnostic info."""
    recommendations = []
    
    if diagnostic['error_type'] == 'INSUFFICIENT_EMPLOYEES':
        recommendations.append({
            'priority': 'HIGH',
            'action': 'ADD_EMPLOYEES',
            'message': 'Add employees with the required role or check availability of existing employees'
        })
    elif diagnostic['error_type'] == 'NO_EMPLOYEES':
        recommendations.append({
            'priority': 'CRITICAL',
            'action': 'ADD_EMPLOYEES',
            'message': 'Add employees to the system'
        })
    elif status == 'INFEASIBLE':
        if data_summary.get('employee_count', 0) < data_summary.get('required_positions', 0):
            recommendations.append({
                'priority': 'HIGH',
                'action': 'ADD_EMPLOYEES',
                'message': f'Required {data_summary.get("required_positions", 0)} positions but only {data_summary.get("employee_count", 0)} employees available'
            })
        else:
            recommendations.append({
                'priority': 'MEDIUM',
                'action': 'RELAX_CONSTRAINTS',
                'message': 'Hard constraints are too restrictive - try converting hard constraints to soft or relaxing their values'
            })
    
    return recommendations

