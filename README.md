# Smart Scheduling

An intelligent employee scheduling system that uses **Mixed Integer Programming (MIP)** to automatically generate optimal shift assignments. The system balances employee preferences, availability, fairness, and business constraints to create schedules that maximize satisfaction while ensuring full coverage.

## Architecture Overview

**Frontend:** React 19 + Vite + TailwindCSS 4  
**Backend:** FastAPI + SQLAlchemy + Celery  
**Database:** PostgreSQL 14  
**Optimization Engine:** Python-MIP with CBC Solver  
**Task Queue:** Redis + Celery + Flower  
**Deployment:** Docker Compose

### Core Functionality

- **Automated Optimization**: MIP-based solver generates optimal shift assignments
- **Employee Management**: User roles, preferences, and time-off management
- **Schedule Management**: Weekly schedules with planned shifts and assignments
- **Constraint Validation**: System-wide work rules (max hours, rest periods, consecutive days)
- **Time-Off System**: Employee requests with manager approval workflow
- **Optimization Configuration**: Configurable optimization parameters and weights

### Technical Stack

- **Frontend**: React 19 + Vite 7 + TailwindCSS 4
- **Backend**: FastAPI + SQLAlchemy + JWT Authentication
- **Database**: PostgreSQL
- **Optimization**: Python-MIP (CBC solver)
- **Dev/Run**: Docker Compose or local development

## 📋 Quick Start

### Docker (Recommended)

Prerequisites: Docker and Docker Compose installed.

```bash
# From the repo root
docker compose up --build
```

Services:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000 (docs at /docs)
- **Postgres**: localhost:5432 (user: postgres, password: postgres, db: scheduler_db)

### Local Development

#### 1) Database

- Install PostgreSQL and create a database named `scheduler_db`
- Connection string: `postgresql://postgres:postgres@localhost:5432/scheduler_db`

#### 2) Backend (FastAPI)

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Create backend/.env
cat > .env << 'EOF'
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scheduler_db
JWT_SECRET_KEY=change-me-in-dev
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=3
EOF

# Run API
uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs

#### 3) Frontend (React)

```bash
cd frontend
npm install
# Optional: point to API if different than default
echo 'VITE_API_URL=http://localhost:8000' > .env.local
npm run dev
```

- App: http://localhost:5173

## 🏗️ Project Structure

```
smart-scheduling/
├── frontend/          # React app (Vite)
│   ├── src/
│   │   ├── api/       # API client functions
│   │   ├── components/ # React components
│   │   ├── pages/     # Page components
│   │   └── contexts/  # React contexts
│   └── package.json
├── backend/           # FastAPI app
│   ├── app/
│   │   ├── api/       # API routes and controllers
│   │   ├── db/        # SQLAlchemy models
│   │   ├── services/  # Business logic
│   │   │   ├── scheduling/  # Optimization engine
│   │   │   └── optimization_data_services/
│   │   └── schemas/    # Pydantic schemas
│   └── requirements.txt
└── docker-compose.yml  # Local dev stack
```

## 🎯 Architecture Overview

### Optimization Engine

The system uses **Mixed Integer Programming (MIP)** to solve the shift assignment problem:

- **Decision Variables**: Binary variables `x[i,j,k]` = 1 if employee `i` assigned to shift `j` in role `k`
- **Hard Constraints**:
  - All required roles filled
  - No time-off conflicts
  - Role qualifications
  - No overlapping shifts
  - Minimum rest between shifts
  - Max consecutive working days
  - Max hours per week
- **Objective Function**: Minimize weighted sum of:
  - Workload imbalance (fairness)
  - Coverage gaps
  - Preference violations (optional)

### Key Services

1. **SchedulingService**: Orchestrates optimization, builds MIP model, runs solver
2. **ConstraintService**: Validates work rules and constraints
3. **OptimizationDataBuilder**: Extracts and prepares data for MIP model
4. **MIP Solver**: Python-MIP with CBC solver

### Data Models

**Core Entities:**

- `User` - Employees with roles and manager status
- `Role` - Job positions (Waiter, Bartender, etc.)
- `ShiftTemplate` - Predefined shift types
- `WeeklySchedule` - Container for a week's schedule
- `PlannedShift` - Specific shift instances
- `ShiftAssignment` - Employee-to-shift assignments

**Optimization Entities:**

- `TimeOffRequest` - Employee time-off requests
- `EmployeePreferences` - Shift preferences
- `SystemConstraints` - System-wide work rules
- `OptimizationConfig` - Optimization parameters
- `SchedulingRun` - Optimization execution tracking
- `SchedulingSolution` - Proposed assignments from optimizer


### API Documentation

## Technology Stack

### Frontend
- **React 19** - UI framework with hooks and context
- **Vite 7** - Fast build tool and dev server
- **TailwindCSS 4** - Utility-first CSS framework
- **React Router 6** - Client-side routing
- **Axios** - HTTP client for API calls
- **date-fns** - Date manipulation and formatting
- **Lucide React** - Icon library
- **React Hot Toast** - Toast notifications

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL 14** - Primary database
- **Pydantic** - Data validation and settings management
- **Python-JOSE** - JWT token handling
- **Werkzeug** - Password hashing utilities

### Optimization Engine
- **Python-MIP 1.15+** - Mixed Integer Programming library
- **CBC Solver** - Open-source MIP solver (bundled with Python-MIP)
- **NumPy** - Numerical operations and matrix computations
- Algorithm: Multi-objective optimization with weighted preferences, fairness, and coverage

### Task Queue & Background Processing
- **Celery 5.3+** - Distributed task queue for async optimization
- **Redis 7** - Message broker and result backend
- **Flower 2.0+** - Real-time Celery monitoring (http://localhost:5555)

### Authentication & Security
- **JWT (JSON Web Tokens)** - Stateless authentication
- **Werkzeug** - Secure password hashing
- **Role-based Access Control** - Manager vs Employee permissions

### Development & Deployment
- **Docker & Docker Compose** - Containerization and orchestration
- **PostgreSQL 14** - Production-grade relational database
- **Uvicorn** - ASGI server for FastAPI

## Design Patterns & Architecture

### Backend Architecture

**Service Layer Pattern**
- `SchedulingService` - Main orchestrator for optimization
- `ConstraintService` - Manages system constraints
- `OptimizationDataBuilder` - Prepares data for MIP solver
- Separation of concerns: controllers → services → models

**MIP Solver Design**
- `MipSchedulingSolver` - Builds and solves optimization model
- Decision variables: Binary variables x[i,j,r] (employee i, shift j, role r)
- Multi-objective function: Weighted combination of preferences, fairness, and coverage
- Hard constraints: Time-off, availability, max hours, no overlaps, min rest
- Soft constraints: Min shifts per week (with penalties)

**Data Persistence Layer**
- `SchedulingPersistence` - Database operations for solutions
- `SchedulingRunModel` - Tracks optimization executions
- `SchedulingSolutionModel` - Stores optimal assignments

### Frontend Architecture

**Component-Based Design**
- Functional components with React hooks
- Shared UI components library (Button, Card, Skeleton, etc.)
- Layout components (MainLayout, PageLayout)
- Page components with data fetching

**State Management**
- React Context for global state (LoadingContext)
- Local component state with useState
- Auth state persisted in localStorage

**Routing Strategy**
- Protected routes with authentication checks
- Admin-only routes with role verification
- Lazy loading with React Router

**UI/UX Design**
- Blue gradient theme with professional appearance
- Sidebar navigation with icons
- Weekly calendar grid for schedule visualization
- Quick stats dashboard with metrics
- Toast notifications for feedback

### Optimization Algorithm

**MIP Model Components**

1. **Decision Variables**
   - x[i,j,r] = 1 if employee i assigned to shift j in role r, else 0
   - Binary variables for discrete yes/no decisions

2. **Objective Function** (Maximize)
   - Component 1: Preference satisfaction (employee preferences)
   - Component 2: Coverage (fill all required shifts)
   - Component 3: Fairness (balanced workload distribution)
   - Component 4: Soft penalty minimization
   - Weighted combination with configurable weights

3. **Hard Constraints** (Must Satisfy)
   - Coverage: Each shift-role filled exactly once
   - No time-off conflicts
   - Role qualifications required
   - No overlapping shift assignments
   - Maximum hours per week
   - Maximum shifts per week
   - Minimum rest hours between shifts

4. **Soft Constraints** (Penalties)
   - Minimum shifts per week (with violation penalties)

**Solver Configuration**
- Timeout: Configurable max runtime (default 300s)
- MIP Gap: Optimality tolerance (default 0.01 = 1%)
- Solver: CBC (Coin-or Branch and Cut)

## Key Features

### For Employees
- **Dashboard** - View upcoming shifts and weekly summary
- **My Preferences** - Set preferred days, times, and shift templates
- **Time-Off Requests** - Request vacation, sick leave, personal days
- **Weekly Schedule** - Calendar view of assigned shifts

### For Managers
- **Schedule Optimization** - Automatic shift assignment with MIP solver
- **Employee Management** - Add, edit, view employee profiles
- **Shift Templates** - Define recurring shift patterns
- **System Constraints** - Configure business rules (max hours, min rest, etc.)
- **Time-Off Approval** - Review and approve employee requests
- **Optimization Config** - Tune solver weights and parameters

### Optimization Features
- Multi-objective scheduling balancing 3+ criteria
- Fair workload distribution across employees
- Employee preference satisfaction
- Automatic constraint validation
- Infeasibility detection and reporting
- Solution quality metrics
- Background processing with progress tracking

## Useful Links

---
