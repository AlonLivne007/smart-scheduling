"""
Metrics calculation for scheduling solutions.
"""

from typing import Dict, List
from app.services.optimization_data_services import OptimizationData


def calculate_metrics(data: OptimizationData, assignments: List[Dict]) -> Dict:
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

