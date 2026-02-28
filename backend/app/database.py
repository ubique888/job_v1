import sqlite3
import os
from pathlib import Path

DB_PATH = os.environ.get("DB_PATH", str(Path(__file__).parent.parent / "data" / "jobs.db"))


def get_connection() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _migrate_db(conn: sqlite3.Connection):
    """Run incremental migrations. Safe to call repeatedly."""
    job_cols = {row[1] for row in conn.execute("PRAGMA table_info(jobs)").fetchall()}
    if "experience_level" not in job_cols:
        conn.execute("ALTER TABLE jobs ADD COLUMN experience_level TEXT DEFAULT 'entry-level'")
        conn.commit()

    if "yoe_min" not in job_cols:
        conn.execute("ALTER TABLE jobs ADD COLUMN yoe_min INTEGER")
        conn.commit()

    profile_cols = {row[1] for row in conn.execute("PRAGMA table_info(user_profile)").fetchall()}
    if "discord_webhook_url" not in profile_cols:
        conn.execute("ALTER TABLE user_profile ADD COLUMN discord_webhook_url TEXT")
        conn.commit()

    if "llm_provider" not in profile_cols:
        conn.execute("ALTER TABLE user_profile ADD COLUMN llm_provider TEXT DEFAULT 'ollama'")
        conn.execute("ALTER TABLE user_profile ADD COLUMN openai_api_key TEXT")
        conn.commit()

    # Ensure job_summaries table exists (for existing databases)
    existing_tables = {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    if "job_summaries" not in existing_tables:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS job_summaries (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL UNIQUE,
                summary_text TEXT NOT NULL,
                model_name TEXT NOT NULL DEFAULT 'llama3.2:3b',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(job_id) REFERENCES jobs(id)
            )
        """)
        conn.commit()

    # Ensure custom_tracks table exists (for existing databases)
    if "custom_tracks" not in existing_tables:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS custom_tracks (
                id TEXT PRIMARY KEY,
                user_id TEXT DEFAULT 'default',
                name TEXT NOT NULL,
                keywords_json TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(user_id, name)
            )
        """)
        conn.commit()


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    _migrate_db(conn)
    conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS user_profile (
    user_id TEXT PRIMARY KEY DEFAULT 'default',
    track TEXT,
    locations_json TEXT DEFAULT '[]',
    seniority TEXT,
    posted_within TEXT DEFAULT '7d',
    remote_only INTEGER DEFAULT 0,
    discord_webhook_url TEXT,
    llm_provider TEXT DEFAULT 'ollama',
    openai_api_key TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS seeds (
    id TEXT PRIMARY KEY,
    user_id TEXT DEFAULT 'default',
    provider TEXT NOT NULL CHECK(provider IN ('greenhouse', 'lever')),
    company TEXT NOT NULL,
    board_url TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS search_runs (
    id TEXT PRIMARY KEY,
    user_id TEXT DEFAULT 'default',
    track TEXT NOT NULL,
    posted_within TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending',
    started_at TEXT DEFAULT (datetime('now')),
    finished_at TEXT,
    stats_json TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    user_id TEXT DEFAULT 'default',
    run_id TEXT,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    location TEXT,
    platform TEXT NOT NULL,
    source_url TEXT NOT NULL,
    apply_url TEXT,
    apply_url_status TEXT NOT NULL DEFAULT 'unknown' CHECK(apply_url_status IN ('direct', 'derived', 'unknown')),
    posted_date TEXT,
    posted_age_hours REAL,
    jd_raw_text TEXT,
    jd_hash TEXT,
    track TEXT,
    experience_level TEXT DEFAULT 'entry-level',
    yoe_min INTEGER,
    scrape_ts TEXT DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(run_id) REFERENCES search_runs(id)
);

CREATE TABLE IF NOT EXISTS job_evidence (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    text TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS job_dedupe_index (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    company_norm TEXT NOT NULL,
    title_norm TEXT NOT NULL,
    location_norm TEXT NOT NULL,
    pk_hash TEXT NOT NULL UNIQUE,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS queue_items (
    id TEXT PRIMARY KEY,
    user_id TEXT DEFAULT 'default',
    job_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'bookmarked' CHECK(status IN ('bookmarked', 'in_queue', 'applied', 'rejected', 'archived')),
    notes TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id TEXT PRIMARY KEY,
    user_id TEXT DEFAULT 'default',
    track TEXT NOT NULL,
    experience_level TEXT,
    location_filter TEXT,
    is_active INTEGER DEFAULT 1,
    interval_minutes INTEGER DEFAULT 60,
    last_checked_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    user_id TEXT DEFAULT 'default',
    subscription_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(subscription_id) REFERENCES subscriptions(id),
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_alerts_sub_job
    ON alerts(subscription_id, job_id);

CREATE TABLE IF NOT EXISTS job_summaries (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL UNIQUE,
    summary_text TEXT NOT NULL,
    model_name TEXT NOT NULL DEFAULT 'llama3.2:3b',
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS custom_tracks (
    id TEXT PRIMARY KEY,
    user_id TEXT DEFAULT 'default',
    name TEXT NOT NULL,
    keywords_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, name)
);

INSERT OR IGNORE INTO user_profile (user_id) VALUES ('default');
"""
