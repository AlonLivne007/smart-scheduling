# Entity Relationships - Optimal Scheduling

## Existing Entities (No Changes Needed)

```
UserModel (users)
├── user_id (PK)
├── user_full_name
├── user_email
├── is_manager
└── Relationships:
    ├── roles (many-to-many via user_roles)
    ├── weekly_schedules (one-to-many, created_by)
    └── assignments (one-to-many, shift_assignments)

RoleModel (roles)
├── role_id (PK)
├── role_name
└── Relationships:
    ├── users (many-to-many via user_roles)
    ├── shift_templates (many-to-many via shift_role_requirements)
    └── assignments (one-to-many, shift_assignments)

ShiftTemplateModel (shift_templates)
├── shift_template_id (PK)
├── shift_template_name
├── start_time
├── end_time
├── location
└── Relationships:
    ├── required_roles (many-to-many via shift_role_requirements)
    └── planned_shifts (one-to-many)

WeeklyScheduleModel (shift_weekly_schedule)
├── weekly_schedule_id (PK)
├── week_start_date
├── created_by_id (FK → users)
└── Relationships:
    └── planned_shifts (one-to-many)

PlannedShiftModel (planned_shifts)
├── planned_shift_id (PK)
├── weekly_schedule_id (FK → shift_weekly_schedule)
├── shift_template_id (FK → shift_templates)
├── date
├── start_time
├── end_time
├── location
├── status (PLANNED, PARTIALLY_ASSIGNED, FULLY_ASSIGNED, CANCELLED)
└── Relationships:
    ├── weekly_schedule (many-to-one)
    ├── shift_template (many-to-one)
    └── assignments (one-to-many, shift_assignments)

ShiftAssignmentModel (shift_assignments)
├── assignment_id (PK)
├── planned_shift_id (FK → planned_shifts)
├── user_id (FK → users)
├── role_id (FK → roles)
└── Relationships:
    ├── planned_shift (many-to-one)
    ├── user (many-to-one)
    └── role (many-to-one)

shift_role_requirements (association table)
├── shift_template_id (FK → shift_templates)
├── role_id (FK → roles)
└── required_count (Integer)
```

---

## New Entities for Optimal Scheduling

### 1. TimeOffRequest

```
TimeOffRequest (time_off_requests)
├── request_id (PK)
├── user_id (FK → users)
├── start_date (Date)
├── end_date (Date)
├── request_type (Enum: VACATION, SICK, PERSONAL, OTHER)
├── status (Enum: PENDING, APPROVED, REJECTED)
├── requested_at (DateTime)
├── approved_by_id (FK → users, nullable)
├── approved_at (DateTime, nullable)
└── notes (Text, nullable)

Relationships:
├── user (many-to-one → users)
└── approved_by (many-to-one → users)
```

**Purpose:** Track employee time-off requests and approvals

---

### 2. EmployeePreferences

```
EmployeePreferences (employee_preferences)
├── preference_id (PK)
├── user_id (FK → users)
├── preferred_shift_template_id (FK → shift_templates, nullable)
├── preferred_day_of_week (Integer, nullable)
├── preferred_start_time (Time, nullable)
├── preferred_end_time (Time, nullable)
├── preference_weight (Float, default=1.0)
├── effective_from (Date)
└── effective_to (Date, nullable)

Relationships:
├── user (many-to-one → users)
└── preferred_shift_template (many-to-one → shift_templates)
```

**Purpose:** Store employee shift preferences for optimization

---

### 3. SystemConstraints

```
SystemConstraints (system_constraints)
├── constraint_id (PK)
├── constraint_type (Enum: MAX_HOURS_PER_WEEK, MIN_HOURS_PER_WEEK,
│                     MAX_CONSECUTIVE_DAYS, MIN_REST_HOURS,
│                     MAX_SHIFTS_PER_WEEK, MIN_SHIFTS_PER_WEEK)
├── constraint_value (Float/Integer)
├── is_hard_constraint (Boolean)
├── effective_from (Date)
├── effective_to (Date, nullable)
└── notes (Text, nullable)
```

**Purpose:** Define system-wide work rules that apply to all employees

---

### 4. OptimizationConfig

```
OptimizationConfig (optimization_configs)
├── config_id (PK)
├── config_name (String, unique)
├── weight_fairness (Float, default=1.0)
├── weight_preferences (Float, default=1.0)
├── weight_cost (Float, default=0.0)
├── weight_coverage (Float, default=1.0)
├── max_runtime_seconds (Integer, default=300)
├── mip_gap (Float, default=0.01)
├── is_default (Boolean, default=False)
├── created_at (DateTime)
└── updated_at (DateTime)
```

**Purpose:** Store optimization parameters and objective weights

---

### 5. SchedulingRun

```
SchedulingRun (scheduling_runs)
├── run_id (PK)
├── weekly_schedule_id (FK → shift_weekly_schedule)
├── run_type (Enum: FULL_OPTIMIZATION, INCREMENTAL, MANUAL_OVERRIDE)
├── status (Enum: PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
├── started_at (DateTime)
├── completed_at (DateTime, nullable)
├── solver_name (String)
├── objective_value (Float, nullable)
├── solver_status (String, nullable)
├── runtime_seconds (Float, nullable)
├── constraints_satisfied (Integer, nullable)
├── constraints_violated (Integer, nullable)
├── created_by_id (FK → users)
└── notes (Text, nullable)

Relationships:
├── weekly_schedule (many-to-one → shift_weekly_schedule)
├── created_by (many-to-one → users)
└── solutions (one-to-many → scheduling_solutions)
```

**Purpose:** Track optimization execution and results

---

### 6. SchedulingSolution

```
SchedulingSolution (scheduling_solutions)
├── solution_id (PK)
├── run_id (FK → scheduling_runs)
├── planned_shift_id (FK → planned_shifts)
├── user_id (FK → users)
├── role_id (FK → roles)
├── is_selected (Boolean)
├── assignment_score (Float, nullable)
└── created_at (DateTime)

Relationships:
├── run (many-to-one → scheduling_runs)
├── planned_shift (many-to-one → planned_shifts)
├── user (many-to-one → users)
└── role (many-to-one → roles)
```

**Purpose:** Store proposed assignments from optimizer (before applying to ShiftAssignments)

---

## Complete Entity Relationship Diagram

```
┌─────────────────┐
│     Users       │
│  (user_id PK)   │
└────────┬────────┘
         │
         │ 1:N
         ├─────────────────────────────────────────────┐
         │                                             │
         │                                             │
    ┌────▼──────────┐                          ┌─────▼────────────┐
    │  Employee     │                          │  TimeOffRequest  │
    │ Availability  │                          │  (request_id PK) │
    │(availability_│                          └──────────────────┘
    │  id PK)       │
    └───────────────┘
         │
    ┌────▼──────────┐
    │  Employee     │
    │ Preferences   │
    │(preference_id │
    │  PK)          │
    └───────────────┘
         │
    ┌────▼──────────┐
    │  Employee     │
    │ Constraints   │
    │(constraint_id │
    │  PK)          │
    └───────────────┘

┌─────────────────┐
│ WeeklySchedule  │
│(weekly_schedule │
│  _id PK)        │
└────────┬────────┘
         │
         │ 1:N
    ┌────▼──────────┐
    │ PlannedShift  │
    │(planned_shift │
    │  _id PK)      │
    └────┬──────────┘
         │
         │ 1:N
    ┌────▼──────────┐         ┌──────────────┐
    │ShiftAssignment│────────▶│  Scheduling  │
    │(assignment_id │         │   Solution   │
    │  PK)          │         │(solution_id  │
    └────┬──────────┘         │   PK)        │
         │                    └──────┬───────┘
         │                           │
         │                           │ N:1
         │                    ┌──────▼───────┐
         │                    │ SchedulingRun│
         │                    │  (run_id PK) │
         │                    └──────┬───────┘
         │                           │
         │                           │ N:1
         │                    ┌──────▼───────┐
         │                    │Optimization  │
         │                    │   Config     │
         │                    │(config_id PK)│
         └────────────────────┴──────────────┘
```

---

## Data Flow for Optimization

```
1. User triggers optimization
   ↓
2. SchedulingService receives request
   ↓
3. OptimizationDataBuilder extracts:
   - Employees (from Users)
   - PlannedShifts (from WeeklySchedule)
   - RoleRequirements (from ShiftTemplate → shift_role_requirements)
   - TimeOff (from TimeOffRequest, status=APPROVED)
   - Preferences (from EmployeePreferences)
   - Constraints (from SystemConstraints - system-wide)
   ↓
4. SchedulingService builds MIP model
   - Decision variables: x[i,j,k]
   - Hard constraints (from SystemConstraints, TimeOff)
   - Objective function (from Preferences, OptimizationConfig)
   ↓
5. MIP Solver runs
   ↓
6. SchedulingService stores results:
   - SchedulingRun (metadata, status, metrics)
   - SchedulingSolution (proposed assignments)
   ↓
7. User reviews solution
   ↓
8. User applies solution
   ↓
9. System creates ShiftAssignment records
   ↓
10. System updates PlannedShift.status = FULLY_ASSIGNED
```

---

## Key Relationships Summary

| Entity              | Relationship                | Target Entity  | Type        |
| ------------------- | --------------------------- | -------------- | ----------- |
| TimeOffRequest      | user_id                     | Users          | Many-to-One |
| TimeOffRequest      | approved_by_id              | Users          | Many-to-One |
| EmployeePreferences | user_id                     | Users          | Many-to-One |
| EmployeePreferences | preferred_shift_template_id | ShiftTemplates | Many-to-One |
| SchedulingRun       | weekly_schedule_id          | WeeklySchedule | Many-to-One |
| SchedulingRun       | created_by_id               | Users          | Many-to-One |
| SchedulingSolution  | run_id                      | SchedulingRun  | Many-to-One |
| SchedulingSolution  | planned_shift_id            | PlannedShift   | Many-to-One |
| SchedulingSolution  | user_id                     | Users          | Many-to-One |
| SchedulingSolution  | role_id                     | Roles          | Many-to-One |

---

## Indexes to Add

### TimeOffRequest

- `idx_timeoff_user` on (user_id)
- `idx_timeoff_status` on (status)
- `idx_timeoff_dates` on (start_date, end_date)

### EmployeePreferences

- `idx_preferences_user` on (user_id)

### SystemConstraints

- `idx_constraints_type` on (constraint_type)
- `idx_constraints_effective` on (effective_from, effective_to)

### SchedulingRun

- `idx_runs_schedule` on (weekly_schedule_id)
- `idx_runs_status` on (status)
- `idx_runs_created` on (created_by_id)

### SchedulingSolution

- `idx_solution_run` on (run_id)
- `idx_solution_shift` on (planned_shift_id)
- `idx_solution_user` on (user_id)
- `idx_solution_selected` on (is_selected)
