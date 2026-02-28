import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ..database import get_connection
from ..models.schemas import (
    POSTED_WITHIN_HOURS,
    JobResponse,
    PostedWithin,
    SearchRunCreate,
    SearchRunDetailResponse,
    SearchRunResponse,
)
from ..search_engine import execute_search_run
from ..track_matcher import get_all_track_names

router = APIRouter(prefix="/v1/search", tags=["search"])


@router.post("/runs", response_model=SearchRunResponse, status_code=201)
async def create_search_run(body: SearchRunCreate, bg: BackgroundTasks):
    # Validate track exists (built-in or custom)
    valid_tracks = get_all_track_names()
    if body.track not in valid_tracks:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown track '{body.track}'. Valid tracks: {valid_tracks}",
        )

    conn = get_connection()

    # Validate at least 1 seed exists for enabled providers
    seeds = conn.execute("SELECT provider FROM seeds WHERE user_id = 'default'").fetchall()
    enabled_providers = {p for p, v in body.provider_enabled.items() if v}
    seed_providers = {s["provider"] for s in seeds}

    if not enabled_providers & seed_providers:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="No seeds found for enabled providers. Add seeds first.",
        )

    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    conn.execute(
        "INSERT INTO search_runs (id, user_id, track, posted_within, state, started_at) VALUES (?, ?, ?, ?, ?, ?)",
        (run_id, "default", body.track, body.posted_within.value, "pending", now),
    )
    conn.commit()
    conn.close()

    # Execute synchronously for MVP (fast enough with API calls)
    await execute_search_run(
        run_id=run_id,
        user_id="default",
        track=body.track,
        posted_within=body.posted_within.value,
        provider_enabled=body.provider_enabled,
        limit_per_provider=body.limit_per_provider,
    )

    return {"run_id": run_id, "state": "completed"}


@router.get("/runs/{run_id}", response_model=SearchRunDetailResponse)
def get_search_run(run_id: str):
    conn = get_connection()
    run = conn.execute("SELECT * FROM search_runs WHERE id = ?", (run_id,)).fetchone()
    if not run:
        conn.close()
        raise HTTPException(status_code=404, detail="Search run not found")

    # Fetch jobs matching this run's track, filtered by posted_within window
    max_hours = POSTED_WITHIN_HOURS.get(PostedWithin(run["posted_within"]))
    jobs = conn.execute(
        """SELECT * FROM jobs
           WHERE user_id = 'default' AND track = ?
             AND (posted_age_hours IS NULL OR posted_age_hours <= ?)
           ORDER BY created_at DESC""",
        (run["track"], max_hours),
    ).fetchall()

    job_responses = []
    for j in jobs:
        evidence = conn.execute(
            "SELECT evidence_type, text FROM job_evidence WHERE job_id = ?", (j["id"],)
        ).fetchall()
        job_responses.append(
            JobResponse(
                id=j["id"],
                company=j["company"],
                title=j["title"],
                location=j["location"],
                platform=j["platform"],
                source_url=j["source_url"],
                apply_url=j["apply_url"],
                apply_url_status=j["apply_url_status"],
                posted_date=j["posted_date"],
                posted_age_hours=j["posted_age_hours"],
                jd_raw_text=j["jd_raw_text"],
                track=j["track"],
                experience_level=j["experience_level"],
                yoe_min=j["yoe_min"],
                scrape_ts=j["scrape_ts"],
                evidence=[{"type": e["evidence_type"], "text": e["text"]} for e in evidence],
            )
        )

    stats = json.loads(run["stats_json"]) if run["stats_json"] else {}

    conn.close()
    return SearchRunDetailResponse(
        run_id=run["id"],
        state=run["state"],
        track=run["track"],
        posted_within=run["posted_within"],
        started_at=run["started_at"],
        finished_at=run["finished_at"],
        stats=stats,
        discovered_jobs=job_responses,
    )
