import sqlite3
from contextlib import contextmanager
from typing import Generator
from app.config import DATABASE_PATH

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_date TEXT NOT NULL,         -- Format: YYYY-MM-DD
    start_time TEXT NOT NULL,        -- Format: HH:MM
    end_time TEXT NOT NULL,          -- Format: HH:MM
    is_booked INTEGER NOT NULL DEFAULT 0, -- 0 = available, 1 = booked
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    CONSTRAINT uq_slot_time UNIQUE (slot_date, start_time)
);

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id INTEGER NOT NULL UNIQUE, -- 1:1 relationship guarantees no double booking
    customer_name TEXT NOT NULL,
    notes TEXT,
    booked_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    FOREIGN KEY (slot_id) REFERENCES slots(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_slots_date_booked ON slots (slot_date, is_booked);
CREATE INDEX IF NOT EXISTS idx_bookings_slot_id ON bookings (slot_id);
"""

def get_connection(db_path: str = None) -> sqlite3.Connection:
    target_path = db_path if db_path is not None else DATABASE_PATH
    conn = sqlite3.connect(
        target_path,
        timeout=20.0,
        check_same_thread=False,
        isolation_level=None  # Enable autocommit mode so we control transactions explicitly
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    if target_path != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def init_db(db_path: str = None) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
    finally:
        conn.close()

@contextmanager
def get_db_context(db_path: str = None) -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()

def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency for obtaining a database connection."""
    with get_db_context() as conn:
        yield conn
