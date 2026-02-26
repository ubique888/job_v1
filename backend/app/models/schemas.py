from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Track(str, Enum):
    BACKEND = "Backend"
    FRONTEND = "Frontend"
    FULLSTACK = "Fullstack"
    DEVOPS = "DevOps"
    DATA = "Data"
    ML = "ML"
    AI_AGENT = "AI Agent"
    CONSULTING = "Consulting"


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
    track: Optional[Track] = None
    locations: Optional[list[str]] = None
    seniority: Optional[str] = None
    posted_within: Optional[PostedWithin] = None
    remote_only: Optional[bool] = None


class ProfileResponse(BaseModel):
    user_id: str
    track: Optional[str]
    locations_json: str
    seniority: Optional[str]
    posted_within: str
    remote_only: bool
    updated_at: str


class SearchRunCreate(BaseModel):
    track: Track
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
