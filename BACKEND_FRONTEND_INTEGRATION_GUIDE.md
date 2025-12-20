# Backend-Frontend Integration Guide

## Current Data Model & APIs

### 🏢 Core Entities (Currently Implemented)

#### 1. **User**
- Fields: `user_id`, `user_full_name`, `user_email`, `hashed_password`, `is_manager`
- Relationships: roles (many-to-many), assignments, time_off_requests, weekly_schedules
- **Available Endpoints:**
  - `POST /users/login` → Returns JWT token + user data
  - `GET /users/me` → Current authenticated user
  - `GET /users/` → All users (authenticated)
  - `GET /users/{user_id}` → Single user
  - `POST /users/` → Create user (manager only)
  - `PUT /users/{user_id}` → Update user (manager only)
  - `DELETE /users/{user_id}` → Delete user (manager only)

#### 2. **Role**
- Fields: `role_id`, `role_name` (unique)
- Relationships: users (many-to-many), shift_templates, assignments
- **Available Endpoints:**
  - `GET /roles/` → All roles
  - `GET /roles/{role_id}` → Single role
  - `POST /roles/` → Create role (manager only)
  - `PUT /roles/{role_id}` → Update role (manager only)
  - `DELETE /roles/{role_id}` → Delete role (manager only)

#### 3. **ShiftTemplate**
- Fields: `shift_template_id`, `shift_template_name`, `start_time`, `end_time`, `location`
- Relationships: required_roles (many-to-many), planned_shifts
- **Available Endpoints:**
  - `GET /shift-templates/` → All templates
  - `GET /shift-templates/{template_id}` → Single template
  - `POST /shift-templates/` → Create template
  - `PUT /shift-templates/{template_id}` → Update template
  - `DELETE /shift-templates/{template_id}` → Delete template

#### 4. **WeeklySchedule**
- Fields: `weekly_schedule_id`, `week_start_date`, `created_by_id`
- Relationships: created_by (User), planned_shifts (cascade delete)
- **Available Endpoints:**
  - `GET /weekly-schedules/` → All schedules
  - `GET /weekly-schedules/{schedule_id}` → Single schedule (with planned_shifts)
  - `POST /weekly-schedules/` → Create schedule
  - `DELETE /weekly-schedules/{schedule_id}` → Delete schedule (cascades to planned shifts)

#### 5. **PlannedShift**
- Fields: `planned_shift_id`, `weekly_schedule_id`, `shift_template_id`, `date`, `start_time`, `end_time`, `location`, `status` (PLANNED, PARTIALLY_ASSIGNED, FULLY_ASSIGNED, CANCELLED)
- Relationships: weekly_schedule, shift_template, assignments
- **Available Endpoints:**
  - `GET /planned-shifts/` → All shifts
  - `GET /planned-shifts/{shift_id}` → Single shift (with assignments)
  - `GET /planned-shifts/by-schedule/{schedule_id}` → Shifts for a schedule
  - `POST /planned-shifts/` → Create shift
  - `PUT /planned-shifts/{shift_id}` → Update shift
  - `DELETE /planned-shifts/{shift_id}` → Delete shift

#### 6. **ShiftAssignment**
- Fields: `assignment_id`, `planned_shift_id`, `user_id`, `role_id`
- Constraint: Unique per (planned_shift_id, user_id)
- Relationships: planned_shift, user, role
- **Available Endpoints:**
  - `GET /shift-assignments/` → All assignments
  - `GET /shift-assignments/{assignment_id}` → Single assignment
  - `GET /shift-assignments/by-shift/{shift_id}` → Assignments for a shift
  - `GET /shift-assignments/by-user/{user_id}` → Assignments for a user
  - `POST /shift-assignments/` → Create assignment
  - `DELETE /shift-assignments/{assignment_id}` → Delete assignment

#### 7. **TimeOffRequest** ⭐ NEW (Partially Complete)
- Fields: `request_id`, `user_id`, `start_date`, `end_date`, `request_type` (VACATION, SICK, PERSONAL, OTHER), `status` (PENDING, APPROVED, REJECTED), `requested_at`, `approved_by_id`, `approved_at`
- Relationships: user, approved_by (manager)
- **Available Endpoints:**
  - `POST /time-off/requests/` → Create request (for current user)
  - `GET /time-off/requests/` → All requests
  - `GET /time-off/requests/{request_id}` → Single request
  - `PUT /time-off/requests/{request_id}` → Update request (for pending requests)
  - `DELETE /time-off/requests/{request_id}` → Delete request (for pending requests)
  - `POST /time-off/requests/{request_id}/approve` → Approve request (manager only)
  - `POST /time-off/requests/{request_id}/reject` → Reject request (manager only)

#### 8. **SystemConstraints** ⭐ NEW (Partially Complete)
- Fields: `constraint_id`, `constraint_type`, `constraint_value`, `is_hard_constraint`
- Constraint Types: MAX_HOURS_PER_WEEK, MIN_HOURS_PER_WEEK, MAX_CONSECUTIVE_DAYS, MIN_REST_HOURS, MAX_SHIFTS_PER_WEEK, MIN_SHIFTS_PER_WEEK
- **Available Endpoints:**
  - `GET /system-constraints/` → All constraints
  - `GET /system-constraints/{constraint_id}` → Single constraint
  - `POST /system-constraints/` → Create constraint
  - `PUT /system-constraints/{constraint_id}` → Update constraint
  - `DELETE /system-constraints/{constraint_id}` → Delete constraint

---

## Future Entities (Roadmap - Phase 1-2)

### 🚀 Planned for Implementation

1. **EmployeePreferences** (NOT YET IMPLEMENTED)
   - Store shift preferences per employee
   - Fields: preference_id, user_id, shift_template_id, preference_level (PREFERRED, NEUTRAL, AVOID)
   
2. **OptimizationConfig** (NOT YET IMPLEMENTED)
   - Store optimization parameters
   - Fields: config_id, optimization_strategy, fairness_weight, preference_weight, etc.
   
3. **SchedulingRun** (NOT YET IMPLEMENTED)
   - Track optimization execution
   - Fields: run_id, weekly_schedule_id, started_at, completed_at, status
   
4. **SchedulingSolution** (NOT YET IMPLEMENTED)
   - Store proposed assignments from optimizer
   - Fields: solution_id, scheduling_run_id, assignment_proposals (JSON), score

---

## Authentication & Authorization

### JWT Authentication Flow
1. User calls `POST /users/login` with email/password
2. Backend returns `access_token` (JWT) and user data (including `is_manager` flag)
3. Frontend stores token in `localStorage` as `access_token`
4. Frontend stores user data in `localStorage` as `auth_user`
5. All subsequent requests include `Authorization: Bearer <token>` header

### Role-Based Access Control
- **Authenticated Users**: Can view basic data, manage own time-off requests
- **Managers**: Can create/edit users, assign shifts, approve time-off, manage system constraints

---

## Frontend Data Flow Examples

### 📊 Dashboard Metrics (HomePage)
```
Frontend needs:
1. GET /users/ → count total employees
2. GET /planned-shifts/ → count upcoming shifts for next 7 days
3. GET /shift-assignments/ → calculate coverage rate
   (count assigned shifts / total required assignments * 100)
```

### 📅 Schedule Management (SchedulePage)
```
Frontend flow:
1. GET /weekly-schedules/ → show list of schedules
2. Click on schedule → GET /weekly-schedules/{schedule_id}
3. View planned_shifts from response
4. For each shift → GET /planned-shifts/{shift_id}
5. Can then POST /shift-assignments/ to assign employees
6. DELETE /shift-assignments/{assignment_id} to remove assignment
```

### 👥 Employee Directory
```
Frontend flow:
1. GET /users/ → list all employees
2. GET /users/{user_id} → detailed view with roles
3. GET /time-off/requests/ → filter by user_id (coming soon)
4. GET /shift-assignments/by-user/{user_id} → show their assignments
```

### ⏳ Time-Off Management (Employees)
```
Employee flow:
1. POST /time-off/requests/ → create new request (auto uses current user)
2. GET /time-off/requests/ → see own pending requests
3. PUT /time-off/requests/{request_id} → modify pending request
4. DELETE /time-off/requests/{request_id} → cancel pending request

Manager flow:
1. GET /time-off/requests/ → see all requests
2. POST /time-off/requests/{request_id}/approve → approve
3. POST /time-off/requests/{request_id}/reject → reject
```

### ⚙️ System Constraints (Managers)
```
Manager flow:
1. GET /system-constraints/ → view all constraints
2. PUT /system-constraints/{constraint_id} → update max hours, rest periods, etc.
```

---

## Current Data Structure Summary

### Relationships Map
```
User
├── roles (many-to-many) → Role
├── assignments (one-to-many) → ShiftAssignment
│                                    ├── planned_shift → PlannedShift
│                                    └── role → Role
├── time_off_requests (one-to-many) → TimeOffRequest
│                                       └── approved_by → User
└── weekly_schedules (one-to-many) → WeeklySchedule
                                        └── planned_shifts (one-to-many) → PlannedShift
                                                                              ├── shift_template → ShiftTemplate
                                                                              └── assignments (one-to-many) → ShiftAssignment

Role
├── users (many-to-many) → User
├── shift_templates (many-to-many) → ShiftTemplate
└── assignments (one-to-many) → ShiftAssignment

ShiftTemplate
├── required_roles (many-to-many) → Role
└── planned_shifts (one-to-many) → PlannedShift

SystemConstraints
└── (global - applies to all users)
```

---

## Key API Response Patterns

### User Response (GET /users/me)
```json
{
  "user_id": 1,
  "user_full_name": "John Doe",
  "user_email": "john@example.com",
  "is_manager": true,
  "roles": [
    {"role_id": 1, "role_name": "Manager"}
  ]
}
```

### PlannedShift Response (with relationships)
```json
{
  "planned_shift_id": 5,
  "weekly_schedule_id": 2,
  "shift_template_id": 1,
  "date": "2025-01-15",
  "start_time": "2025-01-15T09:00:00",
  "end_time": "2025-01-15T17:00:00",
  "location": "Store A",
  "status": "PARTIALLY_ASSIGNED",
  "assignments": [
    {
      "assignment_id": 10,
      "user_id": 1,
      "role_id": 1,
      "user_full_name": "John Doe",
      "role_name": "Waiter"
    }
  ]
}
```

### TimeOffRequest Response
```json
{
  "request_id": 3,
  "user_id": 2,
  "start_date": "2025-02-01",
  "end_date": "2025-02-05",
  "request_type": "VACATION",
  "status": "PENDING",
  "requested_at": "2025-01-10T10:30:00",
  "approved_by_id": null,
  "approved_at": null,
  "user_full_name": "Jane Smith",
  "approved_by_name": null
}
```

---

## Notes for Frontend Development

1. **Nested Data**: Most responses include related data (e.g., assignments include user/role names), so minimal additional queries needed
2. **Cascading Deletes**: Deleting a WeeklySchedule cascades to PlannedShifts and their Assignments
3. **Time Handling**: `date` fields are Date (YYYY-MM-DD), `start_time`/`end_time` are DateTime (ISO 8601)
4. **Status Enums**: PlannedShift status and TimeOffRequest status/type are enums - store as strings in frontend
5. **Auth Header Required**: Except for `/login`, all endpoints require `Authorization: Bearer <token>`
6. **Manager Operations**: Endpoints marked as "manager only" will return 403 if not manager

---

## Ready to Build

✅ **Users & Authentication** - Complete with JWT
✅ **Roles Management** - Complete  
✅ **Schedule Templates** - Complete
✅ **Weekly Schedules & Planned Shifts** - Complete
✅ **Shift Assignments** - Complete
⭐ **Time-Off Requests** - Complete with approval workflow
⭐ **System Constraints** - Complete

🚀 **Phase 2 (Future)**: Employee Preferences, Optimization Engine
