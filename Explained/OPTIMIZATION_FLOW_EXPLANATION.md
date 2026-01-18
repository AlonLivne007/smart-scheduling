# הסבר מפורט: תהליך אופטימיזציה לשיבוץ שבוע

## 📋 סקירה כללית

כשמשתמש בוחר לעשות אופטימיזציה לשיבוץ של שבוע מסוים, המערכת משתמשת ב-**Celery** ו-**Redis** לביצוע אסינכרוני של המשימה. זה מונע timeout של הבקשה ומאפשר למשתמש להמשיך לעבוד בזמן שהאופטימיזציה רצה ברקע.

---

## 🔄 זרימת התהליך המלאה

### שלב 1: המשתמש לוחץ על "Run Optimization" (Frontend)

**מיקום**: `frontend/src/components/OptimizationPanel.jsx` - שורות 94-113

```javascript
async function handleRunOptimization() {
  setLoading(true);
  try {
    const result = await triggerOptimization(weeklyScheduleId);
    toast.success('Optimization started!');
    await loadRuns();
    
    // Auto-select the new run
    if (result.run_id) {
      const newRun = await getRun(result.run_id);
      setSelectedRun(newRun);
    }
  } catch (error) {
    // Error handling...
  }
}
```

**מה קורה?**
- המשתמש לוחץ על כפתור "Run Optimization"
- הפונקציה קוראת ל-`triggerOptimization()` מ-`frontend/src/api/optimization.js`
- זה שולח בקשה POST ל-`/scheduling/optimize/{weekly_schedule_id}`

---

### שלב 2: API Endpoint מקבל את הבקשה (Backend)

**מיקום**: `backend/app/api/routes/schedulingRoutes.py` - שורות 48-116

```python
@router.post("/optimize/{weekly_schedule_id}", dependencies=[Depends(require_manager)])
async def optimize_schedule(
    weekly_schedule_id: int,
    config_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    # 1. בודק שהשבוע קיים
    schedule = db.query(WeeklyScheduleModel).filter(...).first()
    
    # 2. יוצר רשומת SchedulingRun עם סטטוס PENDING
    run = SchedulingRunModel(
        weekly_schedule_id=weekly_schedule_id,
        config_id=config_id,
        status=SchedulingRunStatus.PENDING
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    
    # 3. שולח משימת Celery ל-Redis
    task = run_optimization_task.delay(run.run_id)
    
    # 4. מחזיר מיד למשתמש (לא מחכה לסיום)
    return {
        "run_id": run.run_id,
        "status": run.status.value,
        "task_id": task.id,
        "message": "Optimization task dispatched. Poll GET /scheduling/runs/{run.run_id} for status."
    }
```

**מה קורה?**
1. ✅ **בודק שהשבוע קיים** - אם לא, מחזיר 404
2. ✅ **יוצר רשומת `SchedulingRun`** במסד הנתונים עם סטטוס `PENDING`
3. ✅ **שולח משימת Celery** - `run_optimization_task.delay(run.run_id)` שולח את המשימה ל-**Redis**
4. ✅ **מחזיר מיד תשובה** - לא מחכה לסיום האופטימיזציה!

**🔑 נקודה חשובה**: ה-API endpoint **לא מחכה** לסיום האופטימיזציה. הוא מחזיר מיד `run_id` ו-`task_id`, והמשתמש יכול לבדוק את הסטטוס אחר כך.

---

### שלב 3: Redis מקבל את המשימה (Message Broker)

**מיקום**: `backend/app/celery_app.py` - שורות 12-18

```python
# Get Redis URL from environment or use default
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Create Celery app
celery_app = Celery(
    'smart_scheduling',
    broker=REDIS_URL,      # Redis משמש כ-Message Broker
    backend=REDIS_URL,     # Redis משמש גם ל-Result Backend
    include=['app.tasks.optimization_tasks']
)
```

**מה קורה?**
- **Redis** משמש כ-**Message Broker** - תור הודעות בין FastAPI ל-Celery Worker
- כשקוראים ל-`run_optimization_task.delay()`, Celery שולח את המשימה ל-Redis
- Redis שומר את המשימה בתור (queue) עד ש-Celery Worker יקרא אותה

**תפקיד Redis:**
1. **Message Broker** - תור משימות בין FastAPI ל-Celery Worker
2. **Result Backend** - שומר תוצאות זמניות של משימות (אפשר לשאול עליהן אחר כך)
3. **Task Queue** - תור משימות ממתינות לביצוע

**מיקום ב-Docker**: `docker-compose.yml` - שורות 47-58

```yaml
redis:
  image: redis:7-alpine
  restart: always
  ports:
    - "6379:6379"
  networks:
    - app-network
```

---

### שלב 4: Celery Worker קורא את המשימה מ-Redis

**מיקום**: `backend/app/tasks/optimization_tasks.py` - שורות 17-89

```python
@celery_app.task(bind=True, name='app.tasks.optimization_tasks.run_optimization')
def run_optimization_task(
    self,
    run_id: int
):
    """
    Celery task to run schedule optimization asynchronously.
    """
    db = SessionLocal()
    
    try:
        # 1. מוצא את רשומת SchedulingRun
        run = db.query(SchedulingRunModel).filter(
            SchedulingRunModel.run_id == run_id
        ).first()
        
        # 2. מעדכן סטטוס ב-Celery (לניטור)
        self.update_state(
            state='RUNNING',
            meta={'status': 'Building optimization model', 'run_id': run_id}
        )
        
        # 3. יוצר SchedulingService ומריץ אופטימיזציה
        scheduling_service = SchedulingService(db)
        run, solution = scheduling_service._execute_optimization_for_run(run)
        
        # 4. מחזיר תוצאות
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
        # טיפול בשגיאות - מעדכן את הרשומה ל-FAILED
        run.status = SchedulingRunStatus.FAILED
        run.completed_at = datetime.now()
        run.error_message = str(e)
        db.commit()
        raise
    finally:
        db.close()
```

**מה קורה?**
1. **Celery Worker** קורא את המשימה מ-Redis
2. **מעדכן סטטוס** - `self.update_state()` מעדכן את הסטטוס ב-Redis (ניתן לראות ב-Flower)
3. **מריץ את האופטימיזציה** - קורא ל-`SchedulingService._execute_optimization_for_run()`
4. **מחזיר תוצאות** - התוצאות נשמרות ב-Redis (Result Backend)

**מיקום ב-Docker**: `docker-compose.yml` - שורות 60-73

```yaml
celery-worker:
  build: ./backend
  command: celery -A app.celery_app worker --loglevel=info
  volumes:
    - ./backend:/app
  env_file:
    - ./backend/.env
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_healthy
  networks:
    - app-network
```

---

### שלב 5: SchedulingService מבצע את האופטימיזציה

**מיקום**: `backend/app/services/scheduling/scheduling_service.py` - שורות 119-178

```python
def _execute_optimization_for_run(
    self,
    run: SchedulingRunModel
) -> Tuple[SchedulingRunModel, SchedulingSolution]:
    """
    Execute optimization for an existing run record (used by async Celery task).
    """
    try:
        # מריץ את האופטימיזציה (ללא יישום הקצאות)
        run, solution = self._execute_run(run, apply_assignments=False)
        return run, solution
    except Exception as e:
        # טיפול בשגיאות...
        raise
```

**מה קורה בתוך `_execute_run()`?** (שורות 180-215)

```python
def _execute_run(
    self,
    run: SchedulingRunModel,
    apply_assignments: bool = True
) -> Tuple[SchedulingRunModel, SchedulingSolution]:
    # 1. מעדכן סטטוס ל-RUNNING (עם הגנה מפני race conditions)
    run = self._start_run(run)
    
    # 2. טוען קונפיגורציה
    config = self._load_optimization_config(run)
    
    # 3. בונה מודל MIP ופותר אותו
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

**תהליך האופטימיזציה כולל:**
1. **בניית נתונים** - `OptimizationDataBuilder` בונה את כל הנתונים הנדרשים
2. **בניית מודל MIP** - `MipSchedulingSolver` בונה את המודל המתמטי
3. **פתרון** - הסולבר (CBC/Gurobi) פותר את המודל
4. **ולידציה** - בודק שהפתרון עומד בכל ה-HARD constraints
5. **שמירה** - שומר את הפתרון ב-`SchedulingSolutionModel` (לא מיישם עדיין!)

---

### שלב 6: Frontend בודק את הסטטוס (Polling)

**מיקום**: `frontend/src/components/OptimizationPanel.jsx` - שורות 40-53

```javascript
// Poll for running optimizations
useEffect(() => {
  if (runs.some(r => r.status === 'RUNNING' || r.status === 'PENDING')) {
    setPolling(true);
    const interval = setInterval(() => {
      loadRuns(true); // Silent reload
    }, 3000); // Poll every 3 seconds

    return () => {
      clearInterval(interval);
      setPolling(false);
    };
  }
}, [runs]);
```

**מה קורה?**
- כל 3 שניות, ה-frontend שולח בקשה ל-`GET /scheduling/runs?weekly_schedule_id={id}`
- בודק אם יש ריצות עם סטטוס `PENDING` או `RUNNING`
- אם יש, ממשיך לבדוק כל 3 שניות
- כשהסטטוס משתנה ל-`COMPLETED` או `FAILED`, מפסיק לבדוק

**API Endpoint**: `backend/app/api/routes/schedulingRunRoutes.py` - שורות 62-77

```python
@router.get(
    "/",
    response_model=List[SchedulingRunRead],
    status_code=status.HTTP_200_OK,
    summary="Get all scheduling runs",
    dependencies=[Depends(require_auth)],
)
async def list_runs(
    weekly_schedule_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    return await get_all_scheduling_runs(
        db, 
        weekly_schedule_id=weekly_schedule_id,
        status_filter=status_filter
    )
```

---

### שלב 7: המשתמש רואה את התוצאות ומחיל פתרון

**מיקום**: `frontend/src/components/OptimizationPanel.jsx` - שורות 115-143

```javascript
async function handleApplySolution(overwrite = false) {
  if (!selectedRun) return;
  
  setApplying(true);
  try {
    const result = await applySolution(selectedRun.run_id, overwrite);
    toast.success(result.message || 'Solution applied successfully!');
    if (onSolutionApplied) {
      onSolutionApplied();
    }
  } catch (error) {
    // Error handling...
  } finally {
    setApplying(false);
  }
}
```

**מה קורה?**
- המשתמש בוחר ריצה שהושלמה (`status === 'COMPLETED'`)
- לוחץ על "Apply Solution to Schedule"
- זה קורא ל-`POST /scheduling/runs/{run_id}/apply`
- ה-API endpoint מיישם את כל ההקצאות מהפתרון ל-`ShiftAssignmentModel`

**API Endpoint**: `backend/app/api/routes/schedulingRunRoutes.py` - שורות 100-120

```python
@router.post(
    "/{run_id}/apply",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Apply scheduling solution to schedule",
    dependencies=[Depends(require_manager)],
)
async def apply_solution(
    run_id: int,
    overwrite: bool = Query(False, description="Overwrite existing assignments"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    return await apply_scheduling_solution(db, run_id, overwrite, current_user.user_id)
```

---

## 📊 דיאגרמת זרימה

```
┌─────────────┐
│   User      │
│  (Frontend) │
└──────┬──────┘
       │ 1. POST /scheduling/optimize/{id}
       ▼
┌─────────────────────────────────┐
│   FastAPI Backend               │
│   (schedulingRoutes.py)         │
│                                 │
│   - יוצר SchedulingRun (PENDING)│
│   - שולח משימה ל-Redis         │
│   - מחזיר run_id + task_id      │
└──────┬──────────────────────────┘
       │ 2. run_optimization_task.delay(run_id)
       ▼
┌─────────────────────────────────┐
│   Redis                         │
│   (Message Broker)              │
│                                 │
│   - שומר משימה בתור            │
│   - ממתין ל-Celery Worker       │
└──────┬──────────────────────────┘
       │ 3. Celery Worker קורא משימה
       ▼
┌─────────────────────────────────┐
│   Celery Worker                 │
│   (optimization_tasks.py)       │
│                                 │
│   - מעדכן סטטוס ל-RUNNING      │
│   - קורא ל-SchedulingService    │
└──────┬──────────────────────────┘
       │ 4. _execute_optimization_for_run()
       ▼
┌─────────────────────────────────┐
│   SchedulingService              │
│   (scheduling_service.py)        │
│                                 │
│   - בונה OptimizationData       │
│   - בונה מודל MIP               │
│   - פותר עם CBC/Gurobi         │
│   - שומר פתרון ב-DB            │
│   - מעדכן סטטוס ל-COMPLETED    │
└──────┬──────────────────────────┘
       │ 5. מחזיר תוצאות ל-Redis
       ▼
┌─────────────────────────────────┐
│   Redis                         │
│   (Result Backend)              │
│                                 │
│   - שומר תוצאות                │
│   - זמין לשאילתות              │
└──────┬──────────────────────────┘
       │ 6. Frontend בודק סטטוס (polling)
       ▼
┌─────────────────────────────────┐
│   Frontend                      │
│   (OptimizationPanel.jsx)       │
│                                 │
│   - בודק כל 3 שניות            │
│   - מציג תוצאות                │
│   - מאפשר יישום פתרון          │
└─────────────────────────────────┘
```

---

## 🔧 תפקידים של כל רכיב

### Redis

**תפקידים:**
1. **Message Broker** - תור משימות בין FastAPI ל-Celery Worker
2. **Result Backend** - שומר תוצאות זמניות של משימות
3. **Task Queue** - תור משימות ממתינות לביצוע

**מיקום בקוד:**
- הגדרה: `backend/app/celery_app.py` - שורות 12-18
- Docker: `docker-compose.yml` - שורות 47-58

**איך זה עובד?**
- כשקוראים ל-`task.delay()`, Celery שולח הודעה ל-Redis
- Redis שומר את ההודעה בתור (queue)
- Celery Worker קורא הודעות מהתור ומבצע אותן
- התוצאות נשמרות ב-Redis (עם TTL של 24 שעות)

---

### Celery

**תפקידים:**
1. **Task Queue System** - מערכת תור משימות אסינכרוניות
2. **Background Processing** - עיבוד ברקע ללא חסימת ה-API
3. **Distributed Processing** - אפשר להריץ מספר Workers במקביל

**מיקום בקוד:**
- הגדרה: `backend/app/celery_app.py`
- Task: `backend/app/tasks/optimization_tasks.py` - שורות 17-89
- Docker: `docker-compose.yml` - שורות 60-73

**איך זה עובד?**
- `@celery_app.task` מגדיר פונקציה כמשימת Celery
- `task.delay()` שולח את המשימה ל-Redis
- Celery Worker קורא משימות מ-Redis ומבצע אותן
- התוצאות נשמרות ב-Redis

**תצורת Celery** (`celery_app.py` - שורות 23-35):
```python
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    result_expires=86400,  # Results expire after 24 hours
)
```

---

### Flower (Monitoring)

**תפקידים:**
1. **Real-time Monitoring** - ניטור משימות Celery בזמן אמת
2. **Task Dashboard** - Dashboard לניהול משימות
3. **Performance Metrics** - מדדי ביצועים

**מיקום:**
- Docker: `docker-compose.yml` - שורות 75-86
- URL: http://localhost:5555

**מה אפשר לראות ב-Flower?**
- רשימת כל המשימות (PENDING, RUNNING, COMPLETED, FAILED)
- סטטוס של כל משימה בזמן אמת
- זמן ריצה, שגיאות, תוצאות
- ביצועים של Workers

---

## 📝 סיכום - מה קורה בכל שלב?

| שלב | רכיב | פעולה | זמן |
|-----|------|-------|-----|
| 1 | Frontend | משתמש לוחץ "Run Optimization" | מיידי |
| 2 | FastAPI | יוצר `SchedulingRun` (PENDING), שולח ל-Redis | < 1 שנייה |
| 3 | Redis | שומר משימה בתור | מיידי |
| 4 | Celery Worker | קורא משימה, מעדכן ל-RUNNING | < 1 שנייה |
| 5 | SchedulingService | בונה נתונים, מודל MIP, פותר | 10-300 שניות |
| 6 | PostgreSQL | שומר פתרון ב-`SchedulingSolutionModel` | < 1 שנייה |
| 7 | Redis | שומר תוצאות | מיידי |
| 8 | Frontend | בודק סטטוס (polling כל 3 שניות) | כל 3 שניות |
| 9 | Frontend | משתמש רואה תוצאות, מיישם פתרון | לפי המשתמש |

---

## 🔗 קישורים לקוד

### Frontend
- **OptimizationPanel**: `frontend/src/components/OptimizationPanel.jsx`
- **API Client**: `frontend/src/api/optimization.js`

### Backend - API
- **Optimize Endpoint**: `backend/app/api/routes/schedulingRoutes.py:48-116`
- **Run Status Endpoint**: `backend/app/api/routes/schedulingRunRoutes.py:62-77`
- **Apply Solution Endpoint**: `backend/app/api/routes/schedulingRunRoutes.py:100-120`

### Backend - Celery
- **Celery Config**: `backend/app/celery_app.py`
- **Optimization Task**: `backend/app/tasks/optimization_tasks.py:17-89`

### Backend - Services
- **SchedulingService**: `backend/app/services/scheduling/scheduling_service.py`
  - `_execute_optimization_for_run()`: שורות 119-178
  - `_execute_run()`: שורות 180-215
  - `_build_and_solve()`: בונה ופותר את המודל

### Infrastructure
- **Docker Compose**: `docker-compose.yml`
  - Redis: שורות 47-58
  - Celery Worker: שורות 60-73
  - Flower: שורות 75-86

---

## 💡 שאלות נפוצות

### Q: למה צריך Celery ו-Redis? למה לא פשוט להריץ את האופטימיזציה ישירות?

**A**: כי אופטימיזציה יכולה לקחת 10-300 שניות. אם נעשה את זה סינכרוני:
- ❌ הבקשה תתקע (timeout)
- ❌ המשתמש לא יכול לעבוד בזמן ההמתנה
- ❌ אם יש שגיאה, כל התהליך נכשל

עם Celery:
- ✅ הבקשה חוזרת מיד
- ✅ המשתמש יכול להמשיך לעבוד
- ✅ אפשר לבדוק סטטוס בזמן אמת
- ✅ אם Worker נופל, המשימה נשמרת ב-Redis וניתן להריץ שוב

### Q: מה קורה אם Celery Worker נופל באמצע?

**A**: 
- המשימה נשמרת ב-Redis
- Worker אחר (או אותו Worker אחרי restart) יכול להריץ את המשימה
- אם המשימה כבר התחילה, היא תסומן כ-FAILED במסד הנתונים

### Q: כמה זמן נשמרות התוצאות ב-Redis?

**A**: 24 שעות (86400 שניות) - מוגדר ב-`result_expires=86400` ב-`celery_app.py`

### Q: איך אפשר לראות מה קורה בזמן אמת?

**A**: 
1. **Flower** - http://localhost:5555 - Dashboard מלא
2. **API** - `GET /scheduling/runs/{run_id}` - סטטוס מהמסד נתונים
3. **Frontend** - `OptimizationPanel` בודק כל 3 שניות

### Q: מה ההבדל בין `apply_assignments=True` ל-`False`?

**A**:
- **`apply_assignments=False`** (משימת Celery): רק שומר פתרון ב-`SchedulingSolutionModel`, לא מיישם
- **`apply_assignments=True`** (סינכרוני): שומר פתרון **וגם** מיישם אותו ל-`ShiftAssignmentModel`

הסיבה: במשימת Celery, אנחנו לא רוצים ליישם אוטומטית - המשתמש צריך לבחור אם ליישם את הפתרון.
