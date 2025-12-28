# Backend User Stories - Optimal Scheduling Feature

> **Priority Legend:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low

---

## PHASE 1: FOUNDATION - DATA MODELS & ENTITIES 🔴

### US-1: Time-Off Request System ✅
**Priority:** 🟠 High  
**Story Points:** 8  
**As an** employee  
**I want to** request time off  
**So that** I can plan my vacations and personal days  

**As a** manager  
**I want to** approve/reject time-off requests  
**So that** I can ensure adequate staffing coverage  

**Acceptance Criteria:**
- [x] Employee can create time-off requests (date range, type: vacation/sick/personal)
- [x] Manager can view pending requests
- [x] Manager can approve/reject requests
- [x] System respects approved time-off in optimization
- [x] Employees can view their request status

**Technical Notes:**
- Entity: `TimeOffRequest`
- Fields: user_id, start_date, end_date, request_type, status, approved_by_id
- API: CRUD + approve/reject endpoints
- Status: PENDING, APPROVED, REJECTED

---

### US-2: Employee Preferences ✅
**Priority:** 🟠 High  
**Story Points:** 5  
**As an** employee  
**I want to** set my shift preferences  
**So that** the system can assign me to shifts that match my availability and preferences  

**Acceptance Criteria:**
- [x] Employee can set preferred shift templates
- [x] Employee can set preferred days of week
- [x] Employee can set preferred time ranges
- [x] Employee can weight preferences (importance)
- [x] Preferences are used in optimization objective function

**Technical Notes:**
- Entity: `EmployeePreferences`
- Fields: user_id, preferred_shift_template_id, preferred_day_of_week, preferred_start_time, preferred_end_time, preference_weight
- API: GET/POST /api/employees/{id}/preferences

---

### US-3: System Constraints ✅
**Priority:** 🟠 High  
**Story Points:** 5  
**As a** manager  
**I want to** set system-wide work rules  
**So that** all employee schedules comply with labor laws and company policies  

**Acceptance Criteria:**
- [x] Manager can set max/min hours per week
- [x] Manager can set max consecutive working days
- [x] Manager can set minimum rest hours between shifts
- [x] Manager can set max/min shifts per week
- [x] Constraints can be hard (must satisfy) or soft (preferred)
- [x] System validates constraints during optimization

**Technical Notes:**
- Entity: `SystemConstraints`
- Fields: constraint_type, constraint_value, is_hard_constraint
- Constraint types: MAX_HOURS, MIN_HOURS, MAX_CONSECUTIVE_DAYS, MIN_REST_HOURS, MAX_SHIFTS, MIN_SHIFTS
- API: GET/POST/PUT/DELETE /api/system/constraints
- No user_id (applies to all employees)

---

### US-4: Optimization Configuration ✅
**Priority:** 🔴 Critical  
**Story Points:** 5  
**As a** manager  
**I want to** configure optimization parameters  
**So that** I can balance fairness, employee preferences, and operational needs when generating schedules  

**Acceptance Criteria:**
- [x] Manager can create optimization configurations
- [x] Manager can set weights for: fairness, preferences, cost, coverage
- [x] Manager can set solver timeout and optimality gap
- [x] System has a default configuration
- [x] Manager can select configuration when optimizing

**Technical Notes:**
- Entity: `OptimizationConfig`
- Fields: config_name, weight_fairness, weight_preferences, weight_cost, weight_coverage, max_runtime_seconds, mip_gap
- API: CRUD endpoints for configs
- Database tables created and verified
- Full CRUD API implemented and tested

---

## PHASE 2: CORE OPTIMIZATION ENGINE 🔴

### US-6: MIP Model Builder ✅
**Priority:** 🔴 Critical  
**Story Points:** 13  
**As a** manager  
**I want the** system to automatically prepare all scheduling data  
**So that** optimization can generate optimal shift assignments efficiently  

**Acceptance Criteria:**
- [x] System extracts eligible employees (active, with roles)
- [x] System extracts planned shifts from weekly schedule
- [x] System builds role requirements matrix
- [x] System builds availability matrix (employee × shift)
- [x] System builds preference scores
- [x] System detects shift overlaps
- [x] System prepares all data for MIP solver

**Technical Notes:**
- Service: `OptimizationDataBuilder` ✅
- Methods: build_employee_set(), build_shift_set(), build_availability_matrix(), build_preference_scores()
- Input: weekly_schedule_id
- Output: Structured data for MIP model
- Tested with 4 employees × 21 shifts (84 total assignments)
- Availability matrix: 75% available assignments
- Preference scores: avg 0.549, uses employee preferences and time overlaps

---

### US-7: Constraint Validation Service ✅
**Priority:** 🔴 Critical  
**Story Points:** 8  
**As a** manager  
**I want the** system to validate all work rules and constraints  
**So that** generated schedules are always compliant and feasible  

**Acceptance Criteria:**
- [x] System validates employee availability
- [x] System validates time-off conflicts
- [x] System validates role qualifications
- [x] System validates shift overlaps
- [x] System validates rest periods between shifts
- [x] System validates consecutive day limits
- [x] System validates weekly hour limits
- [x] System provides detailed validation errors

**Technical Notes:**
- Service: `ConstraintService` ✅
- Methods: validate_assignment(), validate_weekly_schedule(), check_employee_availability(), check_time_off_conflicts(), validate_hard_constraints()
- Returns ValidationResult with error details and severity (HARD/SOFT)
- Supports both individual assignment and full weekly schedule validation
- Tested with role qualifications, time-off, and weekly limits

---

### US-8: MIP Solver Integration ✅
**Priority:** 🔴 Critical  
**Story Points:** 13  
**As a** manager  
**I want the** system to automatically find the best possible schedule assignments  
**So that** I can ensure fair workload distribution and employee satisfaction  

**Acceptance Criteria:**
- [x] System creates MIP decision variables (x[i,j,k])
- [x] System adds all hard constraints
- [x] System defines objective function with soft constraints
- [x] System runs Python-MIP solver
- [x] System handles solver status (OPTIMAL, FEASIBLE, INFEASIBLE)
- [x] System stores solver results and runtime
- [x] System handles solver timeouts gracefully

**Implementation:**
- ✅ Created `SchedulingService` with MIP model builder
- ✅ Binary decision variables: x[i,j] for employee i assigned to shift j
- ✅ Coverage constraints: each shift-role filled exactly once
- ✅ No-overlap constraints: no conflicting assignments
- ✅ Fairness constraints: balanced workload distribution
- ✅ Multi-objective function: 0.6×preferences + 0.15×coverage - 0.2×fairness_deviation
- ✅ CBC solver integration with timeout and gap settings
- ✅ Test results: OPTIMAL solution in 0.09s, 100% coverage, 63 assignments

**Technical Notes:**
- Service: `SchedulingService`
- Dependencies: `mip` library v1.15.0 (installed ✅)
- Methods: optimize_schedule(), _build_and_solve_mip()
- Error handling for infeasible problems
- Returns SchedulingSolution with assignments and metrics

---

### US-9: Solution Storage & Tracking ✅
**Priority:** 🟠 High  
**Story Points:** 8  
**As a** manager  
**I want the** system to save all optimization results  
**So that** I can review, compare, and apply the best schedule solutions  

**Acceptance Criteria:**
- [x] System creates SchedulingRun record when optimization starts
- [x] System updates run status (PENDING → RUNNING → COMPLETED/FAILED)
- [x] System stores solver metrics (objective value, runtime, status)
- [x] System stores proposed assignments in SchedulingSolution
- [x] System tracks which assignments optimizer selected
- [x] Users can view optimization history

**Implementation:**
- ✅ Updated `SchedulingService.optimize_schedule()` to return (run, solution) tuple
- ✅ Creates SchedulingRun with status tracking (PENDING → RUNNING → COMPLETED)
- ✅ Stores solver metrics: runtime, objective value, MIP gap, total assignments
- ✅ Maps solver status to SolverStatus enum (OPTIMAL, FEASIBLE, INFEASIBLE)
- ✅ Creates SchedulingSolution records for all assignments with preference scores
- ✅ Error handling with FAILED status and error message storage
- ✅ Test results: Run ID 11, 516 solutions stored, 0.39s runtime

**Test Results (Comprehensive Dataset):**
- 27 employees, 76 shifts, 3 time-off requests
- Status: OPTIMAL
- Runtime: 0.39 seconds
- Assignments: 516 (avg 20.64 per employee)
- Coverage: 100% (76/76 shifts filled)
- Avg preference score: 0.73
- Database: All solutions persisted correctly

**Technical Notes:**
- Entities: `SchedulingRun`, `SchedulingSolution` (tables created ✅)
- SchedulingRun: tracks run metadata, status, solver results
- SchedulingSolution: stores proposed assignments (user, shift, role)
- API: GET /api/scheduling/runs/{id}

---

## PHASE 3: API & INTEGRATION 🟠

### US-10: Optimization API Endpoints
**Priority:** 🔴 Critical  
**Story Points:** 8  
**As a** manager  
**I want to** trigger schedule optimization via API  
**So that** I can automatically generate optimal shift assignments for my team  

**Acceptance Criteria:**
- [ ] POST /api/scheduling/optimize triggers optimization
- [ ] Request includes weekly_schedule_id and optional config_id
- [ ] Returns SchedulingRun object with run_id
- [ ] GET /api/scheduling/runs/{id} returns run status and results
- [ ] GET /api/scheduling/runs returns list of all runs
- [ ] API handles errors gracefully

**Technical Notes:**
- Routes: `/api/scheduling/optimize`, `/api/scheduling/runs`
- Controller: `schedulingController.py`
- Async processing (optimization runs in background)
- Returns immediately with run_id, status updates via polling

---

### US-11: Apply Solution to Assignments
**Priority:** 🟠 High  
**Story Points:** 5  
**As a** manager  
**I want to** apply an optimization solution  
**So that** the proposed schedule assignments become active and employees are notified of their shifts  

**Acceptance Criteria:**
- [ ] POST /api/scheduling/runs/{id}/apply creates ShiftAssignments from solution
- [ ] Request includes solution_id
- [ ] Option to overwrite existing assignments or merge
- [ ] System validates solution before applying
- [ ] System updates PlannedShift status to FULLY_ASSIGNED
- [ ] Returns list of created assignments

**Technical Notes:**
- Endpoint: POST /api/scheduling/runs/{id}/apply
- Creates ShiftAssignment records from SchedulingSolution
- Updates PlannedShift.status
- Transaction handling for rollback on errors

---

### US-12: Employee Management API
**Priority:** 🟡 Medium  
**Story Points:** 8  
**As an** employee  
**I want to** manage my preferences via API  
**So that** I can update my shift preferences programmatically  

**As a** manager  
**I want to** manage system constraints via API  
**So that** I can configure work rules programmatically  

**Acceptance Criteria:**
- [ ] GET/POST /api/employees/{id}/availability
- [ ] GET/POST /api/employees/{id}/preferences
- [ ] GET/POST /api/employees/{id}/constraints
- [ ] All endpoints support CRUD operations
- [ ] Proper validation and error handling
- [ ] Authentication/authorization (employees can only edit their own)

**Technical Notes:**
- Routes: `/api/employees/{id}/availability`, `/api/employees/{id}/preferences`, `/api/employees/{id}/constraints`
- Controllers: `employeeAvailabilityController`, `employeePreferencesController`, `employeeConstraintsController`
- Authorization middleware

---

### US-13: Time-Off Management API
**Priority:** 🟡 Medium  
**Story Points:** 8  
**As an** employee  
**I want to** manage my time-off requests via API  
**So that** I can submit and track requests programmatically  

**As a** manager  
**I want to** approve/reject time-off requests via API  
**So that** I can manage approvals efficiently  

**Acceptance Criteria:**
- [ ] GET /api/time-off/requests (list all, filtered by user/status)
- [ ] POST /api/time-off/requests (create request)
- [ ] PUT /api/time-off/requests/{id}/approve (manager only)
- [ ] PUT /api/time-off/requests/{id}/reject (manager only)
- [ ] GET /api/time-off/requests/{id} (get single request)
- [ ] Proper validation and authorization

**Technical Notes:**
- Routes: `/api/time-off/requests`
- Controller: `timeOffController.py`
- Authorization: employees can create/view own, managers can approve/reject

---

## PHASE 4: FRONTEND INTEGRATION 🟡

### US-14: Optimization UI
**Priority:** 🔴 Critical  
**Story Points:** 13  
**As a** manager  
**I want to** trigger and view optimization results in the UI  
**So that** I can easily generate and review optimal schedules without using technical APIs  

**Acceptance Criteria:**
- [ ] Button to trigger optimization for a weekly schedule
- [ ] View optimization run status (pending, running, completed, failed)
- [ ] View optimization metrics (objective value, runtime, solver status)
- [ ] View proposed assignments in solution
- [ ] Button to apply solution
- [ ] Ability to compare multiple solutions
- [ ] Progress indicator for running optimizations

**Technical Notes:**
- Page/Component: `OptimizationPage.jsx` or `ScheduleOptimization.jsx`
- API integration with scheduling endpoints
- Real-time status updates (polling or websocket)
- Table/list view of solutions

---

### US-15: Employee Preferences UI
**Priority:** 🟠 High  
**Story Points:** 13  
**As an** employee  
**I want to** set my preferences in the UI  
**So that** I can easily communicate my shift preferences and request time off through a user-friendly interface  

**Acceptance Criteria:**
- [ ] Form to set shift preferences
- [ ] Form to view/edit constraints (if allowed)
- [ ] Time-off request form
- [ ] View time-off request status

**Technical Notes:**
- Page: `EmployeeSettingsPage.jsx` or `MyPreferencesPage.jsx`
- Components: `PreferencesForm`, `TimeOffRequestForm`
- API integration with employee management endpoints

---

### US-16: Time-Off Management UI (Manager)
**Priority:** 🟠 High  
**Story Points:** 8  
**As a** manager  
**I want to** approve/reject time-off requests in the UI  
**So that** I can efficiently review and manage employee time-off requests with full visibility of the schedule impact  

**Acceptance Criteria:**
- [ ] List view of all time-off requests
- [ ] Filter by status (pending, approved, rejected)
- [ ] Filter by employee
- [ ] Calendar view showing time-off periods
- [ ] Approve/reject buttons with comments
- [ ] Notification when new requests arrive

**Technical Notes:**
- Page: `TimeOffManagementPage.jsx`
- Components: `TimeOffRequestList`, `TimeOffRequestCard`, `TimeOffCalendar`
- API integration with time-off endpoints
- Real-time updates

---

## SUMMARY

### Progress Overview:

**Phase 1 - Foundation:** ✅ **COMPLETE** (23 points)
- ✅ US-1: Time-Off Request System (8 pts)
- ✅ US-2: Employee Preferences (5 pts)
- ✅ US-3: System Constraints (5 pts)
- ✅ US-4: Optimization Configuration (5 pts)

**Phase 2 - Core Optimization Engine:** ✅ **COMPLETE** (42 points)
- ✅ US-6: MIP Model Builder (13 pts)
- ✅ US-7: Constraint Validation Service (8 pts)
- ✅ US-8: MIP Solver Integration (13 pts)
- ✅ US-9: Solution Storage & Tracking (8 pts)

**Phase 3 - API & Integration:** ⏸️ **NOT STARTED** (29 points)
- ⏳ US-10: Optimization API Endpoints (8 pts)
- ⏳ US-11: Apply Solution to Assignments (5 pts)
- ⏳ US-12: Employee Management API (8 pts)
- ⏳ US-13: Time-Off Management API (8 pts)

**Phase 4 - Frontend Integration:** ⏸️ **NOT STARTED** (34 points)
- ⏳ US-14: Optimization UI (13 pts)
- ⏳ US-15: Employee Preferences UI (13 pts)
- ⏳ US-16: Time-Off Management UI (8 pts)

### Total Story Points:
- **Completed:** 44 points (34%)
- **Remaining:** 84 points (66%)
- **Total:** 128 points

### Next Steps:
1. **Immediate:** US-8 (MIP Solver Integration) - Build and solve optimization model
2. **Then:** US-9 (Solution Storage) - Store and track optimization results
3. **Then:** Phase 3 API endpoints

### Dependencies:
- Phase 1 ✅ must complete before Phase 2
- Phase 2 must complete before Phase 3
- Phase 3 must complete before Phase 4
- US-6, US-7, US-8 can be worked on in parallel after US-4

### Technical Infrastructure Completed:
- ✅ MIP Solver (Python-MIP v1.15.0) installed and tested
- ✅ NumPy (v2.2.6) installed
- ✅ Database tables: `optimization_configs`, `scheduling_runs`, `scheduling_solutions`
- ✅ Optimization Config CRUD API tested and working
- ✅ Sample optimization config created

---

## ADDITIONAL CONSIDERATIONS

### Technical Debt:
**Total Progress:** 65 / 128 story points (51%)

**Timeline:**
- Phase 1: ✅ COMPLETE (23 points)
- Phase 2: ✅ COMPLETE (42 points)
- Phase 3: ⏸️ 0/29 points (0%)
- Phase 4: ⏸️ 0/34 points (0%)

**Next Priority:**
🔴 US-10: Optimization API Endpoints (8 pts) - Start Phase 3!

---

## Technical Notes

### Dependencies:
- Python-MIP v1.15.0 ✅
- NumPy v2.2.6 ✅
- PostgreSQL database ✅
- Docker environment ✅

### Services Completed:
1. ✅ OptimizationDataBuilder - Data extraction and matrix building
2. ✅ ConstraintService - Validation with HARD/SOFT severity
3. ✅ SchedulingService - MIP model, CBC solver, and database storage

### Comprehensive Test Results (27 employees, 76 shifts):
- **Status:** OPTIMAL
- **Runtime:** 0.39 seconds
- **Assignments:** 516 total (avg 20.64 per employee, min 18, max 21)
- **Coverage:** 100% (76/76 shifts filled)
- **Preference Score:** 0.73 average (range 0.72-0.75)
- **Employees Used:** 25 out of 27 available
- **Time-off Respected:** 3 approved requests honored
- **Database Storage:** SchedulingRun #11 with 516 SchedulingSolution records

### Data Seeding:
- Comprehensive seed script: `seed_comprehensive_data.py`
- Creates 27 employees across 4 roles (Waiter, Bartender, Hostess, Manager)
- 54 employee preferences with varied shift/day preferences
- 6 system-wide constraints (hours, shifts, rest periods)
- 3 approved time-off requests for current week
- 76 planned shifts across 7 days (morning, afternoon, evening)

### Performance Notes:
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
