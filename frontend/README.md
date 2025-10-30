# Smart Scheduling — Frontend

React + Vite app for the Smart Scheduling system.

## Tech

- React 19, Vite 7
- TailwindCSS 4
- Axios for API calls

## Environment

- `VITE_API_URL` — backend base URL (default: `http://localhost:8000`)

Create a local env file if needed:

```bash
echo 'VITE_API_URL=http://localhost:8000' > .env.local
```

## Scripts

```bash
npm install          # install deps
npm run dev          # start dev server (http://localhost:5173)
npm run build        # production build to dist/
npm run preview      # preview the built app
```

## Running with Docker

This service is included in the root `docker-compose.yml`.

```bash
# From repo root
docker compose up --build
```

Frontend will be available at http://localhost:5173
