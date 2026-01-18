---
# PART 3: ASYNC PROCESSING INTERNALS (CELERY & REDIS)
## Smart Scheduling System - Backend Infrastructure Deep Dive
### Backend Infrastructure Engineer Analysis

**Author:** Smart Scheduling Development Team  
**Date:** January 2026  
**Audience:** Expert Computer Science Faculty  
**Purpose:** Complete explanation of asynchronous task processing architecture

---

## Table of Contents
1. [The Problem: Blocking I/O & HTTP Timeouts](#1-the-problem-blocking-io--http-timeouts)
2. [Why Celery is Essential](#2-why-celery-is-essential)
3. [System Architecture: Producer-Broker-Consumer](#3-system-architecture-producer-broker-consumer)
4. [The Components in Detail](#4-the-components-in-detail)
5. [Task Flow: Step-by-Step](#5-task-flow-step-by-step)
6. [Monitoring with Flower](#6-monitoring-with-flower)
7. [Code Implementation](#7-code-implementation)
8. [Summary & Performance Analysis](#8-summary--performance-analysis)

---

## 1. The Problem: Blocking I/O & HTTP Timeouts

### 1.1 Traditional Synchronous Request-Response

```
┌─────────────────────────────────────────────────────────────┐
│ User clicks "Optimize Schedule"                             │
│ Browser sends HTTP request                                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ FastAPI Server receives request                             │
│ Handler starts execution: optimize_schedule()                │
├──────────────────────────────────────────────────────────────┤
│ solver.solve(data, config)  ← BLOCKING CALL                │
│                                                              │
│ Server is STUCK here for 300 seconds                        │
│ Can't handle other requests                                 │
│ Browser waits... waits... waits...                          │
│                                                              │
│ (After ~30 seconds, browser times out)                      │
│ Error: "504 Gateway Timeout"                                │
│                                                              │
│ Meanwhile, the solver is STILL running                      │
│ Result computed after 300 seconds but too late!             │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
Browser: "Server died" ❌
Server: Still solving (waste of resources)
```

### 1.2 Resource Exhaustion Without Celery

```
Scenario: 100 users click "Optimize" simultaneously

WITHOUT CELERY:
──────────────

Request 1: Thread 1 locked (300s)
Request 2: Thread 2 locked (300s)
Request 3: Thread 3 locked (300s)
...
Request 100: Thread 100 locked (300s)

System state:
  - 100 threads blocked
  - Each thread = 2MB stack memory → 200MB just for stacks
  - Each thread = 1 file descriptor → 100 FDs used
  - OS context switches between threads (expensive)
  - After ~30 requests: browser timeouts
  
  At 1024 concurrent requests: "Too many open files" ❌
  Server becomes unresponsive
  Crashes with OOM (Out of Memory)
```

### 1.3 The HTTP Timeout Problem

```
HTTP/1.1 specification:
  Connection timeout: Typically 30-60 seconds
  
Your solver: Takes 300 seconds

Timeline:
  t=0s:    Browser sends request
  t=0s:    Server starts solver
  t=30s:   Browser timeout → closes connection
  t=300s:  Solver finishes, tries to send response
           But connection already closed!
           Response lost, no way to tell user
```

### 1.4 Why This Breaks Everything

```
❌ Problem 1: Blocking I/O
   One slow request blocks the entire request handler
   No other users can be served

❌ Problem 2: Resource Limits
   Each concurrent request = OS thread/process
   Default: ~1000 concurrent connections max
   Memory: 100 MB * 1000 = 100 GB (!)

❌ Problem 3: Browser Timeout
   HTTP doesn't support "wait forever"
   Default timeout: 30-60 seconds
   Your solver: 300+ seconds

❌ Problem 4: User Experience
   User gets timeout error immediately
   Doesn't know if computation is happening
   Can't check progress
   Can't cancel gracefully

❌ Problem 5: No Scalability
   Add more users → Need more servers
   Each server has same 1000 connection limit
```

---

## 2. Why Celery is Essential

### 2.1 The Solution: Decouple Long-Running Tasks

```
WITH CELERY:
────────────

Request 1: Handler → Queue task → Return immediately (100ms)
  │
  └─ Worker 1 picks up: solve for 300s (in background)
  
Request 2: Handler → Queue task → Return immediately (100ms)
  │
  └─ Worker 2 picks up: solve for 300s (in background)

...

Request 100: Handler → Queue task → Return immediately (100ms)
  │
  └─ Worker N picks up: solve for 300s (in background)

System state:
  - FastAPI handlers finish immediately (100ms each)
  - Only 4 Worker processes (not 100 threads)
  - Each worker processes tasks sequentially
  - Users can poll for results asynchronously
```

### 2.2 Request Flow Comparison

**Synchronous (Without Celery):**

```
Browser                 Server (Blocked)          Database
  │                          │                        │
  ├─ POST /optimize ────────→│                        │
  │                          │                        │
  │                          ├─ START COMPUTATION ───→│ (300s locked)
  │                          │  (Handler blocked)     │
  │                          │←─ Results ────────────┤
  │                          │                        │
  │ (timeout ~30s)           │                        │
  ├─ TIMEOUT ERROR ←─────────┤                        │
  │                          │
  └─ (sad user)              (Server still computing)
```

**Asynchronous (With Celery):**

```
Browser              FastAPI             Redis           Celery Workers      Database
  │                    │                  │                   │               │
  ├─ POST /opt. ───────→│                 │                   │               │
  │                     ├─ Create task ──→│ TASK QUEUED       │               │
  │                     │                 │                   │               │
  │                     ├─ Return 200 OK ─→│                  │               │
  │←─ {run_id, task_id}─┤                 │                   │               │
  │                     │                 ├─ BRPOP ──────────→│               │
  │ (User sees status)  │                 │                   ├─ START ──────→│
  │                     │                 │                   │  solve (300s)  │
  ├─ GET /runs/{id} ────→│                 │                   │     ...       │
  │←─ {status: RUNNING}─┤                 │                   │               │
  │                     │                 │                   │               │
  │ (after 300s)        │                 │                   │               │
  ├─ GET /runs/{id} ────→│                 │                   │               │
  │←─ {status: SUCCESS, │                 │                   ├─ DONE ───────→│
  │   result: ...}      │                 │                   │               │
  │                     │                 │                   │               │
  └─ (happy user)       │                 │                   │               │
```

### 2.3 The Benefits

| Aspect | Without Celery | With Celery |
|--------|---|---|
| **Handler Time** | 300s (blocked) | 0.1s (queued) |
| **User Timeout** | ❌ Fails (>30s) | ✅ Succeeds |
| **Concurrent Users** | ~10 (then timeout) | 1000s (scaled by workers) |
| **Resource Usage** | 100 threads | 4 worker processes |
| **Memory** | 200MB overhead | Minimal |
| **User Experience** | "Waiting..." forever | "Queued, check status later" |
| **Scalability** | Add servers | Add workers (same server or different) |

---

## 3. System Architecture: Producer-Broker-Consumer

### 3.1 The Three Components

```
┌──────────────────────────────────────────────────────────────────┐
│ PRODUCER: FastAPI Application                                    │
│                                                                  │
│ Responsibility:                                                  │
│  1. Receive HTTP request from client                            │
│  2. Validate input (Pydantic)                                   │
│  3. Create task metadata (task_id, parameters)                  │
│  4. Send to Broker (NOT execute directly)                       │
│  5. Return immediately with task_id                            │
│                                                                  │
│ Code location: app/api/routes/schedulingRoutes.py              │
│ Key function: run_optimization_task.delay(run_id=...)          │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   │ .delay() → Task serialized to JSON
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ BROKER: Redis (Message Queue)                                    │
│                                                                  │
│ Responsibility:                                                  │
│  1. Receive task message from Producer                          │
│  2. Store in Queue (actually a List)                            │
│  3. Distribute to available Consumers                           │
│  4. Track task state (PENDING → STARTED → SUCCESS)            │
│  5. Return results when Consumer completes                      │
│                                                                  │
│ Data structures used:                                            │
│  - LIST: celery queue (FIFO task queue)                        │
│  - HASH: celery-task-meta-{task_id} (task state/result)       │
│  - SET: celery tasks (active task tracking)                    │
│                                                                  │
│ Location: In-memory cache server (Redis container)              │
│ URL: redis://redis:6379/0                                      │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   │ Consumer polls queue
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ CONSUMER: Celery Worker                                          │
│                                                                  │
│ Responsibility:                                                  │
│  1. Poll Broker for new tasks (BRPOP - blocking pop)          │
│  2. Deserialize task message                                    │
│  3. Execute task function (e.g., run_optimization_task)        │
│  4. Capture result or error                                     │
│  5. Send result back to Broker                                 │
│  6. Mark task as DONE in task state                            │
│                                                                  │
│ Configuration:                                                   │
│  - Max concurrent tasks: 4 (worker_prefetch_multiplier=1)     │
│  - Max lifetime: 50 tasks then restart                         │
│  - Timeout: 1 hour hard limit, 55 min soft limit              │
│                                                                  │
│ Code location: app/tasks/optimization_tasks.py                │
│ Key function: @celery_app.task                                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. The Components in Detail

### 4.1 The Producer (FastAPI)

**File:** `backend/app/api/routes/schedulingRoutes.py`

```python
from app.tasks.optimization_tasks import run_optimization_task

@router.post("/optimize/{weekly_schedule_id}")
async def optimize_schedule(
    weekly_schedule_id: int,
    config_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    PRODUCER RESPONSIBILITY:
    1. Validate input
    2. Create SchedulingRun record (tracks the optimization)
    3. Queue async task
    4. Return immediately
    """
    
    # Step 1: Verify schedule exists
    schedule = db.query(WeeklyScheduleModel).filter(
        WeeklyScheduleModel.weekly_schedule_id == weekly_schedule_id
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Step 2: Create SchedulingRun record (PENDING status)
    # This is stored in database so we can track progress
    run = SchedulingRunModel(
        weekly_schedule_id=weekly_schedule_id,
        config_id=config_id,
        status=SchedulingRunStatus.PENDING,
        started_at=datetime.now()
    )
    db.add(run)
    db.commit()
    db.refresh(run)  # Get auto-generated run_id
    
    # Step 3: Queue the task (THE MAGIC)
    # This does NOT execute the task!
    # It sends a message to Redis: "Hey workers, please run this task"
    task = run_optimization_task.delay(run_id=run.run_id)
    
    # run_optimization_task.delay() returns a Celery AsyncResult
    # It has:
    #   - task.id: Unique task ID (e.g., "abc-123-def")
    #   - task.status: Current status ("PENDING" initially)
    #   - task.ready(): Boolean, is it done?
    #   - task.result: The result (when done)
    
    # Step 4: Return immediately (in <100ms)
    # Client now knows:
    #   - run_id: Database record ID
    #   - task_id: Celery task ID (for monitoring)
    #   - Both IDs allow polling for results
    return {
        "run_id": run.run_id,
        "status": run.status.value,  # "PENDING"
        "task_id": str(task.id),
        "message": "Optimization queued. Poll /api/scheduling/runs/{run_id} for status"
    }
```

**What happens when we call `.delay()`:**

```python
# This line:
task = run_optimization_task.delay(run_id=789)

# Is equivalent to:
# 1. Serialize task metadata
message = {
    "task": "app.tasks.optimization_tasks.run_optimization",
    "id": "abc-123-def-456",  # Generated task ID
    "args": [],
    "kwargs": {"run_id": 789},
    "headers": {
        "task_id": "abc-123-def-456",
        "lang": "py",
        "retries": 0,
        "timelimit": [3600, 3300]  # Hard/soft limits
    }
}

# 2. Convert to JSON
json_message = json.dumps(message)

# 3. Send to Redis
redis_client.lpush("celery", json_message)
#  LPUSH = Left Push (add to left of list)
#  This queues the task

# 4. Return AsyncResult object
return AsyncResult(task_id="abc-123-def-456")
```

### 4.2 The Broker (Redis)

#### How Redis Stores Tasks

```
Redis is an in-memory data store with different data structures:

KEY: "celery"
TYPE: LIST (queue)
VALUE:
[
  0: {"task": "...", "id": "task-1", "kwargs": {"run_id": 789}},
  1: {"task": "...", "id": "task-2", "kwargs": {"run_id": 790}},
  2: {"task": "...", "id": "task-3", "kwargs": {"run_id": 791}},
  ...
]

Operations:
  LPUSH celery {task}  - Add task to LEFT (queue end)
  RPOP celery         - Remove from RIGHT (dequeue)
  LLEN celery         - Check queue length

FIFO: First In, First Out
  Task-1 goes in first → Worker processes it first
```

#### Task State Storage

```
KEY: "celery-task-meta-abc-123-def-456"
TYPE: HASH (dictionary)
VALUE:
{
  "status": "PENDING",
  "result": null,
  "traceback": null,
  "children": [],
  "date_done": null
}

As task progresses:
  t=0s:    {"status": "PENDING", ...}
  t=1s:    {"status": "STARTED", ...}
  t=300s:  {"status": "SUCCESS", "result": {...objective_value...}, "date_done": "2026-01-18T10:05:00Z"}
```

#### Redis Operations (Internal)

```python
# Celery broker does these operations automatically:

# When Producer calls .delay():
redis.lpush("celery", json.dumps(task_message))
redis.hset(f"celery-task-meta-{task_id}", mapping={
    "status": "PENDING",
    "result": "",
    "date_done": None
})

# When Worker picks up task:
task = redis.rpop("celery")  # Dequeue
redis.hset(f"celery-task-meta-{task_id}", "status", "STARTED")
redis.hset(f"celery-task-meta-{task_id}", "date_started", datetime.now().isoformat())

# When task completes:
redis.hset(f"celery-task-meta-{task_id}", "status", "SUCCESS")
redis.hset(f"celery-task-meta-{task_id}", "result", json.dumps(result))
redis.hset(f"celery-task-meta-{task_id}", "date_done", datetime.now().isoformat())

# Set expiration (cleanup after 24 hours)
redis.expire(f"celery-task-meta-{task_id}", 86400)
```

### 4.3 The Consumer (Celery Worker)

**File:** `backend/app/celery_app.py` (Configuration)

```python
from celery import Celery
import os

REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

celery_app = Celery(
    'smart_scheduling',
    broker=REDIS_URL,        # Where to get tasks from
    backend=REDIS_URL,       # Where to store results
    include=['app.tasks.optimization_tasks']  # Which task modules to load
)

celery_app.conf.update(
    # Serialization: How to encode/decode tasks
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Task tracking
    task_track_started=True,  # Track when task starts
    
    # Timeouts
    task_time_limit=3600,      # Hard limit: 1 hour (kill task)
    task_soft_time_limit=3300, # Soft limit: 55 min (task can cleanup)
    
    # Prefetch strategy
    worker_prefetch_multiplier=1,    # Only grab 1 task at a time
    worker_max_tasks_per_child=50,   # Restart worker every 50 tasks
    
    # Results cleanup
    result_expires=86400,  # Keep results for 24 hours
)
```

**File:** `backend/app/tasks/optimization_tasks.py` (The Task)

```python
from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.scheduling.scheduling_service import SchedulingService

@celery_app.task(
    bind=True,  # Pass 'self' (the task instance) as first arg
    name='app.tasks.optimization_tasks.run_optimization'  # Unique task name
)
def run_optimization_task(self, run_id: int):
    """
    WORKER RESPONSIBILITY:
    1. Receive deserialized task from Broker
    2. Execute the optimization logic
    3. Capture results or errors
    4. Send results back to Broker
    
    The 'self' parameter allows us to report progress:
    - self.update_state(state, meta)
    - self.retry() for failed tasks
    """
    db = SessionLocal()
    
    try:
        # Load the SchedulingRun record from database
        run = db.query(SchedulingRunModel).filter(
            SchedulingRunModel.run_id == run_id
        ).first()
        
        if not run:
            raise ValueError(f"SchedulingRun {run_id} not found")
        
        # Update task state (for monitoring)
        # This sends a message to Broker saying "I'm working on this"
        self.update_state(
            state='RUNNING',
            meta={'status': 'Building optimization model', 'run_id': run_id}
        )
        
        # Perform the actual optimization (300+ seconds)
        # This is what takes so long!
        scheduling_service = SchedulingService(db)
        run, solution = scheduling_service._execute_optimization_for_run(run)
        
        # Return result (automatically sent to Broker)
        return {
            'run_id': run.run_id,
            'status': run.status.value,
            'solver_status': run.solver_status.value if run.solver_status else None,
            'objective_value': float(run.objective_value) if run.objective_value else None,
            'runtime_seconds': float(run.runtime_seconds) if run.runtime_seconds else None,
            'solutions_count': run.total_assignments or 0,
            'message': 'Optimization completed successfully'
        }
        
    except Exception as e:
        # Handle errors gracefully
        try:
            run = db.query(SchedulingRunModel).filter(
                SchedulingRunModel.run_id == run_id
            ).first()
            
            if run:
                run.status = SchedulingRunStatus.FAILED
                run.completed_at = datetime.now()
                run.error_message = str(e)
                db.commit()
        except:
            pass
        
        # Re-raise so Celery marks task as FAILED
        raise
        
    finally:
        db.close()
```

#### Worker Loop: How It Stays Alive

```python
# Conceptual worker main loop:

def celery_worker_main():
    while True:
        # BRPOP = "Blocking Right Pop"
        # Wait for task from Redis (blocks until available)
        # Timeout: 1 second (to check for signals)
        task_message = redis.brpop("celery", timeout=1)
        
        if task_message:
            # Got a task! Deserialize it
            task_json = task_message[1]  # [0] is queue name
            task_dict = json.loads(task_json)
            
            # Update task state: PENDING → RUNNING
            redis.hset(
                f"celery-task-meta-{task_dict['id']}",
                "status",
                "RUNNING"
            )
            
            # Execute the task function
            try:
                # Import the task function
                task_func = import_task(task_dict['task'])
                
                # Call with arguments
                result = task_func(
                    *task_dict['args'],
                    **task_dict['kwargs']
                )
                
                # Task succeeded: store result
                redis.hset(
                    f"celery-task-meta-{task_dict['id']}",
                    mapping={
                        "status": "SUCCESS",
                        "result": json.dumps(result),
                        "date_done": datetime.now().isoformat()
                    }
                )
                
            except Exception as e:
                # Task failed: store error
                redis.hset(
                    f"celery-task-meta-{task_dict['id']}",
                    mapping={
                        "status": "FAILURE",
                        "result": str(e),
                        "traceback": traceback.format_exc(),
                        "date_done": datetime.now().isoformat()
                    }
                )
        
        # Check for signals (SIGTERM for graceful shutdown)
        if received_shutdown_signal():
            break
```

---

## 5. Task Flow: Step-by-Step

### Complete Timeline from Request to Result

```
t=0ms:   USER ACTION
         User clicks "Optimize" button in React frontend
         
t=5ms:   FRONTEND
         React state: { weekly_schedule_id: 456 }
         Axios serializes to JSON:
           POST /api/scheduling/optimize/456
           Body: {}
           Headers: { Authorization: "Bearer ...", Content-Type: "application/json" }

t=10ms:  NETWORK
         HTTP request travels to backend server
         
t=20ms:  FASTAPI VALIDATION
         FastAPI receives request
         Pydantic validates path parameter (456 is integer)
         Dependency injection: get_db() returns Session
         Dependency injection: require_manager checks JWT

t=30ms:  DATABASE QUERY 1
         Query: SELECT * FROM weekly_schedule WHERE id = 456
         Result: Found schedule ✓

t=40ms:  DATABASE INSERT
         INSERT INTO scheduling_run (weekly_schedule_id, status, created_at)
         VALUES (456, 'PENDING', NOW())
         RETURNING run_id
         Result: run_id = 789

t=50ms:  CELERY SERIALIZATION
         run_optimization_task.delay(run_id=789)
         
         Celery creates task message:
         {
             "task": "app.tasks.optimization_tasks.run_optimization",
             "id": "c4f53-8a92-4d21-9e8e-abc123def456",
             "kwargs": {"run_id": 789},
             "headers": {...}
         }

t=55ms:  REDIS OPERATION
         redis.lpush("celery", json_message)
         
         Redis LIST now contains:
         celery: [
           0: {task: ..., id: c4f53..., kwargs: {run_id: 789}}
         ]

t=60ms:  FASTAPI RESPONSE
         Handler returns:
         {
             "run_id": 789,
             "status": "PENDING",
             "task_id": "c4f53-8a92-4d21-9e8e-abc123def456",
             "message": "Optimization queued..."
         }

t=65ms:  NETWORK
         HTTP response with 200 OK travels back to frontend
         
t=75ms:  BROWSER
         JavaScript receives response
         Updates UI: "Status: Queued, Task ID: c4f53..."
         User sees immediate feedback ✓

════════════════════════════════════════════════════════════════

Meanwhile, at the CELERY WORKER:

t=0ms:   WORKER STARTUP
         $ celery -A app.celery_app worker
         
         Worker connects to Redis
         Enters main loop: redis.brpop("celery", timeout=1)
         Blocks, waiting for tasks

t=50ms:  (Same time as REDIS OPERATION above)
         Worker wakes up! redis.brpop() unblocks
         Gets task message: {task: ..., id: c4f53..., kwargs: {run_id: 789}}

t=55ms:  TASK DESERIALIZATION
         Parse JSON
         Import task function: run_optimization_task
         
t=56ms:  STATE UPDATE
         redis.hset("celery-task-meta-c4f53...", "status", "RUNNING")

t=57ms:  TASK EXECUTION STARTS
         run_optimization_task(run_id=789)
         
         Inside task:
         - Load SchedulingRun from database
         - self.update_state('Building optimization model')
         - Create SchedulingService
         - Execute: scheduling_service._execute_optimization_for_run(run)
         
         THE SOLVER RUNS (300+ seconds) ⏳

t=300s: TASK EXECUTION ENDS
        Solver finished
        Result computed: objective_value = 12345.67
        Return result dictionary

t=301s: TASK COMPLETION
        redis.hset("celery-task-meta-c4f53...", mapping={
            "status": "SUCCESS",
            "result": {objective_value: 12345.67, ...}
        })
        
        Worker goes back to main loop (waiting for next task)

════════════════════════════════════════════════════════════════

Back at the FRONTEND (polling for results):

t=100ms: USER POLLS
         Every 2 seconds, frontend calls:
         GET /api/scheduling/runs/789
         
         Server queries database:
         SELECT * FROM scheduling_run WHERE run_id = 789
         
         Returns: {
             status: "RUNNING",
             started_at: "2026-01-18T10:00:00Z",
             completed_at: null
         }
         
         UI updates: "Status: Running... (300 seconds elapsed: 0/300)"

t=2100ms: USER POLLS AGAIN
          GET /api/scheduling/runs/789
          Returns: {status: "RUNNING", ...}
          UI: "Status: Running... (100/300)"

...polling continues...

t=300,100ms: USER POLLS AFTER SOLVER FINISHES
            GET /api/scheduling/runs/789
            
            Database query:
            SELECT * FROM scheduling_run WHERE run_id = 789
            
            Returns: {
                status: "SUCCESS",
                completed_at: "2026-01-18T10:05:00Z",
                objective_value: 12345.67,
                runtime_seconds: 300.23,
                total_assignments: 487
            }
            
            UI updates with results ✓
            User sees optimal schedule!
```

---

## 6. Monitoring with Flower

### 6.1 What is Flower?

Flower is a **web-based monitoring tool for Celery**. It provides:
- Real-time task queue visualization
- Worker status and statistics
- Task execution history
- Performance metrics
- Task filtering and debugging

### 6.2 How Flower Hooks Into the Flow

```
┌────────────────────────────────────────────┐
│ Celery Broker (Redis)                      │
│                                            │
│ Every task generates events:               │
│  - task-sent (when .delay() called)        │
│  - task-received (when worker gets it)     │
│  - task-started (when execution begins)    │
│  - task-progress (updates during execution)│
│  - task-success (when completed)           │
│  - task-failure (if error occurs)          │
└────────────────┬───────────────────────────┘
                 │
                 │ Flower listens to these events
                 │ via Redis pub/sub or events API
                 │
                 ▼
        ┌────────────────────┐
        │ Flower Web Server  │
        │ (running on port   │
        │  5555)             │
        └────────────────────┘
                 ▲
                 │ Browser HTTP requests
                 │
        ┌────────────────────┐
        │ Your Browser       │
        │ http://localhost:  │
        │   5555             │
        └────────────────────┘
```

### 6.3 Flower Dashboard Features

```
┌──────────────────────────────────────────────────────────┐
│ FLOWER DASHBOARD (http://localhost:5555)                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Tasks (In Real-Time)                                    │
│ ┌─────────────────────────────────────────────────────┐│
│ │ Task ID         Task Name        Status    Time     ││
│ │ abc-123-def     run_optimization RUNNING   2m 15s  ││
│ │ xyz-456-abc     run_optimization SUCCESS   5m 02s  ││
│ │ def-789-xyz     run_optimization PENDING   --      ││
│ │ ghi-012-def     run_optimization FAILURE   1m 30s  ││
│ └─────────────────────────────────────────────────────┘│
│                                                          │
│ Workers                                                 │
│ ┌─────────────────────────────────────────────────────┐│
│ │ Worker Name      Status   Tasks   Processed  Pool   ││
│ │ celery@worker1   ONLINE   1/4    1500      prefork ││
│ │ celery@worker2   ONLINE   0/4    1642      prefork ││
│ │ celery@worker3   ONLINE   0/4    1511      prefork ││
│ │ celery@worker4   ONLINE   2/4    1589      prefork ││
│ └─────────────────────────────────────────────────────┘│
│                                                          │
│ Statistics                                              │
│ ├─ Queue Length: 23 tasks waiting                      │
│ ├─ Total Tasks: 6844 processed                         │
│ ├─ Success Rate: 99.2%                                 │
│ └─ Avg Task Time: 4m 15s                               │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 6.4 Docker Compose Integration

**File:** `docker-compose.yml` (Flower service)

```yaml
services:
  # ... other services ...
  
  flower:
    image: mher/flower:2.0
    command: celery -A app.celery_app --broker=redis://redis:6379 flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
      - celery_worker
    networks:
      - app-network
```

When you run `docker-compose up`, Flower automatically:
1. Connects to Redis broker
2. Listens for Celery events
3. Starts HTTP server on port 5555
4. Displays real-time dashboard

---

## 7. Code Implementation

### 7.1 Complete Request Flow (Actual Code)

**Step 1: Frontend Makes Request**

```javascript
// frontend/src/api/optimization.js
import api from "@/lib/axios";

export const startOptimization = async (weeklyScheduleId, configId = null) => {
    const response = await api.post(
        `/scheduling/optimize/${weeklyScheduleId}`,
        {},
        {
            params: configId ? { config_id: configId } : {}
        }
    );
    
    // Response:
    // {
    //   "run_id": 789,
    //   "status": "PENDING",
    //   "task_id": "abc-123-def",
    //   "message": "..."
    // }
    
    return response.data;
};
```

**Step 2: Backend Receives & Queues**

```python
# backend/app/api/routes/schedulingRoutes.py
from app.tasks.optimization_tasks import run_optimization_task

@router.post("/optimize/{weekly_schedule_id}")
async def optimize_schedule(
    weekly_schedule_id: int,
    config_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    
    # Verify schedule
    schedule = db.query(WeeklyScheduleModel).filter(
        WeeklyScheduleModel.weekly_schedule_id == weekly_schedule_id
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Create run record
    run = SchedulingRunModel(
        weekly_schedule_id=weekly_schedule_id,
        config_id=config_id,
        status=SchedulingRunStatus.PENDING,
        started_at=datetime.now()
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    
    # QUEUE THE TASK (key line!)
    task = run_optimization_task.delay(run_id=run.run_id)
    
    return {
        "run_id": run.run_id,
        "status": run.status.value,
        "task_id": str(task.id),
        "message": f"Task {task.id} queued"
    }
```

**Step 3: Celery Worker Processes**

```python
# backend/app/tasks/optimization_tasks.py
from app.celery_app import celery_app

@celery_app.task(bind=True, name='app.tasks.optimization_tasks.run_optimization')
def run_optimization_task(self, run_id: int):
    """
    Celery task wrapper.
    
    The @celery_app.task decorator:
    1. Registers this function as a Celery task
    2. Adds the .delay() method
    3. Handles serialization/deserialization
    4. Enables monitoring via self.update_state()
    """
    db = SessionLocal()
    
    try:
        run = db.query(SchedulingRunModel).filter(
            SchedulingRunModel.run_id == run_id
        ).first()
        
        if not run:
            raise ValueError(f"SchedulingRun {run_id} not found")
        
        # Report progress
        self.update_state(
            state='RUNNING',
            meta={'status': 'Building optimization model', 'run_id': run_id}
        )
        
        # Execute optimization (the slow part)
        scheduling_service = SchedulingService(db)
        run, solution = scheduling_service._execute_optimization_for_run(run)
        
        # Return result (automatically stored in Redis)
        return {
            'run_id': run.run_id,
            'status': run.status.value,
            'objective_value': float(run.objective_value) if run.objective_value else None,
            'runtime_seconds': float(run.runtime_seconds) if run.runtime_seconds else None,
            'solutions_count': run.total_assignments or 0
        }
        
    except Exception as e:
        # Store error in database
        try:
            run = db.query(SchedulingRunModel).filter(
                SchedulingRunModel.run_id == run_id
            ).first()
            if run:
                run.status = SchedulingRunStatus.FAILED
                run.error_message = str(e)
                db.commit()
        except:
            pass
        raise
    finally:
        db.close()
```

**Step 4: Frontend Polls for Status**

```javascript
// frontend/src/pages/MySchedulePage.jsx
import { useEffect, useState } from "react";
import api from "@/lib/axios";

export default function OptimizationStatus({ runId }) {
    const [status, setStatus] = useState("PENDING");
    const [result, setResult] = useState(null);
    
    useEffect(() => {
        // Poll every 2 seconds
        const interval = setInterval(async () => {
            try {
                const response = await api.get(`/scheduling/runs/${runId}`);
                const { status, objective_value, completed_at } = response.data;
                
                setStatus(status);
                
                if (status === "SUCCESS") {
                    setResult(response.data);
                    clearInterval(interval);  // Stop polling
                } else if (status === "FAILED") {
                    clearInterval(interval);
                }
            } catch (error) {
                console.error("Error polling status:", error);
            }
        }, 2000);
        
        return () => clearInterval(interval);
    }, [runId]);
    
    return (
        <div>
            <h2>Optimization Status: {status}</h2>
            
            {status === "PENDING" && <p>Waiting in queue...</p>}
            {status === "RUNNING" && <p>Computing optimal schedule...</p>}
            
            {status === "SUCCESS" && (
                <div>
                    <p>✓ Optimization successful!</p>
                    <p>Objective Value: {result.objective_value}</p>
                    <p>Assignments: {result.total_assignments}</p>
                    <p>Runtime: {result.runtime_seconds}s</p>
                </div>
            )}
            
            {status === "FAILED" && (
                <p>✗ Optimization failed: {result?.error_message}</p>
            )}
        </div>
    );
}
```

### 7.2 Understanding `.delay()` Under the Hood

```python
# When you write:
task = run_optimization_task.delay(run_id=789)

# Celery internally does:

class Task:
    def delay(self, *args, **kwargs):
        """
        Send task to broker without waiting for execution.
        
        Returns AsyncResult for monitoring.
        """
        # Step 1: Generate unique task ID
        task_id = generate_uuid()
        
        # Step 2: Serialize arguments
        args_json = json.dumps(args)
        kwargs_json = json.dumps(kwargs)
        
        # Step 3: Create task message
        message = {
            'id': task_id,
            'task': self.name,  # 'app.tasks.optimization_tasks.run_optimization'
            'args': args,
            'kwargs': kwargs,
            'headers': {
                'task_id': task_id,
                'lang': 'py',
                'retries': 0,
                'timelimit': [3600, 3300]
            }
        }
        
        # Step 4: Send to broker
        self.broker.send(
            exchange='celery',
            routing_key='celery',
            body=json.dumps(message),
            properties={
                'correlation_id': task_id,
                'reply_to': 'celery.reply.queue'
            }
        )
        
        # Step 5: Initialize task state in result backend
        self.result_backend.set_state(
            task_id,
            'PENDING',
            result=None
        )
        
        # Step 6: Return AsyncResult for client tracking
        return AsyncResult(task_id=task_id, app=self.app)
```

---

## 8. Summary & Performance Analysis

### 8.1 The Problem Solved

| Without Celery | With Celery |
|---|---|
| Request blocks for 300s | Request returns in <100ms |
| Browser timeout (30s) | No timeout ✓ |
| 100 concurrent users → crash | 1000+ concurrent users possible |
| Thread overhead (200MB) | Minimal overhead |
| No progress tracking | Real-time monitoring (Flower) |
| Entire server blocked | Other requests processed normally |

### 8.2 System Capacity

**Without Celery:**
```
Max concurrent requests: ~100 (browser timeouts after 30s)
Memory per request: 2MB thread stack
Max threads: 1000 (OS limit)
Practical limit: 500 concurrent users (with 4GB RAM)
```

**With Celery (4 workers):**
```
Concurrent HTTP requests: Unlimited (non-blocking)
Worker processes: 4 (solving concurrently)
Queue depth: Unlimited (Redis stores in memory)
Practical capacity: 1000s of concurrent HTTP requests
                    4 concurrent optimizations
                    Remaining queued until worker available
```

### 8.3 Key Metrics

**Timing Breakdown for Single Optimization:**

```
Solver time:           300 seconds (unavoidable, complex computation)
  - Data building:     ~5 seconds
  - Model creation:    ~10 seconds
  - Solving:           ~280 seconds
  - Result storage:    ~5 seconds

Overhead:              <1 second total
  - HTTP request:      50ms
  - Pydantic parsing:  10ms
  - DB query:          30ms
  - Task queuing:      20ms
  - Task dequeue:      10ms
  - Task deserialize:  20ms
  - Result storage:    50ms

Total with Celery:     ~300 seconds (same as solver)
Total without Celery:  300+ seconds + browser timeout (FAILED)
```

### 8.4 Why This Architecture Wins

```
✓ User Experience
  - Immediate feedback (task queued)
  - Can track progress (polling status)
  - No arbitrary timeouts

✓ Scalability
  - Add more workers for higher throughput
  - Each optimization independent
  - No connection limit

✓ Reliability
  - Tasks survive server restart
  - Redis persists queue
  - Failed tasks can be retried

✓ Observability
  - Flower shows real-time status
  - Task metrics and statistics
  - Error tracking and debugging

✓ Resource Management
  - Prevents thread explosion
  - Graceful degradation (queue grows, not memory)
  - Database connection pooling
```

---

## Conclusion

The Celery + Redis architecture is **essential** for this project:

1. **The Problem:** MIP solver takes 300+ seconds, HTTP timeout is 30 seconds → impossible without async
2. **The Solution:** Decouple task submission from execution using message queue
3. **The Components:**
   - **Producer (FastAPI):** Queue task immediately, return task_id
   - **Broker (Redis):** Store tasks, manage state, distribute to workers
   - **Consumer (Celery):** Poll queue, execute tasks, report results
4. **The Monitoring:** Flower provides real-time visibility into queue, workers, and tasks
5. **The Code:** `@celery_app.task` decorator + `.delay()` method = simple, powerful async API

This is a **production-grade solution** for long-running computations in web applications.

---
