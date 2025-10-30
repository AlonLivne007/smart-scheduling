# Smart Scheduling — Backend (FastAPI)

FastAPI service providing user, role, and scheduling APIs.

## Tech

- FastAPI, Uvicorn
- SQLAlchemy ORM
- PostgreSQL
- JWT auth (`python-jose`)

## Environment

Create `backend/.env` (defaults work in Docker):

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/scheduler_db
JWT_SECRET_KEY=change-me-in-dev
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=3
```

See `JWT_SETUP.md` for details.

## Run (local)

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs

By default, the app will attempt to connect to Postgres at `DATABASE_URL`. Ensure your local DB is running (e.g., `postgresql://postgres:postgres@localhost:5432/scheduler_db`) if not using Docker.

## Run (Docker)

This service is included in the root `docker-compose.yml`.

```bash
# From repo root
docker compose up --build
```

Backend will be available at http://localhost:8000
