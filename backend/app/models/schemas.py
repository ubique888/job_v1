from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


class Track(str, Enum):
    """Built-in tracks. Kept as reference; API accepts any string track name."""
    BACKEND = "Backend"
    FRONTEND = "Frontend"
    FULLSTACK = "Fullstack"
    DEVOPS = "DevOps"
    DATA = "Data"
    ML = "ML"
    AI_AGENT = "AI Agent"
    CONSULTING = "Consulting"
    PRODUCT_MANAGER = "Product Manager"


BUILTIN_TRACK_NAMES: set[str] = {t.value for t in Track}


class PostedWithin(str, Enum):
    H24 = "24h"
    H48 = "48h"
    D7 = "7d"
    D30 = "30d"


POSTED_WITHIN_HOURS = {
    PostedWithin.H24: 24,
    PostedWithin.H48: 48,
    PostedWithin.D7: 168,
    PostedWithin.D30: 720,
}


class Provider(str, Enum):
    GREENHOUSE = "greenhouse"
    LEVER = "lever"


class ApplyUrlStatus(str, Enum):
    DIRECT = "direct"
    DERIVED = "derived"
    UNKNOWN = "unknown"


class QueueStatus(str, Enum):
    BOOKMARKED = "bookmarked"
    IN_QUEUE = "in_queue"
    APPLIED = "applied"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ExperienceLevel(str, Enum):
    INTERN = "intern"
    ENTRY_LEVEL = "entry-level"
    HIGHER_LEVEL = "higher-level"


class LlmProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"


# --- Request / Response models ---

class SeedCreate(BaseModel):
    provider: Provider
    company: str = Field(..., min_length=1, max_length=200)
    board_url: str = Field(..., min_length=1)

    model_config = {"json_schema_extra": {"examples": [{"provider": "greenhouse", "company": "Stripe", "board_url": "https://boards.greenhouse.io/stripe"}]}}


class SeedResponse(BaseModel):
    id: str
    provider: Provider
    company: str
    board_url: str
    created_at: str


class ProfileUpdate(BaseModel):
    track: Optional[str] = None
    locations: Optional[list[str]] = None
    seniority: Optional[str] = None
    posted_within: Optional[PostedWithin] = None
    remote_only: Optional[bool] = None
    discord_webhook_url: Optional[str] = None
    llm_provider: Optional[LlmProvider] = None
    openai_api_key: Optional[str] = None


class ProfileResponse(BaseModel):
    user_id: str
    track: Optional[str]
    locations_json: str
    seniority: Optional[str]
    posted_within: str
    remote_only: bool
    discord_webhook_url: Optional[str] = None
    llm_provider: str = "ollama"
    openai_api_key_set: bool = False
    updated_at: str


class SearchRunCreate(BaseModel):
    track: str = Field(..., min_length=1, max_length=50)
    posted_within: PostedWithin = PostedWithin.D7
    provider_enabled: dict[str, bool] = Field(default_factory=lambda: {"greenhouse": True, "lever": True})
    limit_per_provider: int = Field(default=50, ge=1, le=200)


class SearchRunResponse(BaseModel):
    run_id: str
    state: str


class JobResponse(BaseModel):
    id: str
    company: str
    title: str
    location: Optional[str]
    platform: str
    source_url: str
    apply_url: Optional[str]
    apply_url_status: str
    posted_date: Optional[str]
    posted_age_hours: Optional[float]
    jd_raw_text: Optional[str]
    track: Optional[str]
    experience_level: Optional[str] = None
    yoe_min: Optional[int] = None
    scrape_ts: str
    evidence: list[dict] = []


class SearchRunDetailResponse(BaseModel):
    run_id: str
    state: str
    track: str
    posted_within: str
    started_at: str
    finished_at: Optional[str]
    stats: dict
    discovered_jobs: list[JobResponse]


class QueueItemCreate(BaseModel):
    job_id: str
    status: QueueStatus = QueueStatus.BOOKMARKED
    notes: str = ""


class QueueItemUpdate(BaseModel):
    status: Optional[QueueStatus] = None
    notes: Optional[str] = None


class QueueItemResponse(BaseModel):
    id: str
    job_id: str
    status: str
    notes: str
    created_at: str
    updated_at: str
    job: Optional[JobResponse] = None


# --- Subscription / Alert models ---

class SubscriptionCreate(BaseModel):
    track: str = Field(..., min_length=1, max_length=50)
    experience_level: Optional[ExperienceLevel] = None
    location_filter: Optional[str] = None
    interval_minutes: int = Field(default=60, ge=15, le=1440)


class SubscriptionUpdate(BaseModel):
    track: Optional[str] = Field(default=None, min_length=1, max_length=50)
    experience_level: Optional[ExperienceLevel] = None
    location_filter: Optional[str] = None
    interval_minutes: Optional[int] = Field(default=None, ge=15, le=1440)
    is_active: Optional[bool] = None


class SubscriptionResponse(BaseModel):
    id: str
    track: str
    experience_level: Optional[str]
    location_filter: Optional[str]
    is_active: bool
    interval_minutes: int
    last_checked_at: Optional[str]
    created_at: str
    updated_at: str
    unread_count: int = 0


class AlertResponse(BaseModel):
    id: str
    subscription_id: str
    job_id: str
    is_read: bool
    created_at: str
    job: Optional[JobResponse] = None


class SummaryResponse(BaseModel):
    job_id: str
    summary_text: str
    model_name: str
    created_at: str


# --- Custom Track models ---

class CustomTrackCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    keywords: list[str] = Field(..., min_length=1)

    @field_validator("name")
    @classmethod
    def name_not_builtin(cls, v: str) -> str:
        if v in BUILTIN_TRACK_NAMES or v.lower() in {t.lower() for t in BUILTIN_TRACK_NAMES}:
            raise ValueError(f"'{v}' is a built-in track and cannot be used as a custom track name")
        return v.strip()

    @field_validator("keywords")
    @classmethod
    def clean_keywords(cls, v: list[str]) -> list[str]:
        cleaned = [kw.strip().lower() for kw in v if kw.strip()]
        if not cleaned:
            raise ValueError("At least one non-empty keyword is required")
        return cleaned


class CustomTrackResponse(BaseModel):
    id: str
    name: str
    keywords: list[str]
    created_at: str
