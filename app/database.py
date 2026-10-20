import sqlite3
from contextlib import contextmanager
from typing import Generator
from app.config import DATABASE_PATH

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('PATIENT', 'DOCTOR', 'ADMIN')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

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
    slot_id INTEGER NOT NULL,
    customer_name TEXT NOT NULL,
    notes TEXT,
    booked_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    user_id INTEGER,
    status TEXT NOT NULL DEFAULT 'CONFIRMED' CHECK(status IN ('CONFIRMED', 'COMPLETED', 'CANCELLED')),
    FOREIGN KEY (slot_id) REFERENCES slots(id) ON DELETE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
"""

INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_slots_date_booked ON slots (slot_date, is_booked);
CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings (user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_bookings_active_slot_id ON bookings (slot_id) WHERE status != 'CANCELLED';
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
        # 1. Create base tables
        conn.executescript(SCHEMA_SQL)

        # 2. Check if bookings has the partial unique index or needs migration
        cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='bookings'")
        row = cursor.fetchone()
        table_sql = row["sql"] if row else ""

        # If existing bookings table still has the old unconditional UNIQUE constraint on slot_id
        if "slot_id INTEGER NOT NULL UNIQUE" in table_sql or "UNIQUE (slot_id)" in table_sql:
            conn.execute("PRAGMA foreign_keys = OFF")

            # Detect available columns in old table
            col_cursor = conn.execute("PRAGMA table_info(bookings)")
            old_cols = [c["name"] for c in col_cursor.fetchall()]
            has_user_id = "user_id" in old_cols
            has_status = "status" in old_cols

            select_user_id = "user_id" if has_user_id else "NULL"
            select_status = "status" if has_status else "'CONFIRMED'"

            conn.execute("""
                CREATE TABLE IF NOT EXISTS bookings_v2 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slot_id INTEGER NOT NULL,
                    customer_name TEXT NOT NULL,
                    notes TEXT,
                    booked_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
                    user_id INTEGER,
                    status TEXT NOT NULL DEFAULT 'CONFIRMED' CHECK(status IN ('CONFIRMED', 'COMPLETED', 'CANCELLED')),
                    FOREIGN KEY (slot_id) REFERENCES slots(id) ON DELETE RESTRICT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            """)

            conn.execute(f"""
                INSERT INTO bookings_v2 (id, slot_id, customer_name, notes, booked_at, user_id, status)
                SELECT id, slot_id, customer_name, notes, booked_at, {select_user_id}, {select_status}
                FROM bookings
            """)
            conn.execute("DROP TABLE bookings")
            conn.execute("ALTER TABLE bookings_v2 RENAME TO bookings")
            conn.execute("PRAGMA foreign_keys = ON")
        else:
            # Ensure columns exist if not already migrated
            cursor = conn.execute("PRAGMA table_info(bookings)")
            columns = [c["name"] for c in cursor.fetchall()]
            if "user_id" not in columns:
                conn.execute("ALTER TABLE bookings ADD COLUMN user_id INTEGER REFERENCES users(id)")
            if "status" not in columns:
                conn.execute("ALTER TABLE bookings ADD COLUMN status TEXT NOT NULL DEFAULT 'CONFIRMED'")

        # 3. Create indexes including partial unique index
        conn.executescript(INDEXES_SQL)
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
