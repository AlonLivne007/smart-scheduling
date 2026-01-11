# Smart Scheduling - מערכת אופטימיזציה של משמרות עובדים עם MIP

מערכת אוטומטית ליצירת לוחות זמנים שבועיים באמצעות **Mixed Integer Programming (MIP)**. המערכת מאזנת בין העדפות עובדים, זמינות, כיסוי תפקידים והוגנות בעומס עבודה.

---

## תוכן עניינים

- [1. מטרות הפרויקט](#1-מטרות-הפרויקט)
- [2. טכנולוגיות מרכזיות](#2-טכנולוגיות-מרכזיות)
- [3. ארכיטקטורת המערכת](#3-ארכיטקטורת-המערכת)
- [4. בניית מודל האופטימיזציה](#4-בניית-מודל-האופטימיזציה)
- [5. מודל MIP: משתני החלטה, אילוצים ופונקציית מטרה](#5-מודל-mip-משתני-החלטה-אילוצים-ופונקציית-מטרה)
  - [5.1 משתני החלטה](#51-משתני-החלטה)
  - [5.2 אילוצים קשים](#52-אילוצים-קשים)
  - [5.3 אילוצים רכים](#53-אילוצים-רכים)
  - [5.4 פונקציית מטרה](#54-פונקציית-מטרה)
  - [5.5 זרימת נתונים מקצה לקצה](#55-זרימת-נתונים-מקצה-לקצה)
- [סיכום](#סיכום)

---

## 1) מטרות הפרויקט

### הבעיה שהמערכת פותרת

- **ניהול ידני מורכב**: יצירת לוח זמנים שבועי עם עשרות עובדים, משמרות ותפקידים דורש שעות עבודה
- **קונפליקטים ואי-הוגנות**: קושי לאזן בין העדפות עובדים, זמינות, כיסוי תפקידים והוגנות בעומס עבודה
- **אילוצים מורכבים**: שעות מנוחה מינימליות, מקסימום שעות שבועי, חפיפות משמרות, חופשות מאושרות

### למי מיועדת המערכת

- **מנהלי משמרות** (Restaurant Managers, Shift Supervisors)
- **מחלקות משאבי אנוש** המנהלות לוחות זמנים שבועיים
- **עובדים** המבקשים לראות את המשמרות שלהם ולעדכן העדפות

### מדדי הצלחה

- **הוגנות**: חלוקה מאוזנת של משמרות בין עובדים (מינימום סטייה מהממוצע)
- **כיסוי מלא**: כל משמרת מקבלת את כל התפקידים הנדרשים (Coverage = 100%)
- **העדפות עובדים**: מקסימום שביעות רצון מהתאמה להעדפות (preference scores)
- **הפחתת עבודה ידנית**: מ-4-6 שעות ליצירת לוח זמנים שבועי → דקות ספורות
- **איכות פתרון**: פתרון אופטימלי או קרוב לאופטימלי (MIP gap < 1%)

---

## 2) טכנולוגיות מרכזיות

### Backend

- **FastAPI** - Framework מודרני ל-API עם OpenAPI docs אוטומטיים
- **PostgreSQL 14** - מסד נתונים יחסי
- **SQLAlchemy** - ORM לניהול מודלים (15 מודלים)
- **Celery 5.3+** - עיבוד רקע אסינכרוני
- **Redis 7** - Message broker עבור Celery

### Frontend

- **React 19** - UI framework

### Optimization Engine

- **Python-MIP >= 1.15.0** - ספריית MIP
- **CBC Solver** - פתרון MIP open-source (bundled עם Python-MIP)

### Deployment

- **Docker** - קונטיינריזציה
- **Docker Compose** - אורכיסטרציה של כל השירותים:
  - `db` (PostgreSQL)
  - `backend` (FastAPI)
  - `frontend` (React/Vite)
  - `redis` (Celery broker)
  - `celery-worker` (background tasks)
  - `flower` (Celery monitoring)

---

## 3) ארכיטקטורת המערכת

### רכיבים מרכזיים

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

### מודולים מרכזיים

1. **SchedulingService**

   - Orchestrator ראשי: `optimize_schedule()` → `_execute_run()` → `_build_and_solve()`
   - ניהול SchedulingRun records, טיפול בשגיאות, validation

2. **OptimizationDataBuilder**

   - `build()` - איסוף נתונים מ-DB והכנה למודל MIP
   - בניית מטריצות זמינות והעדפות, mapping של אינדקסים

3. **MipSchedulingSolver** (`app/services/scheduling/mip_solver.py`)

   - `solve()` - בניית מודל MIP ופתרון
   - משתני החלטה, אילוצים, פונקציית מטרה

4. **ConstraintService** (`app/services/constraintService.py`)
   - `validate_weekly_schedule()` - בדיקת הפתרון נגד אילוצים קשים
   - בדיקת חפיפות, חופשות, שעות מנוחה, מקסימום שעות

### זרימת נתונים (End-to-End)

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

## 4) בניית מודל האופטימיזציה

### תפקיד OptimizationDataBuilder

1. **מיפוי תפקידים**

   - `role_requirements`: `{shift_id: [role_id, ...]}` - אילו תפקידים נדרשים לכל משמרת
   - `employee_roles`: `{user_id: [role_id, ...]}` - אילו תפקידים יש לכל עובד

2. **בניית מטריצות** (`_build_matrices()`)

   - `availability_matrix`: `np.ndarray(employees × shifts)` - 1=זמין, 0=לא זמין
   - `preference_scores`: `np.ndarray(employees × shifts)` - ציון העדפה 0.0-1.0

3. **זיהוי קונפליקטים** (`_build_constraints_and_conflicts()`)

   - `shift_overlaps`: משמרות חופפות (לא ניתן להקצות אותו עובד)
   - `time_off_conflicts`: עובדים עם חופשות מאושרות
   - `shift_rest_conflicts`: משמרות שלא מספקות שעות מנוחה מינימליות

4. **אילוצי מערכת** (`build_system_constraints()`)

   - `system_constraints`: `{SystemConstraintType: (value, is_hard)}`
   - דוגמאות: MAX_HOURS_PER_WEEK, MIN_REST_HOURS, MAX_SHIFTS_PER_WEEK

5. **הקצאות קיימות** (`build_existing_assignments()`)

   - `existing_assignments`: `{(employee_id, shift_id, role_id)}` - הקצאות שנשמרו

6. **משך משמרות** (`build_shift_durations()`)
   - `shift_durations`: `{shift_id: duration_hours}` - לחישוב שעות שבועיות

---

## 5) מודל MIP: משתני החלטה, אילוצים ופונקציית מטרה

### 5.1 משתני החלטה

#### הגדרה מתמטית

- **x(i,j,r) ∈ {0,1}** - משתנה בינארי
  - **i** = אינדקס עובד (0..n_employees-1)
  - **j** = אינדקס משמרת (0..n_shifts-1)
  - **r** = role_id (תפקיד: Waiter, Bartender, Chef, וכו')
  - **x(i,j,r) = 1** אם עובד i מוקצה למשמרת j בתפקיד r, אחרת 0

#### אינטואיציה

- כל משתנה מייצג החלטה: "האם להקצות עובד X למשמרת Y בתפקיד Z?"
- משתנים נוצרים רק עבור צירופים תקפים:
  - עובד זמין למשמרת (`availability_matrix[i,j] == 1`)
  - עובד בעל התפקיד הנדרש (`role_id in employee_roles[user_id]`)
  - משמרת דורשת את התפקיד (`role_id in shift['required_roles']`)

#### קוד - יצירת משתנים

```python
def _build_decision_variables(model, data, n_employees, n_shifts):
    x = {}  # {(i, j, role_id): var}
    vars_by_emp_shift = {}  # {(i, j): [var1, var2, ...]} - for performance

    for i, emp in enumerate(data.employees):
        for j, shift in enumerate(data.shifts):
            if data.availability_matrix[i, j] != 1:
                continue  # Skip if employee not available

            required_roles = shift.get('required_roles') or []
            if not required_roles:
                continue

            emp_role_ids = set(emp.get('roles') or [])

            # Create variable for each role that employee has AND shift requires
            for role_req in required_roles:
                role_id = role_req['role_id']
                if role_id in emp_role_ids:
                    var = model.add_var(var_type=mip.BINARY, name=f'x_{i}_{j}_{role_id}')
                    x[i, j, role_id] = var

                    # Build index for performance
                    if (i, j) not in vars_by_emp_shift:
                        vars_by_emp_shift[(i, j)] = []
                    vars_by_emp_shift[(i, j)].append(var)

    return x, vars_by_emp_shift
```

---

### 5.2 אילוצים קשים

#### 5.2.1 Coverage Constraint (כיסוי תפקידים)

- **אינטואיציה**: כל משמרת חייבת לקבל בדיוק את מספר העובדים הנדרש לכל תפקיד
- **נוסחה**: `Σ_i x(i,j,r) = required_count[j,r]` לכל j, r

```python
def _add_coverage_constraints(model, data, x, n_employees, n_shifts):
    for j, shift in enumerate(data.shifts):
        required_roles = shift.get('required_roles') or []
        if not required_roles:
            continue

        for role_req in required_roles:
            role_id = role_req['role_id']
            required_count = int(role_req['required_count'])

            eligible_vars = [x[i, j, role_id] for i in range(n_employees)
                           if (i, j, role_id) in x]

            if not eligible_vars:
                if required_count > 0:
                    raise ValueError(f"Infeasible coverage: shift {shift['planned_shift_id']} "
                                   f"requires role {role_id} count={required_count}, "
                                   f"but no eligible employees exist")
                continue

            model += mip.xsum(eligible_vars) == required_count, \
                    f'coverage_shift_{j}_role_{role_id}'
```

#### 5.2.2 Single Role Per Shift

- **אינטואיציה**: עובד לא יכול להיות מוקצה ליותר מתפקיד אחד באותה משמרת
- **נוסחה**: `Σ_r x(i,j,r) ≤ 1` לכל i, j

```python
def _add_single_role_constraints(model, x, vars_by_emp_shift, n_employees, n_shifts):
    for i in range(n_employees):
        for j in range(n_shifts):
            if (i, j) in vars_by_emp_shift:
                role_vars = vars_by_emp_shift[(i, j)]
                if len(role_vars) > 1:  # Only if employee has multiple roles for this shift
                    model += mip.xsum(role_vars) <= 1, f'single_role_emp_{i}_shift_{j}'
```

#### 5.2.3 No Overlapping Shifts

- **אינטואיציה**: עובד לא יכול להיות מוקצה למשמרות חופפות בזמן
- **נוסחה**: `Σ_r x(i,j1,r) + Σ_r x(i,j2,r) ≤ 1` לכל i, (j1,j2) חופפים

```python
def _add_overlap_constraints(model, data, x, vars_by_emp_shift, n_employees):
    for shift_id, overlapping_ids in data.shift_overlaps.items():
        if not overlapping_ids:
            continue

        shift_idx = data.shift_index[shift_id]
        for overlapping_id in overlapping_ids:
            overlapping_idx = data.shift_index[overlapping_id]

            for i in range(n_employees):
                vars_shift = vars_by_emp_shift.get((i, shift_idx), [])
                vars_overlap = vars_by_emp_shift.get((i, overlapping_idx), [])

                if vars_shift and vars_overlap:
                    model += mip.xsum(vars_shift) + mip.xsum(vars_overlap) <= 1, \
                            f'no_overlap_emp_{i}_shift_{shift_idx}_{overlapping_idx}'
```

#### 5.2.4 Minimum Rest Hours

- **אינטואיציה**: עובד חייב לקבל שעות מנוחה מינימליות בין משמרות
- **נוסחה**: `Σ_r x(i,j1,r) + Σ_r x(i,j2,r) ≤ 1` לכל i, (j1,j2) עם מנוחה לא מספקת

```python
min_rest_constraint = data.system_constraints.get(SystemConstraintType.MIN_REST_HOURS)
if min_rest_constraint and min_rest_constraint[1]:  # is_hard
    for shift_id, conflicting_ids in data.shift_rest_conflicts.items():
        shift_idx = data.shift_index[shift_id]
        for conflicting_id in conflicting_ids:
            conflicting_idx = data.shift_index[conflicting_id]

            for i in range(n_employees):
                vars_shift = vars_by_emp_shift.get((i, shift_idx), [])
                vars_conflict = vars_by_emp_shift.get((i, conflicting_idx), [])

                if vars_shift and vars_conflict:
                    model += mip.xsum(vars_shift) + mip.xsum(vars_conflict) <= 1, \
                            f'min_rest_emp_{i}_shift_{shift_idx}_{conflicting_idx}'
```

#### 5.2.5 Max Shifts Per Week

- **אינטואיציה**: עובד לא יכול לעבוד יותר מ-X משמרות בשבוע
- **נוסחה**: `Σ_j Σ_r x(i,j,r) ≤ max_shifts` לכל i

#### 5.2.6 Max Hours Per Week

- **אינטואיציה**: עובד לא יכול לעבוד יותר מ-X שעות בשבוע
- **נוסחה**: `Σ_j Σ_r x(i,j,r) * duration(j) ≤ max_hours` לכל i

---

### 5.3 אילוצים רכים

#### מושג אילוצים רכים

- **אילוצים רכים** = אילוצים שניתן להפר, אך עם עונש (penalty) בפונקציית המטרה
- **Slack Variables**: משתנים עזר שמייצגים את הסטייה מהאילוץ
- **Penalty Weight**: משקל גבוה (100.0) כדי להרתיע הפרות, אך לא למנוע אותן

#### דוגמה: Minimum Hours Per Week (Soft)

- **אינטואיציה**: רצוי שכל עובד יעבוד לפחות X שעות, אך אם לא ניתן - יש עונש
- **נוסחה**: `deficit_i = max(0, min_hours - Σ_j Σ_r x(i,j,r) * duration(j))`

```python
min_hours_constraint = data.system_constraints.get(SystemConstraintType.MIN_HOURS_PER_WEEK)
if min_hours_constraint and not min_hours_constraint[1]:  # is_soft
    min_hours = min_hours_constraint[0]
    for i in range(n_employees):
        # Calculate total hours
        emp_hours_vars = []
        for (ei, ej) in vars_by_emp_shift.keys():
            if ei == i:
                shift = data.shifts[ej]
                shift_id = shift['planned_shift_id']
                shift_duration = data.shift_durations.get(shift_id, 0.0)
                if shift_duration > 0:
                    for var in vars_by_emp_shift[(ei, ej)]:
                        emp_hours_vars.append(shift_duration * var)

        if emp_hours_vars:
            total_hours = mip.xsum(emp_hours_vars)
            # Slack variable: deficit = max(0, min_hours - total_hours)
            deficit = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'min_hours_deficit_{i}')
            model += deficit >= min_hours - total_hours
            soft_penalty_component += deficit
```

#### דוגמה: Minimum Shifts Per Week (Soft)

```python
min_shifts_constraint = data.system_constraints.get(SystemConstraintType.MIN_SHIFTS_PER_WEEK)
if min_shifts_constraint and not min_shifts_constraint[1]:  # is_soft
    min_shifts = int(min_shifts_constraint[0])
    for i in range(n_employees):
        emp_vars = []
        for (ei, ej) in vars_by_emp_shift.keys():
            if ei == i:
                emp_vars.extend(vars_by_emp_shift[(ei, ej)])

        if emp_vars:
            total_shifts = mip.xsum(emp_vars)
            # Slack variable: deficit = max(0, min_shifts - total_shifts)
            deficit = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'min_shifts_deficit_{i}')
            model += deficit >= min_shifts - total_shifts
            soft_penalty_component += deficit
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
for i, emp_total in enumerate(assignments_per_employee):
    deviation_pos = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'dev_pos_{i}')
    deviation_neg = model.add_var(var_type=mip.CONTINUOUS, lb=0, name=f'dev_neg_{i}')

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

### 5.4 פונקציית מטרה

#### פירוק למרכיבים

1. **Preference Component** (מקסימיזציה של שביעות רצון)

   - `Σ_(i,j,r) preference_scores[i,j] * x(i,j,r)`
   - ככל שהעובד מעדיף את המשמרת, הציון גבוה יותר

2. **Fairness Component** (מינימיזציה של אי-הוגנות)

   - `-Σ_i (deviation_pos_i + deviation_neg_i)`
   - מינימיזציה של סטיות מהממוצע (מינוס כי זה penalty)

3. **Soft Penalty Component** (מינימיזציה של הפרות אילוצים רכים)
   - `-100.0 * soft_penalty_component`
   - משקל גבוה (100.0) להרתיע הפרות

#### נוסחה מלאה

```
maximize:
    objective = (
        config.weight_preferences * preference_component
        - config.weight_fairness * fairness_component
        - soft_penalty_weight * soft_penalty_component
    )
```

---

### 5.5 זרימת נתונים מקצה לקצה

#### שלב 1: בניית נתונים → משתנים ואילוצים

```
OptimizationDataBuilder.build(weekly_schedule_id)
  ↓
OptimizationData object created
  ↓
MipSchedulingSolver.solve(data, config)
  ↓
_build_decision_variables() → x dict created
  ↓
_add_coverage_constraints() → coverage constraints added
_add_single_role_constraints() → single-role constraints added
_add_overlap_constraints() → overlap constraints added
_add_hard_constraints() → max_shifts, max_hours, min_rest constraints added
  ↓
_build_objective() → objective function created
```

#### שלב 2: פתרון המודל

```python
model = mip.Model(sense=mip.MAXIMIZE, solver_name=mip.CBC)
model.max_seconds = config.max_runtime_seconds
model.max_mip_gap = config.mip_gap

# ... add variables and constraints ...

status = model.optimize()  # Solve!

if status in [mip.OptimizationStatus.OPTIMAL, mip.OptimizationStatus.FEASIBLE]:
    solution.objective_value = model.objective_value
    solution.mip_gap = model.gap
    solution.assignments = self._extract_assignments(x, data)
```

#### שלב 3: חילוץ פתרון

```python
def _extract_assignments(self, x, data):
    assignments = []
    for (i, j, role_id), var in x.items():
        if var.x > 0.5:  # Variable is 1 (assigned)
            emp = data.employees[i]
            shift = data.shifts[j]
            assignments.append({
                'user_id': emp['user_id'],
                'planned_shift_id': shift['planned_shift_id'],
                'role_id': role_id,
                'preference_score': float(data.preference_scores[i, j])
            })
    return assignments
```

#### שלב 4: החזרת תוצאות

הפתרון מוחזר כ-`SchedulingSolution` עם:

- `assignments`: רשימת הקצאות (user_id, planned_shift_id, role_id)
- `objective_value`: ערך פונקציית המטרה
- `mip_gap`: פער מאופטימליות
- `status`: סטטוס הפתרון (OPTIMAL, FEASIBLE, INFEASIBLE)
- `metrics`: מדדי איכות (ממוצע העדפות, הוגנות, וכו')

---

## סיכום

מערכת **Smart Scheduling** מציגה פתרון מלא לאופטימיזציה של משמרות עובדים באמצעות MIP. המערכת משלבת:

- **מודל MIP מדויק** עם משתנים x(i,j,r) ותמיכה בתפקידים מרובים
- **אילוצים קשים ורכים** עם penalties ו-fairness
- **ארכיטקטורה נקייה** עם הפרדת אחריות
- **Background processing** עם Celery ו-Redis
- **Validation מלא** לפני החזרת הפתרון

### קבצים מרכזיים

- `backend/app/services/scheduling/mip_solver.py` - מודל MIP ופתרון
- `backend/app/services/optimization_data_services/optimization_data_builder.py` - בניית נתונים
- `backend/app/services/scheduling/scheduling_service.py` - orchestrator ראשי
- `backend/app/services/constraintService.py` - validation
