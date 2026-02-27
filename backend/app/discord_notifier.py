"""Discord webhook notifier — sends rich embeds when new job alerts are found."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

MAX_FIELDS_PER_EMBED = 10  # Discord limit is 25, but keep it readable


def _build_embeds(jobs: list[dict[str, Any]], subscription: dict[str, Any]) -> list[dict]:
    """Build Discord embed objects from matched jobs, batched into groups."""
    track = subscription.get("track", "?")
    level = subscription.get("experience_level") or "any level"
    location = subscription.get("location_filter") or "any location"

    embeds = []
    for i in range(0, len(jobs), MAX_FIELDS_PER_EMBED):
        batch = jobs[i : i + MAX_FIELDS_PER_EMBED]
        is_first = i == 0
        total = len(jobs)

        description_lines = []
        for j in batch:
            company = j.get("company", "Unknown")
            title = j.get("title", "Unknown Role")
            loc = j.get("location") or "Remote/Unknown"
            exp = j.get("experience_level") or "—"
            apply_url = j.get("apply_url") or j.get("source_url", "")
            if apply_url:
                description_lines.append(f"**{company}** — [{title}]({apply_url})\n{loc} · {exp}")
            else:
                description_lines.append(f"**{company}** — {title}\n{loc} · {exp}")

        embed: dict[str, Any] = {
            "color": 0x3FB950,  # green
            "description": "\n\n".join(description_lines),
        }

        if is_first:
            embed["title"] = f"New Job Alerts: {track} ({total} job{'s' if total != 1 else ''})"

        embed["footer"] = {
            "text": f"Track: {track} · Level: {level} · Location: {location}",
        }

        embeds.append(embed)

    return embeds


async def send_discord_alert(
    webhook_url: str,
    jobs: list[dict[str, Any]],
    subscription: dict[str, Any],
) -> bool:
    """Post job alerts to a Discord webhook. Returns True on success."""
    if not webhook_url or not jobs:
        return False

    embeds = _build_embeds(jobs, subscription)

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Discord allows max 10 embeds per message
            for i in range(0, len(embeds), 10):
                batch = embeds[i : i + 10]
                payload = {"embeds": batch}
                resp = await client.post(webhook_url, json=payload)
                if resp.status_code not in (200, 204):
                    logger.warning(
                        "Discord webhook returned %d: %s", resp.status_code, resp.text[:200]
                    )
                    return False
        return True
    except Exception as e:
        logger.error("Discord webhook failed: %s", e)
        return False


async def send_test_message(webhook_url: str) -> bool:
    """Send a test message to verify the webhook URL works."""
    if not webhook_url:
        return False

    payload = {
        "embeds": [
            {
                "title": "Job Search Autopilot — Test",
                "description": "Discord notifications are working! You'll receive alerts here when new matching jobs are found.",
                "color": 0x58A6FF,
                "footer": {"text": "Job Search Autopilot"},
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(webhook_url, json=payload)
            return resp.status_code in (200, 204)
    except Exception as e:
        logger.error("Discord test message failed: %s", e)
        return False
