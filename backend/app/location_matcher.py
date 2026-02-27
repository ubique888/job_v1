"""Location matching — server-side equivalent of frontend LOCATION_PATTERNS."""

from typing import Optional

LOCATION_PATTERNS: dict[str, list[str]] = {
    "New York": ["new york", "nyc", "brooklyn", "manhattan"],
    "Seattle": ["seattle", "bellevue", "redmond"],
    "Los Angeles": ["los angeles", "la,", "la ", "santa monica", "culver city", "venice, ca", "hollywood"],
    "San Francisco": ["san francisco", "sf,", "sf ", "bay area", "palo alto", "mountain view", "sunnyvale", "san jose", "san mateo", "menlo park", "redwood city", "cupertino", "santa clara"],
    "Boston": ["boston", "cambridge, ma", "somerville, ma", "waltham"],
    "London": ["london"],
    "Paris": ["paris"],
    "Remote": ["remote"],
}


def matches_location(job_location: Optional[str], location_filter: Optional[str]) -> bool:
    """Check if a job location matches a filter label. None/All = match everything."""
    if not location_filter or location_filter == "All":
        return True
    loc = (job_location or "").lower()
    if location_filter == "Other":
        return not any(
            any(p in loc for p in patterns)
            for patterns in LOCATION_PATTERNS.values()
        )
    patterns = LOCATION_PATTERNS.get(location_filter, [])
    return any(p in loc for p in patterns)
