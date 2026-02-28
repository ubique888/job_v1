"""Track keyword matching — filters jobs by role track (Backend, DevOps, etc.)."""

import json
from .database import get_connection

# Keywords are matched against lowercased title + JD text.
# Order doesn't matter. Matching is substring-based.
TRACK_KEYWORDS: dict[str, list[str]] = {
    "Backend": [
        "backend", "back-end", "back end",
        "server-side", "server side",
        "api developer", "api engineer",
        "python developer", "python engineer",
        "java developer", "java engineer",
        "golang", "go developer", "go engineer",
        "rust developer", "rust engineer",
        "node.js", "nodejs",
        "django", "flask", "spring boot", "spring",
        "microservices", "distributed systems",
        "backend engineer", "backend developer",
        "software engineer, backend",
        "software developer, backend",
    ],
    "Frontend": [
        "frontend", "front-end", "front end",
        "react developer", "react engineer",
        "vue", "angular",
        "ui engineer", "ui developer",
        "ux engineer",
        "web developer", "web engineer",
        "javascript developer", "javascript engineer",
        "typescript developer", "typescript engineer",
        "frontend engineer", "frontend developer",
        "software engineer, frontend",
        "software engineer, web",
    ],
    "Fullstack": [
        "fullstack", "full-stack", "full stack",
        "software engineer, fullstack",
    ],
    "DevOps": [
        "devops", "dev-ops", "dev ops",
        "infrastructure engineer", "infrastructure developer",
        "sre", "site reliability",
        "platform engineer", "platform engineering",
        "kubernetes", "k8s",
        "docker",
        "terraform",
        "ansible",
        "ci/cd", "cicd", "ci cd",
        "cloud engineer", "cloud infrastructure",
        "systems engineer", "systems administrator",
        "linux engineer", "linux administrator",
        "deployment engineer",
        "release engineer",
        "network engineer",
        "security engineer",
    ],
    "Data": [
        "data engineer", "data developer",
        "data analyst", "data analytics",
        "data science", "data scientist",
        "analytics engineer",
        "etl", "data pipeline",
        "data warehouse", "data modeling",
        "bigquery", "snowflake", "redshift",
        "spark", "dbt",
        "business intelligence", "bi engineer",
        "bi developer", "bi analyst",
    ],
    "ML": [
        "machine learning", "ml engineer", "ml developer",
        "deep learning",
        "artificial intelligence", "ai engineer", "ai developer",
        "ai/ml",
        "nlp", "natural language processing",
        "computer vision",
        "model training",
        "pytorch", "tensorflow",
        "research scientist",
        "applied scientist",
    ],
    "AI Agent": [
        "ai agent", "ai agents",
        "agentic", "agentic ai",
        "autonomous agent",
        "langchain", "langgraph",
        "llm engineer", "llm developer",
        "large language model",
        "prompt engineer", "prompt engineering",
        "generative ai", "genai", "gen ai",
        "conversational ai",
        "chatbot", "chat bot",
        "rag ", "retrieval augmented",
        "llmops", "llm ops",
        "ai platform",
        "foundation model",
        "ai application", "ai product",
        "copilot",
        "openai", "anthropic",
    ],
    "Consulting": [
        "consultant", "consulting",
        "advisory", "advisor",
        "solutions architect", "solution architect",
        "solutions engineer", "solution engineer",
        "technical account manager",
        "customer engineer",
        "engagement manager",
        "professional services",
        "implementation engineer",
        "implementation consultant",
        "technical consultant",
        "management consultant",
        "strategy consultant",
        "technology consultant",
        "client engineer",
        "client solutions",
        "partner engineer",
        "pre-sales engineer", "presales",
    ],
    "Product Manager": [
        "product manager", "product management",
        "product owner", "product lead",
        "senior product manager", "group product manager",
        "associate product manager", "apm",
        "technical product manager", "tpm",
        "product director",
        "product strategist", "product strategy",
        "product analyst",
        "product operations", "product ops",
        "growth product manager",
        "platform product manager",
        "product marketing manager",
    ],
}


def _load_custom_tracks(user_id: str = "default") -> dict[str, list[str]]:
    """Load custom tracks from the database."""
    try:
        conn = get_connection()
        rows = conn.execute(
            "SELECT name, keywords_json FROM custom_tracks WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        conn.close()
        result = {}
        for row in rows:
            result[row["name"]] = json.loads(row["keywords_json"])
        return result
    except Exception:
        return {}


def get_all_keywords(user_id: str = "default") -> dict[str, list[str]]:
    """Return merged dict of built-in + custom track keywords."""
    merged = dict(TRACK_KEYWORDS)
    custom = _load_custom_tracks(user_id)
    merged.update(custom)
    return merged


def get_all_track_names(user_id: str = "default") -> list[str]:
    """Return ordered list of all track names (built-in first, then custom)."""
    builtin = list(TRACK_KEYWORDS.keys())
    custom = _load_custom_tracks(user_id)
    custom_names = [n for n in custom if n not in TRACK_KEYWORDS]
    return builtin + sorted(custom_names)


def matches_track(title: str, jd_text: str | None, track: str) -> bool:
    """Check if a job matches the given track based on title and JD keywords."""
    all_keywords = get_all_keywords()
    keywords = all_keywords.get(track)
    if keywords is None:
        return True  # Unknown track — don't filter

    searchable = title.lower()
    if jd_text:
        searchable += " " + jd_text.lower()

    return any(kw in searchable for kw in keywords)
