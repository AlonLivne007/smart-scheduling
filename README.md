<div align="center">

# 🎯 Smart Scheduling

### An Intelligent Employee Scheduling System Powered by Mixed Integer Programming (MIP)

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

**Automatically generates optimal shift assignments** by balancing employee preferences, availability, fairness, and business constraints using advanced optimization algorithms.

---

</div>

## 🎥 Watch the Demo

<div align="center">

### 📺 **Application Walkthrough & Demo Video**

[![Watch the video](https://img.youtube.com/vi/N3eFIohtxmY/maxresdefault.jpg)](https://www.youtube.com/watch?v=N3eFIohtxmY)

**[▶️ Click to watch on YouTube](https://www.youtube.com/watch?v=N3eFIohtxmY)**

This comprehensive demo showcases:
- 🏗️ System architecture and core features
- ⚙️ Optimization workflow and MIP solver
- 🎨 User interface and navigation
- 📅 Schedule management capabilities
- 🔧 Optimization configuration and execution
- 📊 Real-time metrics and analytics

---

</div>

## 🎯 What Problem Does This Solve?

### The Challenge

- **📋 Manual Scheduling is Complex**: Creating weekly schedules with dozens of employees, shifts, and roles requires hours of manual work
- **⚖️ Conflicts & Unfairness**: Difficult to balance employee preferences, availability, role coverage, and workload fairness
- **🔒 Complex Constraints**: Minimum rest hours, maximum weekly hours, shift overlaps, approved time-off requests

### The Solution

**Smart Scheduling** uses **Mixed Integer Programming (MIP)** to automatically generate optimal shift assignments in minutes instead of hours, ensuring:

- ✅ **Full Coverage**: Every shift-role combination is filled exactly once
- ⚖️ **Fair Distribution**: Balanced workload across all employees
- 😊 **Employee Satisfaction**: Maximizes preference satisfaction scores
- 🔒 **Constraint Compliance**: Enforces all business rules automatically
- 🎯 **Optimal Solutions**: MIP gap < 1% for high-quality results

---

## 🚀 Quick Start

### 🐳 Docker (Recommended)

The easiest way to get started:

```bash
# Clone the repository
git clone <repository-url>
cd smart-scheduling

# Start all services
docker compose up --build
```

**Services will be available at:**

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | React application |
| **Backend API** | http://localhost:8000 | FastAPI REST API |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Flower** | http://localhost:5555 | Celery task monitor |
| **PostgreSQL** | localhost:5432 | Database |
| **Redis** | localhost:6379 | Task queue |

### 💻 Local Development

<details>
<summary><b>Click to expand local setup instructions</b></summary>

#### 1️⃣ Database Setup

Install PostgreSQL 14 and create a database:

```bash
createdb scheduler_db
```

Connection string: `postgresql://postgres:postgres@localhost:5432/scheduler_db`

#### 2️⃣ Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cat > .env << 'EOF'
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scheduler_db
JWT_SECRET_KEY=change-me-in-dev
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=3
REDIS_URL=redis://localhost:6379/0
EOF

# Run API server
uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```

#### 3️⃣ Frontend Setup

```bash
cd frontend
npm install

# Optional: Create .env.local
echo 'VITE_API_URL=http://localhost:8000' > .env.local

# Run dev server
npm run dev
```

#### 4️⃣ Celery Worker (Background Tasks)

```bash
cd backend
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info
```

#### 5️⃣ Flower (Task Monitor)

```bash
cd backend
source venv/bin/activate
celery -A app.celery_app flower --port=5555
```

</details>

---

## 🏗️ Architecture Overview

<div align="center">

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Frontend (React 19 + Vite + TailwindCSS)             │  │
│  │  Port: 5173                                            │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                    HTTP/REST API
                    JWT Auth
                            │
┌─────────────────────────────────────────────────────────────┐
│                 APPLICATION LAYER                            │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Backend API (FastAPI)                                  │  │
│  │  Port: 8000                                             │  │
│  │  ├── Controllers (REST API)                             │  │
│  │  ├── Services (Business Logic)                          │  │
│  │  └── Models (SQLAlchemy ORM)                            │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│              DATA & PROCESSING LAYER                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ PostgreSQL   │  │    Redis     │  │  Celery Worker   │  │
│  │ Port: 5432   │  │  Port: 6379  │  │  (Background)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Optimization Engine (MIP Solver)              │  │
│  │  ├── Data Builder (Extract & Prepare)                 │  │
│  │  ├── MIP Solver (Python-MIP + CBC)                    │  │
│  │  └── Validator (Constraint Checking)                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

</div>

### 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 19, Vite 7, TailwindCSS 4 | Modern UI framework with fast build tool |
| **Backend** | FastAPI, SQLAlchemy | High-performance Python web framework |
| **Database** | PostgreSQL 14 | Production-grade relational database |
| **Optimization** | Python-MIP 1.15+, CBC Solver | Mixed Integer Programming solver |
| **Task Queue** | Celery 5.3+, Redis 7 | Asynchronous background processing |
| **Monitoring** | Flower 2.0+ | Real-time Celery task monitoring |
| **Deployment** | Docker, Docker Compose | Containerization and orchestration |

---

## ✨ Key Features

### 👤 For Employees

- 📊 **Dashboard** - View upcoming shifts, weekly summary, and quick statistics
- ⚙️ **My Preferences** - Set preferred days, times, and shift templates
- 🏖️ **Time-Off Requests** - Request vacation, sick leave, personal days with status tracking
- 📅 **My Schedule** - Calendar view of assigned shifts with weekly navigation
- 📝 **Activity Feed** - View recent system activities and changes
- ⚙️ **Settings** - User profile and notification preferences

### 👔 For Managers

- 🎯 **Schedule Optimization** - Automatic shift assignment with MIP solver
- 📋 **Schedule Management** - Create, edit, and manage weekly schedules
- 📢 **Schedule Publishing** - Publish/unpublish schedules with employee notifications
- 👥 **Employee Management** - Add, edit, view employee profiles and roles
- 🔄 **Shift Templates** - Define recurring shift patterns and role requirements
- 🔒 **System Constraints** - Configure business rules (max hours, min rest, consecutive days, etc.)
- ✅ **Time-Off Approval** - Review and approve/reject employee requests
- ⚙️ **Optimization Config** - Tune solver weights and parameters
- 📊 **Dashboard Metrics** - View key statistics (employees, shifts, coverage, pending requests)
- 📄 **Export Schedules** - Export schedules to PDF or Excel/CSV formats
- 📝 **Activity Logs** - Monitor all system activities and changes
- 🎭 **Roles Management** - Create and manage job roles and qualifications

### ⚡ Optimization Features

- 🎯 Multi-objective scheduling balancing 3+ criteria
- ⚖️ Fair workload distribution across employees
- 😊 Employee preference satisfaction
- ✅ Automatic constraint validation
- 🚫 Infeasibility detection and reporting
- 📊 Solution quality metrics
- 🔄 Background processing with progress tracking
- ⚙️ Configurable optimization weights and parameters

---

## 🧮 Optimization Engine

The system uses **Mixed Integer Programming (MIP)** to solve the shift assignment problem:

### 📐 MIP Model Components

#### 1. Decision Variables
- `x[i,j,r]` = 1 if employee `i` assigned to shift `j` in role `r`, else 0
- Binary variables for discrete yes/no decisions

#### 2. Objective Function (Maximize)
- **Component 1**: Preference satisfaction (employee preferences)
- **Component 2**: Coverage (fill all required shifts)
- **Component 3**: Fairness (balanced workload distribution)
- **Component 4**: Soft penalty minimization
- Weighted combination with configurable weights

#### 3. Hard Constraints (Must Satisfy)
- ✅ Coverage: Each shift-role filled exactly once
- 🚫 No time-off conflicts
- 🎭 Role qualifications required
- ⏰ No overlapping shift assignments
- ⏱️ Maximum hours per week
- 📊 Maximum shifts per week
- 📅 Maximum consecutive working days
- 😴 Minimum rest hours between shifts

#### 4. Soft Constraints (Penalties)
- 📉 Minimum shifts per week (with violation penalties)

### ⚙️ Solver Configuration

- **Timeout**: Configurable max runtime (default 300s)
- **MIP Gap**: Optimality tolerance (default 0.01 = 1%)
- **Solver**: CBC (Coin-or Branch and Cut)

### 🔧 Key Services

1. **SchedulingService** - Orchestrates optimization, builds MIP model, runs solver
2. **ConstraintService** - Validates work rules and constraints
3. **OptimizationDataBuilder** - Extracts and prepares data for MIP model
4. **MipSchedulingSolver** - Builds and solves the optimization model
5. **SchedulingPersistence** - Database operations for solutions

---

## 📊 Data Models

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

---

## 📚 API Documentation

The API is fully documented using FastAPI's automatic OpenAPI documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 🔌 Main API Endpoints

| Category | Endpoints | Description |
|----------|-----------|-------------|
| **Authentication** | `POST /users/login`, `GET /users/me` | User authentication |
| **Users** | `GET /users`, `POST /users`, `PUT /users/{id}` | User management |
| **Roles** | `GET /roles`, `POST /roles`, `PUT /roles/{id}` | Role management |
| **Schedules** | `GET /schedules`, `POST /schedules`, `PUT /schedules/{id}` | Schedule management |
| **Optimization** | `POST /scheduling/optimize/{schedule_id}`, `GET /scheduling/runs` | Run optimization |
| **Time-Off** | `GET /time-off/requests`, `POST /time-off/requests` | Time-off management |
| **Export** | `GET /export/schedule/{schedule_id}?format=pdf` | Export schedules |

For complete API documentation, visit the Swagger UI at http://localhost:8000/docs

---

## 🗂️ Project Structure

```
smart-scheduling/
├── frontend/                    # React app (Vite)
│   ├── src/
│   │   ├── api/                # API client functions
│   │   ├── components/         # React components
│   │   │   ├── ui/             # Reusable UI components
│   │   │   ├── feedback/       # Alert, Modal components
│   │   │   └── navigation/     # Navigation components
│   │   ├── pages/              # Page components
│   │   │   ├── Admin/          # Manager-only pages
│   │   │   ├── login/          # Authentication pages
│   │   │   └── TimeOff/        # Time-off pages
│   │   ├── layouts/            # Layout components
│   │   ├── contexts/           # React contexts
│   │   ├── lib/                # Utilities
│   │   └── styles/             # Global styles
│   └── package.json
├── backend/                    # FastAPI app
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/         # API route definitions
│   │   │   ├── controllers/    # Request handlers
│   │   │   └── dependencies/   # Auth dependencies
│   │   ├── data/
│   │   │   └── models/         # SQLAlchemy ORM models
│   │   ├── services/           # Business logic
│   │   │   ├── scheduling/     # MIP solver and optimization
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

---

## 🌱 Seeding Data

The project includes a comprehensive seed script for populating the database with test data:

```bash
cd backend
source venv/bin/activate
python seed_comprehensive_data.py
```

**Options:**
- **Default mode**: Small realistic dataset for basic functionality
- **`--big` flag**: Large stress-test dataset (~100 employees, high coverage, preferences, time off)

The seed script creates:
- 👥 Users (employees and managers)
- 🎭 Roles and user-role assignments
- 🔄 Shift templates with role requirements
- 🔒 System constraints
- ⚙️ Optimization configurations
- 😊 Employee preferences
- 🏖️ Time-off requests
- 📅 Weekly schedules with planned shifts

---

## 🔧 Environment Configuration

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

---

## 🏛️ Design Patterns & Architecture

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

**UI/UX Design**
- Blue gradient theme with professional appearance
- Sidebar navigation with icons
- Weekly calendar grid for schedule visualization
- Quick stats dashboard with metrics
- Toast notifications for feedback
- Activity feed component for system updates

---

## 📖 Useful Links

### 📚 Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Python-MIP Documentation](https://python-mip.readthedocs.io/)
- [React Documentation](https://react.dev/)
- [TailwindCSS Documentation](https://tailwindcss.com/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### 🎥 Demo & Tutorials
- [Application Demo Video](https://www.youtube.com/watch?v=N3eFIohtxmY)

---

<div align="center">

**Made with ❤️ using Mixed Integer Programming**

[⬆ Back to Top](#-smart-scheduling)

</div>
