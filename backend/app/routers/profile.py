import json
from datetime import datetime, timezone

from fastapi import APIRouter

from ..database import get_connection
from ..models.schemas import ProfileResponse, ProfileUpdate

router = APIRouter(prefix="/v1/user", tags=["profile"])


@router.get("/profile", response_model=ProfileResponse)
def get_profile():
    conn = get_connection()
    row = conn.execute("SELECT * FROM user_profile WHERE user_id = 'default'").fetchone()
    conn.close()
    return dict(row) | {"remote_only": bool(row["remote_only"])}


@router.put("/profile", response_model=ProfileResponse)
def update_profile(body: ProfileUpdate):
    conn = get_connection()
    updates = []
    params = []

    if body.track is not None:
        updates.append("track = ?")
        params.append(body.track.value)
    if body.locations is not None:
        updates.append("locations_json = ?")
        params.append(json.dumps(body.locations))
    if body.seniority is not None:
        updates.append("seniority = ?")
        params.append(body.seniority)
    if body.posted_within is not None:
        updates.append("posted_within = ?")
        params.append(body.posted_within.value)
    if body.remote_only is not None:
        updates.append("remote_only = ?")
        params.append(int(body.remote_only))

    if updates:
        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        params.append("default")
        conn.execute(
            f"UPDATE user_profile SET {', '.join(updates)} WHERE user_id = ?",
            params,
        )
        conn.commit()

    row = conn.execute("SELECT * FROM user_profile WHERE user_id = 'default'").fetchone()
    conn.close()
    return dict(row) | {"remote_only": bool(row["remote_only"])}
