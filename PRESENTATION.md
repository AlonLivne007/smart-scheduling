# Smart Scheduling - מערכת אופטימיזציה של משמרות עובדים עם MIP

מערכת אוטומטית ליצירת לוחות זמנים שבועיים באמצעות **Mixed Integer Programming (MIP)**. המערכת מאזנת בין העדפות עובדים, זמינות, כיסוי תפקידים והוגנות בעומס עבודה.

---

## 📑 תוכן עניינים

- [1. מטרות הפרויקט](#1-מטרות-הפרויקט)
- [2. טכנולוגיות מרכזיות](#2-טכנולוגיות-מרכזיות)
- [3. ארכיטקטורת המערכת](#3-ארכיטקטורת-המערכת)
- [4. עיבוד רקע: Celery, Redis ו-Flower](#4-עיבוד-רקע-celery-redis-ו-flower)
- [5. בניית מודל האופטימיזציה](#5-בניית-מודל-האופטימיזציה)
- [6. מודל MIP: משתני החלטה, אילוצים ופונקציית מטרה](#6-מודל-mip-משתני-החלטה-אילוצים-ופונקציית-מטרה)
  - [6.1 משתני החלטה](#61-משתני-החלטה)
  - [6.2 אילוצים קשים](#62-אילוצים-קשים)
  - [6.3 אילוצים רכים](#63-אילוצים-רכים)
  - [6.4 פונקציית מטרה](#64-פונקציית-מטרה)
- [סיכום](#סיכום)

---

## 1️⃣ מטרות הפרויקט

### 🎯 הבעיה שהמערכת פותרת

- **📋 ניהול ידני מורכב**: יצירת לוח זמנים שבועי עם עשרות עובדים, משמרות ותפקידים דורש שעות עבודה
- **⚖️ קונפליקטים ואי-הוגנות**: קושי לאזן בין העדפות עובדים, זמינות, כיסוי תפקידים והוגנות בעומס עבודה
- **🔒 אילוצים מורכבים**: שעות מנוחה מינימליות, מקסימום שעות שבועי, חפיפות משמרות, חופשות מאושרות

### 👥 למי מיועדת המערכת

- **👔 מנהלי משמרות** (Restaurant Managers, Shift Supervisors)
- **🏢 מחלקות משאבי אנוש** המנהלות לוחות זמנים שבועיים
- **👤 עובדים** המבקשים לראות את המשמרות שלהם ולעדכן העדפות

### ✅ מדדי הצלחה

- **⚖️ הוגנות**: חלוקה מאוזנת של משמרות בין עובדים (מינימום סטייה מהממוצע)
- **✅ כיסוי מלא**: כל משמרת מקבלת את כל התפקידים הנדרשים (Coverage = 100%)
- **😊 העדפות עובדים**: מקסימום שביעות רצון מהתאמה להעדפות (preference scores)
- **⚡ הפחתת עבודה ידנית**: מ-4-6 שעות ליצירת לוח זמנים שבועי → דקות ספורות
- **🎯 איכות פתרון**: פתרון אופטימלי או קרוב לאופטימלי (MIP gap < 1%)

---

## 2️⃣ טכנולוגיות מרכזיות

### 🔧 Backend

| טכנולוגיה         | תיאור                                            |
| ----------------- | ------------------------------------------------ |
| **FastAPI**       | Framework מודרני ל-API עם OpenAPI docs אוטומטיים |
| **PostgreSQL 14** | מסד נתונים יחסי                                  |
| **SQLAlchemy**    | ORM לניהול מודלים (15 מודלים)                    |
| **Celery 5.3+**   | עיבוד רקע אסינכרוני                              |
| **Redis 7**       | Message broker עבור Celery                       |

### 🎨 Frontend

| טכנולוגיה    | תיאור               |
| ------------ | ------------------- |
| **React 19** | UI framework מודרני |

### ⚙️ Optimization Engine

| טכנולוגיה                | תיאור                                         |
| ------------------------ | --------------------------------------------- |
| **Python-MIP >= 1.15.0** | ספריית MIP                                    |
| **CBC Solver**           | פתרון MIP open-source (bundled עם Python-MIP) |

### 🐳 Deployment

| טכנולוגיה          | תיאור                      |
| ------------------ | -------------------------- |
| **Docker**         | קונטיינריזציה              |
| **Docker Compose** | אורכיסטרציה של כל השירותים |

**שירותים ב-Docker Compose:**

- `db` (PostgreSQL)
- `backend` (FastAPI)
- `frontend` (React/Vite)
- `redis` (Celery broker)
- `celery-worker` (background tasks)
- `flower` (Celery monitoring)

---

## 3️⃣ ארכיטקטורת המערכת

### 🏗️ רכיבים מרכזיים

```
┌─────────────────┐
│   Frontend      │  React 19 + Vite + TailwindCSS
│   (Port 5173)   │  └─ API calls via Axios
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│   Backend API   │  FastAPI (Port 8000)
│   (FastAPI)     │  └─ Controllers → Services → Models
└────────┬────────┘
         │
    ┌────┴────┬──────────────┬──────────────┐
    │         │              │              │
    ▼         ▼              ▼              ▼
┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│   DB   │ │  Celery  │ │Optimization│ │Constraint│
│PostgreSQL│ │  Worker  │ │DataBuilder│ │ Service  │
│  :5432  │ │  (Redis) │ │            │ │          │
└────────┘ └──────────┘ └─────┬──────┘ └──────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ MipSolver    │
                        │ (Python-MIP) │
                        │   + CBC      │
                        └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ Scheduling   │
                        │  Solution    │
                        │  (Assignments)│
                        └──────────────┘
```

### 📦 מודולים מרכזיים

#### 1. **SchedulingService**

- **תפקיד**: Orchestrator ראשי של תהליך האופטימיזציה
- **זרימה**: `optimize_schedule()` → `_execute_run()` → `_build_and_solve()`
- **אחריות**: ניהול SchedulingRun records, טיפול בשגיאות, validation

#### 2. **OptimizationDataBuilder**

- **תפקיד**: הכנת נתונים למודל MIP
- **פונקציה עיקרית**: `build()` - איסוף נתונים מ-DB והכנה למודל MIP
- **תוצר**: בניית מטריצות זמינות והעדפות, mapping של אינדקסים

#### 3. **MipSchedulingSolver** (`app/services/scheduling/mip_solver.py`)

- **תפקיד**: בניית ופתרון מודל MIP
- **פונקציה עיקרית**: `solve()` - בניית מודל MIP ופתרון
- **תוצר**: משתני החלטה, אילוצים, פונקציית מטרה

#### 4. **ConstraintService** (`app/services/constraintService.py`)

- **תפקיד**: בדיקת תקינות הפתרון
- **פונקציה עיקרית**: `validate_weekly_schedule()` - בדיקת הפתרון נגד אילוצים קשים
- **בדיקות**: חפיפות, חופשות, שעות מנוחה, מקסימום שעות

### 🔄 זרימת נתונים (End-to-End)

```
User Request (Frontend)
  ↓
API Controller (schedulingRunController.py)
  ↓
SchedulingService.optimize_schedule()
  ↓
OptimizationDataBuilder.build() → OptimizationData
  ↓
MipSchedulingSolver.solve() → SchedulingSolution
  ↓
ConstraintService.validate_weekly_schedule()
  ↓
Response to Frontend: Schedule solution ready
```

---

## 4️⃣ עיבוד רקע: Celery, Redis ו-Flower

### 🎯 למה עיבוד רקע?

תהליך האופטימיזציה של לוח זמנים שבועי יכול לקחת **דקות** (תלוי בגודל הבעיה). ביצוע התהליך באופן סינכרוני יגרום ל:

- ⏱️ **Timeout של בקשות HTTP** (בדרך כלל 30-60 שניות)
- 🔒 **חסימת Thread** של FastAPI
- 😞 **חווית משתמש גרועה** - המשתמש מחכה ללא משוב

**הפתרון**: עיבוד אסינכרוני עם **Celery** ו-**Redis**.

### 🏗️ ארכיטקטורה

```
┌─────────────┐
│  Frontend   │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────────┐
│  FastAPI Backend│
│  (Port 8000)    │
└──────┬──────────┘
       │
       │ 1. Create SchedulingRun (PENDING)
       │ 2. Dispatch Celery Task
       │ 3. Return task_id immediately
       │
       ▼
┌─────────────────┐
│     Redis        │  ← Message Broker
│   (Port 6379)    │  ← Task Queue
└──────┬───────────┘
       │
       │ Task Distribution
       ▼
┌─────────────────┐
│ Celery Worker   │  ← Background Processing
│  (Background)   │  ← Runs optimization
└──────┬──────────┘
       │
       │ Update Status
       ▼
┌─────────────────┐
│   PostgreSQL    │  ← Store Results
└─────────────────┘

┌─────────────────┐
│     Flower      │  ← Monitoring Dashboard
│  (Port 5555)    │  ← Real-time Task Status
└─────────────────┘
```

### 🔧 רכיבים

#### **Redis** - Message Broker

- **תפקיד**: תור הודעות (Message Queue) בין FastAPI ל-Celery Worker
- **שימוש**:
  - FastAPI שולח משימות ל-Redis
  - Celery Worker קורא משימות מ-Redis
  - Redis שומר תוצאות זמניות
- **פורט**: `6379`

#### **Celery Worker** - עיבוד רקע

- **תפקיד**: ביצוע משימות אופטימיזציה ברקע
- **תהליך**:
  1. קורא משימות מ-Redis
  2. מעדכן סטטוס ל-`RUNNING`
  3. מריץ את `SchedulingService._execute_optimization_for_run()`
  4. מעדכן את `SchedulingRun` עם תוצאות
  5. מחזיר תוצאה ל-Redis
- **הגדרות**:
  - `task_time_limit=3600` (שעה מקסימלית)
  - `task_soft_time_limit=3300` (55 דקות soft limit)
  - `worker_max_tasks_per_child=50` (מניעת memory leaks)

#### **Flower** - ניטור ומעקב

- **תפקיד**: Dashboard לניטור משימות Celery בזמן אמת
- **יכולות**:
  - 📊 צפייה במשימות פעילות, ממתינות, מושלמות
  - ⏱️ זמני ביצוע וסטטיסטיקות
  - 🔍 מעקב אחר שגיאות
  - 📈 גרפים ומטריקות
- **גישה**: `http://localhost:5555`

### 🔄 זרימת עבודה

```python
# 1. Frontend שולח בקשה
POST /api/scheduling/optimize?weekly_schedule_id=123

# 2. Backend יוצר רשומה ומשלח משימה
run = SchedulingRunModel(status=PENDING)
db.add(run)
db.commit()

task = run_optimization_task.delay(run.run_id)
return {"run_id": run.run_id, "task_id": task.id}

# 3. Celery Worker מבצע ברקע
@celery_app.task
def run_optimization_task(run_id):
    run.status = RUNNING
    scheduling_service._execute_optimization_for_run(run)
    run.status = COMPLETED
    return results

# 4. Frontend בודק סטטוס (Polling)
GET /api/scheduling/runs/{run_id}
→ {"status": "COMPLETED", "objective_value": 123.45, ...}
```

### ✅ יתרונות

- ⚡ **תגובה מהירה**: API מחזיר מיד (לא מחכה לסיום האופטימיזציה)
- 🔄 **Scalability**: ניתן להוסיף מספר Celery Workers
- 📊 **ניטור**: Flower מספק visibility מלא
- 🛡️ **Resilience**: משימות נשמרות ב-Redis גם אם Worker נופל
- ⏱️ **Timeout Management**: הגבלת זמן אוטומטית למשימות ארוכות

---

## 5️⃣ בניית מודל האופטימיזציה

### 🔨 תפקיד OptimizationDataBuilder

המודול `OptimizationDataBuilder` אחראי על איסוף והכנת כל הנתונים הנדרשים לבניית מודל MIP.

#### 1. **🗺️ מיפוי תפקידים**

- **`role_requirements`**: `{shift_id: [role_id, ...]}` - אילו תפקידים נדרשים לכל משמרת
- **`employee_roles`**: `{user_id: [role_id, ...]}` - אילו תפקידים יש לכל עובד

#### 2. **📊 בניית מטריצות** (`_build_matrices()`)

- **`availability_matrix`**: `np.ndarray(employees × shifts)` - 1=זמין, 0=לא זמין
- **`preference_scores`**: `np.ndarray(employees × shifts)` - ציון העדפה 0.0-1.0

> **💡 טיפול ב-Time Off מאושר:**
>
> - המערכת בונה `time_off_map`: `{user_id: [(start_date, end_date), ...]}` - מפה של כל חופשות מאושרות
> - ב-`build_availability_matrix()`, עבור כל עובד עם time off מאושר:
>   - אם תאריך המשמרת נופל בתוך תקופת ה-time off (`start_date <= shift_date <= end_date`)
>   - המערכת מסמנת `availability_matrix[i, j] = 0` (לא זמין)
> - **תוצאה**: עובד עם time off מאושר לא יכול להיות משובץ למשמרות בתאריכי החופשה שלו

#### 3. **⚠️ זיהוי קונפליקטים** (`_build_constraints_and_conflicts()`)

- **`shift_overlaps`**: משמרות חופפות (לא ניתן להקצות אותו עובד)
- **`time_off_conflicts`**: עובדים עם חופשות מאושרות
- **`shift_rest_conflicts`**: משמרות שלא מספקות שעות מנוחה מינימליות

#### 4. **⚙️ אילוצי מערכת** (`build_system_constraints()`)

- **`system_constraints`**: `{SystemConstraintType: (value, is_hard)}`
- **דוגמאות**: `MAX_HOURS_PER_WEEK`, `MIN_REST_HOURS`, `MAX_SHIFTS_PER_WEEK`

#### 5. **📋 הקצאות קיימות** (`build_existing_assignments()`)

- **`existing_assignments`**: `{(employee_id, shift_id, role_id)}` - הקצאות שנשמרו

#### 6. **⏱️ משך משמרות** (`build_shift_durations()`)

- **`shift_durations`**: `{shift_id: duration_hours}` - לחישוב שעות שבועיות

---

## 6️⃣ מודל MIP: משתני החלטה, אילוצים ופונקציית מטרה

### 6.1 משתני החלטה

#### 📐 הגדרה מתמטית

```
x(i,j,r) ∈ {0,1}  - משתנה בינארי

כאשר:
  i = אינדקס עובד (0..n_employees-1)
  j = אינדקס משמרת (0..n_shifts-1)
  r = role_id (תפקיד: Waiter, Bartender, Chef, וכו')

x(i,j,r) = 1  אם עובד i מוקצה למשמרת j בתפקיד r
x(i,j,r) = 0  אחרת
```

#### 💡 אינטואיציה

כל משתנה מייצג החלטה: **"האם להקצות עובד X למשמרת Y בתפקיד Z?"**

**משתנים נוצרים רק עבור צירופים תקפים:**

- ✅ עובד זמין למשמרת (`availability_matrix[i,j] == 1`)
  - **כולל בדיקה של time off מאושר**: אם לעובד יש time off מאושר בתאריך המשמרת, `availability_matrix[i,j] = 0` → לא נוצר משתנה
- ✅ עובד בעל התפקיד הנדרש (`role_id in employee_roles[user_id]`)
- ✅ משמרת דורשת את התפקיד (`role_id in shift['required_roles']`)

#### 💻 קוד - יצירת משתנים

```python
def _build_decision_variables(model, data, n_employees, n_shifts):
    x = {}  # {(emp_idx, shift_idx, role_id): var}
    vars_by_emp_shift = {}  # {(emp_idx, shift_idx): [var1, var2, ...]} - for performance
    vars_by_employee = {}  # {emp_idx: [var1, var2, ...]} - for O(1) access

    for emp_idx, emp in enumerate(data.employees):
        for shift_idx, shift in enumerate(data.shifts):
            if data.availability_matrix[emp_idx, shift_idx] != 1:
                continue  # Skip if employee not available

            required_roles = shift.get('required_roles') or []
            if not required_roles:
                continue

            emp_role_ids = set(emp.get('roles') or [])

            # Create variable for each role that employee has AND shift requires
            for role_req in required_roles:
                role_id = role_req['role_id']
                if role_id in emp_role_ids:
                    var = model.add_var(var_type=mip.BINARY, name=f'x_{emp_idx}_{shift_idx}_{role_id}')
                    x[emp_idx, shift_idx, role_id] = var

                    # Build indexes for performance
                    if (emp_idx, shift_idx) not in vars_by_emp_shift:
                        vars_by_emp_shift[(emp_idx, shift_idx)] = []
                    vars_by_emp_shift[(emp_idx, shift_idx)].append(var)

                    # Build employee index for O(1) access
                    if emp_idx not in vars_by_employee:
                        vars_by_employee[emp_idx] = []
                    vars_by_employee[emp_idx].append(var)

    return x, vars_by_emp_shift, vars_by_employee
```

---

### 6.2 אילוצים קשים

#### 6.2.1 אילוצים קשים שלא חלק מ-`system_constraints`

אלה אילוצים **תמיד קשים** שמובנים במערכת ולא ניתן לשנות אותם דרך ה-UI.

##### ✅ Coverage Constraint (כיסוי תפקידים)

- **אינטואיציה**: כל משמרת חייבת לקבל בדיוק את מספר העובדים הנדרש לכל תפקיד
- **נוסחה**:
  ```
  Σ_i x(i,j,r) = required_count[j,r]  לכל j, r
  ```

```python
def _add_coverage_constraints(model, data, x, n_employees, n_shifts):
    for shift_idx, shift in enumerate(data.shifts):
        required_roles = shift.get('required_roles') or []
        if not required_roles:
            continue

        for role_req in required_roles:
            role_id = role_req['role_id']
            required_count = int(role_req['required_count'])

            eligible_vars = [x[emp_idx, shift_idx, role_id] for emp_idx in range(n_employees)
                           if (emp_idx, shift_idx, role_id) in x]

            if not eligible_vars:
                if required_count > 0:
                    raise ValueError(f"Infeasible coverage: shift {shift['planned_shift_id']} "
                                   f"requires role {role_id} count={required_count}, "
                                   f"but no eligible employees exist")
                continue

            model += mip.xsum(eligible_vars) == required_count, \
                    f'coverage_shift_{shift_idx}_role_{role_id}'
```

##### 🔒 Single Role Per Shift (תפקיד אחד למשמרת)

- **אינטואיציה**: עובד לא יכול להיות מוקצה ליותר מתפקיד אחד באותה משמרת
- **נוסחה**:
  ```
  Σ_r x(i,j,r) ≤ 1  לכל i, j
  ```

```python
def _add_single_role_constraints(model, x, vars_by_emp_shift, n_employees, n_shifts):
    for emp_idx in range(n_employees):
        for shift_idx in range(n_shifts):
            if (emp_idx, shift_idx) in vars_by_emp_shift:
                role_vars = vars_by_emp_shift[(emp_idx, shift_idx)]
                if len(role_vars) > 1:  # Only if employee has multiple roles for this shift
                    model += mip.xsum(role_vars) <= 1, f'single_role_emp_{emp_idx}_shift_{shift_idx}'
```

##### ⚠️ No Overlapping Shifts (אין משמרות חופפות)

- **אינטואיציה**: עובד לא יכול להיות מוקצה למשמרות חופפות בזמן
- **נוסחה**:
  ```
  Σ_r x(i,j1,r) + Σ_r x(i,j2,r) ≤ 1  לכל i, (j1,j2) חופפים
  ```

```python
def _add_overlap_constraints(model, data, x, vars_by_emp_shift, n_employees):
    for shift_id, overlapping_ids in data.shift_overlaps.items():
        if not overlapping_ids:
            continue

        shift_idx = data.shift_index[shift_id]
        for overlapping_id in overlapping_ids:
            overlapping_idx = data.shift_index[overlapping_id]

            for emp_idx in range(n_employees):
                vars_shift = vars_by_emp_shift.get((emp_idx, shift_idx), [])
                vars_overlap = vars_by_emp_shift.get((emp_idx, overlapping_idx), [])

                if vars_shift and vars_overlap:
                    model += mip.xsum(vars_shift) + mip.xsum(vars_overlap) <= 1, \
                            f'no_overlap_emp_{emp_idx}_shift_{shift_idx}_{overlapping_idx}'
```

##### 🏖️ Time Off מאושר (Approved Time Off)

- **אינטואיציה**: עובד עם time off מאושר לא יכול להיות משובץ למשמרות בתאריכי החופשה שלו
- **איך זה מטופל**: **לא דרך אילוץ מפורש**, אלא דרך **מטריצת הזמינות**
  - אם לעובד יש time off מאושר בתאריך המשמרת, `availability_matrix[i, j] = 0`
  - ב-`_build_decision_variables()`, אם `availability_matrix[i, j] != 1`, לא נוצר משתנה `x[i, j, role_id]`
  - **ללא משתנה = לא ניתן להקצות**: הפתרון לא יכול להקצות עובד למשמרת אם אין משתנה עבורו

> **💡 למה זה יעיל יותר מאילוץ מפורש?**
>
> - ✅ פחות משתנים = מודל קטן יותר = פתרון מהיר יותר
> - ✅ אין צורך להוסיף אילוצים נוספים למודל
> - ✅ הגישה מבטיחה 100% שלא ניתן להקצות עובד ב-time off (כי אין משתנה)

#### 6.2.2 אילוצים שהם חלק מ-`system_constraints` (קשים)

אלה אילוצים שניתן להגדיר דרך ה-UI כ**קשים** (hard) או **רכים** (soft), בהתאם ל-`is_hard_constraint`. כאן מוצגים כאשר הם מוגדרים כקשים.

##### Minimum Rest Hours (MIN_REST_HOURS)

- **אינטואיציה**: עובד חייב לקבל שעות מנוחה מינימליות בין משמרות
- **נוסחה**: `Σ_r x(i,j1,r) + Σ_r x(i,j2,r) ≤ 1` לכל i, (j1,j2) עם מנוחה לא מספקת

```python
min_rest_constraint = data.system_constraints.get(SystemConstraintType.MIN_REST_HOURS)
if min_rest_constraint and min_rest_constraint[1]:  # is_hard
    for shift_id, conflicting_ids in data.shift_rest_conflicts.items():
        shift_idx = data.shift_index[shift_id]
        for conflicting_id in conflicting_ids:
            conflicting_idx = data.shift_index[conflicting_id]

            for emp_idx in range(n_employees):
                vars_shift = vars_by_emp_shift.get((emp_idx, shift_idx), [])
                vars_conflict = vars_by_emp_shift.get((emp_idx, conflicting_idx), [])

                if vars_shift and vars_conflict:
                    model += mip.xsum(vars_shift) + mip.xsum(vars_conflict) <= 1, \
                            f'min_rest_emp_{emp_idx}_shift_{shift_idx}_{conflicting_idx}'
```

##### Max Shifts Per Week (MAX_SHIFTS_PER_WEEK)

- **אינטואיציה**: עובד לא יכול לעבוד יותר מ-X משמרות בשבוע
- **נוסחה**: `Σ_j Σ_r x(i,j,r) ≤ max_shifts` לכל i

```python
max_shifts_constraint = data.system_constraints.get(SystemConstraintType.MAX_SHIFTS_PER_WEEK)
if max_shifts_constraint and max_shifts_constraint[1]:  # is_hard
    max_shifts = int(max_shifts_constraint[0])
    for emp_idx in range(n_employees):
        emp_vars = self._get_employee_vars(emp_idx, vars_by_employee)
        if emp_vars:
            model += mip.xsum(emp_vars) <= max_shifts, f'max_shifts_emp_{emp_idx}'
```

##### Max Hours Per Week (MAX_HOURS_PER_WEEK)

- **אינטואיציה**: עובד לא יכול לעבוד יותר מ-X שעות בשבוע
- **נוסחה**: `Σ_j Σ_r x(i,j,r) * duration(j) ≤ max_hours` לכל i

```python
max_hours_constraint = data.system_constraints.get(SystemConstraintType.MAX_HOURS_PER_WEEK)
if max_hours_constraint and max_hours_constraint[1]:  # is_hard
    max_hours = max_hours_constraint[0]
    for emp_idx in range(n_employees):
        emp_hours_vars = self._get_employee_hours_vars(emp_idx, vars_by_emp_shift, data)
        if emp_hours_vars:
            model += mip.xsum(emp_hours_vars) <= max_hours, f'max_hours_emp_{emp_idx}'
```

##### Max Consecutive Days (MAX_CONSECUTIVE_DAYS)

- **אינטואיציה**: עובד לא יכול לעבוד יותר מ-X ימים רצופים
- **נוסחה**: עבור כל רצף של `max_consecutive+1` ימים רצופים, `Σ_d works_on_day[i,d] ≤ max_consecutive`
- **מימוש**: משתמש במשתנים בינאריים `works_on_day[i, date]` שמסמנים אם עובד עובד ביום מסוים

```python
max_consecutive_constraint = data.system_constraints.get(SystemConstraintType.MAX_CONSECUTIVE_DAYS)
if max_consecutive_constraint and max_consecutive_constraint[1]:  # is_hard
    max_consecutive = int(max_consecutive_constraint[0])
    # Build works_on_day variables and add constraints for consecutive sequences
    date_to_shifts = self._build_date_to_shifts_mapping(data)
    works_on_day = self._build_works_on_day_variables(...)

    # For each sequence of (max_consecutive+1) consecutive days
    for sequence_dates in consecutive_sequences:
        for emp_idx in range(n_employees):
            day_vars = [works_on_day[(emp_idx, d)] for d in sequence_dates]
            model += mip.xsum(day_vars) <= max_consecutive
```

##### Min Hours Per Week (MIN_HOURS_PER_WEEK)

- **אינטואיציה**: עובד חייב לעבוד לפחות X שעות בשבוע
- **נוסחה**: `Σ_j Σ_r x(i,j,r) * duration(j) ≥ min_hours` לכל i

```python
min_hours_constraint = data.system_constraints.get(SystemConstraintType.MIN_HOURS_PER_WEEK)
if min_hours_constraint and min_hours_constraint[1]:  # is_hard
    min_hours = min_hours_constraint[0]
    for emp_idx in range(n_employees):
        emp_hours_vars = self._get_employee_hours_vars(emp_idx, vars_by_emp_shift, data)
        if emp_hours_vars:
            model += mip.xsum(emp_hours_vars) >= min_hours, f'min_hours_emp_{emp_idx}'
```

##### Min Shifts Per Week (MIN_SHIFTS_PER_WEEK)

- **אינטואיציה**: עובד חייב לעבוד לפחות X משמרות בשבוע
- **נוסחה**: `Σ_j Σ_r x(i,j,r) ≥ min_shifts` לכל i

```python
min_shifts_constraint = data.system_constraints.get(SystemConstraintType.MIN_SHIFTS_PER_WEEK)
if min_shifts_constraint and min_shifts_constraint[1]:  # is_hard
    min_shifts = int(min_shifts_constraint[0])
    for emp_idx in range(n_employees):
        emp_vars = self._get_employee_vars(emp_idx, vars_by_employee)
        if emp_vars:
            model += mip.xsum(emp_vars) >= min_shifts, f'min_shifts_emp_{emp_idx}'
```

---

### 6.3 אילוצים רכים (חלק מ-`system_constraints`)

#### מושג אילוצים רכים

- **אילוצים רכים** = אילוצים שניתן להפר, אך עם עונש (penalty) בפונקציית המטרה
- **Slack Variables**: משתנים עזר שמייצגים את הסטייה מהאילוץ
- **Penalty Weight**: משקל גבוה (100.0) כדי להרתיע הפרות, אך לא למנוע אותן

#### Minimum Hours Per Week (MIN_HOURS_PER_WEEK - Soft)

- **אינטואיציה**: רצוי שכל עובד יעבוד לפחות X שעות, אך אם לא ניתן - יש עונש
- **נוסחה**: `deficit_i = max(0, min_hours - Σ_j Σ_r x(i,j,r) * duration(j))`

```python
min_hours_constraint = data.system_constraints.get(SystemConstraintType.MIN_HOURS_PER_WEEK)
if min_hours_constraint and not min_hours_constraint[1]:  # is_soft
    min_hours = min_hours_constraint[0]
    for emp_idx in range(n_employees):
        emp_hours_vars = self._get_employee_hours_vars(emp_idx, vars_by_emp_shift, data)
        if emp_hours_vars:
            total_hours = mip.xsum(emp_hours_vars)
            deficit = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'min_hours_deficit_{emp_idx}')
            model += deficit >= min_hours - total_hours
            soft_penalty_component += deficit
```

#### Minimum Shifts Per Week (MIN_SHIFTS_PER_WEEK - Soft)

```python
min_shifts_constraint = data.system_constraints.get(SystemConstraintType.MIN_SHIFTS_PER_WEEK)
if min_shifts_constraint and not min_shifts_constraint[1]:  # is_soft
    min_shifts = int(min_shifts_constraint[0])
    for emp_idx in range(n_employees):
        emp_vars = self._get_employee_vars(emp_idx, vars_by_employee)
        if emp_vars:
            total_shifts = mip.xsum(emp_vars)
            deficit = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'min_shifts_deficit_{emp_idx}')
            model += deficit >= min_shifts - total_shifts
            soft_penalty_component += deficit
```

#### Max Hours Per Week (MAX_HOURS_PER_WEEK - Soft)

- **אינטואיציה**: רצוי שעובד לא יעבוד יותר מ-X שעות בשבוע, אך אם לא ניתן - יש עונש
- **נוסחה**: `excess_i = max(0, Σ_j Σ_r x(i,j,r) * duration(j) - max_hours)`

```python
max_hours_constraint = data.system_constraints.get(SystemConstraintType.MAX_HOURS_PER_WEEK)
if max_hours_constraint and not max_hours_constraint[1]:  # is_soft
    max_hours = max_hours_constraint[0]
    for emp_idx in range(n_employees):
        emp_hours_vars = self._get_employee_hours_vars(emp_idx, vars_by_emp_shift, data)
        if emp_hours_vars:
            total_hours = mip.xsum(emp_hours_vars)
            excess = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'max_hours_excess_{emp_idx}')
            model += excess >= total_hours - max_hours
            soft_penalty_component += excess
```

#### Max Shifts Per Week (MAX_SHIFTS_PER_WEEK - Soft)

- **אינטואיציה**: רצוי שעובד לא יעבוד יותר מ-X משמרות בשבוע, אך אם לא ניתן - יש עונש
- **נוסחה**: `excess_i = max(0, Σ_j Σ_r x(i,j,r) - max_shifts)`

```python
max_shifts_constraint = data.system_constraints.get(SystemConstraintType.MAX_SHIFTS_PER_WEEK)
if max_shifts_constraint and not max_shifts_constraint[1]:  # is_soft
    max_shifts = int(max_shifts_constraint[0])
    for emp_idx in range(n_employees):
        emp_vars = self._get_employee_vars(emp_idx, vars_by_employee)
        if emp_vars:
            total_shifts = mip.xsum(emp_vars)
            excess = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'max_shifts_excess_{emp_idx}')
            model += excess >= total_shifts - max_shifts
            soft_penalty_component += excess
```

#### Min Rest Hours (MIN_REST_HOURS - Soft)

- **אינטואיציה**: רצוי שעובד יקבל שעות מנוחה מינימליות בין משמרות, אך אם לא ניתן - יש עונש
- **נוסחה**: `violation = max(0, Σ_r x(i,j1,r) + Σ_r x(i,j2,r) - 1)` לכל i, (j1,j2) עם מנוחה לא מספקת

```python
min_rest_constraint = data.system_constraints.get(SystemConstraintType.MIN_REST_HOURS)
if min_rest_constraint and not min_rest_constraint[1]:  # is_soft
    for shift_id, conflicting_ids in data.shift_rest_conflicts.items():
        shift_idx = data.shift_index[shift_id]
        for conflicting_id in conflicting_ids:
            conflicting_idx = data.shift_index[conflicting_id]

            for emp_idx in range(n_employees):
                vars_shift = vars_by_emp_shift.get((emp_idx, shift_idx), [])
                vars_conflict = vars_by_emp_shift.get((emp_idx, conflicting_idx), [])

                if vars_shift and vars_conflict:
                    total_assignments = mip.xsum(vars_shift) + mip.xsum(vars_conflict)
                    violation = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'min_rest_violation_emp_{emp_idx}_shift_{shift_idx}_{conflicting_idx}')
                    model += violation >= total_assignments - 1
                    soft_penalty_component += violation
```

#### Max Consecutive Days (MAX_CONSECUTIVE_DAYS - Soft)

- **אינטואיציה**: רצוי שעובד לא יעבוד יותר מ-X ימים רצופים, אך אם לא ניתן - יש עונש
- **נוסחה**: `excess_days = max(0, Σ_d works_on_day[i,d] - max_consecutive)` עבור כל רצף של `max_consecutive+1` ימים רצופים

```python
max_consecutive_constraint = data.system_constraints.get(SystemConstraintType.MAX_CONSECUTIVE_DAYS)
if max_consecutive_constraint and not max_consecutive_constraint[1]:  # is_soft
    max_consecutive = int(max_consecutive_constraint[0])
    date_to_shifts = self._build_date_to_shifts_mapping(data)
    works_on_day = self._build_works_on_day_variables(...)

    # For each sequence of (max_consecutive+1) consecutive days
    for sequence_dates in consecutive_sequences:
        for emp_idx in range(n_employees):
            day_vars = [works_on_day[(emp_idx, d)] for d in sequence_dates]
            if day_vars:
                total_days = mip.xsum(day_vars)
                excess_days = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'max_consecutive_excess_emp_{emp_idx}_days_{start_idx}')
                model += excess_days >= total_days - max_consecutive
                soft_penalty_component += excess_days
```

#### Fairness Deviations (סטיות מהוגנות)

- **אינטואיציה**: רצוי שכל עובד יעבוד מספר דומה של משמרות (הוגנות)
- **מטרה**: למזער את הסטייה המוחלטת של כל עובד מהממוצע
- **למה שני משתנים?** (deviation_pos ו-deviation_neg):
  - אם עובד עובד **יותר** מהממוצע: `emp_total > avg` → `deviation_pos = emp_total - avg`, `deviation_neg = 0`
  - אם עובד עובד **פחות** מהממוצע: `emp_total < avg` → `deviation_pos = 0`, `deviation_neg = avg - emp_total`
  - אם עובד עובד **בדיוק** הממוצע: `emp_total = avg` → `deviation_pos = 0`, `deviation_neg = 0`
- **האילוץ**: `emp_total - avg = deviation_pos - deviation_neg`
  - מבטיח ש-`deviation_pos - deviation_neg` שווה בדיוק לסטייה מהממוצע (חיובית או שלילית)
- **מינימיזציה**: בפונקציית המטרה, אנו ממזערים את `Σ_i (deviation_pos_i + deviation_neg_i)`
  - זה מייצג את **הסטייה המוחלטת** מהממוצע (absolute deviation)
  - ככל שהערך קטן יותר, כל העובדים קרובים יותר לממוצע → הוגנות גבוהה יותר

```python
for emp_idx, emp_total in enumerate(assignments_per_employee):
    deviation_pos = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'dev_pos_{emp_idx}')
    deviation_neg = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'dev_neg_{emp_idx}')

    # emp_total - avg = deviation_pos - deviation_neg
    model += emp_total - avg_assignments == deviation_pos - deviation_neg

    fairness_vars.append(deviation_pos + deviation_neg)  # Absolute deviation
```

**איך זה גורם להתקרבות לממוצע?**

- בפונקציית המטרה, אנו **ממזערים** את `-weight_fairness * Σ_i (deviation_pos_i + deviation_neg_i)`
- מכיוון שזה עם מינוס, מינימיזציה של זה = מקסימיזציה של ההוגנות
- הפתרון יבחר הקצאות שמביאות את כל העובדים קרוב ככל האפשר לממוצע
- אם עובד אחד עובד יותר מדי, זה יגדיל את `deviation_pos` שלו → יגדיל את העונש → הפתרון ינסה לאזן

---

### 6.4 פונקציית מטרה

#### 📊 פירוק למרכיבים

1. **😊 Preference Component** (מקסימיזציה של שביעות רצון)

   ```
   Σ_(i,j,r) preference_scores[i,j] * x(i,j,r)
   ```

   - ככל שהעובד מעדיף את המשמרת, הציון גבוה יותר

2. **⚖️ Fairness Component** (מינימיזציה של אי-הוגנות)

   ```
   -Σ_i (deviation_pos_i + deviation_neg_i)
   ```

   - מינימיזציה של סטיות מהממוצע (מינוס כי זה penalty)

3. **⚠️ Soft Penalty Component** (מינימיזציה של הפרות אילוצים רכים)
   ```
   -100.0 * soft_penalty_component
   ```
   - משקל גבוה (100.0) להרתיע הפרות

#### 📐 נוסחה מלאה

```math
maximize:
    objective = (
        config.weight_preferences * preference_component
        - config.weight_fairness * fairness_component
        - soft_penalty_weight * soft_penalty_component
    )
```

---

## 📊 סיכום

מערכת **Smart Scheduling** מציגה פתרון מלא לאופטימיזציה של משמרות עובדים באמצעות MIP. המערכת משלבת:

### 🎯 יכולות מרכזיות

- **📐 מודל MIP מדויק** עם משתנים x(i,j,r) ותמיכה בתפקידים מרובים
- **🔒 אילוצים קשים ורכים** עם penalties ו-fairness
- **🏗️ ארכיטקטורה נקייה** עם הפרדת אחריות
- **⚡ Background processing** עם Celery, Redis ו-Flower
- **✅ Validation מלא** לפני החזרת הפתרון

### 🚀 טכנולוגיות

| שכבה                 | טכנולוגיות                      |
| -------------------- | ------------------------------- |
| **Frontend**         | React 19, Vite, TailwindCSS     |
| **Backend**          | FastAPI, SQLAlchemy, PostgreSQL |
| **Optimization**     | Python-MIP, CBC Solver          |
| **Background Tasks** | Celery, Redis, Flower           |
| **Deployment**       | Docker, Docker Compose          |

### 📈 תוצאות

- ⚡ **מהירות**: מ-4-6 שעות עבודה ידנית → דקות ספורות
- ⚖️ **הוגנות**: חלוקה מאוזנת של משמרות
- ✅ **כיסוי מלא**: 100% כיסוי תפקידים
- 😊 **שביעות רצון**: מקסימיזציה של העדפות עובדים
