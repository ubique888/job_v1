import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ..database import get_connection
from ..discord_notifier import send_test_message
from ..models.schemas import ProfileResponse, ProfileUpdate
from ..summarizer import check_openai_health

router = APIRouter(prefix="/v1/user", tags=["profile"])


def _row_to_response(row) -> dict:
    d = dict(row)
    d["remote_only"] = bool(row["remote_only"])
    d["llm_provider"] = row["llm_provider"] or "ollama"
    d["openai_api_key_set"] = bool(row["openai_api_key"])
    # Never expose the raw API key
    d.pop("openai_api_key", None)
    return d


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
        params.append(body.track)
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
    if body.llm_provider is not None:
        updates.append("llm_provider = ?")
        params.append(body.llm_provider.value)
    if body.openai_api_key is not None:
        updates.append("openai_api_key = ?")
        # Allow clearing by sending empty string
        params.append(body.openai_api_key if body.openai_api_key else None)

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


@router.post("/profile/test-openai")
async def test_openai_key():
    """Verify the configured OpenAI API key works."""
    conn = get_connection()
    row = conn.execute(
        "SELECT openai_api_key FROM user_profile WHERE user_id = 'default'"
    ).fetchone()
    conn.close()

    key = row["openai_api_key"] if row else None
    if not key:
        raise HTTPException(status_code=400, detail="No OpenAI API key configured")

    success = await check_openai_health(key)
    if not success:
        raise HTTPException(
            status_code=502,
            detail="OpenAI API key is invalid or the API is unreachable",
        )

    return {"status": "ok", "message": "OpenAI API key is valid"}
