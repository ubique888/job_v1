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


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS user_profile (
    user_id TEXT PRIMARY KEY DEFAULT 'default',
    track TEXT,
    locations_json TEXT DEFAULT '[]',
    seniority TEXT,
    posted_within TEXT DEFAULT '7d',
    remote_only INTEGER DEFAULT 0,
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

INSERT OR IGNORE INTO user_profile (user_id) VALUES ('default');
"""
