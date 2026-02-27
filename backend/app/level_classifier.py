"""Experience-level classification — tags jobs as intern, entry-level, or higher-level.

Uses a two-pass approach:
  1. Title keywords (high confidence — "Senior", "Intern", "Junior" in title)
  2. YOE regex extraction from JD body (fills the gap for ambiguous titles)
  3. JD body keyword fallback
"""

import re
from typing import Optional

# ── YOE regex patterns ──────────────────────────────────────────────────
# Each pattern captures the *minimum* years number as group 1.

YOE_PATTERNS: list[re.Pattern] = [
    re.compile(r"(\d+)\s*\+\s*years?", re.IGNORECASE),
    re.compile(r"(\d+)\s*[-–—]\s*\d+\s*years?", re.IGNORECASE),
    re.compile(r"(\d+)\s+to\s+\d+\s+years?", re.IGNORECASE),
    re.compile(r"minimum\s+(?:of\s+)?(\d+)\s+years?", re.IGNORECASE),
    re.compile(r"at\s+least\s+(\d+)\s+years?", re.IGNORECASE),
    re.compile(r"(\d+)\s+years?['\u2019]?\s+(?:of\s+)?experience", re.IGNORECASE),
    re.compile(r"(\d+)\s+years?\s+or\s+more", re.IGNORECASE),
]


def extract_yoe_min(text: str) -> Optional[int]:
    """Extract minimum years-of-experience from JD text.

    Finds all YOE patterns in the text and returns the smallest value found.
    Returns None if no pattern is matched.
    """
    if not text:
        return None

    matches: list[int] = []
    for pattern in YOE_PATTERNS:
        for m in pattern.finditer(text):
            val = int(m.group(1))
            if 0 <= val <= 30:  # sanity bound — ignore "100+ years of innovation"
                matches.append(val)

    return min(matches) if matches else None


# ── Keyword lists (title-focused) ───────────────────────────────────────
# Matched via case-insensitive substring against lowered text.
# YOE-related strings removed — handled by regex now.

INTERN_KEYWORDS: list[str] = [
    "intern ", "internship", "interns ",
    "co-op", "coop ",
    "summer analyst", "summer associate",
    "working student", "student worker",
    "apprentice", "apprenticeship",
    "placement year", "industrial placement",
    "trainee",
]

ENTRY_LEVEL_KEYWORDS: list[str] = [
    "entry level", "entry-level", "entrylevel",
    "junior", "jr ", "jr.",
    "new grad", "new graduate", "recent graduate",
    "associate engineer", "associate developer",
    "associate software",
    "software engineer i ", "software engineer i,",
    "engineer i ", "engineer i,",
    "developer i ", "developer i,",
    "level 1", "level i ",
    "early career", "early-career",
    "rotational program", "rotation program",
    "graduate program", "graduate scheme",
]

HIGHER_LEVEL_KEYWORDS: list[str] = [
    "senior", "sr ", "sr.",
    "staff", "principal", "distinguished",
    "lead ", "lead,", "tech lead",
    "manager", "director", "head of",
    "vp ", "vice president",
    "architect",
    " iii", " iv", " ii",
    "level 3", "level 4", "level 5",
]


def classify_level(title: str, jd_text: Optional[str] = None) -> tuple[str, Optional[int]]:
    """Classify a job into intern, entry-level, or higher-level.

    Returns (experience_level, yoe_min) tuple.

    Priority:
      1. Title keywords — highest confidence
      2. YOE from JD body — resolves ambiguous titles
      3. JD body keywords — fallback
      4. Default: entry-level
    """
    title_lower = " " + title.lower() + " "
    yoe_min = extract_yoe_min(jd_text) if jd_text else None

    # Pass 1: title keywords (most reliable signal)
    if any(kw in title_lower for kw in INTERN_KEYWORDS):
        return ("intern", yoe_min)
    if any(kw in title_lower for kw in HIGHER_LEVEL_KEYWORDS):
        return ("higher-level", yoe_min)
    if any(kw in title_lower for kw in ENTRY_LEVEL_KEYWORDS):
        return ("entry-level", yoe_min)

    # Pass 2: YOE-based classification (for ambiguous titles like "Software Engineer")
    if yoe_min is not None:
        if yoe_min >= 5:
            return ("higher-level", yoe_min)
        # 0-4 years → entry-level
        return ("entry-level", yoe_min)

    # Pass 3: JD body keyword fallback
    if jd_text:
        body_lower = jd_text.lower()
        if any(kw in body_lower for kw in INTERN_KEYWORDS):
            return ("intern", yoe_min)
        if any(kw in body_lower for kw in HIGHER_LEVEL_KEYWORDS):
            return ("higher-level", yoe_min)
        if any(kw in body_lower for kw in ENTRY_LEVEL_KEYWORDS):
            return ("entry-level", yoe_min)

    # Default
    return ("entry-level", yoe_min)
