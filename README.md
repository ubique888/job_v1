<div align="center">

# Job Search Autopilot

### A full-stack job discovery dashboard powered by local AI

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![SQLite](https://img.shields.io/badge/SQLite-WAL-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Ollama](https://img.shields.io/badge/Ollama-llama3.2-000000?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.com)
[![Vite](https://img.shields.io/badge/Vite-7.3-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vite.dev)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.5-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://docs.pydantic.dev)
[![Discord](https://img.shields.io/badge/Discord-Webhooks-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com)
[![nginx](https://img.shields.io/badge/nginx-Alpine-009639?style=for-the-badge&logo=nginx&logoColor=white)](https://nginx.org)

Aggregates software engineering roles from public ATS boards (Greenhouse & Lever).<br>
Summarizes job descriptions with a local LLM. Sends alerts to Discord.<br>
**No scraping. No auto-apply. No API keys required.**

---

[English](#english) | [中文](#中文) | [日本語](#日本語) | [한국어](#한국어) | [Español](#español) | [Français](#français) | [Deutsch](#deutsch) | [Português](#português) | [Русский](#русский) | [العربية](#العربية) | [हिन्दी](#हिन्दी)

---

</div>

<a name="english"></a>

## Highlights

<table>
<tr>
<td width="50%">

### AI Job Description Summarizer
> Click **Summarize** on any job listing to get a structured breakdown powered by `llama3.2:3b` running **locally** via Ollama.

- **Responsibilities** — 3-5 key duties
- **Required Skills** — must-have technologies
- **Nice-to-Have** — bonus skills
- **Experience Level** — inferred seniority
- **Compensation** — salary if disclosed
- **Red Flags** — unusual requirements or perks

Summaries are **cached in SQLite** — each job is processed only once.

</td>
<td width="50%">

### Discord Webhook Alerts
> Get **push notifications** in Discord when new jobs match your subscription filters.

**Setup in 5 steps:**
1. Discord server **Settings > Integrations > Webhooks**
2. Create webhook, copy URL
3. Paste in app's **Alerts** page, click **Save**
4. Click **Test** to verify
5. Set subscription interval (15 min to 24 hours)

The app checks automatically in the background and sends rich embeds with job details and apply links.

</td>
</tr>
</table>

---

## Quick Start

```bash
# One command with Docker (includes Ollama + LLM auto-download)
docker compose up --build

# Or run locally
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

| Service | Docker | Local |
|---------|--------|-------|
| Frontend | `http://localhost:3080` | `http://localhost:5173` |
| Backend API | `http://localhost:8000` | `http://localhost:8000` |
| Ollama | `http://localhost:11434` (auto) | Install from [ollama.com](https://ollama.com) |
| API Docs | `http://localhost:8000/docs` | `http://localhost:8000/docs` |

> First Docker run downloads the LLM model (~2 GB). Subsequent starts are instant.

---

## Table of Contents

- [Highlights](#highlights)
- [Quick Start](#quick-start)
- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [AI Summarization Setup](#ai-summarization-setup)
- [Discord Webhook Setup](#discord-webhook-setup)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [How It Works](#how-it-works)
- [Testing](#testing)
- [Configuration](#configuration)
- [Translations](#translations)
- [License](#license)

---

## Overview

Most job boards are noisy. This tool takes a different approach:

| Step | What Happens |
|------|-------------|
| **1. Add Seeds** | Provide company board URLs from Greenhouse or Lever (or pick from 33 curated presets) |
| **2. Pick a Track** | Backend, Frontend, Fullstack, DevOps, Data, ML, AI Agent, or Consulting |
| **3. Run Search** | Engine fetches listings via public APIs, filters by track, deduplicates, classifies experience level |
| **4. Review & Summarize** | Browse results, click Summarize for AI-powered key points, add to your application queue |
| **5. Get Alerts** | Set up subscriptions and receive Discord notifications for new matches |

> **No credentials required. No auto-apply. Every listing links back to its original source.**

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
                                │        :11434  ───────── │ llama3.2:3b │
                       ┌────────▼─────────┐                └─────────────┘
                       │    jobs.db        │
                       │  9 tables         │        ┌─────────────┐
                       │  dedup index      │        │   Discord   │
                       │  summary cache    │        │   Webhook   │
                       └──────────────────┘        └─────────────┘
```

| Flow | Pipeline |
|------|----------|
| **Search** | Frontend → FastAPI → Provider APIs → Parse & Filter → Dedupe → SQLite → Response |
| **Summarize** | Frontend → FastAPI → Ollama (local LLM) → Cache in SQLite → Response |
| **Alerts** | Background loop → Provider APIs → Match filters → SQLite → Discord Webhook |

---

## Features

| Category | Feature | Description |
|----------|---------|-------------|
| **AI** | JD Summarization | Local LLM extracts responsibilities, skills, compensation, and red flags |
| **Notifications** | Discord Webhooks | Push alerts when new jobs match your subscriptions |
| **Alerts** | Subscription System | Automated background checks on custom intervals (15 min – 24 hours) |
| **Search** | Multi-Provider | Greenhouse and Lever public board APIs |
| **Search** | Track Filtering | Keyword matching across 8 role categories |
| **Search** | Experience Classification | Regex-based YOE extraction from JD text |
| **UI** | Inline JD Preview | Expand any row to peek at the description |
| **UI** | Sortable & Filterable | Sort by column, filter by location and level |
| **Data** | Smart Deduplication | Normalized hashing prevents duplicates across searches |
| **Data** | 33 Preset Companies | Curated list across Big Tech, SaaS, Fintech, and more |
| **Data** | Evidence Tracking | Missing data is flagged, not guessed |
| **Pipeline** | Application Queue | Track jobs: bookmarked → in queue → applied → rejected/archived |
| **Deploy** | Docker-Ready | Single `docker compose up` with Ollama auto-setup |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | ![Python](https://img.shields.io/badge/-Python_3.12-3776AB?style=flat-square&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) | REST API server |
| **Database** | ![SQLite](https://img.shields.io/badge/-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white) | Persistent storage (WAL mode) |
| **HTTP Client** | ![httpx](https://img.shields.io/badge/-httpx-2D2D2D?style=flat-square) | Async requests to provider APIs |
| **HTML Parsing** | ![selectolax](https://img.shields.io/badge/-selectolax-444?style=flat-square) | Extract job description text |
| **Frontend** | ![React](https://img.shields.io/badge/-React_19-61DAFB?style=flat-square&logo=react&logoColor=black) ![TypeScript](https://img.shields.io/badge/-TypeScript_5.9-3178C6?style=flat-square&logo=typescript&logoColor=white) | Single-page application |
| **Build Tool** | ![Vite](https://img.shields.io/badge/-Vite_7.3-646CFF?style=flat-square&logo=vite&logoColor=white) | Dev server and production builds |
| **Routing** | ![React Router](https://img.shields.io/badge/-React_Router_7-CA4245?style=flat-square&logo=reactrouter&logoColor=white) | Client-side navigation |
| **LLM** | ![Ollama](https://img.shields.io/badge/-Ollama-000000?style=flat-square&logo=ollama&logoColor=white) | Local AI summarization (no API keys) |
| **Notifications** | ![Discord](https://img.shields.io/badge/-Discord-5865F2?style=flat-square&logo=discord&logoColor=white) | Push alerts for new matching jobs |
| **Deployment** | ![Docker](https://img.shields.io/badge/-Docker-2496ED?style=flat-square&logo=docker&logoColor=white) ![nginx](https://img.shields.io/badge/-nginx-009639?style=flat-square&logo=nginx&logoColor=white) | Containerized production setup |
| **Testing** | ![pytest](https://img.shields.io/badge/-pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white) | Backend unit and integration tests |
| **Validation** | ![Pydantic](https://img.shields.io/badge/-Pydantic_2-E92063?style=flat-square&logo=pydantic&logoColor=white) | Request/response schema validation |

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

> First run takes a few minutes to download the LLM model (~2 GB). Subsequent starts are instant.

---

## AI Summarization Setup

### With Docker (automatic)

Ollama is included as a Docker Compose service. Run `docker compose up` and the model downloads automatically. **No extra steps.**

### Without Docker (local)

```bash
# 1. Install Ollama from https://ollama.com

# 2. Pull the model (~2 GB download)
ollama pull llama3.2:3b

# 3. Ollama runs automatically in the background after install
# 4. Start the app — the Summarize button appears when Ollama is detected
```

> **Graceful fallback:** If Ollama is not running, the app works normally. The Summarize button shows an error and raw JD text remains visible.

---

## Discord Webhook Setup

| Step | Action |
|------|--------|
| **1** | In Discord: **Server Settings > Integrations > Webhooks > New Webhook** |
| **2** | Name it (e.g. "Job Alerts"), choose a channel, **copy the webhook URL** |
| **3** | In the app: go to the **Alerts** page |
| **4** | Paste the URL in **Discord Webhook** section, click **Save** |
| **5** | Click **Test** — you should see a test message in Discord |

When subscriptions find new matches, the app sends rich Discord embeds with:
- Job title and company
- Location and experience level
- Direct apply link
- The subscription filters that matched

> **Note:** The backend must be running for alerts to process. In Docker, this runs continuously.

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

> Full interactive documentation available at `/docs` (Swagger UI) when the backend is running.

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

<a name="translations"></a>

## Translations

<details>
<summary><a name="中文"></a><strong>中文 (Chinese)</strong></summary>

### Job Search Autopilot — 求职自动化仪表板

一个全栈求职发现仪表板，从公共ATS（申请人跟踪系统）平台聚合软件工程职位。通过Greenhouse和Lever API搜索真实、经过验证的职位列表。

**核心功能：**
- **AI职位描述摘要** — 使用本地运行的 `llama3.2:3b` 模型，将职位描述提炼为结构化要点（职责、技能要求、薪资等）
- **Discord Webhook通知** — 当新职位匹配您的订阅条件时，自动发送Discord通知
- **智能去重** — 跨搜索自动去重，避免重复职位
- **8个职业方向** — Backend、Frontend、Fullstack、DevOps、Data、ML、AI Agent、Consulting

**快速开始：**
```bash
docker compose up --build
```
首次运行会自动下载LLM模型（约2GB），后续启动秒级完成。
</details>

<details>
<summary><a name="日本語"></a><strong>日本語 (Japanese)</strong></summary>

### Job Search Autopilot — 求人検索自動化ダッシュボード

パブリックATS（応募者追跡システム）のボードからソフトウェアエンジニアリングの求人を集約するフルスタック求人検索ダッシュボードです。

**主な機能：**
- **AI求人要約** — ローカルLLM（`llama3.2:3b`）で求人内容を構造化された要点に要約（責務、必要スキル、給与など）
- **Discord Webhook通知** — 新しい求人がサブスクリプション条件に一致した際、Discordに自動通知
- **スマート重複排除** — 検索をまたいだ自動重複排除
- **8つの職種トラック** — Backend、Frontend、Fullstack、DevOps、Data、ML、AI Agent、Consulting

**クイックスタート：**
```bash
docker compose up --build
```
</details>

<details>
<summary><a name="한국어"></a><strong>한국어 (Korean)</strong></summary>

### Job Search Autopilot — 구직 자동화 대시보드

공개 ATS(지원자 추적 시스템) 보드에서 소프트웨어 엔지니어링 채용 공고를 집계하는 풀스택 구직 대시보드입니다.

**주요 기능:**
- **AI 채용공고 요약** — 로컬 LLM(`llama3.2:3b`)으로 채용 설명을 구조화된 핵심 정보로 요약 (책임, 기술 요건, 연봉 등)
- **Discord Webhook 알림** — 새 채용공고가 구독 조건과 일치하면 Discord로 자동 알림
- **스마트 중복 제거** — 검색 간 자동 중복 제거
- **8개 직무 트랙** — Backend, Frontend, Fullstack, DevOps, Data, ML, AI Agent, Consulting

**빠른 시작:**
```bash
docker compose up --build
```
</details>

<details>
<summary><a name="español"></a><strong>Español (Spanish)</strong></summary>

### Job Search Autopilot — Panel de Descubrimiento de Empleo

Un panel de descubrimiento de empleo full-stack que agrega roles de ingeniería de software desde tableros ATS públicos (Greenhouse y Lever).

**Funciones principales:**
- **Resumen de JD con IA** — LLM local (`llama3.2:3b`) extrae responsabilidades, habilidades requeridas, salario y señales de alerta
- **Notificaciones Discord Webhook** — Recibe alertas automáticas cuando nuevos empleos coincidan con tus suscripciones
- **Deduplicación inteligente** — Evita duplicados entre búsquedas
- **8 categorías profesionales** — Backend, Frontend, Fullstack, DevOps, Data, ML, AI Agent, Consulting

**Inicio rápido:**
```bash
docker compose up --build
```
</details>

<details>
<summary><a name="français"></a><strong>Français (French)</strong></summary>

### Job Search Autopilot — Tableau de Bord de Recherche d'Emploi

Un tableau de bord full-stack de découverte d'emplois qui agrège les postes en ingénierie logicielle depuis les plateformes ATS publiques (Greenhouse et Lever).

**Fonctionnalités principales :**
- **Résumé IA des offres** — LLM local (`llama3.2:3b`) extrait responsabilités, compétences, salaire et points d'attention
- **Notifications Discord Webhook** — Alertes automatiques quand de nouveaux postes correspondent à vos abonnements
- **Déduplication intelligente** — Évite les doublons entre les recherches
- **8 filières professionnelles** — Backend, Frontend, Fullstack, DevOps, Data, ML, AI Agent, Consulting

**Démarrage rapide :**
```bash
docker compose up --build
```
</details>

<details>
<summary><a name="deutsch"></a><strong>Deutsch (German)</strong></summary>

### Job Search Autopilot — Stellensuche-Dashboard

Ein Full-Stack-Dashboard zur Stellensuche, das Software-Engineering-Positionen von öffentlichen ATS-Plattformen (Greenhouse und Lever) aggregiert.

**Hauptfunktionen:**
- **KI-Stellenbeschreibung-Zusammenfassung** — Lokales LLM (`llama3.2:3b`) extrahiert Verantwortlichkeiten, erforderliche Fähigkeiten, Gehalt und Auffälligkeiten
- **Discord Webhook-Benachrichtigungen** — Automatische Benachrichtigungen wenn neue Stellen Ihren Abonnementkriterien entsprechen
- **Intelligente Deduplizierung** — Verhindert Duplikate über Suchen hinweg
- **8 Berufsfelder** — Backend, Frontend, Fullstack, DevOps, Data, ML, AI Agent, Consulting

**Schnellstart:**
```bash
docker compose up --build
```
</details>

<details>
<summary><a name="português"></a><strong>Português (Portuguese)</strong></summary>

### Job Search Autopilot — Painel de Busca de Vagas

Um painel full-stack de descoberta de vagas que agrega posições de engenharia de software de plataformas ATS públicas (Greenhouse e Lever).

**Funcionalidades principais:**
- **Resumo de JD com IA** — LLM local (`llama3.2:3b`) extrai responsabilidades, habilidades necessárias, salário e pontos de atenção
- **Notificações Discord Webhook** — Alertas automáticos quando novas vagas correspondem às suas assinaturas
- **Deduplicação inteligente** — Evita duplicatas entre buscas
- **8 trilhas profissionais** — Backend, Frontend, Fullstack, DevOps, Data, ML, AI Agent, Consulting

**Início rápido:**
```bash
docker compose up --build
```
</details>

<details>
<summary><a name="русский"></a><strong>Русский (Russian)</strong></summary>

### Job Search Autopilot — Панель Поиска Вакансий

Полнофункциональная панель поиска вакансий, агрегирующая позиции в разработке ПО с публичных ATS-платформ (Greenhouse и Lever).

**Основные функции:**
- **ИИ-резюме вакансий** — Локальная LLM (`llama3.2:3b`) извлекает обязанности, требуемые навыки, зарплату и важные детали
- **Discord Webhook уведомления** — Автоматические оповещения при появлении вакансий, соответствующих вашим подпискам
- **Умная дедупликация** — Предотвращение дублирования между поисками
- **8 профессиональных направлений** — Backend, Frontend, Fullstack, DevOps, Data, ML, AI Agent, Consulting

**Быстрый старт:**
```bash
docker compose up --build
```
</details>

<details>
<summary><a name="العربية"></a><strong>العربية (Arabic)</strong></summary>

### Job Search Autopilot — لوحة البحث عن الوظائف

لوحة متكاملة لاكتشاف الوظائف تجمع وظائف هندسة البرمجيات من منصات ATS العامة (Greenhouse و Lever).

**الميزات الرئيسية:**
- **ملخص الوظائف بالذكاء الاصطناعي** — نموذج LLM محلي (`llama3.2:3b`) يستخرج المسؤوليات والمهارات المطلوبة والراتب والملاحظات المهمة
- **إشعارات Discord Webhook** — تنبيهات تلقائية عند ظهور وظائف جديدة تطابق اشتراكاتك
- **إزالة التكرارات الذكية** — منع التكرار عبر عمليات البحث المتعددة
- **8 مسارات مهنية** — Backend، Frontend، Fullstack، DevOps، Data، ML، AI Agent، Consulting

**البدء السريع:**
```bash
docker compose up --build
```
</details>

<details>
<summary><a name="हिन्दी"></a><strong>हिन्दी (Hindi)</strong></summary>

### Job Search Autopilot — नौकरी खोज डैशबोर्ड

एक फुल-स्टैक नौकरी खोज डैशबोर्ड जो सार्वजनिक ATS प्लेटफॉर्म (Greenhouse और Lever) से सॉफ्टवेयर इंजीनियरिंग पदों को एकत्रित करता है।

**मुख्य विशेषताएं:**
- **AI नौकरी विवरण सारांश** — स्थानीय LLM (`llama3.2:3b`) जिम्मेदारियों, आवश्यक कौशल, वेतन और महत्वपूर्ण बिंदुओं को निकालता है
- **Discord Webhook सूचनाएं** — जब नई नौकरियां आपकी सदस्यता शर्तों से मेल खाती हैं तो स्वचालित अलर्ट
- **स्मार्ट डिडुप्लिकेशन** — खोजों के बीच डुप्लिकेट को रोकता है
- **8 करियर ट्रैक** — Backend, Frontend, Fullstack, DevOps, Data, ML, AI Agent, Consulting

**त्वरित शुरुआत:**
```bash
docker compose up --build
```
</details>

---

## License

This project is for personal use.
