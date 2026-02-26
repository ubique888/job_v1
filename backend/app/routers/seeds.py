import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ..database import get_connection
from ..models.schemas import SeedCreate, SeedResponse

router = APIRouter(prefix="/v1/seeds", tags=["seeds"])


@router.get("", response_model=list[SeedResponse])
def list_seeds():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM seeds WHERE user_id = 'default' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("", response_model=SeedResponse, status_code=201)
def create_seed(body: SeedCreate):
    conn = get_connection()
    seed_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    conn.execute(
        "INSERT INTO seeds (id, user_id, provider, company, board_url, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (seed_id, "default", body.provider.value, body.company, body.board_url, now),
    )
    conn.commit()

    row = conn.execute("SELECT * FROM seeds WHERE id = ?", (seed_id,)).fetchone()
    conn.close()
    return dict(row)


@router.delete("/{seed_id}", status_code=204)
def delete_seed(seed_id: str):
    conn = get_connection()
    result = conn.execute("DELETE FROM seeds WHERE id = ? AND user_id = 'default'", (seed_id,))
    conn.commit()
    conn.close()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Seed not found")
