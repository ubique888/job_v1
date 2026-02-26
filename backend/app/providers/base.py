from dataclasses import dataclass, field
from typing import Optional, Protocol


@dataclass
class JobCard:
    company: str
    title: str
    location: Optional[str]
    platform: str
    source_url: str
    apply_url: Optional[str]
    apply_url_status: str  # direct | derived | unknown
    posted_date: Optional[str]
    posted_age_hours: Optional[float]
    jd_raw_text: Optional[str]
    evidence: list[dict] = field(default_factory=list)


class IJobSourceProvider(Protocol):
    async def search(
        self,
        board_url: str,
        company: str,
        track: str,
        posted_within: str,
        limit: int,
    ) -> list[JobCard]: ...
