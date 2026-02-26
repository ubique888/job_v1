# Job Autopilot — Getting Started

## Quick Start with Docker

```bash
docker compose up --build
```

Open http://localhost:3080 — that's it. The database persists in a Docker volume.

To stop: `docker compose down`
To reset the database: `docker compose down -v`

---

## Local Development (without Docker)

### Prerequisites

- Python 3.11+
- Node.js 18+ or Bun

### 1. Backend Setup

```bash
cd backend

# Create virtual environment (first time only)
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --port 8000
```

The API is now at http://localhost:8000.
Health check: http://localhost:8000/health
API docs: http://localhost:8000/docs

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
bun install        # or: npm install

# Start dev server
bun dev            # or: npm run dev
```

The dashboard is now at http://localhost:5173.

### 3. Using the App

1. Open http://localhost:5173
2. Click **Manage Sources** to add company job boards
3. Add a seed:
   - Provider: `Greenhouse` or `Lever`
   - Company: e.g. `Cloudflare`
   - URL: e.g. `https://boards.greenhouse.io/cloudflare`
4. Select your **Track** (Backend, Frontend, etc.) and **Posted Within** window
5. Click **Run Search** — real jobs appear with apply links
6. Click **Apply** to open the application page, **Copy** the link, or **+ Queue** to track it
7. Go to the **Queue** tab to manage your application pipeline

### Example Seeds

| Provider   | Company    | Board URL                                  |
|------------|------------|--------------------------------------------|
| Greenhouse | Cloudflare | https://boards.greenhouse.io/cloudflare    |
| Greenhouse | Stripe     | https://boards.greenhouse.io/stripe        |
| Greenhouse | Figma      | https://boards.greenhouse.io/figma         |
| Lever      | Netflix    | https://jobs.lever.co/netflix              |
| Lever      | Notion     | https://jobs.lever.co/notion               |

### 4. Running Tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

### 5. Production Build (Frontend)

```bash
cd frontend
bun run build      # or: npm run build
# Output in frontend/dist/
```

## Project Structure

```
backend/
  app/
    main.py              # FastAPI app entry point
    database.py          # SQLite schema + connection
    dedupe.py            # Normalization + dedup hashing
    search_engine.py     # Orchestrates providers, stores jobs
    models/schemas.py    # Pydantic request/response models
    providers/
      base.py            # IJobSourceProvider interface
      greenhouse.py      # Greenhouse boards API provider
      lever.py           # Lever postings API provider
    routers/
      profile.py         # GET/PUT /v1/user/profile
      seeds.py           # GET/POST/DELETE /v1/seeds
      search.py          # POST/GET /v1/search/runs
      queue.py           # GET/POST/PATCH /v1/queue/items
  tests/
    fixtures/            # Greenhouse + Lever JSON fixtures
    test_providers.py    # Provider parsing tests
    test_dedupe.py       # Normalization + hash tests
    test_api.py          # API contract tests
  data/
    jobs.db              # SQLite database (auto-created)

frontend/
  src/
    App.tsx              # Router + nav
    App.css              # Global styles
    lib/
      api.ts             # Backend API client
      types.ts           # TypeScript types
    pages/
      SearchPage.tsx     # Search + results + detail drawer
      QueuePage.tsx      # Application tracking queue
```
