# 🏗️ ארכיטקטורת המערכת - High Level Overview

תיאור מפורט של ארכיטקטורת המערכת Smart Scheduling ברמה גבוהה, כולל רכיבים, שכבות, תקשורת ודפוסי עיצוב.

---

## 📋 סקירה כללית

**Smart Scheduling** היא מערכת לניהול שיבוץ עובדים המשתמשת ב-**Mixed Integer Programming (MIP)** לאופטימיזציה אוטומטית של הקצאות משמרות.

### מטרת המערכת

- ניהול שיבוץ שבועי של עובדים
- אופטימיזציה אוטומטית של הקצאות משמרות
- ניהול העדפות עובדים ובקשות חופש
- אכיפת אילוצים עסקיים (שעות מקסימליות, מנוחה, ימים רצופים)
- פרסום לוחות זמנים לעובדים

---

## 🎯 ארכיטקטורה כללית

המערכת בנויה כ-**Microservices Architecture** עם הפרדה ברורה בין Frontend, Backend, Database, ו-Background Processing.

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Frontend (React + Vite)                                  │  │
│  │  - React 19 + Hooks + Context                            │  │
│  │  - TailwindCSS 4                                          │  │
│  │  - React Router 6                                         │  │
│  │  - Axios (HTTP Client)                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST API
                              │ (JWT Authentication)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Backend (FastAPI)                                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │   Routes     │→ │ Controllers  │→ │   Services   │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  │         │                  │                  │          │  │
│  │         └──────────────────┴──────────────────┘          │  │
│  │                          │                               │  │
│  │                          ▼                               │  │
│  │                   ┌──────────────┐                       │  │
│  │                   │   Schemas    │                       │  │
│  │                   │  (Pydantic)  │                       │  │
│  │                   └──────────────┘                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ SQLAlchemy ORM
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL 14                                            │  │
│  │  - Users, Roles, Schedules                                │  │
│  │  - Shift Assignments                                      │  │
│  │  - Optimization Runs & Solutions                          │  │
│  │  - Constraints & Preferences                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   BACKGROUND PROCESSING LAYER                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Celery Worker                                            │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Optimization Tasks                                  │  │  │
│  │  │  - SchedulingService                                 │  │  │
│  │  │  - MipSchedulingSolver                               │  │  │
│  │  │  - ConstraintService                                 │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              │ Task Queue                        │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Redis 7                                                 │  │
│  │  - Message Broker                                        │  │
│  │  - Result Backend                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 רכיבים עיקריים

### 1. Frontend (React Application)

**מיקום**: `frontend/`

**טכנולוגיות:**

- **React 19** - UI Framework
- **Vite 7** - Build tool & Dev server
- **TailwindCSS 4** - Styling
- **React Router 6** - Routing
- **Axios** - HTTP Client
- **React Hot Toast** - Notifications

**מבנה:**

```
frontend/src/
├── api/              # API client functions
├── components/       # React components
│   ├── ui/          # Reusable UI components
│   └── ...
├── pages/           # Page components
│   ├── Admin/       # Manager pages
│   └── ...
├── layouts/         # Layout components
├── contexts/        # React Contexts
├── lib/            # Utilities (auth, axios)
└── styles/         # Global styles
```

**תפקידים:**

- ממשק משתמש למנהלים ועובדים
- ניהול state מקומי (useState, Context)
- קריאות API אסינכרוניות
- Routing עם הגנת routes
- Polling לסטטוס אופטימיזציה

---

### 2. Backend (FastAPI Application)

**מיקום**: `backend/app/`

**טכנולוגיות:**

- **FastAPI** - Web Framework
- **SQLAlchemy** - ORM
- **Pydantic** - Data Validation
- **Python-JOSE** - JWT
- **Uvicorn** - ASGI Server

**מבנה (Layered Architecture):**

```
backend/app/
├── api/
│   ├── routes/          # API route definitions
│   ├── controllers/     # Request handlers (business logic)
│   └── dependencies/    # Auth dependencies
├── db/
│   └── models/         # SQLAlchemy ORM models
├── schemas/            # Pydantic schemas (validation)
├── services/           # Business logic layer
│   ├── scheduling/     # Optimization services
│   └── ...
├── tasks/              # Celery tasks
├── core/               # Configuration
└── server.py           # Application entry point
```

**שכבות:**

#### 2.1 Routes Layer

- **תפקיד**: הגדרת API endpoints
- **דוגמה**: `schedulingRoutes.py`, `usersRoutes.py`
- **תכונות**:
  - HTTP methods (GET, POST, PUT, DELETE)
  - Path parameters & Query parameters
  - Dependencies (auth, permissions)

#### 2.2 Controllers Layer

- **תפקיד**: עיבוד בקשות HTTP
- **דוגמה**: `schedulingRunController.py`, `userController.py`
- **תכונות**:
  - Validation של input
  - קריאה ל-Services
  - טיפול בשגיאות
  - החזרת responses

#### 2.3 Services Layer

- **תפקיד**: לוגיקה עסקית
- **דוגמה**: `SchedulingService`, `ConstraintService`
- **תכונות**:
  - Business rules
  - Data transformation
  - קריאה ל-Models
  - Orchestration

#### 2.4 Models Layer (ORM)

- **תפקיד**: מיפוי ל-Database
- **דוגמה**: `UserModel`, `SchedulingRunModel`
- **תכונות**:
  - SQLAlchemy ORM
  - Relationships (one-to-many, many-to-many)
  - Database operations

#### 2.5 Schemas Layer

- **תפקיד**: Validation & Serialization
- **דוגמה**: `UserSchema`, `SchedulingRunSchema`
- **תכונות**:
  - Pydantic models
  - Input validation
  - Output serialization
  - Type safety

---

### 3. Database (PostgreSQL)

**מיקום**: Docker container

**טכנולוגיות:**

- **PostgreSQL 14** - Relational Database
- **SQLAlchemy ORM** - Object-Relational Mapping

**מודלים עיקריים:**

#### Core Models

- **UserModel** - עובדים ומנהלים
- **RoleModel** - תפקידים (Waiter, Bartender, etc.)
- **UserRoleModel** - קשר many-to-many בין עובדים לתפקידים
- **ShiftTemplateModel** - תבניות משמרות
- **WeeklyScheduleModel** - לוחות זמנים שבועיים
- **PlannedShiftModel** - משמרות מתוכננות
- **ShiftAssignmentModel** - הקצאות בפועל

#### Optimization Models

- **SchedulingRunModel** - ריצות אופטימיזציה
- **SchedulingSolutionModel** - פתרונות מוצעים
- **OptimizationConfigModel** - הגדרות אופטימיזציה

#### Configuration Models

- **SystemConstraintsModel** - אילוצים עסקיים
- **EmployeePreferencesModel** - העדפות עובדים
- **TimeOffRequestModel** - בקשות חופש

#### System Models

- **ActivityLogModel** - לוג פעולות

**Relationships:**

- User ↔ Role (Many-to-Many)
- User → ShiftAssignment (One-to-Many)
- WeeklySchedule → PlannedShift (One-to-Many)
- PlannedShift → ShiftAssignment (One-to-Many)
- SchedulingRun → SchedulingSolution (One-to-Many)

---

### 4. Background Processing (Celery + Redis)

**מיקום**: Docker containers

**טכנולוגיות:**

- **Celery 5.3+** - Distributed Task Queue
- **Redis 7** - Message Broker & Result Backend
- **Flower** - Celery Monitoring

**תפקידים:**

#### 4.1 Celery Worker

- **תפקיד**: ביצוע משימות אסינכרוניות
- **דוגמה**: `run_optimization_task`
- **תכונות**:
  - Background processing
  - Long-running tasks
  - Error handling
  - Progress tracking

#### 4.2 Redis

- **תפקיד**: Message Broker & Result Backend
- **תכונות**:
  - Task queue management
  - Result storage (24 hours TTL)
  - State tracking

#### 4.3 Flower

- **תפקיד**: Monitoring & Dashboard
- **תכונות**:
  - Real-time task monitoring
  - Performance metrics
  - Error tracking

---

### 5. Optimization Engine

**מיקום**: `backend/app/services/scheduling/`

**טכנולוגיות:**

- **Python-MIP 1.15+** - MIP Library
- **CBC Solver** - Open-source MIP Solver
- **NumPy** - Numerical operations

**רכיבים:**

#### 5.1 SchedulingService

- **תפקיד**: Orchestrator ראשי
- **תכונות**:
  - ניהול ריצות אופטימיזציה
  - קואורדינציה בין רכיבים
  - Error handling
  - Validation

#### 5.2 OptimizationDataBuilder

- **תפקיד**: בניית נתונים למודל
- **תכונות**:
  - איסוף נתונים מהמסד נתונים
  - טרנספורמציה למודל MIP
  - הכנת constraints

#### 5.3 MipSchedulingSolver

- **תפקיד**: בניית ופתרון מודל MIP
- **תכונות**:
  - יצירת משתני החלטה
  - בניית אילוצים
  - בניית פונקציית מטרה
  - קריאה ל-Solver

#### 5.4 ConstraintService

- **תפקיד**: ולידציה של אילוצים
- **תכונות**:
  - בדיקת HARD constraints
  - בדיקת SOFT constraints
  - דיווח על הפרות

#### 5.5 SchedulingPersistence

- **תפקיד**: שמירת פתרונות
- **תכונות**:
  - שמירה ב-SchedulingSolutionModel
  - יישום ל-ShiftAssignmentModel
  - Transaction management

---

## 🔄 תקשורת בין רכיבים

### 1. Frontend ↔ Backend

```
Frontend (React)
    │
    │ HTTP/REST API
    │ JWT Authentication
    │
    ▼
Backend (FastAPI)
    │
    │ Routes → Controllers → Services → Models
    │
    ▼
Database (PostgreSQL)
```

**פרוטוקול**: HTTP/HTTPS
**Format**: JSON
**Authentication**: JWT Tokens
**CORS**: מוגדר ל-localhost:5173

### 2. Backend ↔ Database

```
Backend (FastAPI)
    │
    │ SQLAlchemy ORM
    │ Connection Pool
    │
    ▼
Database (PostgreSQL)
```

**פרוטוקול**: PostgreSQL Protocol
**ORM**: SQLAlchemy
**Connection**: Connection Pooling

### 3. Backend ↔ Celery

```
Backend (FastAPI)
    │
    │ Celery Client
    │ task.delay()
    │
    ▼
Redis (Message Broker)
    │
    │ Task Queue
    │
    ▼
Celery Worker
    │
    │ Execute Task
    │
    ▼
Redis (Result Backend)
```

**פרוטוקול**: Redis Protocol
**Format**: JSON
**Pattern**: Producer-Consumer

---

## 🎨 דפוסי עיצוב (Design Patterns)

### 1. Layered Architecture

**תיאור**: הפרדה לשכבות ברורות

```
Routes (API Layer)
    ↓
Controllers (Request Handling)
    ↓
Services (Business Logic)
    ↓
Models (Data Access)
    ↓
Database
```

**יתרונות**:

- Separation of Concerns
- Testability
- Maintainability
- Scalability

### 2. Service Layer Pattern

**תיאור**: לוגיקה עסקית ב-Services נפרדים

**דוגמאות**:

- `SchedulingService` - אופטימיזציה
- `ConstraintService` - ולידציה
- `OptimizationDataBuilder` - בניית נתונים

**יתרונות**:

- Reusability
- Testability
- Single Responsibility

### 3. Repository Pattern (implicit)

**תיאור**: גישה ל-Database דרך Models

**דוגמה**:

```python
# דרך SQLAlchemy ORM
db.query(UserModel).filter(...).first()
```

### 4. Dependency Injection

**תיאור**: FastAPI מספק DI אוטומטי

**דוגמה**:

```python
async def endpoint(db: Session = Depends(get_db)):
    # data מוזרק אוטומטית
```

### 5. Async Task Queue Pattern

**תיאור**: Celery למשימות ארוכות

**דוגמה**:

```python
# Backend שולח משימה
task = run_optimization_task.delay(run_id)

# Celery Worker מבצע ברקע
@celery_app.task
def run_optimization_task(run_id):
    # Long-running task
```

---

## 🔐 אבטחה

### 1. Authentication

**מנגנון**: JWT (JSON Web Tokens)

**תהליך**:

1. משתמש מתחבר → `POST /users/login`
2. Backend בודק credentials
3. מחזיר JWT token
4. Frontend שומר token ב-localStorage
5. כל בקשה כוללת `Authorization: Bearer <token>`

### 2. Authorization

**מנגנון**: Role-Based Access Control (RBAC)

**תפקידים**:

- **Employee** - גישה מוגבלת (לוח זמנים אישי, העדפות)
- **Manager** - גישה מלאה (ניהול, אופטימיזציה, אישורים)

**יישום**:

```python
@router.post("/optimize/{id}", dependencies=[Depends(require_manager)])
async def optimize_schedule(...):
    # רק מנהלים יכולים לגשת
```

### 3. Password Security

**מנגנון**: Werkzeug password hashing

**תכונות**:

- Hashing עם salt
- Secure password storage
- No plain text passwords

---

## 📊 Data Flow

### 1. קריאת נתונים (Read Flow)

```
User Action (Frontend)
    ↓
API Call (GET /schedules)
    ↓
Route Handler
    ↓
Controller
    ↓
Service (optional)
    ↓
Model Query (SQLAlchemy)
    ↓
Database (SELECT)
    ↓
Response (JSON)
    ↓
Frontend Display
```

### 2. כתיבת נתונים (Write Flow)

```
User Action (Frontend)
    ↓
API Call (POST /schedules)
    ↓
Route Handler
    ↓
Controller
    ↓
Schema Validation (Pydantic)
    ↓
Service (Business Logic)
    ↓
Model Save (SQLAlchemy)
    ↓
Database (INSERT/UPDATE)
    ↓
Response (JSON)
    ↓
Frontend Update
```

### 3. אופטימיזציה (Optimization Flow)

```
User Clicks "Run Optimization"
    ↓
POST /scheduling/optimize/{id}
    ↓
Backend Creates SchedulingRun (PENDING)
    ↓
Celery Task Dispatched to Redis
    ↓
Response (run_id) - Immediate Return
    ↓
Celery Worker Picks Up Task
    ↓
SchedulingService Executes
    ↓
MipSchedulingSolver Solves
    ↓
Solution Saved to DB
    ↓
Frontend Polls Status
    ↓
User Sees Results
```

---

## 🚀 Deployment Architecture

### Docker Compose Stack

```
┌─────────────────────────────────────────────────┐
│  Docker Network: app-network                    │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐           │
│  │   Frontend    │  │   Backend    │           │
│  │  (Port 5173)  │  │  (Port 8000)  │           │
│  └──────────────┘  └──────────────┘           │
│         │                  │                    │
│         │                  │                    │
│  ┌──────────────┐  ┌──────────────┐           │
│  │  PostgreSQL   │  │    Redis     │           │
│  │  (Port 5432)  │  │  (Port 6379)  │           │
│  └──────────────┘  └──────────────┘           │
│         │                  │                    │
│         │                  │                    │
│  ┌──────────────┐  ┌──────────────┐           │
│  │ Celery Worker │  │    Flower    │           │
│  │               │  │  (Port 5555) │           │
│  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────┘
```

**Services:**

1. **db** - PostgreSQL 14
2. **backend** - FastAPI application
3. **frontend** - React application
4. **redis** - Message broker
5. **celery-worker** - Background tasks
6. **flower** - Celery monitoring

**Networking:**

- כל השירותים ב-`app-network`
- תקשורת פנימית דרך Docker network
- Ports חשופים ל-localhost

---

## 📈 Scalability Considerations

### 1. Horizontal Scaling

**Frontend:**

- Stateless - ניתן להריץ מספר instances
- Load balancer מול instances

**Backend:**

- Stateless API - ניתן להריץ מספר instances
- Shared database
- Shared Redis

**Celery Workers:**

- ניתן להריץ מספר workers
- Redis מחלק משימות אוטומטית

### 2. Database Scaling

**Options:**

- Read replicas לשאילתות read-only
- Connection pooling
- Query optimization
- Indexing

### 3. Caching

**Current:**

- Redis משמש רק ל-Celery

**Potential:**

- Cache API responses
- Cache optimization results
- Cache user sessions

---

## 🔧 Configuration Management

### Environment Variables

**Backend** (`.env`):

```env
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=...
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=3
REDIS_URL=redis://...
```

**Frontend** (`.env.local`):

```env
VITE_API_URL=http://localhost:8000
```

### Configuration Files

- **docker-compose.yml** - Service definitions
- **requirements.txt** - Python dependencies
- **package.json** - Node dependencies

---

## 🧪 Testing Strategy

### Backend Tests

**Location**: `backend/tests/`

**Types:**

- Unit tests - Services, Models
- Integration tests - API endpoints
- E2E tests - Full flows

**Tools:**

- pytest
- SQLAlchemy test database

### Frontend Tests

**Potential:**

- Component tests
- Integration tests
- E2E tests (Cypress/Playwright)

---

## 📚 טכנולוגיות - סיכום

### Frontend Stack

- React 19
- Vite 7
- TailwindCSS 4
- React Router 6
- Axios

### Backend Stack

- FastAPI
- SQLAlchemy
- Pydantic
- Python-JOSE
- Uvicorn

### Database

- PostgreSQL 14

### Optimization

- Python-MIP
- CBC Solver
- NumPy

### Background Processing

- Celery 5.3+
- Redis 7
- Flower

### Deployment

- Docker
- Docker Compose

---

## 🎯 עקרונות ארכיטקטוריים

### 1. Separation of Concerns

- Frontend = UI/UX
- Backend = Business Logic
- Database = Data Storage
- Celery = Background Processing

### 2. Single Responsibility

- כל Service אחראי לתחום אחד
- כל Model מייצג entity אחד
- כל Route מטפל ב-resource אחד

### 3. DRY (Don't Repeat Yourself)

- Shared components
- Reusable services
- Common utilities

### 4. SOLID Principles

- **S**ingle Responsibility
- **O**pen/Closed
- **L**iskov Substitution
- **I**nterface Segregation
- **D**ependency Inversion

### 5. Async-First

- Celery למשימות ארוכות
- FastAPI async endpoints
- Non-blocking operations

---

## 🔗 קישורים לקוד

### Frontend

- **Entry Point**: `frontend/src/main.jsx`
- **App**: `frontend/src/App.jsx`
- **API Client**: `frontend/src/api/`
- **Components**: `frontend/src/components/`

### Backend

- **Entry Point**: `backend/app/server.py`
- **Routes**: `backend/app/api/routes/`
- **Controllers**: `backend/app/api/controllers/`
- **Services**: `backend/app/services/`
- **Models**: `backend/app/db/models/`
- **Schemas**: `backend/app/schemas/`

### Infrastructure

- **Docker Compose**: `docker-compose.yml`
- **Backend Dockerfile**: `backend/Dockerfile`
- **Frontend Dockerfile**: `frontend/Dockerfile`

---

## 💡 סיכום

המערכת בנויה כ-**Modern Full-Stack Application** עם:

✅ **Frontend** - React SPA עם routing ו-state management  
✅ **Backend** - FastAPI REST API עם layered architecture  
✅ **Database** - PostgreSQL עם SQLAlchemy ORM  
✅ **Background Processing** - Celery + Redis למשימות ארוכות  
✅ **Optimization Engine** - MIP Solver לאופטימיזציה  
✅ **Security** - JWT authentication + RBAC  
✅ **Deployment** - Docker Compose לפריסה קלה

הארכיטקטורה תומכת ב:

- Scalability - ניתן להרחיב כל רכיב בנפרד
- Maintainability - קוד מאורגן ושכבות ברורות
- Testability - הפרדה מאפשרת בדיקות קלות
- Performance - Async processing למשימות ארוכות
