# 🔄 זרימה מקצה-לקצה: Run Optimization

תיאור מפורט של הזרימה המלאה מלוחץ המשתמש על "Run Optimization" ועד שהפתרון נשמר ב-DB ומוחזר למשתמש.

---

## 📋 סקירה כללית

הזרימה כוללת 5 רכיבים עיקריים:
1. **Frontend** - ממשק המשתמש
2. **Backend (FastAPI)** - API endpoints
3. **Celery / Redis** - עיבוד אסינכרוני
4. **Solver** - פתרון מודל MIP
5. **DB** - מסד הנתונים

---

## 🎯 שלב 1: Frontend - לחיצה על "Run Optimization"

### מיקום בקוד
- **קומפוננטה**: `frontend/src/components/OptimizationPanel.jsx`
- **API Client**: `frontend/src/api/optimization.js`

### מה קורה?

```javascript
// OptimizationPanel.jsx - שורה 94
async function handleRunOptimization() {
  setLoading(true);
  try {
    // 1. שולח בקשה ל-API
    const result = await triggerOptimization(weeklyScheduleId);
    
    // 2. מציג הודעת הצלחה
    toast.success('Optimization started!');
    
    // 3. טוען מחדש את רשימת הריצות
    await loadRuns();
    
    // 4. בוחר אוטומטית את הריצה החדשה
    if (result.run_id) {
      const newRun = await getRun(result.run_id);
      setSelectedRun(newRun);
    }
  } catch (error) {
    toast.error('Failed to start optimization');
  } finally {
    setLoading(false);
  }
}
```

```javascript
// optimization.js - שורה 19
export const triggerOptimization = async (weeklyScheduleId, configId = null) => {
  const url = `/scheduling/optimize/${weeklyScheduleId}`;
  const params = configId ? { config_id: configId } : {};
  
  // שולח POST request ל-FastAPI
  const response = await api.post(url, null, { params });
  return response.data; // { run_id, status, task_id, message }
};
```

### תוצאה
- ✅ בקשה POST נשלחת ל-`/scheduling/optimize/{weekly_schedule_id}`
- ✅ המשתמש מקבל מיד תשובה עם `run_id` ו-`task_id`
- ✅ ה-Frontend מתחיל לבדוק סטטוס כל 3 שניות (polling)

---

## 🚀 שלב 2: Backend (FastAPI) - קבלת הבקשה

### מיקום בקוד
- **Route**: `backend/app/api/routes/schedulingRoutes.py`
- **שורות**: 48-116

### מה קורה?

```python
@router.post("/optimize/{weekly_schedule_id}", dependencies=[Depends(require_manager)])
async def optimize_schedule(
    weekly_schedule_id: int,
    config_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Trigger async optimization for a specific weekly schedule.
    """
    # 1. בודק שהשבוע קיים במסד הנתונים
    schedule = db.query(WeeklyScheduleModel).filter(
        WeeklyScheduleModel.weekly_schedule_id == weekly_schedule_id
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Weekly schedule not found")
    
    # 2. בודק קונפיגורציה (אם צוינה)
    if config_id:
        config = db.query(OptimizationConfigModel).filter(
            OptimizationConfigModel.config_id == config_id
        ).first()
        if not config:
            raise HTTPException(status_code=404, detail="Config not found")
    
    # 3. יוצר רשומת SchedulingRun במסד הנתונים עם סטטוס PENDING
    run = SchedulingRunModel(
        weekly_schedule_id=weekly_schedule_id,
        config_id=config_id,
        status=SchedulingRunStatus.PENDING
    )
    db.add(run)
    db.commit()  # ⚠️ שמירה ראשונה ב-DB
    db.refresh(run)
    
    # 4. שולח משימת Celery ל-Redis (לא מחכה לסיום!)
    task = run_optimization_task.delay(run.run_id)
    
    # 5. מחזיר מיד תשובה למשתמש
    return {
        "run_id": run.run_id,
        "status": run.status.value,  # "PENDING"
        "task_id": task.id,  # Celery task ID
        "message": f"Optimization task dispatched. Poll GET /scheduling/runs/{run.run_id} for status."
    }
```

### תוצאה
- ✅ רשומת `SchedulingRun` נוצרת ב-DB עם סטטוס `PENDING`
- ✅ משימת Celery נשלחת ל-Redis
- ✅ התשובה חוזרת מיד ל-Frontend (לא מחכה לסיום האופטימיזציה!)

---

## 📨 שלב 3: Celery / Redis - תור המשימות

### מיקום בקוד
- **Celery Config**: `backend/app/celery_app.py`
- **Redis**: מוגדר ב-`docker-compose.yml`

### מה קורה?

#### 3.1 Redis - Message Broker

```python
# celery_app.py - שורות 12-20
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

celery_app = Celery(
    'smart_scheduling',
    broker=REDIS_URL,      # Redis משמש כ-Message Broker
    backend=REDIS_URL,     # Redis משמש גם ל-Result Backend
    include=['app.tasks.optimization_tasks']
)
```

**תפקיד Redis:**
1. **Message Broker** - תור הודעות בין FastAPI ל-Celery Worker
2. **Result Backend** - שומר תוצאות זמניות של משימות
3. **Task Queue** - תור משימות ממתינות לביצוע

**מה קורה כשקוראים ל-`task.delay()`?**
- Celery שולח הודעה JSON ל-Redis
- Redis שומר את ההודעה בתור (queue) בשם `celery`
- ההודעה כוללת: `run_id`, שם המשימה, פרמטרים

#### 3.2 Celery Worker - קורא את המשימה

```yaml
# docker-compose.yml
celery-worker:
  build: ./backend
  command: celery -A app.celery_app worker --loglevel=info
  depends_on:
    - redis
    - data
```

**מה קורה?**
- Celery Worker פועל ברקע ומקשיב ל-Redis
- כשהוא רואה משימה חדשה בתור, הוא קורא אותה
- הוא מתחיל לבצע את הפונקציה `run_optimization_task`

---

## ⚙️ שלב 4: Celery Task - ביצוע האופטימיזציה

### מיקום בקוד
- **Task**: `backend/app/tasks/optimization_tasks.py`
- **שורות**: 17-89

### מה קורה?

```python
@celery_app.task(bind=True, name='app.tasks.optimization_tasks.run_optimization')
def run_optimization_task(
    self,
    run_id: int
):
    """
    Celery task to run schedule optimization asynchronously.
    """
    # 1. יוצר session חדש למסד הנתונים
    db = SessionLocal()
    
    try:
        # 2. מוצא את רשומת SchedulingRun מה-DB
        run = db.query(SchedulingRunModel).filter(
            SchedulingRunModel.run_id == run_id
        ).first()
        
        if not run:
            raise ValueError(f"SchedulingRun {run_id} not found")
        
        # 3. מעדכן סטטוס ב-Celery (לניטור ב-Flower)
        self.update_state(
            state='RUNNING',
            meta={'status': 'Building optimization model', 'run_id': run_id}
        )
        
        # 4. יוצר SchedulingService ומריץ אופטימיזציה
        scheduling_service = SchedulingService(db)
        
        # ⚠️ זה המקום שבו כל הקסם קורה!
        # הפונקציה הזו:
        # - בונה נתונים
        # - בונה מודל MIP
        # - פותר עם Solver
        # - שומר פתרון ב-DB
        run, solution = scheduling_service._execute_optimization_for_run(run)
        
        # 5. מחזיר תוצאות (נשמרות ב-Redis Result Backend)
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
        # 6. טיפול בשגיאות - מעדכן את הרשומה ל-FAILED
        try:
            run = db.query(SchedulingRunModel).filter(
                SchedulingRunModel.run_id == run_id
            ).first()
            
            if run:
                run.status = SchedulingRunStatus.FAILED
                run.completed_at = datetime.now()
                run.error_message = str(e)
                db.commit()  # ⚠️ שמירה ב-DB - סטטוס FAILED
        except:
            pass
        
        raise  # מעלה את השגיאה כדי ש-Celery יסמן את המשימה כ-FAILED
        
    finally:
        db.close()
```

### תוצאה
- ✅ Celery Worker מבצע את המשימה ברקע
- ✅ הסטטוס מתעדכן ב-Redis (ניתן לראות ב-Flower)
- ✅ הקוד קורא ל-`SchedulingService` שמבצע את האופטימיזציה

---

## 🧮 שלב 5: Solver - בניית ופתרון מודל MIP

### מיקום בקוד
- **Service**: `backend/app/services/scheduling/scheduling_service.py`
- **Solver**: `backend/app/services/scheduling/mip_solver.py`

### מה קורה בתוך `SchedulingService._execute_optimization_for_run()`?

```python
# scheduling_service.py - שורה 119
def _execute_optimization_for_run(
    self,
    run: SchedulingRunModel
) -> Tuple[SchedulingRunModel, SchedulingSolution]:
    """
    Execute optimization for an existing run record (used by async Celery task).
    """
    # קורא ל-_execute_run עם apply_assignments=False
    # (לא מיישם הקצאות, רק שומר פתרון)
    run, solution = self._execute_run(run, apply_assignments=False)
    return run, solution
```

### מה קורה בתוך `_execute_run()`?

```python
# scheduling_service.py - שורה 180
def _execute_run(
    self,
    run: SchedulingRunModel,
    apply_assignments: bool = True
) -> Tuple[SchedulingRunModel, SchedulingSolution]:
    """
    Shared executor for optimization runs.
    """
    # 1. מעדכן סטטוס ל-RUNNING (עם הגנה מפני race conditions)
    run = self._start_run(run)  # ⚠️ עדכון ב-DB: PENDING → RUNNING
    
    # 2. טוען קונפיגורציה מהמסד נתונים
    config = self._load_optimization_config(run)
    
    # 3. בונה נתונים ופותר מודל MIP
    solution = self._build_and_solve(run, config)
    
    # 4. בודק אם הפתרון לא אפשרי
    if solution.status in ['INFEASIBLE', 'NO_SOLUTION_FOUND']:
        return self._handle_infeasible_solution(run, solution)
    
    # 5. בודק ולידציה של HARD constraints
    if solution.status in ['OPTIMAL', 'FEASIBLE']:
        self._validate_solution(run, solution)
    
    # 6. שומר פתרון במסד הנתונים
    run = self._persist_solution(run, solution, apply_assignments)
    
    return run, solution
```

### מה קורה בתוך `_build_and_solve()`?

```python
# scheduling_service.py - שורה 282
def _build_and_solve(
    self,
    run: SchedulingRunModel,
    config: OptimizationConfigModel
) -> SchedulingSolution:
    """
    Build optimization data and solve MIP model.
    """
    # 1. בונה נתוני אופטימיזציה מהמסד נתונים
    logger.info(f"Building optimization data for weekly schedule {run.weekly_schedule_id}...")
    data = self.data_builder.build(run.weekly_schedule_id)
    # data כולל: employees, shifts, preferences, constraints, וכו'
    
    logger.info(f"Employees: {len(data.employees)}, Shifts: {len(data.shifts)}")
    
    # 2. בונה מודל MIP ופותר אותו
    logger.info(f"Building MIP model...")
    solution = self.solver.solve(data, config)
    # ⚠️ כאן קוראים ל-Solver!
    
    return solution
```

### מה קורה בתוך `MipSchedulingSolver.solve()`?

```python
# mip_solver.py - שורה 28
def solve(
    self,
    data: OptimizationData,
    config: OptimizationConfigModel
) -> SchedulingSolution:
    """
    Build and solve MIP model.
    """
    start_time = datetime.now()
    solution = SchedulingSolution()
    
    # 1. יוצר מודל MIP עם CBC Solver
    model = mip.Model(solver_name=mip.CBC)
    
    # 2. בונה משתני החלטה (decision variables)
    x, vars_by_emp_shift, vars_by_employee = self._build_decision_variables(
        model, data, n_employees, n_shifts
    )
    
    # 3. מוסיף אילוצים קשים (hard constraints)
    self._add_coverage_constraints(model, data, x)
    self._add_single_role_constraints(model, data, x)
    self._add_overlap_constraints(model, data, x)
    self._add_hard_constraints(model, data, x, vars_by_emp_shift, vars_by_employee, n_employees)
    
    # 4. בונה פונקציית מטרה (objective function)
    assignments_per_employee, avg_assignments = self._add_fairness_terms(...)
    soft_penalty_component = self._add_soft_penalties(...)
    objective = self._build_objective(...)
    model.objective = objective
    
    # 5. פותר את המודל עם CBC Solver
    status = model.optimize()  # ⚠️ כאן הפתרון בפועל!
    
    # 6. מטפל בתוצאות
    end_time = datetime.now()
    solution.runtime_seconds = (end_time - start_time).total_seconds()
    solution.status = map_solver_status(status)
    
    if status in [mip.OptimizationStatus.OPTIMAL, mip.OptimizationStatus.FEASIBLE]:
        solution.objective_value = model.objective_value
        solution.mip_gap = model.gap
        
        # 7. מחלץ הקצאות מהפתרון
        solution.assignments = self._extract_assignments(x, data)
        solution.metrics = calculate_metrics(data, solution.assignments)
    
    return solution
```

### תוצאה
- ✅ מודל MIP נבנה עם כל האילוצים
- ✅ Solver (CBC/Gurobi) פותר את המודל
- ✅ הפתרון מוחזר כ-`SchedulingSolution` עם רשימת הקצאות

---

## 💾 שלב 6: DB - שמירת הפתרון

### מיקום בקוד
- **Persistence**: `backend/app/services/scheduling/persistence.py`
- **Service**: `backend/app/services/scheduling/scheduling_service.py` - `_persist_solution()`

### מה קורה?

```python
# scheduling_service.py - שורה 399
def _persist_solution(
    self,
    run: SchedulingRunModel,
    solution: SchedulingSolution,
    apply_assignments: bool
) -> SchedulingRunModel:
    """
    Persist solution and optionally apply assignments.
    """
    # 1. אם apply_assignments=True, מוחק הקצאות קיימות
    if apply_assignments:
        logger.info(f"Clearing existing assignments...")
        self.persistence.clear_existing_assignments(run.weekly_schedule_id, commit=False)
    
    # 2. מעדכן את רשומת SchedulingRun עם תוצאות
    run.status = SchedulingRunStatus.COMPLETED  # ⚠️ עדכון סטטוס
    run.completed_at = datetime.now()
    run.runtime_seconds = solution.runtime_seconds
    run.objective_value = solution.objective_value
    run.mip_gap = solution.mip_gap
    run.total_assignments = len(solution.assignments)
    run.solver_status = map_to_solver_status_enum(solution.status)
    
    # 3. שומר פתרון ב-SchedulingSolutionModel
    logger.info(f"Storing {len(solution.assignments)} solution records...")
    
    try:
        # שומר כל הקצאה כ-SchedulingSolutionModel
        self.persistence.persist_solution_and_apply_assignments(
            run.run_id,
            solution.assignments,
            apply_assignments=apply_assignments,  # False במשימת Celery
            commit=False  # נשמור יחד עם עדכון run
        )
        
        # 4. שומר הכל ב-transaction אחת
        self.db.commit()  # ⚠️ שמירה סופית ב-DB!
        self.db.refresh(run)
        
    except SQLAlchemyError as e:
        self.db.rollback()
        logger.error(f"Failed to persist solution: {e}")
        raise
    
    return run
```

### מה קורה בתוך `persist_solution_and_apply_assignments()`?

```python
# persistence.py - שורה 62
def persist_solution_and_apply_assignments(
    self,
    run_id: int,
    assignments: List[Dict],
    apply_assignments: bool = True,
    commit: bool = True
) -> None:
    """
    Persist solution records and optionally create shift assignments.
    """
    try:
        # יוצר רשומת SchedulingSolutionModel לכל הקצאה
        for assignment in assignments:
            solution_record = SchedulingSolutionModel(
                run_id=run_id,
                planned_shift_id=assignment['planned_shift_id'],
                user_id=assignment['user_id'],
                role_id=assignment['role_id'],
                is_selected=True,
                assignment_score=assignment.get('preference_score')
            )
            self.db.add(solution_record)  # ⚠️ שמירה ב-DB
            
            # אם apply_assignments=True, גם יוצר ShiftAssignmentModel
            if apply_assignments:
                shift_assignment = ShiftAssignmentModel(
                    planned_shift_id=assignment['planned_shift_id'],
                    user_id=assignment['user_id'],
                    role_id=assignment['role_id']
                )
                self.db.add(shift_assignment)
        
        # שומר הכל (אם commit=True)
        if commit:
            self.db.commit()
            
    except SQLAlchemyError as e:
        self.db.rollback()
        raise
```

### מה נשמר ב-DB?

#### 1. עדכון `SchedulingRun`:
```sql
UPDATE scheduling_runs 
SET 
    status = 'COMPLETED',
    completed_at = NOW(),
    runtime_seconds = 45.2,
    objective_value = 1234.56,
    total_assignments = 150,
    solver_status = 'OPTIMAL'
WHERE run_id = 123;
```

#### 2. יצירת `SchedulingSolution` records:
```sql
INSERT INTO scheduling_solutions 
    (run_id, planned_shift_id, user_id, role_id, is_selected, assignment_score)
VALUES
    (123, 1, 10, 2, true, 0.8),
    (123, 1, 11, 3, true, 0.9),
    (123, 2, 10, 2, true, 0.7),
    ...
-- 150 שורות (כל הקצאה)
```

### תוצאה
- ✅ `SchedulingRun` מעודכן עם סטטוס `COMPLETED` וכל המטריקות
- ✅ כל הקצאה נשמרת ב-`SchedulingSolutionModel`
- ✅ הפתרון זמין למשתמש (אבל לא מיושם עדיין!)

---

## 🔄 שלב 7: Frontend - Polling וצפייה בתוצאות

### מיקום בקוד
- **Component**: `frontend/src/components/OptimizationPanel.jsx`
- **שורות**: 40-53 (polling), 55-76 (loadRuns)

### מה קורה?

```javascript
// OptimizationPanel.jsx - שורה 40
// Polling - בודק סטטוס כל 3 שניות
useEffect(() => {
  if (runs.some(r => r.status === 'RUNNING' || r.status === 'PENDING')) {
    setPolling(true);
    const interval = setInterval(() => {
      loadRuns(true); // Silent reload כל 3 שניות
    }, 3000);

    return () => {
      clearInterval(interval);
      setPolling(false);
    };
  }
}, [runs]);
```

```javascript
// OptimizationPanel.jsx - שורה 55
async function loadRuns(silent = false) {
  if (!silent) setLoading(true);
  try {
    // שולח GET request ל-API
    const data = await getAllRuns({ weekly_schedule_id: weeklyScheduleId });
    setRuns(data || []);
    
    // בוחר אוטומטית את הריצה האחרונה שהושלמה
    if (!selectedRun && data && data.length > 0) {
      const completed = data.find(r => r.status === 'COMPLETED');
      if (completed) {
        handleSelectRun(completed);
      }
    }
  } catch (error) {
    if (!silent) {
      toast.error('Failed to load optimization history');
    }
  } finally {
    if (!silent) setLoading(false);
  }
}
```

```javascript
// optimization.js - שורה 36
export const getAllRuns = async (filters = {}) => {
  // שולח GET /scheduling/runs/?weekly_schedule_id=123
  const response = await api.get('/scheduling/runs/', { params: filters });
  return response.data; // [{ run_id, status, runtime_seconds, ... }, ...]
};
```

### מה קורה ב-Backend?

```python
# schedulingRunRoutes.py - שורה 62
@router.get(
    "/",
    response_model=List[SchedulingRunRead],
    dependencies=[Depends(require_auth)]
)
async def list_runs(
    weekly_schedule_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    # קורא מהמסד נתונים
    return await get_all_scheduling_runs(
        db, 
        weekly_schedule_id=weekly_schedule_id,
        status_filter=status_filter
    )
```

### תוצאה
- ✅ Frontend בודק סטטוס כל 3 שניות
- ✅ כש-`status` משתנה ל-`COMPLETED`, המשתמש רואה את התוצאות
- ✅ המשתמש יכול לבחור ריצה ולראות את הפתרון

---

## ✅ שלב 8: Frontend - יישום הפתרון (Apply Solution)

### מיקום בקוד
- **Component**: `frontend/src/components/OptimizationPanel.jsx`
- **שורות**: 115-143

### מה קורה?

```javascript
// OptimizationPanel.jsx - שורה 115
async function handleApplySolution(overwrite = false) {
  setApplying(true);
  try {
    // שולח POST request ל-API
    const result = await applySolution(selectedRun.run_id, overwrite);
    toast.success(result.message || 'Solution applied successfully!');
    
    if (onSolutionApplied) {
      onSolutionApplied(); // מעדכן את התצוגה
    }
  } catch (error) {
    if (error?.response?.status === 409) {
      // קונפליקט - שואל אם לדרוס
      const shouldOverwrite = window.confirm(
        `${error.response.data.detail}\n\nDo you want to overwrite?`
      );
      if (shouldOverwrite) {
        handleApplySolution(true); // ניסיון חוזר עם overwrite
      }
    } else {
      toast.error('Failed to apply solution');
    }
  } finally {
    setApplying(false);
  }
}
```

```javascript
// optimization.js - שורה 73
export const applySolution = async (runId, overwrite = false) => {
  // שולח POST /scheduling/runs/{runId}/apply?overwrite=true/false
  const response = await api.post(`/scheduling/runs/${runId}/apply`, null, {
    params: { overwrite }
  });
  return response.data;
};
```

### מה קורה ב-Backend?

```python
# schedulingRunRoutes.py - שורה 190
@router.post(
    "/{run_id}/apply",
    dependencies=[Depends(require_manager)]
)
async def apply_solution(
    run_id: int,
    overwrite: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    return await apply_scheduling_solution(db, run_id, overwrite, current_user.user_id)
```

```python
# scheduling_run_controller.py - שורה 474
async def apply_scheduling_solution(
    db: Session,
    run_id: int,
    overwrite: bool = False
) -> dict:
    """
    Apply an optimization solution by converting SchedulingSolution records
    into actual ShiftAssignment records.
    """
    # 1. בודק שהריצה קיימת והושלמה
    run = db.query(SchedulingRunModel).filter(...).first()
    if not run or run.status != SchedulingRunStatus.COMPLETED:
        raise HTTPException(400, "Run not found or not completed")
    
    # 2. קורא את כל הפתרונות מהמסד נתונים
    solutions = db.query(SchedulingSolutionModel).filter(
        SchedulingSolutionModel.run_id == run_id,
        SchedulingSolutionModel.is_selected == True
    ).all()
    
    if not solutions:
        raise HTTPException(400, "No solutions found")
    
    # 3. אם overwrite=True, מוחק הקצאות קיימות
    if overwrite:
        shift_ids = [sol.planned_shift_id for sol in solutions]
        db.query(ShiftAssignmentModel).filter(
            ShiftAssignmentModel.planned_shift_id.in_(shift_ids)
        ).delete()
    
    # 4. יוצר ShiftAssignmentModel לכל פתרון
    assignments_created = 0
    for solution in solutions:
        # בודק אם כבר קיים
        existing = db.query(ShiftAssignmentModel).filter(...).first()
        if not existing:
            assignment = ShiftAssignmentModel(
                planned_shift_id=solution.planned_shift_id,
                user_id=solution.user_id,
                role_id=solution.role_id
            )
            db.add(assignment)
            assignments_created += 1
    
    # 5. שומר הכל ב-DB
    db.commit()  # ⚠️ שמירה סופית - הפתרון מיושם!
    
    return {
        "assignments_created": assignments_created,
        "shifts_updated": len(shifts_updated),
        "message": f"Successfully applied {assignments_created} assignments"
    }
```

### תוצאה
- ✅ כל הפתרונות מ-`SchedulingSolutionModel` מומרים ל-`ShiftAssignmentModel`
- ✅ הפתרון מיושם בפועל על הלוח זמנים
- ✅ המשתמש רואה את ההקצאות בלוח הזמנים

---

## 📊 סיכום - טבלת זרימה

| שלב | רכיב | פעולה | זמן | DB Operations |
|-----|------|-------|-----|---------------|
| 1 | **Frontend** | משתמש לוחץ "Run Optimization" | מיידי | - |
| 2 | **Frontend** | שולח POST `/scheduling/optimize/{id}` | < 100ms | - |
| 3 | **FastAPI** | בודק שבוע, יוצר `SchedulingRun` | < 500ms | ✅ INSERT `scheduling_runs` (PENDING) |
| 4 | **FastAPI** | שולח משימת Celery ל-Redis | < 100ms | - |
| 5 | **Redis** | שומר משימה בתור | מיידי | - |
| 6 | **Celery Worker** | קורא משימה, מעדכן סטטוס | < 1s | ✅ UPDATE `scheduling_runs` (RUNNING) |
| 7 | **SchedulingService** | בונה `OptimizationData` | 1-5s | ✅ SELECT (employees, shifts, constraints) |
| 8 | **MipSchedulingSolver** | בונה מודל MIP | 1-10s | - |
| 9 | **CBC/Gurobi Solver** | פותר מודל MIP | 10-300s | - |
| 10 | **SchedulingService** | בודק ולידציה | 1-5s | ✅ SELECT (validation) |
| 11 | **Persistence** | שומר פתרון ב-DB | 1-3s | ✅ INSERT `scheduling_solutions` (150+ rows)<br>✅ UPDATE `scheduling_runs` (COMPLETED) |
| 12 | **Redis** | שומר תוצאות Celery | מיידי | - |
| 13 | **Frontend** | Polling - בודק סטטוס כל 3s | כל 3s | - |
| 14 | **FastAPI** | מחזיר סטטוס מהמסד נתונים | < 100ms | ✅ SELECT `scheduling_runs` |
| 15 | **Frontend** | משתמש רואה תוצאות | מיידי | - |
| 16 | **Frontend** | משתמש לוחץ "Apply Solution" | מיידי | - |
| 17 | **FastAPI** | מיישם פתרון | 1-3s | ✅ DELETE `shift_assignments` (אם overwrite)<br>✅ INSERT `shift_assignments` (150+ rows) |
| 18 | **Frontend** | משתמש רואה הקצאות בלוח זמנים | מיידי | - |

---

## 🔍 נקודות מפתח

### 1. אסינכרוניות
- ✅ FastAPI **לא מחכה** לסיום האופטימיזציה
- ✅ התשובה חוזרת מיד עם `run_id`
- ✅ Frontend בודק סטטוס כל 3 שניות (polling)

### 2. שמירה ב-DB
- ✅ **שלב 1**: יצירת `SchedulingRun` (PENDING) - מיד
- ✅ **שלב 2**: עדכון ל-RUNNING - כשהמשימה מתחילה
- ✅ **שלב 3**: שמירת `SchedulingSolution` records - בסיום
- ✅ **שלב 4**: עדכון ל-COMPLETED - בסיום
- ✅ **שלב 5**: יישום ל-`ShiftAssignment` - רק כשהמשתמש לוחץ "Apply"

### 3. Redis תפקידים
- ✅ **Message Broker** - תור משימות
- ✅ **Result Backend** - תוצאות זמניות (24 שעות)

### 4. Solver
- ✅ **CBC** (ברירת מחדל) או **Gurobi** (אם מותקן)
- ✅ פותר מודל MIP עם אילוצים קשים ורכים
- ✅ מחזיר פתרון אופטימלי או feasible

### 5. הפרדה בין פתרון ליישום
- ✅ **פתרון** נשמר ב-`SchedulingSolutionModel` (רק הצעה)
- ✅ **יישום** נעשה רק כשהמשתמש לוחץ "Apply Solution"
- ✅ זה מאפשר למשתמש לראות כמה פתרונות לפני שהוא מחליט

---

## 🔗 קישורים לקוד

### Frontend
- **OptimizationPanel**: `frontend/src/components/OptimizationPanel.jsx`
- **API Client**: `frontend/src/api/optimization.js`

### Backend - API
- **Optimize Endpoint**: `backend/app/api/routes/schedulingRoutes.py:48-116`
- **Run Status**: `backend/app/api/routes/schedulingRunRoutes.py:62-77`
- **Apply Solution**: `backend/app/api/routes/schedulingRunRoutes.py:190-193`

### Backend - Celery
- **Celery Config**: `backend/app/celery_app.py`
- **Optimization Task**: `backend/app/tasks/optimization_tasks.py:17-89`

### Backend - Services
- **SchedulingService**: `backend/app/services/scheduling/scheduling_service.py`
  - `_execute_optimization_for_run()`: שורה 119
  - `_execute_run()`: שורה 180
  - `_build_and_solve()`: שורה 282
  - `_persist_solution()`: שורה 399
- **MipSchedulingSolver**: `backend/app/services/scheduling/mip_solver.py:28`
- **Persistence**: `backend/app/services/scheduling/persistence.py:62`

### DB Models
- **SchedulingRunModel**: `backend/app/db/models/schedulingRunModel.py`
- **SchedulingSolutionModel**: `backend/app/db/models/schedulingSolutionModel.py`
- **ShiftAssignmentModel**: `backend/app/db/models/shiftAssignmentModel.py`

---

## 💡 שאלות נפוצות

### Q: למה צריך Celery? למה לא פשוט להריץ את האופטימיזציה ישירות ב-FastAPI?

**A**: כי אופטימיזציה יכולה לקחת 10-300 שניות. אם נעשה את זה סינכרוני:
- ❌ הבקשה תתקע (timeout אחרי 30-60 שניות)
- ❌ המשתמש לא יכול לעבוד בזמן ההמתנה
- ❌ אם יש שגיאה, כל התהליך נכשל

עם Celery:
- ✅ הבקשה חוזרת מיד (< 1 שנייה)
- ✅ המשתמש יכול להמשיך לעבוד
- ✅ אפשר לבדוק סטטוס בזמן אמת
- ✅ אם Worker נופל, המשימה נשמרת ב-Redis

### Q: מה ההבדל בין `SchedulingSolution` ל-`ShiftAssignment`?

**A**:
- **`SchedulingSolution`** - פתרון מוצע שנשמר אחרי אופטימיזציה. זה רק הצעה, לא מיושם.
- **`ShiftAssignment`** - הקצאה בפועל שנשמרת בלוח הזמנים. זה מה שהעובדים רואים.

הפרדה זו מאפשרת:
- לראות כמה פתרונות לפני החלטה
- להשוות בין פתרונות
- לא ליישם פתרון אוטומטית

### Q: מה קורה אם Celery Worker נופל באמצע?

**A**:
- המשימה נשמרת ב-Redis
- Worker אחר (או אותו Worker אחרי restart) יכול להריץ את המשימה
- אם המשימה כבר התחילה, היא תסומן כ-FAILED במסד הנתונים

### Q: כמה זמן נשמרות התוצאות ב-Redis?

**A**: 24 שעות (86400 שניות) - מוגדר ב-`result_expires=86400` ב-`celery_app.py`

### Q: איך אפשר לראות מה קורה בזמן אמת?

**A**:
1. **Flower** - http://localhost:5555 - Dashboard מלא של Celery
2. **API** - `GET /scheduling/runs/{run_id}` - סטטוס מהמסד נתונים
3. **Frontend** - `OptimizationPanel` בודק כל 3 שניות ומציג סטטוס

---

## 🎯 סיכום

הזרימה המלאה כוללת:

1. **Frontend** → משתמש לוחץ, שולח בקשה
2. **FastAPI** → יוצר רשומה, שולח ל-Redis, מחזיר מיד
3. **Redis** → שומר משימה בתור
4. **Celery Worker** → קורא משימה, מריץ אופטימיזציה
5. **Solver** → בונה מודל MIP, פותר עם CBC/Gurobi
6. **DB** → שומר פתרון ב-`SchedulingSolutionModel`, מעדכן סטטוס
7. **Frontend** → בודק סטטוס (polling), מציג תוצאות
8. **Frontend** → משתמש מיישם פתרון (אופציונלי)
9. **FastAPI** → מיישם פתרון ל-`ShiftAssignmentModel`

כל התהליך אסינכרוני, מהיר, וניתן לניטור! 🚀
