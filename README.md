# Job Search Autopilot

A full-stack job discovery dashboard that aggregates software engineering roles from public ATS (Applicant Tracking System) boards. Searches Greenhouse and Lever APIs to surface real, verified job listings — no scraping, no auto-apply.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-WAL-003B57?logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development](#local-development)
  - [Docker](#docker)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [How It Works](#how-it-works)
  - [Providers](#providers)
  - [Track Matching](#track-matching)
  - [Deduplication](#deduplication)
- [Testing](#testing)
- [Configuration](#configuration)
- [License](#license)

---

## Overview

Most job boards are noisy. This tool takes a different approach:

1. **You provide seeds** — company board URLs from Greenhouse or Lever (or pick from 33 curated presets).
2. **You pick a track** — Backend, Frontend, Fullstack, DevOps, Data, ML, AI Agent, or Consulting.
3. **The engine searches** — fetches listings via public APIs, filters by track keywords, deduplicates, and flags missing data.
4. **You review and queue** — browse results, inspect job descriptions, and add promising roles to your application queue.

No credentials required. No auto-apply. Every listing links back to its original source.

---

## Architecture

```
┌─────────────┐     HTTP      ┌─────────────────┐     Public APIs     ┌──────────────┐
│   React UI  │ ───────────── │  FastAPI Server  │ ─────────────────── │  Greenhouse  │
│  (Vite/TS)  │   localhost   │   (Python 3.12)  │                     │    Lever     │
└─────────────┘    :5173      └────────┬─────────┘                     └──────────────┘
                                       │
                                       │ SQLite (WAL)
                                       │
                              ┌────────▼─────────┐
                              │    jobs.db        │
                              │  7 tables         │
                              │  dedup index      │
                              └──────────────────┘
```

**Data flow:** Frontend → FastAPI → Provider APIs → Parse & Filter → Dedupe → SQLite → Response

---

## Features

- **Multi-provider search** — Greenhouse and Lever public board APIs
- **Track-based filtering** — keyword matching across 8 role categories
- **Smart deduplication** — normalized hashing prevents duplicate entries across searches
- **33 preset companies** — curated list with verified working board URLs across Big Tech, SaaS, Cybersecurity, Fintech, Consulting, and more
- **Sortable results** — click column headers to sort by company, role, location, or post date
- **Job detail drawer** — view full job descriptions, evidence flags, and apply links
- **Application queue** — bookmark, track, and manage jobs through your pipeline (bookmarked → in queue → applied → rejected/archived)
- **Evidence tracking** — missing apply URLs, job descriptions, or post dates are flagged, not guessed
- **Time filtering** — filter by posted within 24h, 48h, 7d, or 30d
- **Docker-ready** — single `docker compose up` for production deployment

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.12, FastAPI | REST API server |
| **Database** | SQLite (WAL mode) | Persistent storage with concurrent reads |
| **HTTP Client** | httpx | Async requests to provider APIs |
| **HTML Parsing** | selectolax | Extract job description text |
| **Frontend** | React 19, TypeScript 5.9 | Single-page application |
| **Build Tool** | Vite 7.3 | Dev server and production builds |
| **Routing** | React Router 7 | Client-side navigation |
| **Deployment** | Docker, nginx | Containerized production setup |
| **Testing** | pytest, pytest-asyncio | Backend unit and integration tests |

---

## Getting Started

### Prerequisites

- **Python** 3.12+
- **Node.js** 18+ (or Bun)
- **Docker** (optional, for containerized deployment)

### Local Development

**1. Clone the repository**

```bash
git clone git@github.com:ubique888/job_v1.git
cd job_v1
```

**2. Set up the backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**3. Start the backend server**

```bash
uvicorn app.main:app --reload --port 8000
```

The API is now running at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

**4. Set up the frontend** (in a new terminal)

```bash
cd frontend
npm install
npm run dev
```

The UI is now running at `http://localhost:5173`.

### Docker

```bash
docker compose up --build
```

- Frontend: `http://localhost:3080`
- Backend API: `http://localhost:8000`
- Database persisted via Docker volume `db-data`

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point, CORS, router registration
│   │   ├── database.py          # SQLite connection, schema initialization (7 tables)
│   │   ├── search_engine.py     # Orchestrates provider fetching, filtering, dedup, storage
│   │   ├── track_matcher.py     # Keyword-based job-to-track classification
│   │   ├── dedupe.py            # Normalization and SHA256 hash deduplication
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic models, enums (Track, PostedWithin, Provider)
│   │   ├── routers/
│   │   │   ├── profile.py       # GET/PUT /v1/user/profile
│   │   │   ├── seeds.py         # CRUD /v1/seeds
│   │   │   ├── search.py        # POST /v1/search/runs, GET /v1/search/runs/{id}
│   │   │   └── queue.py         # CRUD /v1/queue/items
│   │   └── providers/
│   │       ├── base.py          # Abstract provider interface (JobCard dataclass)
│   │       ├── greenhouse.py    # Greenhouse boards API integration
│   │       └── lever.py         # Lever postings API integration
│   ├── tests/
│   │   ├── test_api.py          # API contract tests (health, profile, seeds, search, queue)
│   │   ├── test_providers.py    # Provider parsing tests with fixture data
│   │   ├── test_dedupe.py       # Normalization and hash tests
│   │   └── fixtures/            # Mock API response JSON files
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx             # React entry, router setup
│   │   ├── App.tsx              # Layout shell, navigation
│   │   ├── App.css              # Global styles (dark theme)
│   │   ├── lib/
│   │   │   ├── api.ts           # Typed fetch wrapper for all API calls
│   │   │   ├── types.ts         # TypeScript interfaces mirroring backend schemas
│   │   │   └── defaultSeeds.ts  # 33 curated company presets with verified board URLs
│   │   └── pages/
│   │       ├── SearchPage.tsx   # Job discovery: controls, seeds, presets, results table
│   │       └── QueuePage.tsx    # Application queue: status tracking, notes, filtering
│   ├── vite.config.ts
│   ├── nginx.conf               # Production reverse proxy config
│   └── Dockerfile
│
└── docker-compose.yml
```

---

## API Reference

### Seeds

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/seeds` | List all company board seeds |
| `POST` | `/v1/seeds` | Add a seed `{ provider, company, board_url }` |
| `DELETE` | `/v1/seeds/{id}` | Remove a seed |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/search/runs` | Execute a search `{ track, posted_within, provider_enabled, limit_per_provider }` |
| `GET` | `/v1/search/runs/{id}` | Get search results with jobs, stats, and evidence |

### Queue

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/queue/items` | List all queued jobs with their status |
| `POST` | `/v1/queue/items` | Add job to queue `{ job_id, status?, notes? }` |
| `PATCH` | `/v1/queue/items/{id}` | Update status or notes `{ status?, notes? }` |

### Other

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/v1/user/profile` | Get user preferences |
| `PUT` | `/v1/user/profile` | Update user preferences |

Full interactive documentation available at `/docs` (Swagger UI) when the backend is running.

---

## How It Works

### Providers

The system fetches jobs from two public ATS APIs:

**Greenhouse** — `https://boards-api.greenhouse.io/v1/boards/{token}/jobs`
- Returns structured JSON with title, location, content (HTML job description), and updated_at
- Apply URLs constructed as `https://boards.greenhouse.io/{token}/jobs/{id}#app`

**Lever** — `https://api.lever.co/v0/postings/{slug}`
- Returns structured JSON with text (title), categories.location, applyUrl, createdAt, and description lists
- Job descriptions assembled from list headers and content blocks

Both providers return a list of `JobCard` objects with normalized fields. Missing data (no apply URL, no JD text, no post date) is tracked as evidence rather than silently dropped.

### Track Matching

Jobs are classified into tracks using keyword matching against the job title and description text:

| Track | Example Keywords |
|-------|-----------------|
| **Backend** | backend, api developer, python engineer, microservices, distributed systems |
| **Frontend** | frontend, react, vue, angular, ui engineer, web developer |
| **Fullstack** | fullstack, full-stack, full stack |
| **DevOps** | devops, infrastructure, sre, platform engineer, kubernetes, terraform, ci/cd |
| **Data** | data engineer, data analyst, analytics engineer, etl, snowflake, dbt |
| **ML** | machine learning, deep learning, nlp, computer vision, pytorch, tensorflow |
| **AI Agent** | ai agent, agentic, llm engineer, langchain, prompt engineer, generative ai, rag |
| **Consulting** | consultant, solutions architect, solutions engineer, technical account manager, presales |

Matching is substring-based on lowercased text. A job only needs to match one keyword to qualify.

### Deduplication

Prevents storing the same job multiple times across search runs:

1. **Normalize** — lowercase, strip punctuation, collapse whitespace, expand abbreviations (NYC → new york city, Sr → senior)
2. **Hash** — SHA256 of `{company}|{title}|{location}|{track}` → 32-char hex prefix
3. **Check** — if hash exists in `job_dedupe_index`, skip; otherwise store

The track is included in the hash so the same job can exist under different tracks if it matches multiple categories.

---

## Testing

```bash
cd backend
source .venv/bin/activate
pytest -v
```

**Test coverage:**

| Suite | Tests | What It Covers |
|-------|-------|---------------|
| `test_api.py` | API endpoints | Health, profile CRUD, seeds CRUD, search validation, queue operations |
| `test_providers.py` | Provider parsing | Greenhouse/Lever JSON parsing, field extraction, evidence flags, error handling |
| `test_dedupe.py` | Deduplication | Text normalization, abbreviation expansion, hash consistency, collision avoidance |

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_PATH` | `data/jobs.db` | SQLite database file path |
| `VITE_API_URL` | `http://localhost:8000` | Backend API URL (frontend) |

---

## License

This project is for personal use.
