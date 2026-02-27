import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ..database import get_connection
from ..models.schemas import (
    JobResponse,
    QueueItemCreate,
    QueueItemResponse,
    QueueItemUpdate,
)

router = APIRouter(prefix="/v1/queue", tags=["queue"])


@router.get("/items", response_model=list[QueueItemResponse])
def list_queue_items():
    conn = get_connection()
    rows = conn.execute(
        """SELECT qi.*, j.company, j.title, j.location, j.platform, j.source_url,
                  j.apply_url, j.apply_url_status, j.posted_date, j.posted_age_hours,
                  j.jd_raw_text, j.track, j.experience_level, j.scrape_ts
           FROM queue_items qi
           JOIN jobs j ON qi.job_id = j.id
           WHERE qi.user_id = 'default'
           ORDER BY qi.updated_at DESC"""
    ).fetchall()
    conn.close()

    items = []
    for r in rows:
        job = JobResponse(
            id=r["job_id"],
            company=r["company"],
            title=r["title"],
            location=r["location"],
            platform=r["platform"],
            source_url=r["source_url"],
            apply_url=r["apply_url"],
            apply_url_status=r["apply_url_status"],
            posted_date=r["posted_date"],
            posted_age_hours=r["posted_age_hours"],
            jd_raw_text=r["jd_raw_text"],
            track=r["track"],
            experience_level=r["experience_level"],
            scrape_ts=r["scrape_ts"],
            evidence=[],
        )
        items.append(
            QueueItemResponse(
                id=r["id"],
                job_id=r["job_id"],
                status=r["status"],
                notes=r["notes"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                job=job,
            )
        )
    return items


@router.post("/items", response_model=QueueItemResponse, status_code=201)
def create_queue_item(body: QueueItemCreate):
    conn = get_connection()

    # Verify job exists
    job = conn.execute("SELECT id FROM jobs WHERE id = ?", (body.job_id,)).fetchone()
    if not job:
        conn.close()
        raise HTTPException(status_code=404, detail="Job not found")

    # Check for existing queue item
    existing = conn.execute(
        "SELECT id FROM queue_items WHERE job_id = ? AND user_id = 'default'",
        (body.job_id,),
    ).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=409, detail="Job already in queue")

    item_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    conn.execute(
        "INSERT INTO queue_items (id, user_id, job_id, status, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (item_id, "default", body.job_id, body.status.value, body.notes, now, now),
    )
    conn.commit()

    row = conn.execute(
        """SELECT qi.*, j.company, j.title, j.location, j.platform, j.source_url,
                  j.apply_url, j.apply_url_status, j.posted_date, j.posted_age_hours,
                  j.jd_raw_text, j.track, j.experience_level, j.scrape_ts
           FROM queue_items qi
           JOIN jobs j ON qi.job_id = j.id
           WHERE qi.id = ?""",
        (item_id,),
    ).fetchone()
    conn.close()

    job_resp = JobResponse(
        id=row["job_id"], company=row["company"], title=row["title"],
        location=row["location"], platform=row["platform"],
        source_url=row["source_url"], apply_url=row["apply_url"],
        apply_url_status=row["apply_url_status"], posted_date=row["posted_date"],
        posted_age_hours=row["posted_age_hours"], jd_raw_text=row["jd_raw_text"],
        track=row["track"], experience_level=row["experience_level"], scrape_ts=row["scrape_ts"], evidence=[],
    )
    return QueueItemResponse(
        id=row["id"], job_id=row["job_id"], status=row["status"],
        notes=row["notes"], created_at=row["created_at"],
        updated_at=row["updated_at"], job=job_resp,
    )


@router.patch("/items/{item_id}", response_model=QueueItemResponse)
def update_queue_item(item_id: str, body: QueueItemUpdate):
    conn = get_connection()
    existing = conn.execute(
        "SELECT * FROM queue_items WHERE id = ? AND user_id = 'default'", (item_id,)
    ).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Queue item not found")

    updates = []
    params = []
    if body.status is not None:
        updates.append("status = ?")
        params.append(body.status.value)
    if body.notes is not None:
        updates.append("notes = ?")
        params.append(body.notes)

    if updates:
        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        params.append(item_id)
        conn.execute(
            f"UPDATE queue_items SET {', '.join(updates)} WHERE id = ?", params
        )
        conn.commit()

    row = conn.execute(
        """SELECT qi.*, j.company, j.title, j.location, j.platform, j.source_url,
                  j.apply_url, j.apply_url_status, j.posted_date, j.posted_age_hours,
                  j.jd_raw_text, j.track, j.experience_level, j.scrape_ts
           FROM queue_items qi
           JOIN jobs j ON qi.job_id = j.id
           WHERE qi.id = ?""",
        (item_id,),
    ).fetchone()
    conn.close()

    job_resp = JobResponse(
        id=row["job_id"], company=row["company"], title=row["title"],
        location=row["location"], platform=row["platform"],
        source_url=row["source_url"], apply_url=row["apply_url"],
        apply_url_status=row["apply_url_status"], posted_date=row["posted_date"],
        posted_age_hours=row["posted_age_hours"], jd_raw_text=row["jd_raw_text"],
        track=row["track"], experience_level=row["experience_level"], scrape_ts=row["scrape_ts"], evidence=[],
    )
    return QueueItemResponse(
        id=row["id"], job_id=row["job_id"], status=row["status"],
        notes=row["notes"], created_at=row["created_at"],
        updated_at=row["updated_at"], job=job_resp,
    )
