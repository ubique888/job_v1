"""Subscription & alert endpoints — CRUD for job alert subscriptions."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ..database import get_connection
from ..models.schemas import (
    AlertResponse,
    JobResponse,
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionUpdate,
)

router = APIRouter(prefix="/v1/subscriptions", tags=["subscriptions"])


def _build_sub_response(row, unread_count: int = 0) -> SubscriptionResponse:
    return SubscriptionResponse(
        id=row["id"],
        track=row["track"],
        experience_level=row["experience_level"],
        location_filter=row["location_filter"],
        is_active=bool(row["is_active"]),
        interval_minutes=row["interval_minutes"],
        last_checked_at=row["last_checked_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        unread_count=unread_count,
    )


def _build_job_response(j) -> JobResponse:
    return JobResponse(
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
        evidence=[],
    )


# ── List subscriptions ────────────────────────────────────────────────

@router.get("", response_model=list[SubscriptionResponse])
def list_subscriptions():
    conn = get_connection()
    subs = conn.execute(
        "SELECT * FROM subscriptions WHERE user_id = 'default' ORDER BY created_at DESC"
    ).fetchall()

    results = []
    for s in subs:
        count = conn.execute(
            "SELECT COUNT(*) as c FROM alerts WHERE subscription_id = ? AND is_read = 0",
            (s["id"],),
        ).fetchone()["c"]
        results.append(_build_sub_response(s, unread_count=count))

    conn.close()
    return results


# ── Create subscription ───────────────────────────────────────────────

@router.post("", response_model=SubscriptionResponse, status_code=201)
def create_subscription(body: SubscriptionCreate):
    conn = get_connection()
    sub_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    conn.execute(
        """INSERT INTO subscriptions
           (id, user_id, track, experience_level, location_filter, interval_minutes, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            sub_id,
            "default",
            body.track,
            body.experience_level.value if body.experience_level else None,
            body.location_filter,
            body.interval_minutes,
            now,
            now,
        ),
    )
    conn.commit()

    row = conn.execute("SELECT * FROM subscriptions WHERE id = ?", (sub_id,)).fetchone()
    conn.close()
    return _build_sub_response(row)


# ── Update subscription ──────────────────────────────────────────────

@router.patch("/{sub_id}", response_model=SubscriptionResponse)
def update_subscription(sub_id: str, body: SubscriptionUpdate):
    conn = get_connection()
    existing = conn.execute(
        "SELECT * FROM subscriptions WHERE id = ? AND user_id = 'default'", (sub_id,)
    ).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Subscription not found")

    updates = []
    params = []
    if body.track is not None:
        updates.append("track = ?")
        params.append(body.track)
    if body.experience_level is not None:
        updates.append("experience_level = ?")
        params.append(body.experience_level.value)
    if body.location_filter is not None:
        updates.append("location_filter = ?")
        params.append(body.location_filter if body.location_filter != "All" else None)
    if body.interval_minutes is not None:
        updates.append("interval_minutes = ?")
        params.append(body.interval_minutes)
    if body.is_active is not None:
        updates.append("is_active = ?")
        params.append(1 if body.is_active else 0)

    if updates:
        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        params.append(sub_id)
        conn.execute(
            f"UPDATE subscriptions SET {', '.join(updates)} WHERE id = ?", params
        )
        conn.commit()

    row = conn.execute("SELECT * FROM subscriptions WHERE id = ?", (sub_id,)).fetchone()
    count = conn.execute(
        "SELECT COUNT(*) as c FROM alerts WHERE subscription_id = ? AND is_read = 0",
        (sub_id,),
    ).fetchone()["c"]
    conn.close()
    return _build_sub_response(row, unread_count=count)


# ── Delete subscription ──────────────────────────────────────────────

@router.delete("/{sub_id}", status_code=204)
def delete_subscription(sub_id: str):
    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM subscriptions WHERE id = ? AND user_id = 'default'", (sub_id,)
    ).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Subscription not found")

    conn.execute("DELETE FROM alerts WHERE subscription_id = ?", (sub_id,))
    conn.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))
    conn.commit()
    conn.close()


# ── List alerts for a subscription ───────────────────────────────────

@router.get("/{sub_id}/alerts", response_model=list[AlertResponse])
def list_alerts(sub_id: str, unread_only: bool = False):
    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM subscriptions WHERE id = ? AND user_id = 'default'", (sub_id,)
    ).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Subscription not found")

    where = "a.subscription_id = ?"
    params: list = [sub_id]
    if unread_only:
        where += " AND a.is_read = 0"

    rows = conn.execute(
        f"""SELECT a.*, j.company, j.title, j.location, j.platform, j.source_url,
                   j.apply_url, j.apply_url_status, j.posted_date, j.posted_age_hours,
                   j.jd_raw_text, j.track, j.experience_level, j.yoe_min, j.scrape_ts
            FROM alerts a
            JOIN jobs j ON a.job_id = j.id
            WHERE {where}
            ORDER BY a.created_at DESC
            LIMIT 200""",
        params,
    ).fetchall()
    conn.close()

    return [
        AlertResponse(
            id=r["id"],
            subscription_id=r["subscription_id"],
            job_id=r["job_id"],
            is_read=bool(r["is_read"]),
            created_at=r["created_at"],
            job=_build_job_response(r),
        )
        for r in rows
    ]


# ── Mark alerts as read ──────────────────────────────────────────────

@router.post("/{sub_id}/alerts/mark-read", status_code=204)
def mark_alerts_read(sub_id: str):
    conn = get_connection()
    conn.execute(
        "UPDATE alerts SET is_read = 1 WHERE subscription_id = ? AND is_read = 0",
        (sub_id,),
    )
    conn.commit()
    conn.close()


# ── Global alert endpoints (for nav badge) ───────────────────────────

from fastapi import APIRouter as _AR  # re-use

alerts_router = APIRouter(prefix="/v1/alerts", tags=["alerts"])


@alerts_router.get("/count")
def unread_alert_count():
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) as c FROM alerts WHERE user_id = 'default' AND is_read = 0"
    ).fetchone()["c"]
    conn.close()
    return {"unread_count": count}
