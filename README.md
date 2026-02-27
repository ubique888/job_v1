# Job Search Autopilot

A full-stack job discovery dashboard that aggregates software engineering roles from public ATS (Applicant Tracking System) boards. Searches Greenhouse and Lever APIs to surface real, verified job listings — no scraping, no auto-apply.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-WAL-003B57?logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-llama3.2:3b-000000?logo=ollama&logoColor=white)

---

## AI-Powered JD Summarization

Summarize job descriptions into structured key points using a local LLM — no API keys, no cloud costs.

**How it works:** Click the **Summarize** button on any expanded job listing. The app sends the raw JD text to a locally running Ollama instance with `llama3.2:3b`, which returns a structured breakdown:

- **Responsibilities** — 3-5 bullet points of key duties
- **Required Skills** — must-have technologies, tools, languages
- **Nice-to-Have** — preferred/bonus skills
- **Experience Level** — inferred seniority and years
- **Compensation** — salary range if mentioned
- **Notable** — red flags, unusual requirements, or standout perks

Summaries are cached in SQLite so each job is only processed once. Subsequent views load instantly.

### Setup

**With Docker (automatic):**

Ollama is included as a Docker Compose service. Run `docker compose up` and the model downloads automatically on first boot. No extra steps.

**Without Docker (local):**

1. Install Ollama from [ollama.com](https://ollama.com)
2. Pull the model:
   ```bash
   ollama pull llama3.2:3b
   ```
3. Keep Ollama running in the background (it starts automatically after install)
4. Start the app normally — the Summarize button appears when Ollama is detected

If Ollama is not running, the app works normally without summarization. The Summarize button shows an error message and the raw JD text remains visible.

---

## Discord Webhook Notifications

Get notified in Discord when new jobs match your alert subscriptions.

### Setup

1. In Discord, go to your server's **Settings > Integrations > Webhooks**
2. Click **New Webhook**, name it (e.g., "Job Alerts"), choose a channel, and copy the webhook URL
3. In the app, go to the **Alerts** page
4. Paste the webhook URL in the **Discord Webhook** section and click **Save**
5. Click **Test** to verify — you should see a test message in your Discord channel

### How it works

When an alert subscription finds new matching jobs (based on your configured track, level, and location filters), the app automatically sends a rich Discord embed to your webhook with:

- Job title and company
- Location and experience level
- Direct apply link
- The subscription filters that matched

Set your subscription interval (e.g., every 12 hours) and the app checks automatically in the background. The backend must be running to process alerts — in Docker, this runs continuously.

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
                                ┌──────┴──────┐
                                │             │
                          SQLite (WAL)   Ollama API        ┌─────────────┐
                                │        :11434  ─────────── │ llama3.2:3b │
                       ┌────────▼─────────┐                └─────────────┘
                       │    jobs.db        │
                       │  9 tables         │        ┌─────────────┐
                       │  dedup index      │        │   Discord   │
                       │  summary cache    │        │   Webhook   │
                       └──────────────────┘        └─────────────┘
```

**Data flow:** Frontend → FastAPI → Provider APIs → Parse & Filter → Dedupe → SQLite → Response
**Summarization:** Frontend → FastAPI → Ollama (local LLM) → Cache in SQLite → Response
**Alerts:** Background loop → Provider APIs → Match filters → SQLite → Discord Webhook

---

## Features

- **AI JD summarization** — local LLM (llama3.2:3b via Ollama) extracts key responsibilities, skills, compensation, and red flags from job descriptions
- **Discord webhook alerts** — get notified in Discord when new jobs match your subscription filters
- **Subscription alerts** — configure automated background checks on custom intervals (15 min to 24 hours)
- **Multi-provider search** — Greenhouse and Lever public board APIs
- **Track-based filtering** — keyword matching across 8 role categories
- **Experience level classification** — regex-based YOE extraction from JD text with title keyword priority
- **Inline JD preview** — expand any job row to peek at the description without leaving the table
- **Smart deduplication** — normalized hashing prevents duplicate entries across searches
- **33 preset companies** — curated list with verified working board URLs across Big Tech, SaaS, Cybersecurity, Fintech, Consulting, and more
- **Sortable results** — click column headers to sort by company, role, location, or post date
- **Location & level filters** — filter results by city (NYC, SF, Seattle, etc.) and experience level
- **Job detail drawer** — view full job descriptions, evidence flags, and apply links
- **Application queue** — bookmark, track, and manage jobs through your pipeline (bookmarked → in queue → applied → rejected/archived)
- **Evidence tracking** — missing apply URLs, job descriptions, or post dates are flagged, not guessed
- **Time filtering** — filter by posted within 24h, 48h, 7d, or 30d
- **Docker-ready** — single `docker compose up` with Ollama auto-setup

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
| **LLM** | Ollama, llama3.2:3b | Local AI summarization (no API keys) |
| **Notifications** | Discord Webhooks | Push alerts for new matching jobs |
| **Deployment** | Docker, nginx | Containerized production setup |
| **Testing** | pytest, pytest-asyncio | Backend unit and integration tests |

---

## Getting Started

### Prerequisites

- **Python** 3.12+
- **Node.js** 18+ (or Bun)
- **Ollama** (optional, for AI summarization) — install from [ollama.com](https://ollama.com)
- **Docker** (optional, for containerized deployment — includes Ollama automatically)

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
- Ollama: `http://localhost:11434` (auto-pulls llama3.2:3b on first start)
- Database persisted via Docker volume `db-data`
- Model persisted via Docker volume `ollama-data`

First run takes a few minutes to download the LLM model (~2 GB). Subsequent starts are instant.

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry point, CORS, router registration
│   │   ├── database.py              # SQLite connection, schema (9 tables), migrations
│   │   ├── search_engine.py         # Orchestrates provider fetching, filtering, dedup, storage
│   │   ├── track_matcher.py         # Keyword-based job-to-track classification
│   │   ├── level_classifier.py      # YOE regex extraction + experience level classification
│   │   ├── location_matcher.py      # Location pattern matching for subscription filters
│   │   ├── dedupe.py                # Normalization and SHA256 hash deduplication
│   │   ├── summarizer.py            # Ollama client for LLM-powered JD summarization
│   │   ├── discord_notifier.py      # Discord webhook notification sender
│   │   ├── subscription_checker.py  # Background loop for alert subscriptions
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic models, enums (Track, PostedWithin, Provider)
│   │   ├── routers/
│   │   │   ├── profile.py           # GET/PUT /v1/user/profile, Discord webhook test
│   │   │   ├── seeds.py             # CRUD /v1/seeds
│   │   │   ├── search.py            # POST /v1/search/runs, GET /v1/search/runs/{id}
│   │   │   ├── queue.py             # CRUD /v1/queue/items
│   │   │   ├── subscriptions.py     # CRUD /v1/subscriptions, alerts
│   │   │   └── summary.py           # POST/GET /v1/jobs/{id}/summary, health check
│   │   └── providers/
│   │       ├── base.py              # Abstract provider interface (JobCard dataclass)
│   │       ├── greenhouse.py        # Greenhouse boards API integration
│   │       └── lever.py             # Lever postings API integration
│   ├── tests/
│   │   ├── test_api.py              # API contract tests
│   │   ├── test_providers.py        # Provider parsing tests with fixture data
│   │   ├── test_dedupe.py           # Normalization and hash tests
│   │   └── fixtures/                # Mock API response JSON files
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx                 # React entry, router setup
│   │   ├── App.tsx                  # Layout shell, navigation
│   │   ├── App.css                  # Global styles (dark theme)
│   │   ├── lib/
│   │   │   ├── api.ts               # Typed fetch wrapper for all API calls
│   │   │   ├── types.ts             # TypeScript interfaces mirroring backend schemas
│   │   │   └── defaultSeeds.ts      # 33 curated company presets with verified board URLs
│   │   └── pages/
│   │       ├── SearchPage.tsx       # Job discovery: search, inline preview, AI summarize
│   │       ├── QueuePage.tsx        # Application queue: status tracking, notes, filtering
│   │       └── AlertsPage.tsx       # Subscriptions, alerts feed, Discord webhook settings
│   ├── vite.config.ts
│   ├── nginx.conf                   # Production reverse proxy config
│   └── Dockerfile
│
└── docker-compose.yml               # Backend + Frontend + Ollama (auto-pulls model)
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

### Summaries (AI)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/jobs/{id}/summary` | Generate AI summary (cached, idempotent) |
| `GET` | `/v1/jobs/{id}/summary` | Get cached summary |
| `GET` | `/v1/jobs/summarizer/health` | Check if Ollama + model are available |

### Subscriptions & Alerts

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/subscriptions` | List alert subscriptions with unread counts |
| `POST` | `/v1/subscriptions` | Create subscription `{ track, experience_level?, location_filter?, interval_minutes? }` |
| `PATCH` | `/v1/subscriptions/{id}` | Update subscription |
| `DELETE` | `/v1/subscriptions/{id}` | Delete subscription |
| `GET` | `/v1/subscriptions/{id}/alerts` | List alerts for a subscription |
| `POST` | `/v1/subscriptions/{id}/alerts/mark-read` | Mark all alerts as read |
| `GET` | `/v1/alerts/count` | Global unread alert count |

### Profile & Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/v1/user/profile` | Get user preferences |
| `PUT` | `/v1/user/profile` | Update user preferences (including `discord_webhook_url`) |
| `POST` | `/v1/user/profile/test-discord` | Send a test message to configured Discord webhook |

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
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API URL (set to `http://ollama:11434` in Docker) |
| `VITE_API_URL` | `http://localhost:8000` | Backend API URL (frontend) |

---

## License

This project is for personal use.
