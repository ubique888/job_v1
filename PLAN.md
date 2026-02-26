# PLAN.md — SWE Job Search Autopilot (Search + Apply Links + Optional Resume Match)

> Goal: Build a compliant, reliable MVP that **finds real jobs online** (from allowed public sources), returns **application links**, and provides a **dashboard** where users can choose their target field/track and optionally enable resume-match filtering.  
> Hard constraint: **NO auto-apply**, **NO captcha bypass**, **NO LinkedIn/Indeed scraping**.

---

## 0) Non-Negotiables (Hard Rules)

1) **No auto-apply**
- The system must never submit applications or fill/submit forms.
- Dashboard actions allowed: **Open apply link**, **Copy apply link**, **Bookmark**, **Add to Queue**, **Mark Applied (manual)**.

2) **Compliant sources only**
- Allowed:
  - User pasted JD / user provided job URL
  - Public ATS/job boards without login/captcha: **Greenhouse**, **Lever** (primary MVP)
  - Optional public job board APIs (only if clearly public and legal to use): e.g., Remotive (if available)
- Forbidden:
  - LinkedIn, Indeed, or anything requiring login/captcha/strong anti-bot
  - Any captcha bypass, stealth automation, or mass scraping

3) **Evidence-only, no guessing**
- If we can’t obtain `posted_date` / `apply_url` / `jd_raw_text`:
  - Set field to `null`
  - Add evidence flag:
    - `posted_date_unknown`
    - `apply_url_unknown`
    - `jd_text_unavailable`
- Never infer from “today” or page metadata unless explicit and reliable.

4) **Auditable**
Every job record must include:
- `source_url`, `scrape_ts`
- `apply_url` + `apply_url_status: direct|derived|unknown`
- `jd_snippet_evidence[]` (<= 200 chars each) when available

5) **Quality via modularity + slices**
- No “big bang” generation.
- Ship in **slices**. Each slice must be runnable and testable before moving on.

---

## 1) Product Scope (MVP)

### MVP Features
- Real job discovery from **Seeds**:
  - User maintains a list of Company Sources (Seeds): `{provider, company, board_url}`
  - System fetches jobs from these seeds (Greenhouse/Lever), normalizes + dedupes + stores
- Dashboard:
  - Track selection: Backend / Frontend / Fullstack / DevOps / Data / ML
  - Posted-within selection: 24h / 48h / 7d / 30d
  - Run Search (pulls from seeds)
  - Results table: show jobs + apply links
  - Queue + tracking (manual status updates)
  - Optional Resume Match Filter toggle (OFF by default)

### Explicitly Not In MVP
- No automated application submission
- No LinkedIn/Indeed scraping
- No “infinite web search” across the whole internet without seeds (too risky)

---

## 2) UX: Dashboard Pages (IA)

### `/search` — Job Search (Core)
- Controls:
  - **Applying For (Track)** dropdown (required)
  - **Posted Within** dropdown (24h/48h/7d/30d)
  - Provider toggles (Greenhouse/Lever)
  - **Manage Sources** (Seeds drawer)
  - **Resume Match Filter** toggle (optional; affects later filtering/ranking)
  - **Run Search** button
- Results table columns:
  - Company / Role / Location / Posted / Apply Link / Actions
- Actions:
  - Open Apply Link
  - Copy Apply Link
  - Bookmark
  - Add to Queue
  - View Details (drawer)

### `/sources` or Seeds Drawer (can be a drawer on /search)
- List seeds
- Add seed: provider + company + board_url
- Delete seed
- Validation: require at least 1 seed before Run Search enabled

### `/queue` — Apply Queue (Manual)
- List items with status:
  - Bookmarked / In Queue / Applied / Rejected / Archived
- Actions:
  - Open apply link
  - Update status
  - Notes field

### `/resume`
- Paste/upload Master Resume → store `master_version`
- When Resume Match Filter = ON and no master resume:
  - show warning **【需要用户确认：上传 Master Resume】**

### `/tracking`
- Lightweight analytics:
  - Count by status
  - Distribution by posted_within
  - Distribution by provider/platform

---

## 3) Data Model (SQLite)

### Tables
- `user_profile(user_id, track, locations_json, seniority, posted_within, remote_only, updated_at)`
- `seeds(id, user_id, provider, company, board_url, created_at)`
- `search_runs(id, user_id, track, posted_within, state, started_at, finished_at, stats_json)`
- `jobs(id, user_id, company, title, location, platform, source_url,
        apply_url, apply_url_status,
        posted_date, posted_age_hours,
        jd_raw_text, jd_hash, track, created_at)`
- `job_evidence(id, job_id, evidence_type, text, created_at)`
- `job_dedupe_index(id, job_id, company_norm, title_norm, location_norm, pk_hash)`
- `queue_items(id, user_id, job_id, status, notes, created_at, updated_at)`

### Dedupe
Primary key hash:
- `company_norm + title_norm + location_norm`
Normalization:
- lowercase
- strip punctuation
- collapse whitespace
- common abbreviations mapping (e.g., NYC → New York City)

---

## 4) API Contract (Backend)

> Backend: FastAPI + OpenAPI. Must export `openapi.json`.  
> All endpoints should include **examples** in schema.

### Profile
- `GET /v1/user/profile`
- `PUT /v1/user/profile`
  - body: `{ track, locations, seniority, posted_within, remote_only }`

### Seeds (Company Sources)
- `GET /v1/seeds`
- `POST /v1/seeds`
  - body: `{ provider:"greenhouse|lever", company:"...", board_url:"..." }`
- `DELETE /v1/seeds/{seed_id}`

### Search
- `POST /v1/search/runs`
  - body:
    ```json
    {
      "track":"Backend|Frontend|Fullstack|DevOps|Data|ML",
      "posted_within":"24h|48h|7d|30d",
      "provider_enabled":{"greenhouse":true,"lever":true},
      "limit_per_provider":50
    }
    ```
  - response: `{ run_id, state }`
- `GET /v1/search/runs/{run_id}`
  - response includes `filters_applied.posted_within` and `discovered_jobs[]`

### Filtering (Optional switch)
- `POST /v1/filter/runs`
  - body:
    ```json
    {
      "job_ids":["..."],
      "posted_within":"24h|48h|7d|30d",
      "enable_resume_match_filter": false,
      "master_resume_version": null
    }
    ```
- `GET /v1/filter/runs/{id}`

### Recommend (Optional)
- `POST /v1/recommend/runs`
- `GET /v1/recommend/runs/{id}`

### Resume (For optional resume-match)
- `POST /v1/resume/master`
  - body: `{ content_text:"..." }`
  - response: `{ master_version:"..." }`

### Queue + Tracking
- `GET /v1/queue/items`
- `POST /v1/queue/items`
- `PATCH /v1/queue/items/{id}`

---

## 5) Providers Architecture (Real Job Discovery)

### Interface
`IJobSourceProvider.search(params) -> JobCard[]`
Params include:
- `track`, `posted_within`, `limit`, optional location/remote/seniority filters

### MVP Providers (Must implement at least 1 first)
1) `GreenhouseProvider`
- Input: `board_url` seeds like `https://boards.greenhouse.io/{company}`
- Extract:
  - job listing URLs
  - job detail content → `jd_raw_text`
  - apply URL (apply button)
  - posted date (if available; else unknown)

2) `LeverProvider`
- Input: `board_url` seeds like `https://jobs.lever.co/{company}`
- Similar extraction

### Evidence flags
- If apply URL missing: `apply_url=null`, `apply_url_status="unknown"`, evidence `apply_url_unknown`
- If JD text missing: evidence `jd_text_unavailable`
- If posted date missing: evidence `posted_date_unknown`

---

## 6) PostedWithin Logic (24h/48h/7d/30d)

### Enum
- `24h` → 24 hours
- `48h` → 48 hours
- `7d`  → 168 hours
- `30d` → 720 hours

### Behavior
- If `posted_age_hours` exists: enforce window
- If unknown: do **not** drop by default; mark risk `posted_date_unknown`
- (Optional config later) `require_posted_date=true` would allow dropping unknowns

---

## 7) Testing Strategy (Why you’re getting “half-baked” outputs)

### Must-have tests (MVP)
- Provider parsing tests with fixtures:
  - `tests/fixtures/greenhouse_job.html`
  - `tests/fixtures/lever_job.html`
  - Assert extraction of: `title`, `company`, `source_url`, `apply_url` (or evidence unknown), and `jd_raw_text` (or evidence)
- Dedupe + normalization tests
- PostedWithin filtering tests
- API contract sanity tests (OpenAPI examples exist, endpoints return required fields)

### Anti-regression
- If mock mode exists:
  - must be **opt-in** or fallback only
  - UI must show visible **Mock Mode** label

---

## 8) Delivery Plan (Slices)

### Slice A — Real Jobs via Seeds (Do this first)
**Goal:** Dashboard runs a real search and shows real jobs + apply links from Greenhouse/Lever seeds.

Backend:
- Seeds CRUD
- Search runs (from seeds)
- At least 1 provider implemented (recommended Greenhouse first)
- Store jobs + evidence + dedupe

Frontend:
- TrackSelect (required)
- PostedWithinSelect
- Manage Sources (Seeds drawer)
- Run Search disabled when seeds empty
- Results table shows `apply_url` and handles unknown correctly
- No default demo jobs

Acceptance checklist:
- With 1 valid seed:
  - Run Search returns non-empty `discovered_jobs` from real parsing
  - Each job has `source_url`
  - apply_url extracted or marked unknown with evidence

### Slice B — Second Provider + Better Extraction
- Add Lever provider
- Improve apply_url + jd_raw_text extraction reliability

### Slice C — PostedWithin End-to-End
- Ensure posted_within is stored on run
- Filtering behavior is consistent and auditable

### Slice D — Queue + Tracking
- Queue persistence + manual status updates
- Tracking summary page

### Slice E — Optional Resume Match Filter
- Resume upload + master_version
- Toggle behavior:
  - OFF: no resume logic
  - ON + missing resume: show “needs confirm” / unknown evidence
  - ON + resume: must-have extraction + low_priority bucket

---

## 9) Definition of Done (MVP)

MVP is done when:
- User selects **Track** + **PostedWithin**
- User adds at least 1 **Seed** (Greenhouse/Lever)
- Clicking **Run Search** returns real jobs (not demo)
- Results include **apply links** (or explicit unknown)
- User can bookmark/add to queue and manually track status
- All key behaviors are covered by tests and auditable in DB

---

## 10) Commands (Example)

### Backend
- `uvicorn app.main:app --reload`
- `pytest -q`

### Frontend
- `bun install` (or `npm install`)
- `bun dev` (or `npm run dev`)

---

## 11) Known Risks & Mitigations

- Provider pages may change HTML → mitigate with fixtures + quick parser updates
- Posted date often missing → treat as unknown (do not guess), allow user to choose “require posted date” later
- Seeds requirement may feel manual → mitigate with:
  - seed templates (list of common companies)
  - “Paste board URL to auto-detect provider”

---

## 12) Next Actions

1) Implement **Slice A** only (Seeds + 1 provider + real results + no demo jobs).
2) Add fixtures + tests before expanding scope.
3) Only after Slice A passes, proceed to Slice B/C.
