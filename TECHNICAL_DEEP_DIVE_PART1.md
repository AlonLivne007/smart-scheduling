---
# PART 1: ARCHITECTURE & TECH STACK
## Smart Scheduling System - Technical Deep Dive
### Senior Systems Architecture Analysis

**Author:** Smart Scheduling Development Team  
**Date:** January 2026  
**Audience:** Expert Computer Science Faculty  
**Purpose:** Complete architectural justification and implementation details

---

## Table of Contents
1. [The Data Flow Pipeline](#1-the-data-flow-pipeline-json--pydantic--sqlalchemy--postgresql)
2. [Database Architecture Decision](#2-why-postgresql-over-nosql)
3. [Frontend-Backend Communication & Authentication](#3-frontend-backend-communication--jwt-authentication)
4. [DevOps & Containerization](#4-docker-and-container-orchestration)
5. [Architectural Summary](#5-architectural-summary)

---

## 1. The Data Flow Pipeline: JSON → Pydantic → SQLAlchemy → PostgreSQL

### 1.1 Why This Strict Typing Flow Matters

The Smart Scheduling System enforces a **five-layer data transformation pipeline** that is fundamentally different from passing dictionaries. Understanding this design decision is critical to understanding system reliability.

#### ❌ The "Dictionary Approach" (What We DON'T Do)

```python
# Anti-pattern: No type safety, no validation
@app.post("/api/optimize")
def optimize(data: dict):
    run_id = data["weekly_schedule_id"]  # What if this key doesn't exist?
    config = data.get("config_id")       # What if it's "config_id": "not_a_number"?
    
    # Problems:
    # 1. No IDE autocomplete
    # 2. No compile-time type checking
    # 3. String "123" could be treated as integer accidentally
    # 4. Missing required fields discovered at runtime (too late!)
    # 5. Database receives invalid data -> corruption
    # 6. No self-documenting API (frontend doesn't know what fields are required)
```

**Why this fails:**
- **Runtime Errors:** Typos like `"weekly_shedule_id"` only appear when code executes
- **Data Corruption:** Invalid data reaches the database, requiring cleanup
- **Debugging Hell:** Error stack trace doesn't show where the bad data came from
- **No Contract:** API doesn't document what it accepts

#### ✅ The Smart Scheduling Approach: Strict Type Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: Frontend (React)                                      │
│  User clicks "Optimize"                                         │
│  state = { weekly_schedule_id: 456, config_id: 2 }             │
└──────────────────┬──────────────────────────────────────────────┘
                   │ Axios sends JSON
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: Network (HTTP)                                        │
│  POST /api/scheduling/optimize/456?config_id=2                 │
│  Content-Type: application/json                                 │
│  Request Body: {"weekly_schedule_id": 456, "config_id": 2}    │
└──────────────────┬──────────────────────────────────────────────┘
                   │ FastAPI receives raw JSON
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: Pydantic Validation (The Guardian)                    │
│  schema = SchedulingRunCreate(**json_dict)                      │
│  ┌─ Parse: "456" (str) → 456 (int)                             │
│  ├─ Validate: Is 456 > 0? Is weekly schedule 456 valid?       │
│  ├─ Type Check: config_id must be int or None                 │
│  └─ Return: SchedulingRunCreate object                         │
│  If ANY validation fails: HTTPException 422 (reject request)   │
└──────────────────┬──────────────────────────────────────────────┘
                   │ Now we have a typed object
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 4: SQLAlchemy ORM (Persistence Mapper)                   │
│  run = SchedulingRunModel(                                      │
│      weekly_schedule_id=schema.weekly_schedule_id,  # type: int│
│      config_id=schema.config_id,  # type: Optional[int]       │
│      status=SchedulingRunStatus.PENDING  # type: Enum         │
│  )                                                              │
│  session.add(run)  # Mark for insertion                        │
│  session.commit()  # Execute INSERT statement                  │
└──────────────────┬──────────────────────────────────────────────┘
                   │ SQL generated with correct types
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 5: PostgreSQL Database                                   │
│  INSERT INTO scheduling_run (                                   │
│      weekly_schedule_id,  -- INTEGER (NOT NULL)                │
│      config_id,           -- INTEGER (nullable)                │
│      status,              -- VARCHAR (ENUM)                    │
│      created_at           -- TIMESTAMP                         │
│  ) VALUES (456, 2, 'PENDING', NOW())                          │
│  RETURNING run_id;                                             │
│  → run_id = 789 (database-generated)                           │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Real Code: The Complete Flow

#### Step 1: Frontend → API Request

**File:** `frontend/src/api/optimization.js`

```javascript
// Frontend state
const schedule = {
  weekly_schedule_id: 456,
  config_id: 2
};

// Axios automatically serializes to JSON and adds JWT token
export const startOptimization = async (weeklyScheduleId, configId = null) => {
  const response = await api.post(
    `/scheduling/optimize/${weeklyScheduleId}`,
    {},  // body is empty, params are in URL/query
    {
      params: configId ? { config_id: configId } : {}
    }
  );
  return response.data;
};

// What gets sent over network:
// POST /api/scheduling/optimize/456?config_id=2
// Headers: {
//   "Content-Type": "application/json",
//   "Authorization": "Bearer eyJhbGciOiJIUzI1NiIs..."
// }
```

#### Step 2: FastAPI Route Handler

**File:** `backend/app/api/routes/schedulingRoutes.py`

```python
@router.post("/optimize/{weekly_schedule_id}")
async def optimize_schedule(
    weekly_schedule_id: int,  # ← FastAPI automatically converts from URL path
    config_id: Optional[int] = Query(None),  # ← Converts query param string to int
    db: Session = Depends(get_db)  # ← Dependency injection
) -> Dict[str, Any]:
    """
    API endpoint that accepts SchedulingRun creation request.
    
    The parameters are ALREADY validated by FastAPI before this function runs.
    If weekly_schedule_id is "not_a_number", FastAPI returns 422 before entering.
    """
    # At this point:
    # - weekly_schedule_id is GUARANTEED to be int
    # - config_id is GUARANTEED to be int or None
    # - db is GUARANTEED to be valid Session
    
    # Verify schedule exists (additional business logic validation)
    schedule = db.query(WeeklyScheduleModel).filter(
        WeeklyScheduleModel.weekly_schedule_id == weekly_schedule_id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weekly schedule {weekly_schedule_id} not found"
        )
    
    # Create SchedulingRun record
    run = SchedulingRunModel(
        weekly_schedule_id=weekly_schedule_id,
        config_id=config_id,
        status=SchedulingRunStatus.PENDING,
        started_at=datetime.now()
    )
    db.add(run)
    db.commit()
    db.refresh(run)  # Refresh to get auto-generated run_id
    
    # Dispatch async Celery task
    task = run_optimization_task.delay(run_id=run.run_id)
    
    return {
        "run_id": run.run_id,
        "status": run.status.value,
        "task_id": str(task.id),
        "message": f"Optimization job {task.id} queued. Poll /api/scheduling/runs/{run.run_id} for status"
    }
```

#### Step 3: Pydantic Schemas (The Gatekeeper)

**File:** `backend/app/schemas/schedulingRunSchema.py`

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from app.db.models.schedulingRunModel import SchedulingRunStatus

class SchedulingRunCreate(BaseModel):
    """
    Schema for creating a scheduling run.
    
    This Pydantic model:
    1. Documents required/optional fields
    2. Validates types (int, str, enum, etc.)
    3. Applies business logic validation (@field_validator)
    4. Provides automatic OpenAPI documentation
    """
    
    weekly_schedule_id: int = Field(
        ...,  # ... means required (no default)
        gt=0,  # Constraint: Greater Than 0
        description="ID of the weekly schedule to optimize"
    )
    
    config_id: Optional[int] = Field(
        None,  # Default: null (optional)
        gt=0,  # If provided, must be > 0
        description="ID of optimization config (defaults to system default)"
    )
    
    @field_validator('weekly_schedule_id')
    @classmethod
    def validate_schedule_id(cls, v):
        """Custom validation: ensure weekly_schedule_id exists."""
        if v < 1:
            raise ValueError('weekly_schedule_id must be positive')
        return v

class SchedulingRunResponse(BaseModel):
    """Schema for API response (what we send back to frontend)."""
    
    run_id: int
    weekly_schedule_id: int
    config_id: Optional[int]
    status: str  # Enum stringified
    task_id: str
    message: str
    
    class Config:
        from_attributes = True  # Allow construction from SQLAlchemy ORM objects

# Usage in route:
# When FastAPI sees `response_model=SchedulingRunResponse`,
# it automatically converts the SQLAlchemy model to JSON
```

#### Step 4: SQLAlchemy ORM Model

**File:** `backend/app/db/models/schedulingRunModel.py`

```python
from sqlalchemy import Column, Integer, String, DateTime, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.db.base import Base

class SchedulingRunStatus(str, Enum):
    """Status of a scheduling optimization run."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class SolverStatus(str, Enum):
    """Status returned by MIP solver."""
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    NO_SOLUTION_FOUND = "NO_SOLUTION_FOUND"

class SchedulingRunModel(Base):
    """
    SQLAlchemy ORM model for SchedulingRun.
    
    Maps to PostgreSQL table 'scheduling_run'.
    Each attribute becomes a column.
    """
    __tablename__ = "scheduling_run"
    
    run_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False
    )
    
    weekly_schedule_id = Column(
        Integer,
        ForeignKey("weekly_schedule.weekly_schedule_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    config_id = Column(
        Integer,
        ForeignKey("optimization_config.config_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    status = Column(
        SQLEnum(SchedulingRunStatus),
        default=SchedulingRunStatus.PENDING,
        nullable=False
    )
    
    solver_status = Column(
        SQLEnum(SolverStatus),
        nullable=True
    )
    
    objective_value = Column(Float, nullable=True)
    runtime_seconds = Column(Float, nullable=True)
    total_assignments = Column(Integer, nullable=True)
    
    error_message = Column(String(1024), nullable=True)
    
    started_at = Column(DateTime, default=datetime.now, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # Relationships (for convenient access)
    weekly_schedule = relationship("WeeklyScheduleModel", back_populates="scheduling_runs")
    optimization_config = relationship("OptimizationConfigModel")
    scheduling_solutions = relationship("SchedulingSolutionModel", back_populates="scheduling_run")
```

#### Step 5: Database Schema (PostgreSQL)

**What SQLAlchemy generates:**

```sql
CREATE TABLE scheduling_run (
    run_id SERIAL PRIMARY KEY,
    weekly_schedule_id INTEGER NOT NULL,
    config_id INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    solver_status VARCHAR(20),
    objective_value FLOAT,
    runtime_seconds FLOAT,
    total_assignments INTEGER,
    error_message VARCHAR(1024),
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (weekly_schedule_id) REFERENCES weekly_schedule(weekly_schedule_id) ON DELETE CASCADE,
    FOREIGN KEY (config_id) REFERENCES optimization_config(config_id) ON DELETE SET NULL,
    
    INDEX idx_weekly_schedule_id (weekly_schedule_id),
    INDEX idx_config_id (config_id)
);
```

### 1.3 Why This Strict Pipeline?

| Aspect | Dictionary Approach | Our Type-Safe Pipeline |
|--------|---------------------|------------------------|
| **Validation** | None (runtime errors only) | 3 layers: Pydantic, SQLAlchemy constraints, DB checks |
| **IDE Support** | No autocomplete | Full type hints, method suggestions |
| **Documentation** | None | Self-documenting (API schema auto-generated) |
| **Catch Errors Early** | Only at runtime | Before database touched |
| **Debugging** | Stack trace gives no context | Clear: schema layer shows exactly where validation failed |
| **Database Integrity** | Bad data reaches DB | Impossible to insert invalid data |
| **Frontend-Backend Contract** | Implicit (guesswork) | Explicit (OpenAPI schema) |
| **Type Safety** | Python dynamic (weak) | Strong typing enforced |

### 1.4 Error Handling: The Safety Net

```python
# Example: Invalid request from frontend

# Frontend sends:
POST /api/scheduling/optimize/456?config_id=invalid_number
```

```python
# FastAPI receives, validates:
try:
    config_id = int("invalid_number")  # ValueError!
except:
    # FastAPI catches this and returns:
    HTTP 422 Unprocessable Entity
    {
        "detail": [
            {
                "type": "value_error",
                "loc": ["query", "config_id"],
                "msg": "value is not a valid integer",
                "input": "invalid_number"
            }
        ]
    }
```

This tells the frontend **exactly** what's wrong before any database operation.

---

## 2. Why PostgreSQL Over NoSQL

### 2.1 The Smart Scheduling Data Model

Smart Scheduling has a **highly relational data structure**. Understanding this is critical to defending the architecture choice.

```
┌─────────────┐
│ User        │
│ (Employee)  │
├─────────────┤
│ user_id (PK)
│ name
│ email
│ roles[]     ←─────┐
└────┬────────┘     │
     │              │
     │ 1:Many       │ Many:Many
     │              │
     ▼              ▼
┌─────────────────────────┐         ┌──────────┐
│ ShiftAssignment         │         │  Role    │
│ (One user, one shift)   │ ◄───────│          │
├─────────────────────────┤         └──────────┘
│ assignment_id (PK)
│ user_id (FK) ──────┐
│ shift_id (FK) ─────┤
│ role_id (FK)  ─────┤
│ status              │
└─────────────────────┘
     │
     │ Many:Many
     │
     ▼
┌──────────────────────┐
│ PlannedShift         │
├──────────────────────┤
│ planned_shift_id (PK)
│ shift_template_id
│ start_time
│ end_time
│ required_roles[]  ────────┐
│ day_of_week          │     │
└──────────────────────┘     │
     │                       │ 1:Many
     │                       │
     ▼                       ▼
┌─────────────────┐    ┌─────────────┐
│ WeeklySchedule  │    │ ShiftTemplate
├─────────────────┤    ├─────────────────┐
│ schedule_id (PK)│    │ template_id (PK)
│ shifts[]        │    │ role_requirements
│ week_start      │    │ duration
│ week_end        │    │ break_duration
└─────────────────┘    └─────────────────┘
```

This is the opposite of a flat document structure. There are:
- **1:Many relationships** (User → many ShiftAssignments)
- **Many:Many relationships** (Employees ↔ Roles)
- **Foreign Keys** (shift_id, user_id, role_id references)
- **Complex queries** (find all shifts for user X in week Y)

### 2.2 PostgreSQL: Enforced Integrity

#### Example: Why Foreign Keys Matter

```python
# Smart Scheduling use case:
# Scenario: Delete a user from the system

# With PostgreSQL (RELATIONAL):
db.query(UserModel).filter(UserModel.user_id == 123).delete()
# PostgreSQL response:
# ERROR: update or delete on table "user" violates foreign key constraint
# "fk_shift_assignment_user_id" on table "shift_assignment"
# DETAIL: Key (user_id)=(123) is still referenced from table "shift_assignment".

# This is GOOD! It prevents orphaned assignments.
```

```javascript
// With MongoDB (DOCUMENT-BASED):
db.collection('users').deleteOne({ user_id: 123 });
// MongoDB response:
// OK, deleted.
//
// Problem: Any shift_assignments with user_id=123 are now orphaned!
// They reference a user that doesn't exist.
// Application code must remember to clean these up (error-prone).
```

#### Cascade Delete with PostgreSQL

```python
# Define the relationship with proper cascade behavior:
class ShiftAssignmentModel(Base):
    __tablename__ = "shift_assignment"
    
    assignment_id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey(
            "user.user_id",
            ondelete="CASCADE"  # ← Database will auto-delete orphans
        ),
        nullable=False
    )

# Now when we delete a user:
db.query(UserModel).filter(UserModel.user_id == 123).delete()

# PostgreSQL automatically:
# 1. Finds all shift_assignments where user_id=123
# 2. Deletes them first (respects FK constraint)
# 3. THEN deletes the user
# All atomic, all in one transaction
```

### 2.3 Query Complexity: SQL vs. Document Queries

#### Use Case: "Show me all shifts assigned to Employee #5 for next week, with role info"

**PostgreSQL (SQL - Clean & Efficient):**

```sql
SELECT 
    s.planned_shift_id,
    s.start_time,
    s.end_time,
    r.role_id,
    r.role_name,
    a.assignment_id
FROM planned_shift s
JOIN shift_assignment a ON s.planned_shift_id = a.shift_id
JOIN role r ON a.role_id = r.role_id
WHERE a.user_id = 5
  AND s.start_time >= NOW()
  AND s.start_time < NOW() + INTERVAL '7 days'
ORDER BY s.start_time ASC;
```

**Result:** One clean query, all data fetched in one round-trip.

**MongoDB (Document-based - Complex):**

```javascript
db.shift_assignments.aggregate([
    {
        $match: {
            user_id: 5,
            start_time: {
                $gte: new Date(),
                $lt: new Date(Date.now() + 7*24*60*60*1000)
            }
        }
    },
    {
        $lookup: {
            from: "planned_shifts",
            localField: "shift_id",
            foreignField: "planned_shift_id",
            as: "shift"
        }
    },
    {
        $unwind: "$shift"
    },
    {
        $lookup: {
            from: "roles",
            localField: "role_id",
            foreignField: "role_id",
            as: "role"
        }
    },
    {
        $unwind: "$role"
    },
    {
        $sort: { "shift.start_time": 1 }
    }
])
```

**Problem:** Much more verbose, multiple aggregation stages, requires careful `$unwind` (can explode data if cardinality mismatch).

### 2.4 Constraints & Data Quality

**PostgreSQL enforces constraints AT THE DATABASE LEVEL:**

```sql
-- Ensure no employee works overlapping shifts
CREATE UNIQUE INDEX unique_no_overlapping_shifts
ON shift_assignment(user_id, shift_id)
WHERE status != 'CANCELLED';

-- Ensure hours don't exceed maximum per week
ALTER TABLE user_weekly_hours
ADD CONSTRAINT max_hours_per_week CHECK (total_hours <= 40);

-- Ensure referential integrity
ALTER TABLE shift_assignment
ADD CONSTRAINT fk_role
FOREIGN KEY (role_id) REFERENCES role(role_id);
```

**MongoDB relies on application code:**

```javascript
// Must implement this in application logic:
async function assignShift(userId, shiftId) {
    // Check for overlaps (query 1)
    const existing = await db.shift_assignments.findOne({
        user_id: userId,
        shift_id: { $exists: true }
    });
    
    if (existingOverlapsWith(existing, newShift)) {
        throw new Error("Overlap!");
    }
    
    // Check weekly hours (query 2, possibly many documents)
    const assignments = await db.shift_assignments.find({
        user_id: userId
    });
    const hours = sumHours(assignments);
    
    // Finally insert (query 3)
    await db.shift_assignments.insertOne({...});
}

// Issues:
// - Multiple queries (slow)
// - Race conditions possible (between check and insert)
// - Duplicate validation logic across endpoints
```

### 2.5 Transaction Safety: ACID Guarantees

#### Scenario: Apply a proposed schedule solution

We need to:
1. Create SchedulingRun record
2. Insert 500+ ShiftAssignment records
3. Update User total_assignments counters
4. Create ActivityLog entries

**PostgreSQL (Full ACID):**

```python
try:
    db.begin()  # START TRANSACTION
    
    # Insert run
    run = SchedulingRunModel(...)
    db.add(run)
    db.flush()  # Get run_id
    
    # Bulk insert assignments
    db.bulk_insert_mappings(ShiftAssignmentModel, assignments)
    
    # Update counters
    for emp_id, count in assignments_by_employee.items():
        db.query(UserModel).filter(
            UserModel.user_id == emp_id
        ).update({"total_assignments": count})
    
    # Log activity
    db.add(ActivityLogModel(...))
    
    db.commit()  # COMMIT TRANSACTION (all-or-nothing)
    
except Exception as e:
    db.rollback()  # Undo everything
    raise
```

**Guarantees:**
- **Atomicity:** All 500+ inserts succeed, or NONE do
- **Consistency:** No partial state (half of assignments inserted, counters not updated)
- **Isolation:** No other transaction sees partial state
- **Durability:** After commit, data survives power loss

**MongoDB:**

```javascript
// Single-document ACID: OK
// Multi-document ACID: Possible since 4.0, but less mature

try {
    session = db.startSession();
    session.startTransaction();
    
    // Insert run
    db.scheduling_run.insertOne({...}, { session });
    
    // Insert 500+ assignments (might take time)
    db.shift_assignments.insertMany(assignments, { session });
    
    // Update counters
    for (let empId of empIds) {
        db.users.updateOne(
            { user_id: empId },
            { $set: { total_assignments: ... } },
            { session }
        );
    }
    
    session.commitTransaction();
} catch (e) {
    session.abortTransaction();
    throw e;
} finally {
    session.endSession();
}

// Concerns:
// - Still not as battle-tested as PostgreSQL ACID
// - Performance penalty for transactions
// - Complexity in retry logic if session fails
```

### 2.6 Summary: PostgreSQL vs. MongoDB

| Criterion | PostgreSQL | MongoDB |
|-----------|-----------|---------|
| **Relationships** | Native foreign keys | Application-managed references |
| **Data Integrity** | Enforced by DB (CONSTRAINTS, FKs) | Application responsible |
| **Complex Queries** | Natural (SQL JOINs) | Verbose (aggregation pipeline) |
| **ACID Transactions** | Full, mature, battle-tested | Multi-doc ACID since 4.0 |
| **Schema** | Fixed (migrations explicit) | Flexible (can cause inconsistency) |
| **Query Performance** | Optimized (query planner) | Good for document lookups |
| **Scalability** | Vertical (easier) | Horizontal (sharding) |
| **Best For** | Structured, relational data | Flexible, document data |

### 2.7 Our Choice: PostgreSQL

**Smart Scheduling has:**
- ✅ Clear, defined schema (Users, Shifts, Roles, Assignments)
- ✅ Complex relationships (many-to-many, one-to-many)
- ✅ Need for data integrity (can't have orphaned assignments)
- ✅ Frequent relational queries (find shifts for user X)
- ✅ Multi-row transactions (apply entire schedule atomically)

**MongoDB would add:**
- ❌ Unnecessary complexity (no schema flexibility benefit)
- ❌ Duplicate validation (must code constraints in app)
- ❌ Race conditions (transactions less mature)
- ❌ Slower queries (aggregation pipeline instead of JOINs)

**Conclusion:** PostgreSQL is the only sensible choice for this domain.

---

## 3. Frontend-Backend Communication & JWT Authentication

### 3.1 The Axios HTTP Client

**What is Axios?** HTTP client library that simplifies making requests from JavaScript.

#### Without Axios (raw `fetch`):

```javascript
// Painful boilerplate
async function getSchedules() {
    const token = localStorage.getItem("access_token");
    
    const response = await fetch(
        "http://localhost:8000/api/schedules",
        {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`,
                "Accept": "application/json"
            }
        }
    );
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    return data;
}

// Repeat this boilerplate for every endpoint!
```

#### With Axios:

```javascript
// Much cleaner
const api = axios.create({
    baseURL: "http://localhost:8000/api"
});

// Interceptor handles token automatically
api.interceptors.request.use((config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

async function getSchedules() {
    const response = await api.get("/schedules");
    return response.data;
}
```

### 3.2 JWT Authentication Flow

#### Overview: How JWT Works

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: User Login                                         │
├─────────────────────────────────────────────────────────────┤
│  Frontend                                                   │
│  POST /api/users/login                                      │
│  Body: { email: "john@company.com", password: "secret123" }│
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend (authController.py)                                │
│  1. Query database: SELECT * FROM user WHERE email = ...   │
│  2. Hash password: bcrypt.verify(password, stored_hash)    │
│  3. If match, create JWT:                                  │
│     payload = {                                             │
│         "sub": "john@company.com",  # subject (standard)   │
│         "user_id": 42,                                      │
│         "exp": 1705618000,   # expiration (7 days from now)│
│         "iat": 1705013200    # issued at                   │
│     }                                                       │
│     secret = "your-secret-key-xyz"                         │
│     token = JWT.encode(payload, secret, algorithm="HS256") │
└─────────────────────┬───────────────────────────────────────┘
                      │ Returns: { access_token: "eyJhbG..." }
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React)                                           │
│  1. Receive token from backend                             │
│  2. Store in localStorage:                                 │
│     localStorage.setItem("access_token", token)            │
│  3. Subsequent requests include token                      │
└─────────────────────────────────────────────────────────────┘
        │
        │ All future API calls:
        │ GET /api/schedules
        │ Headers: { Authorization: "Bearer eyJhbG..." }
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Authenticated Request                              │
├─────────────────────────────────────────────────────────────┤
│  Backend (get_current_user dependency)                      │
│  1. Extract token from Authorization header                │
│  2. Verify signature: JWT.decode(token, secret)            │
│     If signature invalid → 401 Unauthorized               │
│     If expired (exp < now) → 401 Unauthorized             │
│  3. Extract user_id from payload                           │
│  4. Query user: SELECT * FROM user WHERE user_id = ...   │
│  5. Pass user object to route handler                     │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Axios Interceptors: The Magic

**File:** `frontend/src/lib/axios.js`

```javascript
import axios from "axios";

// Create Axios instance with base URL
const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000"
});

/**
 * REQUEST INTERCEPTOR: Runs before every request
 * 
 * Purpose: Automatically add JWT token to Authorization header
 */
api.interceptors.request.use(
    (config) => {
        // Get token from localStorage
        const token = localStorage.getItem("access_token");
        
        if (token) {
            // Add to every request automatically
            config.headers = config.headers || {};
            config.headers.Authorization = `Bearer ${token}`;
        }
        
        return config;  // Pass to next handler
    },
    (error) => {
        return Promise.reject(error);
    }
);

/**
 * RESPONSE INTERCEPTOR: Runs after every response
 * (Can be added for error handling)
 */
api.interceptors.response.use(
    (response) => response,  // Pass successful responses through
    (error) => {
        // Handle 401 Unauthorized (token expired)
        if (error.response?.status === 401) {
            // Clear token and redirect to login
            localStorage.removeItem("access_token");
            window.location.href = "/login";
        }
        return Promise.reject(error);
    }
);

export default api;
```

### 3.4 Real Implementation: Login Flow

**Backend - Login Endpoint:**

```python
# File: backend/app/api/controllers/userController.py

@router.post("/login")
async def login(
    login_request: LoginRequest,  # email, password from frontend
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Authenticate user and return JWT token.
    
    Args:
        login_request: { email: str, password: str }
        db: Database session
    
    Returns:
        { access_token: "eyJhbG...", token_type: "bearer" }
    """
    # 1. Query user by email
    user = db.query(UserModel).filter(
        UserModel.user_email == login_request.email
    ).first()
    
    # 2. Validate user exists and password matches
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.verify_password(login_request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # 3. Create JWT token
    access_token = create_access_token(data={
        "sub": user.user_email,  # sub = subject (standard JWT claim)
        "user_id": user.user_id
    })
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

def create_access_token(data: dict) -> str:
    """
    Create JWT token.
    
    JWT structure:
    {header}.{payload}.{signature}
    
    Example decoded payload:
    {
        "sub": "john@company.com",
        "user_id": 42,
        "exp": 1705618000,  # Unix timestamp
        "iat": 1705013200
    }
    """
    to_encode = data.copy()
    
    # Set expiration: 7 days from now
    expire = datetime.utcnow() + timedelta(days=settings.JWT_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    
    # Encode JWT
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM  # "HS256"
    )
    
    return encoded_jwt
```

**Frontend - Login Component:**

```javascript
// File: frontend/src/pages/LoginPage.jsx

import { useState } from "react";
import api from "@/lib/axios";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    
    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        
        try {
            // Send credentials to backend
            const response = await api.post("/users/login", {
                email,
                password
            });
            
            // Backend returns: { access_token: "...", token_type: "bearer" }
            const { access_token } = response.data;
            
            // Store token in localStorage
            localStorage.setItem("access_token", access_token);
            
            // Redirect to dashboard
            window.location.href = "/dashboard";
            
        } catch (error) {
            if (error.response?.status === 401) {
                alert("Invalid email or password");
            } else {
                alert("Login failed");
            }
        } finally {
            setLoading(false);
        }
    };
    
    return (
        <form onSubmit={handleLogin}>
            <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email"
                required
            />
            <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                required
            />
            <button type="submit" disabled={loading}>
                {loading ? "Logging in..." : "Login"}
            </button>
        </form>
    );
}
```

### 3.5 Using Authenticated Endpoints

Once logged in, all subsequent requests automatically include the token:

```javascript
// File: frontend/src/api/optimization.js

import api from "@/lib/axios";

// This function doesn't need to handle token manually!
// Axios interceptor adds it automatically
export const startOptimization = async (weeklyScheduleId, configId = null) => {
    const response = await api.post(
        `/scheduling/optimize/${weeklyScheduleId}`,
        {},
        {
            params: configId ? { config_id: configId } : {}
        }
    );
    
    // Request headers automatically include:
    // Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    
    return response.data;
};
```

**What the backend receives:**

```python
@router.post("/optimize/{weekly_schedule_id}")
async def optimize_schedule(
    weekly_schedule_id: int,
    current_user: UserModel = Depends(get_current_user),  # <- Injected!
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    The get_current_user dependency:
    1. Extracts token from Authorization header
    2. Verifies signature and expiration
    3. Queries user from database
    4. Passes user object to this handler
    
    If token is invalid or expired → 401 Unauthorized (before entering)
    """
    print(f"Request from: {current_user.user_email}")
    # Only managers can optimize
    if not current_user.is_manager:
        raise HTTPException(status_code=403, detail="Not a manager")
    
    # ... rest of logic
```

### 3.6 Token Refresh Strategy

In a real production system, we'd implement token refresh to improve security:

```python
@router.post("/users/refresh-token")
async def refresh_token(
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Issue a new access token.
    
    Frontend should call this before token expires (proactively)
    or catch 401 and retry with refresh.
    """
    new_token = create_access_token(data={
        "sub": current_user.user_email,
        "user_id": current_user.user_id
    })
    
    return {
        "access_token": new_token,
        "token_type": "bearer"
    }
```

---

## 4. Docker and Container Orchestration

### 4.1 Why Docker?

**The Core Problem:**

```
Developer A: "It works on my machine!"
  - Windows 11, Python 3.10.1, PostgreSQL 14.2, Redis 7.0.1

Developer B: "But I have Python 3.9, it fails!"

DevOps: "It works in production with Python 3.10, but we're using Ubuntu 20.04"

Deployment: "The server has Python 3.8, PostgreSQL 13, Redis 6.2 - it crashed"
```

**Traditional Stack Without Docker:**

```
┌─────────────────────────────────────────────────┐
│ Developer Laptop (Windows)                      │
├─────────────────────────────────────────────────┤
│ Windows 11                                      │
│ Python 3.10 (installed via installer)          │
│ PostgreSQL 14 (installed via MSI)              │
│ Redis 7 (installed via WSL)                    │
│ ↓                                               │
│ Hardcoded configs (localhost:5432)             │
│ Virtual env (.venv)                            │
│ requirements.txt (might miss transitive deps)  │
└─────────────────────────────────────────────────┘
                    ↓ commit & push
┌─────────────────────────────────────────────────┐
│ CI/CD Server (Ubuntu)                           │
├─────────────────────────────────────────────────┤
│ Ubuntu 20.04                                    │
│ Python 3.9 (system default)  ← MISMATCH!       │
│ PostgreSQL 13 (APT package)  ← MISMATCH!       │
│ Redis 6.2 (APT package)      ← MISMATCH!       │
│ ↓ Build fails!                                  │
│ "ModuleNotFoundError: No module named 'asyncpg'"
└─────────────────────────────────────────────────┘
                    ↓ hot-fix deploy
┌─────────────────────────────────────────────────┐
│ Production Server (Amazon Linux)                │
├─────────────────────────────────────────────────┤
│ Amazon Linux 2                                  │
│ Python 3.8 (old OS default)  ← MISMATCH!       │
│ PostgreSQL 12 (RDS instance) ← MISMATCH!       │
│ Redis 5.0 (old ElastiCache)  ← MISMATCH!       │
│ ↓ Crashes in production                        │
└─────────────────────────────────────────────────┘
```

### 4.2 Docker: The Solution

**Key Concept: "Build Once, Run Anywhere"**

Docker packages your entire application in a **container** - a lightweight VM that includes:
- OS dependencies (Linux kernel, system libs)
- Language runtime (Python 3.10)
- Application code
- Configuration

```dockerfile
# Dockerfile: Recipe for building a container
FROM python:3.10  # Start with official Python 3.10 image

WORKDIR /app  # Set working directory

COPY requirements.txt .  # Copy dependency list
RUN pip install -r requirements.txt  # Install all dependencies

COPY . .  # Copy application code

CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

**What happens when you build:**

```bash
$ docker build -t smart-scheduling:1.0 -f backend/Dockerfile .
```

Docker engine:
1. Downloads `python:3.10` base image (or uses cached version)
2. Sets working directory to `/app`
3. Copies `requirements.txt` into container
4. Runs `pip install -r requirements.txt` **inside** the container
5. Copies your source code
6. Records the startup command

**Result:** A **snapshot** of everything needed to run the app.

Now this same container runs identically on:
- Your laptop
- CI/CD server
- Production (AWS, Azure, DigitalOcean, etc.)

### 4.3 Real Implementation: The Docker Setup

**File:** `backend/Dockerfile`

```dockerfile
# Stage 1: Builder (not shown for simplicity, but good practice)
# Stage 2: Runtime
FROM python:3.10

# Metadata
LABEL maintainer="smart-scheduling@company.com"
LABEL description="Smart Scheduling Backend API"

# Set working directory
WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables (can be overridden at runtime)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check (docker will monitor if container is alive)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port (documentation only, doesn't actually open port)
EXPOSE 8000

# Command to run
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

**File:** `frontend/Dockerfile`

```dockerfile
# Stage 1: Build
FROM node:18-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci  # Deterministic install

COPY . .
RUN npm run build  # Produces /app/dist folder

# Stage 2: Serve (minimal runtime image)
FROM nginx:alpine

# Copy built files to nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 4.4 Docker Compose: Multi-Container Orchestration

**The Problem:** Your app needs:
- PostgreSQL database
- Redis cache
- Celery workers
- Backend API
- Frontend

Running each manually is a nightmare:

```bash
# Terminal 1: Database
docker run -d postgres:14 ...

# Terminal 2: Redis
docker run -d redis:7 ...

# Terminal 3: Backend
docker run -d smart-scheduling-backend ...

# Terminal 4: Frontend
docker run -d smart-scheduling-frontend ...

# Terminal 5: Celery worker
docker run -d smart-scheduling-worker ...

# When something breaks, which container? Debug nightmare!
```

**Solution: docker-compose**

**File:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  db:
    image: postgres:14
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: scheduler_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: [ "CMD-SHELL", "pg_isready -U postgres" ]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - app-network

  # Redis Cache & Message Broker
  redis:
    image: redis:7-alpine
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - app-network

  # Backend API
  backend:
    build: ./backend  # Build from backend/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app  # Hot-reload in development
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/scheduler_db
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      db:
        condition: service_healthy  # Wait for DB to be ready
      redis:
        condition: service_started
    networks:
      - app-network

  # Frontend Web UI
  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend
    networks:
      - app-network

  # Celery Worker for async tasks
  celery_worker:
    build: ./backend
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/scheduler_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
      - backend
    networks:
      - app-network

  # Flower: Monitor Celery workers
  flower:
    image: mher/flower:2.0
    command: celery -A app.celery_app --broker=redis://redis:6379 flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis
      - celery_worker
    networks:
      - app-network

# Volumes (persistent storage)
volumes:
  postgres_data:
  redis_data:

# Networks (so containers can reach each other by hostname)
networks:
  app-network:
    driver: bridge
```

### 4.5 Orchestration: What docker-compose Does

```bash
$ docker-compose up
```

Automatically:
1. Creates a network called `app-network` (so containers can talk to each other)
2. Builds the `backend` and `frontend` images
3. Starts all services in dependency order:
   - First: `db` (waits for healthcheck)
   - Then: `redis`
   - Then: `backend` (waits for db healthy)
   - Then: `frontend`
   - Then: `celery_worker`
   - Then: `flower`

4. Connects them on the network:
   - `backend` can reach `db` at hostname `db:5432`
   - `backend` can reach `redis` at hostname `redis:6379`
   - `frontend` can reach `backend` at hostname `backend:8000`

### 4.6 Benefits: Reproducibility

#### Benefit 1: Same Environment Everywhere

```bash
# Local development
$ docker-compose up
# App runs with Python 3.10, PostgreSQL 14, Redis 7

# CI/CD
$ docker-compose up
# EXACT same Python 3.10, PostgreSQL 14, Redis 7

# Production
$ docker-compose up -f docker-compose.prod.yml
# EXACT same (except maybe postgres is externally managed RDS)
```

#### Benefit 2: Easy Onboarding

New developer:
```bash
$ git clone https://github.com/company/smart-scheduling
$ cd smart-scheduling
$ docker-compose up
```

Takes 5 minutes, fully working setup. No "install Python", "install PostgreSQL", "figure out environment variables".

#### Benefit 3: Isolation

Each container:
- Has its own filesystem
- Has its own process space
- Can't interfere with your OS

If you mess something up in a container:
```bash
$ docker-compose down
$ docker-compose up
# Fresh start
```

No system-wide side effects.

#### Benefit 4: Easy Scaling

```bash
# Run 4 Celery workers instead of 1
$ docker-compose up --scale celery_worker=4
```

Docker automatically:
- Starts 4 copies of the worker container
- Load-balances between them (Redis queue distributes tasks)

### 4.7 Production Deployment Pattern

Typically, you'd use an **orchestration platform:**

```
Docker Compose: Development/Testing
         ↓
  Docker Swarm: Small-medium production
         ↓
 Kubernetes (K8s): Large-scale production
```

Example: Deploy to **AWS ECS** (managed container service):

```bash
# 1. Build image
$ docker build -t smart-scheduling:1.0 .

# 2. Push to AWS ECR (container registry)
$ aws ecr get-login-password | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
$ docker tag smart-scheduling:1.0 123456789.dkr.ecr.us-east-1.amazonaws.com/smart-scheduling:1.0
$ docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/smart-scheduling:1.0

# 3. Define ECS task definition (like docker-compose, but AWS format)
# 4. Deploy to ECS cluster
# 5. AWS auto-scales based on load
```

---

## 5. Architectural Summary

### The Complete Data Flow (with all technologies)

```
┌──────────────────────────────────────────────────────────────────────┐
│ 1. FRONTEND (React + Axios)                                          │
│    User clicks "Optimize Schedule"                                   │
│    → state = { weekly_schedule_id: 456 }                             │
│    → axios.post("/api/scheduling/optimize/456")                      │
└──────────────┬───────────────────────────────────────────────────────┘
               │ JSON over HTTPS
               │ + JWT token in Authorization header
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 2. FASTAPI + PYDANTIC (Backend Validation)                           │
│    POST /api/scheduling/optimize/{weekly_schedule_id}                │
│    - Extract & parse: weekly_schedule_id (URL path)                  │
│    - Type-check: Must be integer                                     │
│    - Validate: Must be > 0                                           │
│    → Returns: 422 if invalid, 404 if not found                       │
└──────────────┬───────────────────────────────────────────────────────┘
               │ Valid request passed
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 3. SQLALCHEMY (Object-Relational Mapping)                            │
│    Create SchedulingRunModel object:                                 │
│    run = SchedulingRunModel(                                         │
│        weekly_schedule_id=456,  # validated int                      │
│        status=SchedulingRunStatus.PENDING,                           │
│        started_at=datetime.now()                                     │
│    )                                                                  │
│    db.add(run)                                                       │
│    db.commit()                                                       │
└──────────────┬───────────────────────────────────────────────────────┘
               │ ORM generates SQL
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 4. POSTGRESQL (Relational Database)                                  │
│    INSERT INTO scheduling_run (                                      │
│        weekly_schedule_id, status, started_at, created_at            │
│    ) VALUES (456, 'PENDING', NOW(), NOW())                          │
│    RETURNING run_id;  -- Database generates run_id                   │
│    → run_id = 789                                                    │
│                                                                      │
│    Constraints enforce:                                              │
│    - weekly_schedule_id MUST exist (FK check)                        │
│    - status MUST be valid enum value                                 │
└──────────────┬───────────────────────────────────────────────────────┘
               │ Async task queued
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 5. CELERY + REDIS (Async Task Queue)                                 │
│    run_optimization_task.delay(run_id=789)                           │
│    → Celery serializes: { task: "...", args: [789], ... }           │
│    → Sends to Redis:                                                 │
│       LPUSH celery '{"task": "...", "args": [789], ...}'             │
│    → Worker polls Redis (BRPOP)                                      │
│    → Picks up task, executes                                         │
└──────────────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

| Layer | Technology | Why Chosen |
|-------|-----------|-----------|
| Frontend | React + Axios + JWT | Type-safe state, easy API calls, secure auth |
| Validation | Pydantic | Strict typing, auto-documentation, catch errors early |
| Persistence | SQLAlchemy | ORM abstraction, type-safe models, relationship mapping |
| Database | PostgreSQL | ACID transactions, foreign keys, complex queries, data integrity |
| Async | Celery + Redis | Long-running tasks don't block API, scales horizontally |
| DevOps | Docker + docker-compose | Reproducibility, easy deployment, environment isolation |

### Key Design Principles

1. **Type Safety:** JSON → Pydantic → SQLAlchemy → DB (every step validated)
2. **Data Integrity:** Foreign keys, constraints, ACID transactions
3. **Scalability:** Async queue (Celery) decouples heavy computation from API
4. **Debuggability:** Clear error messages at each layer
5. **Reproducibility:** Docker guarantees same env everywhere
6. **Maintainability:** Each layer has single responsibility

---

## Conclusion

The Smart Scheduling System's architecture is a **well-justified stack of proven technologies**:

- **Frontend:** React + Axios for interactive UX with JWT auth
- **Validation:** Pydantic for strict typing and auto-documentation
- **ORM:** SQLAlchemy for type-safe database interaction
- **Database:** PostgreSQL for relational data and ACID guarantees
- **Async:** Celery + Redis for scalable long-running tasks
- **DevOps:** Docker for reproducible, portable deployments

Each choice directly addresses a specific problem and trades off appropriately against alternatives. This is a **production-ready architecture** that scales with the application's needs.

---
