---
# 🔬 Smart Scheduling - Deep Dive Internals
## הסבר טכני מעמוק ל"מה קורה בדיוק תחת ההוד"
---

# **TOPIC 1: Celery & Redis - עומק מכאני**

## 1. SERIALIZATION - מה קורה כאשר קוראים `task.delay(run_id=123)`?

### 🔍 תהליך פעם-אחר-פעם:

```python
# קוד בFrontend:
response = requests.post("/api/optimize", json={"weekly_schedule_id": 456})

# קוד בBackend:
@app.post("/api/optimize")
async def optimize(data: OptimizeRequest):
    task = run_optimization_task.delay(run_id=456)  # ← כאן קורה הכישוף!
    return {"task_id": task.id}
```

### 📦 תהליך הSerialization:

```
שלב 1: Python Object
  run_id = 456  (int בזיכרון)

שלב 2: Serialization (Python → JSON)
  Celery + Python-MIP בתצורה ברירת מחדל משתמשת ב-JSON
  
  run_id=456 →
    JSON: "456"  (string בפורמט טקסט)
  
  אם היו לנו complex objects (numpy arrays וכו'):
    Celery היה שולח pickle (binary format, unsecure!)
    או MessagePack (binary, more compact)

שלב 3: Encoding to Bytes
  JSON string "456" →
    UTF-8 bytes: b'456'
    (כל character בJSON הופך ל-bytes)

שלב 4: Task Envelope Creation
  Celery בונה "task message":
  {
    "id": "abc-123-def",
    "task": "backend.app.tasks.run_optimization_task",
    "args": [456],  ← הארגומנטים
    "kwargs": {},
    "exchange": "celery",
    "routing_key": "celery",
    "properties": {
      "correlation_id": "abc-123",
      "reply_to": "celery.reply.queue"
    },
    "headers": {
      "task_id": "abc-123-def",
      "lang": "py",
      "group": null
    }
  }

שלב 5: Serialization של הEnvelope
  כל ה-JSON → bytes שוב
  
שלב 6: לRedis!
```

### 💾 בRedis עכשיו:

```
Redis List (במקום Queue):
  Key: "celery"  (default queue name)
  Value: [
    <serialized message 1>,
    <serialized message 2>,
    ...
  ]

Redis actually stores it as:
  LPUSH celery <serialized_bytes>
```

---

## 2. THE BROKER (Redis) - מבנה נתונים ספציפי

### 🔴 Redis Data Structures שCelery משתמש:

```
1️⃣ LISTS (עיקרי - עבור Task Queue)
   ────────────────────────────
   
   Key: "celery"  (Queue name)
   Type: List
   
   Redis command: LPUSH celery <task_payload>
   
   מבנה:
   ┌──────────────────────────────────┐
   │ celery (List)                    │
   ├──────────────────────────────────┤
   │ [0] → {"task": "run_opt...", ... │  ← למחוק עם RPOP
   │ [1] → {"task": "run_opt...", ... │
   │ [2] → {"task": "run_opt...", ... │
   └──────────────────────────────────┘
   
   Worker עושה RPOP (Right Pop) בלולאה
   (מקבל מהקצה הימני, מטבעות מהשמאל)

2️⃣ HASH MAPS (עבור Task State)
   ─────────────────────────────
   
   Key: "celery-task-meta-<task_id>"
   Type: Hash
   
   Value:
   {
     "status": "PENDING",  → שלאחר זמן: "STARTED", "SUCCESS", "FAILURE"
     "result": null,       → אחרי בדיקה: <actual result>
     "traceback": null,
     "children": [],
     "date_done": null
   }
   
   Frontend עושה Polling כדי לבדוק:
   GET celery-task-meta-abc-123-def → {"status": "PENDING"}
   (אחרי 2 שניות)
   GET celery-task-meta-abc-123-def → {"status": "RUNNING"}
   (אחרי עוד 30 שניות)
   GET celery-task-meta-abc-123-def → {"status": "SUCCESS", "result": {...}}

3️⃣ SETS (עבור Task Acks ו-Reservations - complex)
   ──────────────────────────────────────────────
   
   כשWorker קורא task:
     - מוסיף את task_id לSET של "active tasks"
     - אם Worker nope כמו 5 דקות ללא "heartbeat" → removes automatically
```

### 📋 Task Payload בRedis - מה זה למעשה?

```json
{
  "body": [
    "[456]",  // args: [run_id=456]
    {},       // kwargs: empty
    {
      "callbacks": null,
      "errbacks": null,
      "chain": null,
      "chord": null
    }
  ],
  "headers": {
    "lang": "py",
    "task": "backend.app.tasks.run_optimization_task",
    "id": "c4f53-8a92-4d21-9e8e-abc123def456",
    "shadow": null,
    "eta": null,
    "expires": null,
    "group": null,
    "retries": 0,
    "timelimit": [3600, 3300],  // Hard limit 1h, Soft 55m
    "parent_id": null,
    "root_id": "c4f53-8a92-..."
  },
  "content-encoding": "utf-8",
  "content-type": "application/json"
}
```

---

## 3. THE WORKER - איך הוא יודע שיש Task?

### 🤖 Worker Loop - לא Busy Wait!

```python
# Celery Worker בפועל עשה משהו כמו:

def worker_main_loop():
    while True:
        # ❌ זה לא busy wait! 
        # מדוע? כי זה היה בזבוז מחוז CPU
        
        # ✅ זה מה שאמת קורה:
        
        # 1. Block on Redis (תשומת לב!)
        #    Worker עומד בחכייה עד שתגיע task (OS level blocking)
        task = redis.BRPOP("celery", timeout=1)
        #    ↑ BRPOP = "Blocking Right Pop"
        #    Worker SLEEPS עד שיש משהו בתור
        
        if task:
            # 2. Mark as started
            update_task_state(task_id, "STARTED")
            
            # 3. Execute
            result = run_optimization_task(task.args[0])
            
            # 4. Mark as done
            update_task_state(task_id, "SUCCESS", result=result)
        else:
            # timeout hit, continue loop
            continue
```

### ⚙️ Prefetch Multiplier - מה זה בדיוק?

```
ברירת מחדל: worker_prefetch_multiplier = 4
(בפרויקט שלך: 1, כי MaxTasksPerChild = 50)

מה זה עשה?

scenario: Queue יש 10 tasks

Prefetch=4:
  Worker קורא 4 tasks מ-Redis בבת אחת
  ┌────────────┐
  │ Redis      │
  │ Queue [10] │
  └────────────┘
         │
  BRPOP x4
         │
         ▼
  ┌────────────────────┐
  │ Worker Memory      │
  │ [task1, task2,     │
  │  task3, task4] ←   │ In-memory prefetch buffer
  └────────────────────┘
  
  Worker עובד על task1
  בו זמנית, הוא כבר קרא את 2,3,4 מהרחוב
  
  Advantages:
    ✅ אם task1 + task2 קטנים, Worker לא חוזר ל-Redis
    ✅ ניצול בנדווידת מהיר יותר
  
  Disadvantages:
    ❌ אם Worker נפל עם task3 במזיכרון = הוא lost (לא ב-Redis)
    ❌ Memory overhead אם tasks גדולים

בפרויקט שלך:
  prefetch_multiplier = 1
  → Worker קורא רק 1 task בבת אחת
  → יותר safe (אבל קצת יותר slow)
```

---

## 4. THE "WHY" - Python Thread vs. Celery - איזה משאב יסתיים ראשון?

### 🔥 Load Test: 100 Users × 300-second Solve

#### Scenario A: Simple Python Threads (❌ גרוע)

```python
# בFastAPI בלי Celery:
@app.post("/optimize")
async def optimize(data):
    # Just call directly!
    result = solver.solve()  # Blocks for 300 seconds
    return result
```

```
הבעיה:
  - כל בקשה = נוצרת Thread בJVM/OS
  - 100 בקשות בו-זמנית = 100 threads חסומות
  - כל thread = ~2MB stack memory (default)
  - Total: 100 * 2MB = 200MB רק לstacks!
  
  אם המכונה יש 4GB RAM:
    Memory limit reached ≈ 2000 threads
    
    But:
    ❌ GIL (Global Interpreter Lock) בPython!
    → אפילו עם threads, רק אחד בריץ בפועל
    → 99 threads חוכים
    → Context switches = בזבוז CPU
    
    ❌ File Descriptors!
    → כל connection HTTP = 1 file descriptor (FD)
    → Linux default limit: 1024 FDs per process
    → אחרי 1024 connections: "Too many open files" ❌
```

### מה ייסתיים ראשון?

```
1️⃣ File Descriptors (1024) ← זה הראשון! ❌

   כל HTTP connection צורך 1 FD
   Server crash ב-1000 בקשות בו-זמנית
   
   Error: "OSError: [Errno 24] Too many open files"

2️⃣ Memory (2GB for threads)
   100 threads * 2MB = 200MB - בסדר
   1000 threads * 2MB = 2GB - OOM Killer kills process
   
3️⃣ GIL (Global Lock)
   לא בדיוק "runs out" אבל context switches
   מוריד throughput משמעותית
```

#### Scenario B: Celery + Redis (✅ טוב)

```
100 בקשות:
  - FastAPI handler: 100ms כל אחת (non-blocking!)
  - Tasks ב-Redis: מהדורות לקו מחיצה
  - 4 Celery Workers: חלוקת העבודה
  
  Memory:
    - FastAPI: ~100MB (constant)
    - 4 Worker processes: 4 * 300MB = 1.2GB
    - Redis: ~100MB
    Total: ~1.4GB (predictable!)
  
  File Descriptors:
    - FastAPI: ~20-50 FDs
    - Redis: ~10 FDs
    - Workers: ~5 FDs each * 4 = 20 FDs
    Total: ~100 FDs (מתחת לגבול של 1024)
  
  GIL:
    - ❌ כל Worker תהליך משלו (separate Python interpreter)
    - ✅ אין GIL בין processes (רק בתוך)
    - ✅ True parallelism!
```

---

---

# **TOPIC 2: MIP Solver Black Box - Branch and Bound**

## 1. The Search Tree - Branch and Bound (B&B)

### 📊 המראה הכללי:

```
בעיה: הקצה 50 עובדים × 100 משמרות × 5 תפקידים

אם נשתמש בBrute Force:
  - מספר משתנים: 50 * 100 * 5 = 25,000 בינארים
  - Combinations: 2^25000 (כלומר... תוך 10^7000 שניות)
  - ❌ בלתי אפשרי

פתרון: Branch and Bound!
  - סדר חיפוש חכם
  - גיזום (Pruning) של ענפים חסרי תקווה
```

### 🌳 דוגמה קטנה - 3 משתנים בינאריים

```
מטרה: Maximize: 2*x1 + 3*x2 + x3 (כאשר x1,x2,x3 ∈ {0,1})

שלב 1: Linear Relaxation (treat as continuous)
  ────────────────────────────────────────
  x1, x2, x3 ∈ [0, 1] (continuous)
  
  Solution: x1=1, x2=1, x3=1 → Objective = 2 + 3 + 1 = 6
  (אם היו קיימים אילוצים נוספים, היינו קצת פחות מ-6)

  זה **Upper Bound** = 6
  → אנחנו יודעים שהפתרון השלם לעולם לא יעלה על 6

שלב 2: Branch on x1
  ───────────────
  
           [Root: UB=6]
           /         \
        /               \
  [x1=0]              [x1=1]
  UB=4.5              UB=5.8
    /                   /
   /                    \
Branch on x2          Branch on x2
(x1=0)                (x1=1)
     
שלב 3: Solve each subproblem
  ─────────────────────────
  
  Subproblem: x1=0, x2=1, x3∈[0,1]
    Objective ≤ 0 + 3 + 1 = 4 (Upper Bound)
    → אם אנחנו כבר מצאנו פתרון עם 4, prune!
    
  Subproblem: x1=1, x2=1, x3=0
    Objective = 2 + 3 + 0 = 5 (Integer feasible!)
    → זה פתרון חוקי, update best found = 5

שלב 4: Pruning
  ───────────
  
  אם שני נוכל:
    - מצאנו בר = 5
    - Branch בן יש Upper Bound = 4.5
    
  → PRUNE! לעולם לא תוכל להיות טוב מ-5
```

### 🔪 Pruning Rules (יסוד המהירות!)

```
כלל 1: Bound Pruning
  ────────────────
  אם Upper Bound של Branch < Best Found So Far
  → Prune (לעולם לא תוכל להיות ההצעה הטובה ביותר)

כלל 2: Infeasibility Pruning
  ──────────────────────────
  אם הsub-problem הוא INFEASIBLE
  → Prune (אין פתרון כאן)

כלל 3: Integrality Pruning
  ───────────────────────
  אם כל המשתנים בפתרון הם כבר 0 או 1
  → יש לנו פתרון שלם! Save it, don't branch further
```

---

## 2. Linear Relaxation - למה זה טריק אמיתי?

### 🔓 מה קורה כשמתעלמים מהמגבלה של "בינארי"?

```
בעיה מקורית:
  max: 2*x1 + 3*x2 + x3
  s.t.
    x1 + x2 <= 1.5  (constraint)
    x1, x2, x3 ∈ {0, 1}  (binary!)

Linear Relaxation:
  max: 2*x1 + 3*x2 + x3
  s.t.
    x1 + x2 <= 1.5
    x1, x2, x3 ∈ [0, 1]  (continuous!)
    
  Relaxed Solution:
    x1 = 0.5, x2 = 1, x3 = 1
    Objective = 2*0.5 + 3*1 + 1 = 5.5
    
  זה Upper Bound!
  → פתרון שלם לעולם לא יעלה על 5.5
```

### 🎯 למה זה מהיר?

```
1. Linear Programs הם קלים לפתור!
   → Simplex Algorithm יכול לפתור בשניות
   → אפילו עם 1 מיליון משתנים!

2. Upper Bound מיד מועיל!
   - עם Upper Bound = 5.5
   - אם אנחנו מצאנו פתרון בן 5
   - אנחנו יודעים: optimal ∈ [5, 5.5]
   - הפער הוא קטן!
   
   אם עדיין לא מצאנו פתרון:
   - ניתן להמשיך לבדוק רק branches עם potential

3. Pruning טוב יותר!
   - יותר branches מופשלות
   - החיפוש עץ הוא קטן יותר
```

---

## 3. Mathematical Equation - No Overlap Constraint

### 📐 עבור משמרות חופפות, משתנה יחיד

```
תרגום מPython ל-Math:

# Python:
for emp in employees:
    for shift1, shift2 in overlapping_pairs:
        for role in roles:
            if (emp, shift1, role) in x and (emp, shift2, role) in x:
                model += x[(emp, shift1, role)] + x[(emp, shift2, role)] <= 1

# Math (עבור עובד specific i, תפקיד specific r):

∑_{s∈S_overlapping(shift1)} x_{i,s,r} + x_{i,shift1,r} ≤ 1

או בדרך יותר פשוטה לשתי משמרות חופפות:

x_{i, shift1, r} + x_{i, shift2, r} ≤ 1

כאשר:
  i = employee index
  shift1, shift2 = overlapping shift indices
  r = role id
  x_{i,j,r} ∈ {0, 1} = binary variable
```

### אם יש N overlapping shifts:

```
עבור עובד ומשמרות מרובות שחופפות בחלקן:

∑_{j ∈ shifts_that_overlap_with_shift1} x_{i,j,r} ≤ 1

זה מוודא: עובד יכול להיות בלכל היותר 1 מהמשמרות החופפות
```

---

## 4. Pruning Logic - Score 100 vs. UB 80

### 🎯 ה-Moment of Truth:

```
Scenario:
  - Best solution found so far: Score = 100
  - Current branch being explored:
    * Relaxation gives UB = 80
    * (כלומר, אפילו בעולם מושלם, 80 הוא המקסימום)

Logic:
  ┌─────────────────────────────────┐
  │ if (current_branch_UB < best):  │
  │   PRUNE this entire branch!     │
  └─────────────────────────────────┘
  
  כאן:
    UB = 80
    best = 100
    80 < 100? YES!
    
    → PRUNE!
    
  מדוע?
    - זה impossible שנמצא משהו טוב יותר מ-100 בבranch זה
    - כל הילדים של branch זה יהיו בטח עם score ≤ 80
    - כל עבודה נוספת כאן היא בזבוז
```

### 📊 דוגמה עם ספירה:

```
בלי Pruning:
  2^n אפשרויות = 2^25000 (לדוגמה)
  Time: ∞ שניות

עם Pruning (תקציר):
  Start: 100 branches
  ↓ (לאחר Linear Relaxation של כל אחד)
  ↓ Prune 70 branches (UB < best)
  ↓ Explore 30 branches further
  ↓ Branch further: 30 * 2 = 60
  ↓ Prune 50: 10 remain
  ↓ ... iterate until convergence
  
  Final explored: ~150-200 nodes (אם הparameters טובים)
  
  Time: שניות עד דקות (בעקום שבחרנו)!
```

---

---

# **TOPIC 3: Application Stack - Pydantic, ORM, Database**

## 1. Pydantic vs. Dict - למה Schemas?

### 🆚 השוואה:

```python
# ❌ ללא Pydantic (Just Dicts):
@app.post("/optimize")
def optimize(data: dict):
    run_id = data["weekly_schedule_id"]
    # בעיות:
    # - run_id could be "not a number" → string!
    # - data could be {"random_field": 123}
    # - No type checking
    # - No IDE autocomplete

# ✅ עם Pydantic:
from pydantic import BaseModel

class OptimizeRequest(BaseModel):
    weekly_schedule_id: int

@app.post("/optimize")
def optimize(data: OptimizeRequest):
    run_id = data.weekly_schedule_id  # ✅ guaranteed int!
```

### 📋 Data Parsing vs. Validation:

```
PARSING (ממיר סוגים):
  ───────────────────
  
  JSON Input:
    {"weekly_schedule_id": "456"}  ← string!
  
  Pydantic Parsing:
    "456" (string) → 456 (int)
    
  Explicit Coercion Rules:
    "456" → int("456") → 456 ✅
    "abc" → int("abc") → ValueError ❌
    456 (already int) → 456 ✅

VALIDATION (בודק נכונות):
  ──────────────────────
  
  After parsing (data is already correct type):
    weekly_schedule_id = 456 (int)
  
  Validators can check:
    - Is 456 a valid weekly_schedule_id? (exists in DB?)
    - Is 456 > 0? (positive?)
    - Is 456 < 1000000? (reasonable range?)
    
  Example:
    class OptimizeRequest(BaseModel):
        weekly_schedule_id: int
        
        @field_validator('weekly_schedule_id')
        def validate_schedule(cls, v):
            if v < 1:
                raise ValueError('Must be positive')
            return v
```

### 🔥 Runtime Behavior - String to Int:

```python
# Frontend sends:
json_data = {"weekly_schedule_id": "456"}

# Backend FastAPI:
request = OptimizeRequest(**json_data)

# Step-by-step in Pydantic:
1. Parse JSON string "456" → Python object {"weekly_schedule_id": "456"}
2. Check schema: weekly_schedule_id is int, got str
3. Try coerce: int("456") → 456
4. Success! request.weekly_schedule_id = 456 (now int)

# If it was invalid:
json_data = {"weekly_schedule_id": "not_a_number"}

1. Parse JSON → {"weekly_schedule_id": "not_a_number"}
2. Check schema: int expected, got str
3. Try coerce: int("not_a_number") → ValueError
4. Pydantic catches: raises ValidationError
5. FastAPI returns: HTTP 422 Unprocessable Entity
   {
     "detail": [
       {
         "type": "value_error",
         "loc": ["body", "weekly_schedule_id"],
         "msg": "value is not a valid integer"
       }
     ]
   }
```

---

## 2. SQLAlchemy - Session & Transaction (ACID)

### 🔄 מה קורה עם `db.add(model)`?

```python
# Code:
session = SessionLocal()
run = SchedulingRunModel(
    weekly_schedule_id=456,
    status="PENDING"
)
session.add(run)  # ← What happens?
session.commit()
```

### Step-by-step:

```
שלב 1: session.add(run)
  ────────────────────
  
  ✅ Add to session's identity map
  └─ session._identity_map[id(run)] = run
  
  ✅ Mark as "pending" (not yet in DB)
  └─ run._sa_instance_state.persistent = False
  
  ❌ NOT in database yet!
  └─ No SQL executed!
  
  זה חיזוי בלבד של memory

שלב 2: session.commit()
  ──────────────────────
  
  ✅ Session flush (ייצוא לDB)
    INSERT INTO scheduling_run (weekly_schedule_id, status)
    VALUES (456, 'PENDING')
    RETURNING id;
  
  ✅ Commit transaction
    COMMIT;
  
  ✅ Mark as persistent
    run._sa_instance_state.persistent = True
    run.id = <generated_id>
  
  נתונים בDB!
```

### 📊 Transaction & ACID:

```
ACID = Atomicity, Consistency, Isolation, Durability

בהקשר שלנו (scheduling):

ATOMICITY:
  ──────
  
  כאשר אנחנו יוצרים SchedulingRun וכל SchedulingSolutions:
  
  transaction = [
    INSERT INTO scheduling_run (status) VALUES ('PENDING'),
    INSERT INTO scheduling_solution (run_id, user_id, ...) VALUES (...),
    INSERT INTO scheduling_solution (run_id, user_id, ...) VALUES (...),
    ... 1000 more inserts ...
  ]
  
  commit();
  
  אם הקובץ וה-1001 insert נכשל:
    → Entire transaction rolled back
    → 0 שורות בDB
    → No orphan records
    
  מדוע זה critical לScheduling?
    - SchedulingRun ללא Solutions = חסר מטרה
    - Solutions ללא Run = orphaned data
    - Atomicity = או כל או כלום!

CONSISTENCY:
  ──────────
  
  Foreign keys enforced:
    INSERT INTO scheduling_solution (run_id, user_id, ...)
    VALUES (999, 888, ...)
    
  אם run_id=999 לא קיים → ERROR! (FK violation)
  
  Constraints enforced:
    MAX_HOURS_PER_WEEK must be valid
    UNIQUE constraints honored

ISOLATION:
  ───────
  
  אם 2 users לוקחות optimization בו-זמנית:
  
  User A: SELECT weekly_schedule_id=1
  User B: SELECT weekly_schedule_id=1
  
  עם ACID isolation:
    - User A בטוח שB לא יעדכן את זה בעמצע
    - כל Transaction בבדדו (even if concurrent)

DURABILITY:
  ──────────
  
  אחרי COMMIT:
    - נתונים כתובים לדיסק
    - אפילו אם server crashing, data survives
    - Recovery מPower Loss מובטח
```

---

## 3. PostgreSQL vs. NoSQL (Mongo) - למה Relational?

### 🆚 ההשוואה:

```
SCHEDULING REQUIREMENTS:

1. Complex Relations
   ──────────────
   
   User ← has many → Role
   User ← works → Shift
   Shift ← requires → Role
   User ← has-preferences → Shift
   
   SQL (Joins):
     SELECT u.name, s.date, r.name
     FROM users u
     JOIN scheduling_solution ss ON u.id = ss.user_id
     JOIN planned_shift s ON ss.planned_shift_id = s.id
     JOIN role r ON ss.role_id = r.id
     WHERE s.weekly_schedule_id = 456;
   
   (Clean, Declarative)
   
   MongoDB (Embedded/References):
     db.users.find({...}).aggregate([
       {$lookup: {from: "scheduled", ...}},
       {$lookup: {from: "shifts", ...}},
       ...
     ])
   
   (Complex, verbose)

2. Data Integrity (FOREIGN KEYS)
   ─────────────────────────────
   
   SQL:
     ALTER TABLE scheduling_solution
     ADD CONSTRAINT fk_user
     FOREIGN KEY (user_id)
     REFERENCES users(id)
     ON DELETE RESTRICT;
   
   → Database enforces:
     Can't delete user if they have assignments!
   
   MongoDB:
     No enforced FKs!
     → Data corruption possible:
       {user_id: 999} but user 999 doesn't exist
   
   → Application must handle (error-prone)

3. ACID Transactions
   ─────────────────
   
   SQL (Multi-row):
     BEGIN;
     INSERT INTO scheduling_run ...
     INSERT INTO scheduling_solution ... (1000 rows)
     COMMIT;
   
   → All or nothing guarantee
   
   MongoDB:
     Single-document ACID (limited)
     Multi-document ACID (added in 4.0+, less mature)
   
   → Risk of partial failures

4. Querying Flexibility
   ────────────────────
   
   Questions we ask:
     - Find all employees assigned to shift X
     - Find all shifts a user is assigned to
     - Find overlaps
     - Aggregate hours per employee
   
   SQL:
     SELECT * FROM scheduling_solution
     WHERE planned_shift_id = 456;
     
     (1 query, very fast)
   
   MongoDB:
     db.scheduling_solution.find({
       planned_shift_id: ObjectId("...")
     })
     
     (OK, but embedded docs make it harder)

CONCLUSION:
───────────

✅ PostgreSQL דוברת:
  - Complex relationships (many JOINs)
  - Strong consistency (ACID)
  - Referential integrity
  - This is relational data!

❌ MongoDB עדיף:
  - Flexible schema (but ours is fixed!)
  - Horizontal scaling (we don't need, single DB)
  - Document querying (document structure not ideal for scheduling)
```

### 📊 Schema Comparison:

```
POSTGRES (Relational - Normalized):
─────────────────────────────────

TABLE users:
  id INT PRIMARY KEY
  name VARCHAR
  roles INT[] (array of role IDs)

TABLE scheduling_solution:
  id INT PRIMARY KEY
  run_id INT FOREIGN KEY → scheduling_run
  user_id INT FOREIGN KEY → users
  shift_id INT FOREIGN KEY → planned_shift
  role_id INT FOREIGN KEY → roles

Queries are clean:
  SELECT COUNT(*) FROM scheduling_solution
  WHERE user_id = 123 AND role_id = 1;

MONGODB (Document - Denormalized):
──────────────────────────────────

Document structure:
  db.scheduling_solutions.insertOne({
    _id: ObjectId(...),
    run: {
      id: 1,
      status: "PENDING",
      started_at: Date(...),
      config: { weight_fairness: 0.5, ... }
    },
    user: {
      id: 123,
      name: "John",
      roles: [1, 2, 3]
    },
    shift: {
      id: 456,
      date: Date(...),
      start: Time(...),
      end: Time(...)
    },
    role: {
      id: 1,
      name: "Waiter"
    }
  })

Queries are verbose:
  db.scheduling_solutions.find({
    "user.id": 123,
    "role.id": 1
  }).count()

Problems:
  - If user 123 is updated, every document with that user needs update
  - Data duplication + consistency risk
```

---

---

# 🎓 **Summary - Key Concepts to Memorize:**

## CELERY & REDIS:
1. **Serialization**: Python objects → JSON → UTF-8 bytes → Redis
2. **Broker**: Redis Lists (LPUSH/RPOP), Hash Maps (task state)
3. **Worker**: BRPOP (blocking), not busy-wait; Prefetch = in-memory buffer
4. **Why not Threads**: File Descriptors run out at 1024 connections (before memory/GIL)

## MIP SOLVER:
1. **Branch and Bound**: Tree search with pruning; Upper Bound guide
2. **Linear Relaxation**: Relax binary→continuous to get fast UB; helps pruning
3. **No Overlap**: x[i,shift1,r] + x[i,shift2,r] ≤ 1
4. **Pruning Logic**: If (current_UB < best_found) → Prune entire branch

## PYDANTIC & ORM:
1. **Parsing vs. Validation**: Parsing converts types; validation checks correctness
2. **Session & ACID**: add() marks pending; commit() executes SQL; Atomicity = all-or-nothing
3. **PostgreSQL**: Relational, Foreign Keys, ACID → perfect for scheduling complexity

---
