"""Track keyword matching — filters jobs by role track (Backend, DevOps, etc.)."""

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
}


def matches_track(title: str, jd_text: str | None, track: str) -> bool:
    """Check if a job matches the given track based on title and JD keywords."""
    keywords = TRACK_KEYWORDS.get(track)
    if keywords is None:
        return True  # Unknown track — don't filter

    searchable = title.lower()
    if jd_text:
        searchable += " " + jd_text.lower()

    return any(kw in searchable for kw in keywords)
