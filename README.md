# Smart Scheduling

A full-stack app for managing users, roles, and scheduling workflows.

- Frontend: React + Vite + TailwindCSS
- Backend: FastAPI + SQLAlchemy + JWT
- Database: PostgreSQL
- Dev/Run: Docker Compose or run services locally

## Quick Start (Docker)

Prerequisites: Docker and Docker Compose installed.

```bash
# From the repo root
docker compose up --build
```

Services:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000 (docs at /docs)
- Postgres: localhost:5432 (user: postgres, password: postgres, db: scheduler_db)

Environment:

- Backend reads `.env` in `backend/` (see `backend/JWT_SETUP.md` for variables). Defaults work with Docker.
- Frontend can set `VITE_API_URL` (defaults to `http://localhost:8000`).

## Local Development (without Docker)

### 1) Database

- Install PostgreSQL and create a database named `scheduler_db`.
- Optional local connection string example: `postgresql://postgres:postgres@localhost:5432/scheduler_db`.

### 2) Backend (FastAPI)

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

### 3) Frontend (React)

```bash
cd frontend
npm install
# Optional: point to API if different than default
echo 'VITE_API_URL=http://localhost:8000' > .env.local
npm run dev
```

- App: http://localhost:5173

## Project Structure

- `frontend/` — React app (Vite)
- `backend/` — FastAPI app, SQLAlchemy models, JWT auth
- `docker-compose.yml` — Local dev stack for DB, backend, frontend

## Useful Links

- Backend JWT details: `backend/JWT_SETUP.md`
- API docs when running: `http://localhost:8000/docs`
