"""Lever provider — fetches jobs from jobs.lever.co/{company}.

Lever exposes a public JSON API at:
    GET https://api.lever.co/v0/postings/{company}
    GET https://api.lever.co/v0/postings/{company}/{posting_id}
"""

import re
from datetime import datetime, timezone
from typing import Optional

import httpx

from .base import JobCard

_LEVER_URL_PATTERN = re.compile(
    r"https?://jobs\.lever\.co/([^/?#]+)", re.IGNORECASE
)


def _extract_company_slug(board_url: str) -> str:
    m = _LEVER_URL_PATTERN.search(board_url)
    if m:
        return m.group(1)
    return board_url.rstrip("/").rsplit("/", 1)[-1]


def _age_hours(created_at_ms: int) -> Optional[float]:
    try:
        dt = datetime.fromtimestamp(created_at_ms / 1000, tz=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        return round(delta.total_seconds() / 3600, 1)
    except Exception:
        return None


def _strip_html(html: str) -> str:
    import html as html_mod
    text = html_mod.unescape(html)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class LeverProvider:
    """Fetch jobs from Lever public postings API."""

    BASE = "https://api.lever.co/v0/postings"

    async def search(
        self,
        board_url: str,
        company: str,
        track: str,
        posted_within: str,
        limit: int,
    ) -> list[JobCard]:
        slug = _extract_company_slug(board_url)
        list_url = f"{self.BASE}/{slug}"

        cards: list[JobCard] = []

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(list_url, params={"mode": "json"})
            if resp.status_code != 200:
                return cards

            jobs_list = resp.json()
            if not isinstance(jobs_list, list):
                return cards

            for job_data in jobs_list[:limit]:
                card = self._parse_job(job_data, company, slug)
                cards.append(card)

        return cards

    def _parse_job(self, job_data: dict, company: str, slug: str) -> JobCard:
        posting_id = job_data.get("id", "")
        title = job_data.get("text", "Unknown Title")

        # Location
        categories = job_data.get("categories", {})
        location = categories.get("location") if categories else None

        # Source URL
        hosted_url = job_data.get("hostedUrl", "")
        source_url = hosted_url or f"https://jobs.lever.co/{slug}/{posting_id}"

        # Apply URL — Lever provides applyUrl
        apply_url = job_data.get("applyUrl")
        apply_url_status = "direct" if apply_url else "unknown"

        # Posted date (createdAt is a Unix timestamp in ms)
        created_at_ms = job_data.get("createdAt")
        posted_date = None
        posted_age = None
        if created_at_ms:
            try:
                dt = datetime.fromtimestamp(created_at_ms / 1000, tz=timezone.utc)
                posted_date = dt.isoformat()
                posted_age = _age_hours(created_at_ms)
            except Exception:
                pass

        # JD content
        description_plain = job_data.get("descriptionPlain", "")
        desc_html = job_data.get("description", "")
        jd_text = description_plain if description_plain else (_strip_html(desc_html) if desc_html else None)

        # Build additional lists text
        lists_data = job_data.get("lists", [])
        if lists_data and jd_text:
            for lst in lists_data:
                header = lst.get("text", "")
                items = lst.get("content", "")
                if header or items:
                    jd_text += f"\n\n{header}\n{_strip_html(items)}"

        # Evidence
        evidence: list[dict] = []
        if not apply_url:
            evidence.append({"type": "apply_url_unknown", "text": "No applyUrl in API response"})
        if not jd_text:
            evidence.append({"type": "jd_text_unavailable", "text": "No description in API response"})
        if not created_at_ms:
            evidence.append({"type": "posted_date_unknown", "text": "No createdAt in API response"})

        return JobCard(
            company=company,
            title=title,
            location=location,
            platform="lever",
            source_url=source_url,
            apply_url=apply_url,
            apply_url_status=apply_url_status,
            posted_date=posted_date,
            posted_age_hours=posted_age,
            jd_raw_text=jd_text,
            evidence=evidence,
        )
