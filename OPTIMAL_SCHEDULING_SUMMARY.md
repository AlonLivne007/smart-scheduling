# Optimal Scheduling - Quick Summary

## What We're Building

An automated shift scheduling system that uses **Mixed Integer Programming (MIP)** to optimally assign employees to shifts based on:

- Employee availability
- Time-off requests
- Employee preferences
- Work constraints (max hours, rest periods, etc.)
- Fairness (balanced workload)
- Coverage (all roles filled)

---

## Current System vs. New System

### Current System

- ✅ Manual shift assignment (one-by-one)
- ✅ Basic entities: Users, Roles, Shifts, Assignments
- ❌ No automation
- ❌ No optimization
- ❌ No preference system

### New System (After Implementation)

- ✅ Automated optimization
- ✅ Preference-based assignment
- ✅ Constraint validation
- ✅ Fair workload distribution
- ✅ Time-off integration
- ✅ Multiple optimization strategies

---

## New Entities Needed (6 Total)

1. **TimeOffRequest** - Vacation/sick leave requests
2. **EmployeePreferences** - Shift preferences
3. **SystemConstraints** - System-wide work rules (max hours, rest periods) - applies to all employees
4. **OptimizationConfig** - Optimization parameters
5. **SchedulingRun** - Optimization execution tracking
6. **SchedulingSolution** - Proposed assignments from optimizer

**Note:** Employees are available by default. If they're not available, they request time-off. If they're not assigned to a shift, they're free.

---

## How It Works

```
1. Manager creates weekly schedule with planned shifts
   ↓
2. Employees set preferences, request time-off (if unavailable)
   ↓
3. Manager triggers optimization
   ↓
4. System builds MIP model:
   - Decision: Assign employee X to shift Y in role Z? (Yes/No)
   - Constraints: Time-off, existing assignments, max hours, rest periods, etc.
   - Objective: Minimize unfairness, maximize preferences
   ↓
5. MIP solver finds optimal solution
   ↓
6. Manager reviews proposed assignments
   ↓
7. Manager applies solution → Creates ShiftAssignments
```

---

## Implementation Phases

### Phase 1: Foundation (23 story points)

- Add 4 new entities (TimeOff, Preferences, SystemConstraints, Config)
- Basic CRUD APIs
- Database migrations

### Phase 2: Optimization Engine (42 story points)

- MIP model builder
- Constraint validation
- Solver integration
- Solution storage

### Phase 3: API Integration (29 story points)

- Optimization endpoints
- Apply solution endpoint
- Employee management APIs
- Time-off management APIs

### Phase 4: Frontend (34 story points)

- Optimization UI
- Employee preferences UI
- Time-off management UI

**Total: 136 story points**

---

## Key Technical Decisions

### MIP Solver

- **Library:** Python-MIP (https://python-mip.readthedocs.io/)
- **Solver:** CBC (open-source, included)
- **Why:** Easy integration, good for small-medium problems

### Decision Variables

- `x[i,j,k]` = 1 if employee `i` assigned to shift `j` in role `k`, else 0
- Binary variables (Yes/No decisions)

### Constraints (Hard = Must satisfy)

1. ✅ All required roles filled
2. ✅ No time-off conflicts
3. ✅ Employees have required role qualifications
4. ✅ No overlapping shifts
5. ✅ Minimum rest between shifts (system-wide)
6. ✅ Max consecutive working days (system-wide)
7. ✅ Max hours per week (system-wide)

### Objective Function

Minimize weighted sum of:

- Workload imbalance (fairness)
- Preference violations
- Cost (optional)
- Coverage gaps

---

## Example Use Cases

### Use Case 1: Weekly Optimization

1. Manager creates weekly schedule (Monday-Sunday)
2. System has 20 employees, 50 planned shifts
3. Manager clicks "Optimize Schedule"
4. System runs MIP solver (takes 30 seconds)
5. System proposes assignments for all shifts
6. Manager reviews, adjusts if needed, applies solution
7. All employees get balanced schedules respecting preferences

### Use Case 2: Employee Sets Preferences

1. Employee logs in
2. Goes to "My Preferences"
3. Sets: "Prefer morning shifts, Monday-Friday"
4. Sets: "Available 6am-2pm"
5. Requests vacation: Dec 20-27
6. System uses this in next optimization

### Use Case 3: Constraint Violation

1. Manager triggers optimization
2. System finds no feasible solution
3. System reports: "Employee John cannot work 50 hours (max is 40)"
4. Manager adjusts constraints or shifts
5. Re-runs optimization

---

## Files Created

1. **OPTIMAL_SCHEDULING_ARCHITECTURE.md** - Complete technical architecture
2. **JIRA_USER_STORIES.md** - All 16 user stories with acceptance criteria
3. **ENTITY_RELATIONSHIPS.md** - Entity diagrams and relationships
4. **OPTIMAL_SCHEDULING_SUMMARY.md** - This file (quick overview)

---

## Next Steps

1. ✅ Review architecture documents
2. ✅ Create Jira tickets from user stories (US-1 to US-16)
3. ⏭️ Set up development branch
4. ⏭️ Install dependencies (`mip` library)
5. ⏭️ Start Phase 1: Create new entities
6. ⏭️ Implement Phase 2: Optimization engine
7. ⏭️ Implement Phase 3: APIs
8. ⏭️ Implement Phase 4: Frontend

---

## Questions to Answer Before Implementation

1. **Pay Rates:** Do different roles have different pay rates? (affects cost optimization)
2. **Skill Levels:** Are there seniority levels within roles?
3. **Shift Bidding:** Do employees bid on shifts?
4. **Break Requirements:** Mandatory breaks during shifts?
5. **On-Call:** Are there on-call shifts?
6. **Multi-Location:** Do employees work at multiple locations?
7. **Shift Swapping:** Can employees swap shifts after assignment?

---

## Dependencies to Add

```txt
# Add to requirements.txt
mip>=1.15.0          # MIP solver
numpy>=1.24.0        # Numerical operations (if not already included)
```

---

## Success Metrics

- **Optimization Success Rate:** % of runs finding feasible solutions
- **Preference Satisfaction:** % of assignments matching preferences
- **Workload Fairness:** Variance in hours across employees (lower is better)
- **Coverage:** % of required roles filled (target: 100%)
- **Runtime:** Average optimization time (target: < 60 seconds)
- **User Satisfaction:** Manager/employee feedback

---

## Risk Mitigation

| Risk                 | Mitigation                                         |
| -------------------- | -------------------------------------------------- |
| Solver too slow      | Set time limits, use heuristics for large problems |
| No feasible solution | Relax soft constraints, provide diagnostic info    |
| Missing data         | Default values, validation, user warnings          |
| Too many constraints | Prioritize constraints, allow relaxation           |

---

## Resources

- Python-MIP: https://python-mip.readthedocs.io/
- OR-Tools: https://developers.google.com/optimization
- MIP Tutorial: https://python-mip.readthedocs.io/en/latest/quickstart.html

---

## Support

For questions about the architecture or implementation, refer to:

- `OPTIMAL_SCHEDULING_ARCHITECTURE.md` for detailed technical specs
- `JIRA_USER_STORIES.md` for implementation tasks
- `ENTITY_RELATIONSHIPS.md` for database structure
