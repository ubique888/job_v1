"""Search engine — orchestrates provider fetching, dedup, and storage."""

import json
import uuid
from datetime import datetime, timezone

from .database import get_connection
from .dedupe import compute_pk_hash, normalize_text
from .models.schemas import POSTED_WITHIN_HOURS, PostedWithin
from .providers.base import JobCard
from .providers.greenhouse import GreenhouseProvider
from .providers.lever import LeverProvider
from .level_classifier import classify_level
from .track_matcher import matches_track

PROVIDERS = {
    "greenhouse": GreenhouseProvider(),
    "lever": LeverProvider(),
}


async def execute_search_run(
    run_id: str,
    user_id: str,
    track: str,
    posted_within: str,
    provider_enabled: dict[str, bool],
    limit_per_provider: int,
) -> dict:
    """Run a search across all enabled providers using seeds, store results."""
    conn = get_connection()

    # Mark run as running
    conn.execute(
        "UPDATE search_runs SET state = 'running', started_at = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), run_id),
    )
    conn.commit()

    # Fetch seeds for this user
    seeds = conn.execute(
        "SELECT * FROM seeds WHERE user_id = ?", (user_id,)
    ).fetchall()

    all_cards: list[JobCard] = []
    errors: list[str] = []

    for seed in seeds:
        provider_name = seed["provider"]
        if not provider_enabled.get(provider_name, False):
            continue

        provider = PROVIDERS.get(provider_name)
        if not provider:
            continue

        try:
            cards = await provider.search(
                board_url=seed["board_url"],
                company=seed["company"],
                track=track,
                posted_within=posted_within,
                limit=limit_per_provider,
            )
            all_cards.extend(cards)
        except Exception as e:
            errors.append(f"{provider_name}/{seed['company']}: {str(e)}")

    # Filter by track keywords
    matched_cards = [c for c in all_cards if matches_track(c.title, c.jd_raw_text, track)]

    # Filter by posted_within time window
    posted_within_hours = POSTED_WITHIN_HOURS.get(PostedWithin(posted_within))
    if posted_within_hours is not None:
        matched_cards = [
            c for c in matched_cards
            if c.posted_age_hours is None or c.posted_age_hours <= posted_within_hours
        ]

    # Store jobs with dedup
    stored_count = 0
    skipped_count = 0

    for card in matched_cards:
        pk_hash = compute_pk_hash(card.company, card.title, card.location or "", track)

        # Check dedup
        existing = conn.execute(
            "SELECT id FROM job_dedupe_index WHERE pk_hash = ?", (pk_hash,)
        ).fetchone()

        if existing:
            skipped_count += 1
            continue

        job_id = str(uuid.uuid4())
        experience_level, yoe_min = classify_level(card.title, card.jd_raw_text)

        conn.execute(
            """INSERT INTO jobs (id, user_id, run_id, company, title, location, platform,
               source_url, apply_url, apply_url_status, posted_date, posted_age_hours,
               jd_raw_text, jd_hash, track, experience_level, yoe_min, scrape_ts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                job_id, user_id, run_id, card.company, card.title, card.location,
                card.platform, card.source_url, card.apply_url, card.apply_url_status,
                card.posted_date, card.posted_age_hours,
                card.jd_raw_text,
                None,  # jd_hash
                track,
                experience_level,
                yoe_min,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        # Dedupe index
        conn.execute(
            """INSERT INTO job_dedupe_index (id, job_id, company_norm, title_norm, location_norm, pk_hash)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()), job_id,
                normalize_text(card.company),
                normalize_text(card.title),
                normalize_text(card.location or ""),
                pk_hash,
            ),
        )

        # Evidence rows
        for ev in card.evidence:
            conn.execute(
                "INSERT INTO job_evidence (id, job_id, evidence_type, text) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), job_id, ev["type"], ev.get("text", "")),
            )

        stored_count += 1

    # Mark run complete
    stats = {
        "total_fetched": len(all_cards),
        "matched_track": len(matched_cards),
        "stored": stored_count,
        "skipped_dupes": skipped_count,
        "errors": errors,
    }
    conn.execute(
        "UPDATE search_runs SET state = 'completed', finished_at = ?, stats_json = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), json.dumps(stats), run_id),
    )
    conn.commit()
    conn.close()

    return stats
