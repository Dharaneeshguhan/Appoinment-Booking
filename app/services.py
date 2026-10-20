import sqlite3
from typing import List, Optional
from app.models import SlotCreate


class SlotNotFoundError(Exception):
    pass


class SlotAlreadyBookedError(Exception):
    pass


class SlotConflictError(Exception):
    pass


def list_slots(
    conn: sqlite3.Connection,
    slot_date: Optional[str] = None,
    available_only: bool = True
) -> List[dict]:
    query = "SELECT id, slot_date, start_time, end_time, is_booked, created_at FROM slots WHERE 1=1"
    params = []

    if available_only:
        query += " AND is_booked = 0"

    if slot_date:
        query += " AND slot_date = ?"
        params.append(slot_date)

    query += " ORDER BY slot_date ASC, start_time ASC"

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()
    return [
        {
            "id": row["id"],
            "slot_date": row["slot_date"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "is_booked": bool(row["is_booked"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def get_slot_by_id(conn: sqlite3.Connection, slot_id: int) -> Optional[dict]:
    cursor = conn.execute(
        "SELECT id, slot_date, start_time, end_time, is_booked, created_at FROM slots WHERE id = ?",
        (slot_id,)
    )
    row = cursor.fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "slot_date": row["slot_date"],
        "start_time": row["start_time"],
        "end_time": row["end_time"],
        "is_booked": bool(row["is_booked"]),
        "created_at": row["created_at"],
    }


def create_slot(conn: sqlite3.Connection, slot_data: SlotCreate) -> dict:
    conn.execute("BEGIN IMMEDIATE")
    try:
        cursor = conn.execute(
            """
            INSERT INTO slots (slot_date, start_time, end_time)
            VALUES (?, ?, ?)
            """,
            (slot_data.slot_date, slot_data.start_time, slot_data.end_time)
        )
        slot_id = cursor.lastrowid
        conn.execute("COMMIT")
        return get_slot_by_id(conn, slot_id)
    except sqlite3.IntegrityError:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.OperationalError:
            pass
        raise SlotConflictError(f"A slot already exists on {slot_data.slot_date} starting at {slot_data.start_time}.")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.OperationalError:
            pass
        raise


def book_slot(
    conn: sqlite3.Connection,
    slot_id: int,
    customer_name: str,
    notes: Optional[str] = None
) -> dict:
    """
    Atomically books a slot.
    Uses BEGIN IMMEDIATE to acquire a write lock immediately in SQLite,
    preventing any other process or thread from booking the same slot concurrently.
    Also backed by a UNIQUE(slot_id) constraint in the bookings table.
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        # 1. Check if the slot exists and is available
        cursor = conn.execute(
            "SELECT id, slot_date, start_time, end_time, is_booked, created_at FROM slots WHERE id = ?",
            (slot_id,)
        )
        slot_row = cursor.fetchone()

        if not slot_row:
            raise SlotNotFoundError(f"Appointment slot with ID {slot_id} does not exist.")

        if slot_row["is_booked"] != 0:
            raise SlotAlreadyBookedError(f"Appointment slot with ID {slot_id} has already been booked.")

        # 2. Mark the slot as booked
        # Conditional update to add extra resilience
        update_cursor = conn.execute(
            "UPDATE slots SET is_booked = 1 WHERE id = ? AND is_booked = 0",
            (slot_id,)
        )
        if update_cursor.rowcount == 0:
            raise SlotAlreadyBookedError(f"Appointment slot with ID {slot_id} was just claimed by another booking.")

        # 3. Create the booking entry
        insert_cursor = conn.execute(
            """
            INSERT INTO bookings (slot_id, customer_name, notes)
            VALUES (?, ?, ?)
            """,
            (slot_id, customer_name, notes)
        )
        booking_id = insert_cursor.lastrowid

        # 4. Fetch the created booking record
        cursor = conn.execute(
            "SELECT id, slot_id, customer_name, notes, booked_at FROM bookings WHERE id = ?",
            (booking_id,)
        )
        booking_row = cursor.fetchone()

        conn.execute("COMMIT")

        slot_details = {
            "id": slot_row["id"],
            "slot_date": slot_row["slot_date"],
            "start_time": slot_row["start_time"],
            "end_time": slot_row["end_time"],
            "is_booked": True,
            "created_at": slot_row["created_at"],
        }

        return {
            "id": booking_row["id"],
            "slot_id": booking_row["slot_id"],
            "customer_name": booking_row["customer_name"],
            "notes": booking_row["notes"],
            "booked_at": booking_row["booked_at"],
            "slot": slot_details,
        }

    except (SlotNotFoundError, SlotAlreadyBookedError):
        try:
            conn.execute("ROLLBACK")
        except sqlite3.OperationalError:
            pass
        raise
    except sqlite3.IntegrityError:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.OperationalError:
            pass
        raise SlotAlreadyBookedError(f"Appointment slot with ID {slot_id} has already been booked.")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.OperationalError:
            pass
        raise


def get_booking_by_id(conn: sqlite3.Connection, booking_id: int) -> Optional[dict]:
    cursor = conn.execute(
        """
        SELECT b.id, b.slot_id, b.customer_name, b.notes, b.booked_at,
               s.slot_date, s.start_time, s.end_time, s.is_booked, s.created_at
        FROM bookings b
        JOIN slots s ON b.slot_id = s.id
        WHERE b.id = ?
        """,
        (booking_id,)
    )
    row = cursor.fetchone()
    if not row:
        return None

    return {
        "id": row["id"],
        "slot_id": row["slot_id"],
        "customer_name": row["customer_name"],
        "notes": row["notes"],
        "booked_at": row["booked_at"],
        "slot": {
            "id": row["slot_id"],
            "slot_date": row["slot_date"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "is_booked": bool(row["is_booked"]),
            "created_at": row["created_at"],
        }
    }


def list_bookings(conn: sqlite3.Connection) -> List[dict]:
    cursor = conn.execute(
        """
        SELECT b.id, b.slot_id, b.customer_name, b.notes, b.booked_at,
               s.slot_date, s.start_time, s.end_time, s.is_booked, s.created_at
        FROM bookings b
        JOIN slots s ON b.slot_id = s.id
        ORDER BY b.booked_at DESC
        """
    )
    rows = cursor.fetchall()
    return [
        {
            "id": row["id"],
            "slot_id": row["slot_id"],
            "customer_name": row["customer_name"],
            "notes": row["notes"],
            "booked_at": row["booked_at"],
            "slot": {
                "id": row["slot_id"],
                "slot_date": row["slot_date"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "is_booked": bool(row["is_booked"]),
                "created_at": row["created_at"],
            }
        }
        for row in rows
    ]
