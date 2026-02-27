import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ..database import get_connection
from ..discord_notifier import send_test_message
from ..models.schemas import ProfileResponse, ProfileUpdate

router = APIRouter(prefix="/v1/user", tags=["profile"])


def _row_to_response(row) -> dict:
    return dict(row) | {"remote_only": bool(row["remote_only"])}


@router.get("/profile", response_model=ProfileResponse)
def get_profile():
    conn = get_connection()
    row = conn.execute("SELECT * FROM user_profile WHERE user_id = 'default'").fetchone()
    conn.close()
    return _row_to_response(row)


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
    if body.discord_webhook_url is not None:
        updates.append("discord_webhook_url = ?")
        # Allow clearing by sending empty string
        params.append(body.discord_webhook_url if body.discord_webhook_url else None)

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
    return _row_to_response(row)


@router.post("/profile/test-discord")
async def test_discord_webhook():
    """Send a test message to the configured Discord webhook."""
    conn = get_connection()
    row = conn.execute(
        "SELECT discord_webhook_url FROM user_profile WHERE user_id = 'default'"
    ).fetchone()
    conn.close()

    url = row["discord_webhook_url"] if row else None
    if not url:
        raise HTTPException(status_code=400, detail="No Discord webhook URL configured")

    success = await send_test_message(url)
    if not success:
        raise HTTPException(status_code=502, detail="Failed to send test message to Discord")

    return {"status": "ok", "message": "Test message sent to Discord"}
