# Optimal Scheduling - Quick Summary

## What We're Building

An automated shift scheduling system that uses **Mixed Integer Programming (MIP)** to optimally assign employees to shifts based on:

- Employee availability
- Time-off requests
- Work constraints (max hours, rest periods, etc.)
- Fairness (balanced workload)
- Coverage (all roles filled)
- _(Employee preferences removed from MVP - can be added later)_

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
- ✅ Constraint validation
- ✅ Fair workload distribution
- ✅ Time-off integration
- ✅ Multiple optimization strategies
- ⏭️ Preference-based assignment (Future enhancement)

---

## New Entities Needed (3 Total for MVP)

1. **TimeOffRequest** - Vacation/sick leave requests ✅ **COMPLETED**
2. **SystemConstraints** - System-wide work rules (max hours, rest periods) - applies to all employees ✅ **COMPLETED**
3. **SchedulingRun** - Optimization execution tracking (Phase 2)
4. **SchedulingSolution** - Proposed assignments from optimizer (Phase 2)

**Future Enhancement:**

- **EmployeePreferences** - Shift preferences (removed from MVP)
- **OptimizationConfig** - Optimization parameters (removed from MVP - will use hardcoded defaults)

**Note:** Employees are available by default. If they're not available, they request time-off. If they're not assigned to a shift, they're free.

---

## How It Works

```
1. Manager creates weekly schedule with planned shifts
   ↓
2. Employees request time-off (if unavailable)
   ↓
3. Manager triggers optimization
   ↓
4. System builds MIP model:
   - Decision: Assign employee X to shift Y in role Z? (Yes/No)
   - Constraints: Time-off, existing assignments, max hours, rest periods, etc.
   - Objective: Minimize unfairness, maximize coverage
   ↓
5. MIP solver finds optimal solution
   ↓
6. Manager reviews proposed assignments
   ↓
7. Manager applies solution → Creates ShiftAssignments
```

---

## Implementation Phases

### Phase 1: Foundation (13 story points) ✅ **COMPLETED**

- ✅ Add 2 new entities (TimeOff, SystemConstraints)
- ✅ Basic CRUD APIs
- ✅ Database migrations
- _(EmployeePreferences and OptimizationConfig removed from MVP)_

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
- Time-off management UI
- _(Employee preferences UI removed from MVP)_

**Total: 118 story points (MVP)**

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

- **Workload imbalance (fairness)** - Weight: 1.0
- **Coverage gaps** - Weight: 1.0
- _(Preference violations removed from MVP)_
- _(Cost optimization removed - not considered)_

**Default Weights:**
- `weight_fairness = 1.0` - Balance workload evenly across employees
- `weight_coverage = 1.0` - Fill all required roles for all shifts

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

### Use Case 2: Employee Requests Time-Off

1. Employee logs in
2. Requests vacation: Dec 20-27
3. Manager approves request
4. System respects time-off in next optimization
5. _(Preference setting removed from MVP - can be added later)_

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
2. ✅ Create Jira tickets from user stories
3. ✅ **Phase 1: Foundation** - US-1 (Time-Off) and US-3 (System Constraints) **COMPLETED**
4. ⏭️ **Phase 2: Optimization Engine** - US-6 (MIP Model Builder) - **NEXT**
5. ⏭️ Install dependencies (`mip` library) when starting Phase 2
6. ⏭️ Implement Phase 3: APIs
7. ⏭️ Implement Phase 4: Frontend

---

## Questions to Answer Before Implementation

1. **Pay Rates:** Do different roles have different pay rates? _(Note: Cost optimization removed from system - not considered)_
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
- **Workload Fairness:** Variance in hours across employees (lower is better)
- **Coverage:** % of required roles filled (target: 100%)
- **Runtime:** Average optimization time (target: < 60 seconds)
- **User Satisfaction:** Manager/employee feedback
- _(Preference satisfaction metric removed from MVP)_

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
