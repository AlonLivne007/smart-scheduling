# Smart Scheduling

An intelligent employee scheduling system that uses **Mixed Integer Programming (MIP)** to automatically generate optimal shift assignments. The system balances employee preferences, availability, fairness, and business constraints to create schedules that maximize satisfaction while ensuring full coverage.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Technology Stack](#technology-stack)
- [Key Features](#key-features)
- [Data Models](#data-models)
- [API Documentation](#api-documentation)
- [Optimization Engine](#optimization-engine)
- [Design Patterns & Architecture](#design-patterns--architecture)
- [Environment Configuration](#environment-configuration)
- [Testing](#testing)
- [Seeding Data](#seeding-data)
- [Development Guide](#development-guide)

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
- **Schedule Publishing**: Publish/unpublish schedules with employee notifications
- **Constraint Validation**: System-wide work rules (max hours, rest periods, consecutive days)
- **Time-Off System**: Employee requests with manager approval workflow
- **Optimization Configuration**: Configurable optimization parameters and weights
- **Activity Logging**: Comprehensive audit trail of all system actions
- **Export Functionality**: Export schedules to PDF and Excel/CSV formats
- **Dashboard Metrics**: Real-time statistics and key performance indicators

## 📋 Quick Start

### Docker (Recommended)

Prerequisites: Docker and Docker Compose installed.

```bash
# From the repo root
docker compose up --build
```

**Services:**

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000 (docs at /docs)
- **PostgreSQL**: localhost:5432 (user: postgres, password: postgres, db: scheduler_db)
- **Redis**: localhost:6379
- **Flower** (Celery Monitor): http://localhost:5555

### Local Development

#### 1) Database Setup

- Install PostgreSQL 14 and create a database named `scheduler_db`
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
REDIS_URL=redis://localhost:6379/0
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

#### 4) Celery Worker (Optional, for background tasks)

```bash
cd backend
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info
```

#### 5) Flower (Optional, for Celery monitoring)

```bash
cd backend
source venv/bin/activate
celery -A app.celery_app flower --port=5555
```

## 🏗️ Project Structure

```
smart-scheduling/
├── frontend/                    # React app (Vite)
│   ├── src/
│   │   ├── api/                # API client functions
│   │   ├── components/         # React components
│   │   │   ├── ui/             # Reusable UI components
│   │   │   ├── feedback/       # Alert, Modal components
│   │   │   └── navigation/    # Navigation components
│   │   ├── pages/              # Page components
│   │   │   ├── Admin/          # Manager-only pages
│   │   │   ├── login/          # Authentication pages
│   │   │   └── TimeOff/        # Time-off pages
│   │   ├── layouts/            # Layout components
│   │   ├── contexts/           # React contexts (LoadingContext)
│   │   ├── lib/                # Utilities (auth, axios, notifications)
│   │   └── styles/             # Global styles
│   └── package.json
├── backend/                     # FastAPI app
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/         # API route definitions
│   │   │   ├── controllers/    # Request handlers
│   │   │   └── dependencies/   # Auth dependencies
│   │   ├── db/
│   │   │   └── models/         # SQLAlchemy ORM models
│   │   ├── services/           # Business logic
│   │   │   ├── scheduling/    # MIP solver and optimization
│   │   │   └── optimization_data_services/  # Data preparation
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── tasks/              # Celery background tasks
│   │   ├── core/               # Configuration
│   │   └── server.py           # FastAPI app entry point
│   ├── requirements.txt
│   ├── seed_comprehensive_data.py  # Database seeding script
│   └── tests/                  # Test suite
└── docker-compose.yml           # Local dev stack
```

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
- **email-validator** - Email validation

### Optimization Engine

- **Python-MIP 1.15+** - Mixed Integer Programming library
- **CBC Solver** - Open-source MIP solver (bundled with Python-MIP)
- **NumPy 1.24+** - Numerical operations and matrix computations
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

## Key Features

### For Employees

- **Dashboard** - View upcoming shifts, weekly summary, and quick stats
- **My Preferences** - Set preferred days, times, and shift templates
- **Time-Off Requests** - Request vacation, sick leave, personal days with status tracking
- **My Schedule** - Calendar view of assigned shifts with weekly navigation
- **Activity Feed** - View recent system activities and changes
- **Settings** - User profile and notification preferences

### For Managers

- **Schedule Optimization** - Automatic shift assignment with MIP solver
- **Schedule Management** - Create, edit, and manage weekly schedules
- **Schedule Publishing** - Publish/unpublish schedules with employee notifications
- **Employee Management** - Add, edit, view employee profiles and roles
- **Shift Templates** - Define recurring shift patterns and role requirements
- **System Constraints** - Configure business rules (max hours, min rest, consecutive days, etc.)
- **Time-Off Approval** - Review and approve/reject employee requests
- **Optimization Config** - Tune solver weights and parameters
- **Dashboard Metrics** - View key statistics (employees, shifts, coverage, pending requests)
- **Export Schedules** - Export schedules to PDF or Excel/CSV formats
- **Activity Logs** - Monitor all system activities and changes
- **Roles Management** - Create and manage job roles and qualifications

### Optimization Features

- Multi-objective scheduling balancing 3+ criteria
- Fair workload distribution across employees
- Employee preference satisfaction
- Automatic constraint validation
- Infeasibility detection and reporting
- Solution quality metrics
- Background processing with progress tracking
- Configurable optimization weights and parameters

## Data Models

### Core Entities

- **User** - Employees with roles and manager status
- **Role** - Job positions (Waiter, Bartender, Chef, etc.)
- **UserRole** - Junction table linking users to their qualified roles
- **ShiftTemplate** - Predefined shift types with start/end times
- **ShiftRoleRequirements** - Role requirements per shift template
- **WeeklySchedule** - Container for a week's schedule with status (DRAFT, PUBLISHED)
- **PlannedShift** - Specific shift instances within a schedule
- **ShiftAssignment** - Employee-to-shift assignments with role

### Optimization Entities

- **TimeOffRequest** - Employee time-off requests with approval workflow
- **EmployeePreferences** - Shift preferences (preferred days, times, templates)
- **SystemConstraints** - System-wide work rules (max hours, min rest, consecutive days)
- **OptimizationConfig** - Optimization parameters and weights
- **SchedulingRun** - Optimization execution tracking and status
- **SchedulingSolution** - Proposed assignments from optimizer

### System Entities

- **ActivityLog** - Comprehensive audit trail of all system actions (CREATE, UPDATE, DELETE, PUBLISH, APPROVE, etc.)

## API Documentation

The API is fully documented using FastAPI's automatic OpenAPI documentation. Access it at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Endpoints Overview

#### Authentication

- `POST /users/login` - Authenticate user and get JWT token
- `GET /users/me` - Get current authenticated user
- `POST /users/register` - Register new user (if enabled)

#### Users

- `GET /users` - List all users (manager only)
- `GET /users/{id}` - Get user by ID
- `POST /users` - Create new user (manager only)
- `PUT /users/{id}` - Update user (manager only)
- `DELETE /users/{id}` - Delete user (manager only)

#### Roles

- `GET /roles` - List all roles
- `POST /roles` - Create new role (manager only)
- `PUT /roles/{id}` - Update role (manager only)
- `DELETE /roles/{id}` - Delete role (manager only)

#### Shift Templates

- `GET /shift-templates` - List all shift templates
- `POST /shift-templates` - Create shift template (manager only)
- `PUT /shift-templates/{id}` - Update shift template (manager only)
- `DELETE /shift-templates/{id}` - Delete shift template (manager only)

#### Weekly Schedules

- `GET /schedules` - List all schedules
- `GET /schedules/{id}` - Get schedule by ID
- `POST /schedules` - Create new schedule (manager only)
- `PUT /schedules/{id}` - Update schedule (manager only)
- `DELETE /schedules/{id}` - Delete schedule (manager only)

#### Planned Shifts

- `GET /planned-shifts` - List planned shifts (with filters)
- `POST /planned-shifts` - Create planned shift (manager only)
- `PUT /planned-shifts/{id}` - Update planned shift (manager only)
- `DELETE /planned-shifts/{id}` - Delete planned shift (manager only)

#### Shift Assignments

- `GET /shift-assignments` - List shift assignments (with filters)
- `POST /shift-assignments` - Create assignment (manager only)
- `PUT /shift-assignments/{id}` - Update assignment (manager only)
- `DELETE /shift-assignments/{id}` - Delete assignment (manager only)

#### Time-Off Requests

- `GET /time-off/requests` - List time-off requests (filtered by user for employees)
- `POST /time-off/requests` - Create time-off request
- `PUT /time-off/requests/{id}` - Update time-off request
- `POST /time-off/requests/{id}/process` - Approve/reject request (manager only)

#### System Constraints

- `GET /constraints` - Get system constraints
- `PUT /constraints` - Update system constraints (manager only)

#### Employee Preferences

- `GET /preferences` - Get current user's preferences
- `GET /preferences/{user_id}` - Get preferences for user (manager only)
- `PUT /preferences` - Update current user's preferences
- `PUT /preferences/{user_id}` - Update preferences for user (manager only)

#### Optimization

- `POST /scheduling/optimize/{schedule_id}` - Run optimization for a schedule
- `GET /scheduling/runs` - List optimization runs
- `GET /scheduling/runs/{id}` - Get optimization run details
- `POST /scheduling/runs/{id}/apply` - Apply optimization solution to schedule

#### Optimization Configuration

- `GET /optimization-configs` - List optimization configurations
- `POST /optimization-configs` - Create configuration (manager only)
- `PUT /optimization-configs/{id}` - Update configuration (manager only)
- `DELETE /optimization-configs/{id}` - Delete configuration (manager only)

#### Schedule Publishing

- `POST /schedules/{id}/publish` - Publish schedule (manager only)
- `POST /schedules/{id}/unpublish` - Unpublish schedule (manager only)

#### Activity Logs

- `GET /activities` - Get recent activity logs (with filters)

#### Metrics

- `GET /metrics` - Get dashboard metrics

#### Export

- `GET /export/schedule/{schedule_id}?format=pdf` - Export schedule as PDF
- `GET /export/schedule/{schedule_id}?format=excel` - Export schedule as Excel/CSV

## Optimization Engine

The system uses **Mixed Integer Programming (MIP)** to solve the shift assignment problem:

### MIP Model Components

1. **Decision Variables**

   - `x[i,j,r]` = 1 if employee `i` assigned to shift `j` in role `r`, else 0
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
   - Maximum consecutive working days
   - Minimum rest hours between shifts

4. **Soft Constraints** (Penalties)
   - Minimum shifts per week (with violation penalties)

### Solver Configuration

- **Timeout**: Configurable max runtime (default 300s)
- **MIP Gap**: Optimality tolerance (default 0.01 = 1%)
- **Solver**: CBC (Coin-or Branch and Cut)

### Key Services

1. **SchedulingService**: Orchestrates optimization, builds MIP model, runs solver
2. **ConstraintService**: Validates work rules and constraints
3. **OptimizationDataBuilder**: Extracts and prepares data for MIP model
4. **MipSchedulingSolver**: Builds and solves the optimization model
5. **SchedulingPersistence**: Database operations for solutions

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

**Background Processing**

- Celery tasks for async optimization runs
- Redis as message broker
- Flower for monitoring task execution

### Frontend Architecture

**Component-Based Design**

- Functional components with React hooks
- Shared UI components library (Button, Card, Skeleton, InputField, etc.)
- Layout components (MainLayout, PageLayout)
- Page components with data fetching
- Error boundary for error handling

**State Management**

- React Context for global state (LoadingContext)
- Local component state with useState
- Auth state persisted in localStorage

**Routing Strategy**

- Protected routes with authentication checks
- Admin-only routes with role verification
- Lazy loading with React Router
- Route suspense for loading states

**UI/UX Design**

- Blue gradient theme with professional appearance
- Sidebar navigation with icons
- Weekly calendar grid for schedule visualization
- Quick stats dashboard with metrics
- Toast notifications for feedback
- Activity feed component for system updates

## Environment Configuration

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scheduler_db

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=3

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0
```

### Frontend Environment Variables

Create a `.env.local` file in the `frontend/` directory (optional):

```env
VITE_API_URL=http://localhost:8000
```

## Testing

The backend includes a comprehensive test suite using pytest:

```bash
cd backend
source venv/bin/activate
pytest
```

**Test Files:**

- `test_api_optimization_config.py` - Optimization config API tests
- `test_apply_solution.py` - Solution application tests
- `test_constraint_service.py` - Constraint validation tests
- `test_create_config.py` - Config creation tests
- `test_data_builder.py` - Optimization data builder tests
- `test_mip_solver.py` - MIP solver tests
- `test_optimization_tables.py` - Optimization model tests
- `test_scheduling_service.py` - Scheduling service tests
- `test_schemas.py` - Pydantic schema tests

## Seeding Data

The project includes a comprehensive seed script for populating the database with test data:

```bash
cd backend
source venv/bin/activate
python seed_comprehensive_data.py
```

**Options:**

- Default mode: Small realistic dataset for basic functionality
- `--big` flag: Large stress-test dataset (~100 employees, high coverage, preferences, time off)

The seed script creates:

- Users (employees and managers)
- Roles and user-role assignments
- Shift templates with role requirements
- System constraints
- Optimization configurations
- Employee preferences
- Time-off requests
- Weekly schedules with planned shifts

## Development Guide

### Running Tests

```bash
cd backend
source venv/bin/activate
pytest tests/
```

### Code Style

- **Backend**: Follow PEP 8 Python style guide
- **Frontend**: ESLint configuration included

### Database Migrations

The project uses SQLAlchemy with automatic table creation. Tables are created automatically when the server starts.

### Adding New Features

1. **Backend**: Add models → schemas → controllers → routes
2. **Frontend**: Add API client functions → components → pages → routes
3. Update this README with new features

### Debugging

- **Backend**: Use FastAPI's automatic docs at `/docs` for API testing
- **Frontend**: React DevTools and browser console
- **Celery**: Monitor tasks via Flower at http://localhost:5555
- **Database**: Connect using your PostgreSQL client

## Useful Links

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Python-MIP Documentation**: https://python-mip.readthedocs.io/
- **React Documentation**: https://react.dev/
- **TailwindCSS Documentation**: https://tailwindcss.com/
- **Celery Documentation**: https://docs.celeryq.dev/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/

---

**License**: [Add your license here]  
**Contributors**: [Add contributors here]
