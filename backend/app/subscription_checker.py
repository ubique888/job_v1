"""Background subscription checker — polls ATS providers for new matching jobs."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from .database import get_connection
from .discord_notifier import send_discord_alert
from .location_matcher import matches_location
from .search_engine import execute_search_run

logger = logging.getLogger(__name__)


async def check_subscription(sub_id: str) -> int:
    """Check a single subscription for new matching jobs. Returns count of new alerts."""
    conn = get_connection()
    sub = conn.execute("SELECT * FROM subscriptions WHERE id = ?", (sub_id,)).fetchone()
    if not sub or not sub["is_active"]:
        conn.close()
        return 0

    track = sub["track"]
    exp_level = sub["experience_level"]  # may be None = any
    loc_filter = sub["location_filter"]  # may be None = any
    conn.close()

    # Create a background search run (reuses existing engine)
    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    conn.execute(
        "INSERT INTO search_runs (id, user_id, track, posted_within, state, started_at) VALUES (?, ?, ?, ?, ?, ?)",
        (run_id, "default", track, "24h", "pending", now),
    )
    conn.commit()
    conn.close()

    # Execute search across all providers
    await execute_search_run(
        run_id=run_id,
        user_id="default",
        track=track,
        posted_within="24h",
        provider_enabled={"greenhouse": True, "lever": True},
        limit_per_provider=50,
    )

    # Find newly stored jobs from this run that match subscription filters
    conn = get_connection()
    jobs = conn.execute(
        "SELECT id, title, location, experience_level FROM jobs WHERE run_id = ?",
        (run_id,),
    ).fetchall()

    alert_count = 0
    matched_jobs = []
    for job in jobs:
        # Filter by experience level if specified
        if exp_level and job["experience_level"] != exp_level:
            continue
        # Filter by location if specified
        if not matches_location(job["location"], loc_filter):
            continue

        # Create alert (INSERT OR IGNORE to skip duplicates via unique index)
        try:
            conn.execute(
                "INSERT OR IGNORE INTO alerts (id, user_id, subscription_id, job_id) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), "default", sub_id, job["id"]),
            )
            alert_count += 1
            matched_jobs.append(dict(job))
        except Exception:
            pass

    # Update last_checked_at
    conn.execute(
        "UPDATE subscriptions SET last_checked_at = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), sub_id),
    )
    conn.commit()

    # Send Discord notification if webhook is configured and there are new alerts
    if matched_jobs:
        webhook_row = conn.execute(
            "SELECT discord_webhook_url FROM user_profile WHERE user_id = 'default'"
        ).fetchone()
        webhook_url = webhook_row["discord_webhook_url"] if webhook_row else None
        if webhook_url:
            sub_dict = {
                "track": track,
                "experience_level": exp_level,
                "location_filter": loc_filter,
            }
            try:
                await send_discord_alert(webhook_url, matched_jobs, sub_dict)
            except Exception as e:
                logger.error("Discord notification failed for sub %s: %s", sub_id[:8], e)

    conn.close()

    return alert_count


async def run_subscription_loop():
    """Background loop that checks subscriptions on their configured interval.

    Runs every 60 seconds and checks each active subscription whose
    last_checked_at + interval_minutes has elapsed.
    """
    logger.info("Subscription checker started")

    while True:
        try:
            conn = get_connection()
            subs = conn.execute(
                "SELECT * FROM subscriptions WHERE user_id = 'default' AND is_active = 1"
            ).fetchall()
            conn.close()

            now = datetime.now(timezone.utc)

            for sub in subs:
                interval = sub["interval_minutes"] or 60
                last_checked = sub["last_checked_at"]

                if last_checked:
                    last_dt = datetime.fromisoformat(last_checked)
                    # Ensure timezone-aware comparison
                    if last_dt.tzinfo is None:
                        last_dt = last_dt.replace(tzinfo=timezone.utc)
                    elapsed_minutes = (now - last_dt).total_seconds() / 60
                    if elapsed_minutes < interval:
                        continue

                try:
                    count = await check_subscription(sub["id"])
                    if count > 0:
                        logger.info(
                            "Subscription %s (%s/%s/%s): %d new alerts",
                            sub["id"][:8],
                            sub["track"],
                            sub["experience_level"] or "any-level",
                            sub["location_filter"] or "any-location",
                            count,
                        )
                except Exception as e:
                    logger.error("Subscription %s check failed: %s", sub["id"][:8], e)

        except Exception as e:
            logger.error("Subscription loop error: %s", e)

        # Sleep 60 seconds between iterations
        await asyncio.sleep(60)
