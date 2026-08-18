"""
SQLite access for the platform service.

DB path is read from the PLATFORM_DB_PATH env var at call time (not at
import time) so tests can point it at a throwaway file per test run.
Defaults to platform.db in the current working directory.
"""

from __future__ import annotations

import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crm_ids TEXT NOT NULL,          -- JSON array of source CRM ids merged into this row
    full_name TEXT,
    email TEXT,                     -- normalized: trimmed + lowercased
    phone TEXT,
    company TEXT,
    is_active INTEGER,              -- 0 or 1
    source_updated_at TEXT,         -- max updated_at seen from the CRM
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL        -- platform-side last write time
);

CREATE TABLE IF NOT EXISTS sync_quarantine (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crm_id TEXT,
    raw_json TEXT NOT NULL,
    reason TEXT NOT NULL,
    quarantined_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    created_count INTEGER DEFAULT 0,
    updated_count INTEGER DEFAULT 0,
    skipped_count INTEGER DEFAULT 0,
    cursor TEXT
);
"""


def db_path() -> str:
    return os.environ.get("PLATFORM_DB_PATH", "platform.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def reset_db() -> None:
    """Wipe all rows (used by tests). Keeps schema."""
    conn = get_connection()
    try:
        conn.executescript(
            "DELETE FROM customers; DELETE FROM sync_quarantine; DELETE FROM sync_runs;"
        )
        conn.commit()
    finally:
        conn.close()
