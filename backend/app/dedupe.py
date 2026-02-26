"""Deduplication and normalization utilities."""

import hashlib
import re
import unicodedata

ABBREVIATIONS = {
    "nyc": "new york city",
    "sf": "san francisco",
    "la": "los angeles",
    "dc": "washington dc",
    "phx": "phoenix",
    "atl": "atlanta",
    "chi": "chicago",
    "bos": "boston",
    "sea": "seattle",
    "pdx": "portland",
    "aus": "austin",
    "den": "denver",
    "sr": "senior",
    "jr": "junior",
    "mgr": "manager",
    "eng": "engineer",
    "dev": "developer",
    "swe": "software engineer",
}


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    # Remove punctuation except spaces
    text = re.sub(r"[^\w\s]", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Apply abbreviation mapping
    words = text.split()
    words = [ABBREVIATIONS.get(w, w) for w in words]
    return " ".join(words)


def compute_pk_hash(company: str, title: str, location: str, track: str = "") -> str:
    company_norm = normalize_text(company)
    title_norm = normalize_text(title)
    location_norm = normalize_text(location or "")
    track_norm = track.lower().strip()
    key = f"{company_norm}|{title_norm}|{location_norm}|{track_norm}"
    return hashlib.sha256(key.encode()).hexdigest()[:32]
