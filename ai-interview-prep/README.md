# 🎯 AI Interview Preparation Companion

A hackathon scaffold for an AI-powered mock interview practice platform.
Every feature area has a clearly marked stub so all 8 team members can
build in parallel from day one against a working (if fake) API.

---

## Folder ownership

| Folder | Owner pair | Responsibility |
|---|---|---|
| `backend/app/routers/` + `schemas/` | **Backend Pair** | FastAPI endpoints, Pydantic models, DB queries |
| `backend/app/services/scoring.py` | **ML Pair (Scoring)** | Embedding similarity + LLM judge + concept match |
| `backend/app/services/question_generation.py` + `vector_store.py` | **ML Pair (Generation)** | LLM question gen + FAISS/Chroma retrieval |
| `frontend/src/` | **Frontend Pair** | React pages, Tailwind styling, API integration |
| `ml/` | **Both ML Pairs** | Data ingestion, embeddings, offline evaluation |
| `backend/alembic/` | **Backend Pair** | DB migrations as schema evolves |
| `.github/workflows/` | **Everyone** | Keep CI green |

---

## Quick start

### Option A — Backend only (venv + local/hosted Postgres)

```bash
cd ai-interview-prep/backend

# 1. Create and activate a virtual environment
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL to your Postgres connection string

# 4. Run migrations
alembic upgrade head

# 5. Start the API server
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs  
Health check: http://localhost:8000/health

---

### Option B — Frontend only (npm)

```bash
cd ai-interview-prep/frontend

npm install
cp .env.example .env   # VITE_API_URL defaults to /api (proxied to :8000)
npm run dev
```

Frontend available at: http://localhost:5173

> **Note:** The Vite dev server proxies `/api/*` → `http://localhost:8000/*` automatically,
> so you don't need to set CORS manually during local dev.

---

## Deployment

### Backend (Render / Railway)
- **Environment**: Python 3 (pinned via `backend/runtime.txt` to `python-3.11.x`)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**: Set `DATABASE_URL`, `JWT_SECRET`, etc. in service settings.

### Frontend (Vercel)
- **Build Settings**: Auto-detected Vite build (framework preset: Vite). No custom config needed.
- **Environment Variables**: Set `VITE_API_URL` to your deployed backend URL.

---

## Running tests

```bash
cd ai-interview-prep/backend
pytest tests/ -v
```

## Running lint

```bash
# Backend
ruff check backend/app/ backend/tests/

# Frontend
cd frontend && npm run lint
```

---

## API Overview (all return mock data)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness probe |
| `POST` | `/auth/signup` | Register (stub — returns fake JWT) |
| `POST` | `/auth/login` | Login (stub — returns fake JWT) |
| `GET` | `/questions` | List questions (`?role=&topic=`) |
| `POST` | `/sessions` | Create a mock session |
| `POST` | `/sessions/{id}/answers` | Submit answer → get score |
| `GET` | `/dashboard/{user_id}` | Topic progress |
| `GET` | `/study-plan/{user_id}` | Prioritised study plan |

---

## Database schema

10 tables: `users`, `job_roles`, `topics`, `questions`, `mock_sessions`,
`session_questions`, `answers`, `scores`, `topic_progress`, `study_plan`.

See `backend/alembic/versions/0001_initial.py` for the full DDL.

---

## Environment variables

### Backend (`backend/.env`)
| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET` | Long random string for JWT signing |
| `JWT_ALGORITHM` | Default: `HS256` |
| `JWT_EXPIRE_MINUTES` | Default: `1440` (24 h) |
| `CORS_ORIGINS` | JSON array of allowed origins |

### Frontend (`frontend/.env`)
| Variable | Description |
|---|---|
| `VITE_API_URL` | Base URL for the backend API |
