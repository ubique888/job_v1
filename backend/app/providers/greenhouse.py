"""Greenhouse provider — fetches jobs from boards.greenhouse.io/{company}.

Greenhouse exposes a public JSON API at:
    GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs
    GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs/{job_id}

This avoids HTML scraping entirely and is the intended public integration path.
"""

import hashlib
import re
from datetime import datetime, timezone
from typing import Optional

import httpx

from .base import JobCard

# Map board_url → board_token
# e.g. "https://boards.greenhouse.io/stripe" → "stripe"
_BOARD_URL_PATTERN = re.compile(
    r"https?://boards\.greenhouse\.io/([^/?#]+)", re.IGNORECASE
)


def _extract_board_token(board_url: str) -> str:
    m = _BOARD_URL_PATTERN.search(board_url)
    if m:
        return m.group(1)
    # Fallback: treat the last path segment as the token
    return board_url.rstrip("/").rsplit("/", 1)[-1]


def _age_hours(updated_at_str: str) -> Optional[float]:
    """Compute hours since updated_at (ISO 8601 from Greenhouse API)."""
    try:
        dt = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        return round(delta.total_seconds() / 3600, 1)
    except Exception:
        return None


def _strip_html(html: str) -> str:
    """Minimal HTML tag stripping for JD content."""
    import html as html_mod
    text = html_mod.unescape(html)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class GreenhouseProvider:
    """Fetch jobs from Greenhouse public boards API."""

    BASE = "https://boards-api.greenhouse.io/v1/boards"

    async def search(
        self,
        board_url: str,
        company: str,
        track: str,
        posted_within: str,
        limit: int,
    ) -> list[JobCard]:
        token = _extract_board_token(board_url)
        list_url = f"{self.BASE}/{token}/jobs"

        cards: list[JobCard] = []

        async with httpx.AsyncClient(timeout=30) as client:
            # 1) Fetch job listing
            resp = await client.get(list_url, params={"content": "true"})
            if resp.status_code != 200:
                return cards

            data = resp.json()
            jobs_list = data.get("jobs", [])

            for job_data in jobs_list[:limit]:
                card = self._parse_job(job_data, company, token, board_url)
                cards.append(card)

        return cards

    def _parse_job(
        self, job_data: dict, company: str, token: str, board_url: str
    ) -> JobCard:
        job_id = job_data.get("id", "")
        title = job_data.get("title", "Unknown Title")

        # Location
        location_obj = job_data.get("location", {})
        location = location_obj.get("name") if location_obj else None

        # Source URL (the public board page for this job)
        source_url = f"https://boards.greenhouse.io/{token}/jobs/{job_id}"

        # Apply URL — Greenhouse provides an absolute_url
        absolute_url = job_data.get("absolute_url")
        apply_url = f"{absolute_url}#app" if absolute_url else None
        apply_url_status = "direct" if apply_url else "unknown"

        # Posted date
        updated_at = job_data.get("updated_at")
        posted_age = _age_hours(updated_at) if updated_at else None

        # JD content (HTML)
        content_raw = job_data.get("content", "")
        jd_text = _strip_html(content_raw) if content_raw else None

        # Evidence
        evidence: list[dict] = []
        if not apply_url:
            evidence.append({"type": "apply_url_unknown", "text": "No apply URL found in API response"})
        if not jd_text:
            evidence.append({"type": "jd_text_unavailable", "text": "No JD content in API response"})
        if not updated_at:
            evidence.append({"type": "posted_date_unknown", "text": "No updated_at in API response"})

        return JobCard(
            company=company,
            title=title,
            location=location,
            platform="greenhouse",
            source_url=source_url,
            apply_url=apply_url,
            apply_url_status=apply_url_status,
            posted_date=updated_at,
            posted_age_hours=posted_age,
            jd_raw_text=jd_text,
            evidence=evidence,
        )
