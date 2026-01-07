# Smart Scheduling

A full-stack automated shift scheduling system that uses **Mixed Integer Programming (MIP)** to optimally assign employees to shifts based on availability, time-off requests, work constraints, and fairness objectives.

## 🚀 Features

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

When the backend is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc




## 🔐 Authentication

The system uses JWT authentication:

1. User calls `POST /users/login` with email/password
2. Backend returns `access_token` (JWT) and user data
3. Frontend stores token in `localStorage`
4. All subsequent requests include `Authorization: Bearer <token>` header

**Role-Based Access:**

- **Authenticated Users**: View basic data, manage own time-off
- **Managers**: Create/edit users, assign shifts, approve time-off, manage constraints


## 📝 Environment Variables

### Backend (`backend/.env`)

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scheduler_db
JWT_SECRET_KEY=change-me-in-dev
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=3
```

### Frontend (`frontend/.env.local`)

```env
VITE_API_URL=http://localhost:8000
```

---
