# Jira User Stories - Optimal Scheduling Feature

## Epic: Optimal Scheduling with MIP Solver

---

## Phase 1: Foundation - Data Models & Entities

### US-1: Time-Off Request System

**Story:** As an employee, I want to request time off, and as a manager, I want to approve/reject requests.

**Alternative:** As an employee, I want to request time off so that I can plan my vacations and personal days, and as a manager, I want to approve/reject time-off requests so that I can ensure adequate staffing coverage.

**Acceptance Criteria:**

- Employee can create time-off requests (date range, type: vacation/sick/personal)
- Manager can view pending requests
- Manager can approve/reject requests
- System respects approved time-off in optimization
- Employees can view their request status

**Technical:**

- New entity: `TimeOffRequest`
- Fields: user_id, start_date, end_date, request_type, status, approved_by_id
- API: CRUD + approve/reject endpoints
- Status: PENDING, APPROVED, REJECTED

**Estimate:** 8 story points

---

### US-2: Employee Preferences

**Story:** As an employee, I want to set my shift preferences so the optimizer considers them.

**Alternative:** As an employee, I want to set my shift preferences so that the system can assign me to shifts that match my availability and preferences.

**Acceptance Criteria:**

- Employee can set preferred shift templates
- Employee can set preferred days of week
- Employee can set preferred time ranges
- Employee can weight preferences (importance)
- Preferences are used in optimization objective function

**Technical:**

- New entity: `EmployeePreferences`
- Fields: user_id, preferred_shift_template_id, preferred_day_of_week, preferred_start_time, preferred_end_time, preference_weight
- API: GET/POST /api/employees/{id}/preferences

**Estimate:** 5 story points

---

### US-3: Employee Constraints

**Story:** As a manager, I want to set employee constraints so the optimizer respects work rules.

**Alternative:** As a manager, I want to set system-wide work rules so that all employee schedules comply with labor laws and company policies.

**Acceptance Criteria:**

- Manager can set max/min hours per week
- Manager can set max consecutive working days
- Manager can set minimum rest hours between shifts
- Manager can set max/min shifts per week
- Constraints can be hard (must satisfy) or soft (preferred)
- System validates constraints during optimization

**Technical:**

- New entity: `SystemConstraints`
- Fields: constraint_type, constraint_value, is_hard_constraint
- Constraint types: MAX_HOURS, MIN_HOURS, MAX_CONSECUTIVE_DAYS, MIN_REST_HOURS, MAX_SHIFTS, MIN_SHIFTS
- API: GET/POST/PUT/DELETE /api/system/constraints
- No user_id (applies to all employees)

**Estimate:** 5 story points

---

### US-4: Optimization Configuration

**Story:** As a manager, I want to configure optimization parameters so I can prioritize different objectives.

**Alternative:** As a manager, I want to configure optimization parameters so that I can balance fairness, employee preferences, and operational needs when generating schedules.

**Acceptance Criteria:**

- Manager can create optimization configurations
- Manager can set weights for: fairness, preferences, cost, coverage
- Manager can set solver timeout and optimality gap
- System has a default configuration
- Manager can select configuration when optimizing

**Technical:**

- New entity: `OptimizationConfig`
- Fields: config_name, weight_fairness, weight_preferences, weight_cost, weight_coverage, max_runtime_seconds, mip_gap
- API: CRUD endpoints for configs

**Estimate:** 5 story points

---

## Phase 2: Core Optimization Engine

### US-6: MIP Model Builder

**Story:** As a system, I need to build MIP models from schedule data so optimization can run.

**Alternative:** As a manager, I want the system to automatically prepare all scheduling data so that optimization can generate optimal shift assignments efficiently.

**Acceptance Criteria:**

- System extracts eligible employees (active, with roles)
- System extracts planned shifts from weekly schedule
- System builds role requirements matrix
- System builds availability matrix (employee × shift)
- System builds preference scores
- System detects shift overlaps
- System prepares all data for MIP solver

**Technical:**

- New service: `OptimizationDataBuilder`
- Methods: build_employee_set(), build_shift_set(), build_availability_matrix(), build_preference_scores()
- Input: weekly_schedule_id
- Output: Structured data for MIP model

**Estimate:** 13 story points

---

### US-7: Constraint Validation Service

**Story:** As a system, I need to validate constraints so I can check solution feasibility.

**Alternative:** As a manager, I want the system to validate all work rules and constraints so that generated schedules are always compliant and feasible.

**Acceptance Criteria:**

- System validates employee availability
- System validates time-off conflicts
- System validates role qualifications
- System validates shift overlaps
- System validates rest periods between shifts
- System validates consecutive day limits
- System validates weekly hour limits
- System provides detailed validation errors

**Technical:**

- New service: `ConstraintService`
- Methods: check_employee_availability(), check_time_off_conflicts(), validate_hard_constraints()
- Returns validation results with error details

**Estimate:** 8 story points

---

### US-8: MIP Solver Integration

**Story:** As a system, I need to solve MIP models so I can generate optimal schedules.

**Alternative:** As a manager, I want the system to automatically find the best possible schedule assignments so that I can ensure fair workload distribution and employee satisfaction.

**Acceptance Criteria:**

- System creates MIP decision variables (x[i,j,k])
- System adds all hard constraints
- System defines objective function with soft constraints
- System runs Python-MIP solver
- System handles solver status (OPTIMAL, FEASIBLE, INFEASIBLE)
- System stores solver results and runtime
- System handles solver timeouts gracefully

**Technical:**

- New service: `SchedulingService`
- Dependencies: `mip` library
- Methods: build_mip_model(), solve_mip_model()
- Error handling for infeasible problems

**Estimate:** 13 story points

---

### US-9: Solution Storage & Tracking

**Story:** As a system, I need to store optimization runs and solutions so users can review them.

**Alternative:** As a manager, I want the system to save all optimization results so that I can review, compare, and apply the best schedule solutions.

**Acceptance Criteria:**

- System creates SchedulingRun record when optimization starts
- System updates run status (PENDING → RUNNING → COMPLETED/FAILED)
- System stores solver metrics (objective value, runtime, status)
- System stores proposed assignments in SchedulingSolution
- System tracks which assignments optimizer selected
- Users can view optimization history

**Technical:**

- New entities: `SchedulingRun`, `SchedulingSolution`
- SchedulingRun: tracks run metadata, status, solver results
- SchedulingSolution: stores proposed assignments (user, shift, role)
- API: GET /api/scheduling/runs/{id}

**Estimate:** 8 story points

---

## Phase 3: API & Integration

### US-10: Optimization API Endpoints

**Story:** As a manager, I want to trigger optimization via API so I can generate schedules automatically.

**Alternative:** As a manager, I want to trigger schedule optimization via API so that I can automatically generate optimal shift assignments for my team.

**Acceptance Criteria:**

- POST /api/scheduling/optimize triggers optimization
- Request includes weekly_schedule_id and optional config_id
- Returns SchedulingRun object with run_id
- GET /api/scheduling/runs/{id} returns run status and results
- GET /api/scheduling/runs returns list of all runs
- API handles errors gracefully

**Technical:**

- New routes: `/api/scheduling/optimize`, `/api/scheduling/runs`
- Controller: `schedulingController.py`
- Async processing (optimization runs in background)
- Returns immediately with run_id, status updates via polling

**Estimate:** 8 story points

---

### US-11: Apply Solution to Assignments

**Story:** As a manager, I want to apply an optimization solution so assignments are created in the system.

**Alternative:** As a manager, I want to apply an optimization solution so that the proposed schedule assignments become active and employees are notified of their shifts.

**Acceptance Criteria:**

- POST /api/scheduling/runs/{id}/apply creates ShiftAssignments from solution
- Request includes solution_id
- Option to overwrite existing assignments or merge
- System validates solution before applying
- System updates PlannedShift status to FULLY_ASSIGNED
- Returns list of created assignments

**Technical:**

- Endpoint: POST /api/scheduling/runs/{id}/apply
- Creates ShiftAssignment records from SchedulingSolution
- Updates PlannedShift.status
- Transaction handling for rollback on errors

**Estimate:** 5 story points

---

### US-12: Employee Management API

**Story:** As an employee/manager, I want to manage preferences, availability, and constraints via API.

**Alternative:** As an employee, I want to manage my preferences via API so that I can update my shift preferences programmatically, and as a manager, I want to manage system constraints via API so that I can configure work rules programmatically.

**Acceptance Criteria:**

- GET/POST /api/employees/{id}/availability
- GET/POST /api/employees/{id}/preferences
- GET/POST /api/employees/{id}/constraints
- All endpoints support CRUD operations
- Proper validation and error handling
- Authentication/authorization (employees can only edit their own)

**Technical:**

- New routes: `/api/employees/{id}/availability`, `/api/employees/{id}/preferences`, `/api/employees/{id}/constraints`
- Controllers: `employeeAvailabilityController`, `employeePreferencesController`, `employeeConstraintsController`
- Authorization middleware

**Estimate:** 8 story points

---

### US-13: Time-Off Management API

**Story:** As an employee/manager, I want to manage time-off requests via API.

**Alternative:** As an employee, I want to manage my time-off requests via API so that I can submit and track requests programmatically, and as a manager, I want to approve/reject time-off requests via API so that I can manage approvals efficiently.

**Acceptance Criteria:**

- GET /api/time-off/requests (list all, filtered by user/status)
- POST /api/time-off/requests (create request)
- PUT /api/time-off/requests/{id}/approve (manager only)
- PUT /api/time-off/requests/{id}/reject (manager only)
- GET /api/time-off/requests/{id} (get single request)
- Proper validation and authorization

**Technical:**

- New routes: `/api/time-off/requests`
- Controller: `timeOffController.py`
- Authorization: employees can create/view own, managers can approve/reject

**Estimate:** 8 story points

---

## Phase 4: Frontend Integration

### US-14: Optimization UI

**Story:** As a manager, I want to trigger and view optimization results in the UI.

**Alternative:** As a manager, I want to trigger and view optimization results in the UI so that I can easily generate and review optimal schedules without using technical APIs.

**Acceptance Criteria:**

- Button to trigger optimization for a weekly schedule
- View optimization run status (pending, running, completed, failed)
- View optimization metrics (objective value, runtime, solver status)
- View proposed assignments in solution
- Button to apply solution
- Ability to compare multiple solutions
- Progress indicator for running optimizations

**Technical:**

- New page/component: `OptimizationPage.jsx` or `ScheduleOptimization.jsx`
- API integration with scheduling endpoints
- Real-time status updates (polling or websocket)
- Table/list view of solutions

**Estimate:** 13 story points

---

### US-14: Employee Preferences UI

**Story:** As an employee, I want to set my preferences and constraints in the UI.

**Alternative:** As an employee, I want to set my preferences in the UI so that I can easily communicate my shift preferences and request time off through a user-friendly interface.

**Acceptance Criteria:**

- Form to set shift preferences
- Form to view/edit constraints (if allowed)
- Time-off request form
- View time-off request status

**Technical:**

- New page: `EmployeeSettingsPage.jsx` or `MyPreferencesPage.jsx`
- Components: `PreferencesForm`, `TimeOffRequestForm`
- API integration with employee management endpoints

**Estimate:** 13 story points

---

### US-16: Time-Off Management UI (Manager)

**Story:** As a manager, I want to approve/reject time-off requests in the UI.

**Alternative:** As a manager, I want to approve/reject time-off requests in the UI so that I can efficiently review and manage employee time-off requests with full visibility of the schedule impact.

**Acceptance Criteria:**

- List view of all time-off requests
- Filter by status (pending, approved, rejected)
- Filter by employee
- Calendar view showing time-off periods
- Approve/reject buttons with comments
- Notification when new requests arrive

**Technical:**

- New page: `TimeOffManagementPage.jsx`
- Components: `TimeOffRequestList`, `TimeOffRequestCard`, `TimeOffCalendar`
- API integration with time-off endpoints
- Real-time updates

**Estimate:** 8 story points

---

## Summary

### Total Story Points by Phase:

- **Phase 1 (Foundation):** 23 points
- **Phase 2 (Optimization Engine):** 42 points
- **Phase 3 (API):** 29 points
- **Phase 4 (Frontend):** 34 points
- **Total:** 128 story points

### Dependencies:

- Phase 1 must complete before Phase 2
- Phase 2 must complete before Phase 3
- Phase 3 must complete before Phase 4
- US-6, US-7, US-8 can be worked on in parallel after US-1 to US-5

### Priority Order:

1. US-1, US-2, US-3, US-4 (Foundation)
2. US-5, US-6, US-7, US-8 (Core Engine)
3. US-9, US-10, US-11, US-12 (API)
4. US-13, US-14, US-15 (Frontend)

---

## Additional Considerations

### Technical Debt:

- Consider adding indexes on new tables for performance
- Consider caching optimization results
- Consider background job queue for long-running optimizations

### Future Enhancements (Not in MVP):

- Incremental optimization (preserve existing assignments)
- Multi-objective optimization dashboard
- Optimization analytics and reporting
- Automated weekly optimization
- Shift swapping functionality
- Mobile app for employee preferences
