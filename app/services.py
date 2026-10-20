import sqlite3
from typing import List, Optional
from app.models import SlotCreate, BookingStatus
from app.auth import hash_password, verify_password


class SlotNotFoundError(Exception):
    pass


class SlotAlreadyBookedError(Exception):
    pass


class SlotConflictError(Exception):
    pass


class BookingNotFoundError(Exception):
    pass


class ForbiddenActionError(Exception):
    pass


class UserConflictError(Exception):
    pass


# --- User Services ---

def create_user(
    conn: sqlite3.Connection,
    email: str,
    full_name: str,
    password: str,
    role: str = "PATIENT"
) -> dict:
    pwd_hash = hash_password(password)
    try:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.execute(
            """
            INSERT INTO users (email, full_name, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            (email.strip().lower(), full_name.strip(), pwd_hash, role)
        )
        user_id = cursor.lastrowid
        conn.execute("COMMIT")

        return get_user_by_id(conn, user_id)
    except sqlite3.IntegrityError:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.OperationalError:
            pass
        raise UserConflictError(f"A user with email '{email}' already exists.")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.OperationalError:
            pass
        raise


def authenticate_user(conn: sqlite3.Connection, email: str, password: str) -> Optional[dict]:
    cursor = conn.execute(
        "SELECT id, email, full_name, password_hash, role, is_active, created_at FROM users WHERE email = ?",
        (email.strip().lower(),)
    )
    row = cursor.fetchone()
    if not row:
        return None

    if not verify_password(password, row["password_hash"]):
        return None

    return {
        "id": row["id"],
        "email": row["email"],
        "full_name": row["full_name"],
        "role": row["role"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
    }


def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> Optional[dict]:
    cursor = conn.execute(
        "SELECT id, email, full_name, role, is_active, created_at FROM users WHERE id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "email": row["email"],
        "full_name": row["full_name"],
        "role": row["role"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
    }


def list_users(conn: sqlite3.Connection) -> List[dict]:
    cursor = conn.execute(
        "SELECT id, email, full_name, role, is_active, created_at FROM users ORDER BY created_at DESC"
    )
    rows = cursor.fetchall()
    return [
        {
            "id": row["id"],
            "email": row["email"],
            "full_name": row["full_name"],
            "role": row["role"],
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def update_user_status(conn: sqlite3.Connection, user_id: int, is_active: bool) -> dict:
    conn.execute("BEGIN IMMEDIATE")
    try:
        cursor = conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if is_active else 0, user_id))
        if cursor.rowcount == 0:
            raise UserConflictError(f"User with ID {user_id} not found.")
        conn.execute("COMMIT")
        return get_user_by_id(conn, user_id)
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.OperationalError:
            pass
        raise


# --- Slot Services ---

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


def delete_slot(conn: sqlite3.Connection, slot_id: int) -> bool:
    conn.execute("BEGIN IMMEDIATE")
    try:
        # Check if slot exists and is unbooked
        slot = get_slot_by_id(conn, slot_id)
        if not slot:
            raise SlotNotFoundError(f"Slot with ID {slot_id} not found.")
        if slot["is_booked"]:
            raise SlotConflictError("Cannot delete a booked slot. Cancel the appointment first.")

        conn.execute("DELETE FROM slots WHERE id = ?", (slot_id,))
        conn.execute("COMMIT")
        return True
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.OperationalError:
            pass
        raise


# --- Booking Services ---

def book_slot(
    conn: sqlite3.Connection,
    slot_id: int,
    customer_name: str,
    notes: Optional[str] = None,
    user_id: Optional[int] = None
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
        update_cursor = conn.execute(
            "UPDATE slots SET is_booked = 1 WHERE id = ? AND is_booked = 0",
            (slot_id,)
        )
        if update_cursor.rowcount == 0:
            raise SlotAlreadyBookedError(f"Appointment slot with ID {slot_id} was just claimed by another booking.")

        # 3. Create the booking entry (with user_id and default 'CONFIRMED' status)
        insert_cursor = conn.execute(
            """
            INSERT INTO bookings (slot_id, customer_name, notes, user_id, status)
            VALUES (?, ?, ?, ?, 'CONFIRMED')
            """,
            (slot_id, customer_name, notes, user_id)
        )
        booking_id = insert_cursor.lastrowid

        # 4. Fetch the created booking record
        cursor = conn.execute(
            "SELECT id, slot_id, customer_name, notes, booked_at, user_id, status FROM bookings WHERE id = ?",
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
            "user_id": booking_row["user_id"],
            "status": booking_row["status"] or "CONFIRMED",
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


def cancel_booking(
    conn: sqlite3.Connection,
    booking_id: int,
    user_id: Optional[int] = None,
    is_staff: bool = False
) -> dict:
    """
    Cancels a booking. If a patient is cancelling, verifies ownership (user_id matches).
    Frees up the slot (is_booked = 0) so other patients can book it.
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        booking = get_booking_by_id(conn, booking_id)
        if not booking:
            raise BookingNotFoundError(f"Booking with ID {booking_id} not found.")

        # Check ownership unless staff (Doctor / Admin)
        if not is_staff and user_id is not None:
            if booking["user_id"] != user_id:
                raise ForbiddenActionError("You can only cancel your own appointments.")

        # Mark booking status as CANCELLED
        conn.execute("UPDATE bookings SET status = 'CANCELLED' WHERE id = ?", (booking_id,))

        # Free the slot
        conn.execute("UPDATE slots SET is_booked = 0 WHERE id = ?", (booking["slot_id"],))

        conn.execute("COMMIT")
        return get_booking_by_id(conn, booking_id)
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.OperationalError:
            pass
        raise


def update_booking_status(
    conn: sqlite3.Connection,
    booking_id: int,
    new_status: str
) -> dict:
    conn.execute("BEGIN IMMEDIATE")
    try:
        booking = get_booking_by_id(conn, booking_id)
        if not booking:
            raise BookingNotFoundError(f"Booking with ID {booking_id} not found.")

        old_status = booking["status"]
        conn.execute("UPDATE bookings SET status = ? WHERE id = ?", (new_status, booking_id))

        # Adjust slot availability based on status change
        if new_status == "CANCELLED":
            conn.execute("UPDATE slots SET is_booked = 0 WHERE id = ?", (booking["slot_id"],))
        elif old_status == "CANCELLED" and new_status in ("CONFIRMED", "COMPLETED"):
            conn.execute("UPDATE slots SET is_booked = 1 WHERE id = ?", (booking["slot_id"],))

        conn.execute("COMMIT")
        return get_booking_by_id(conn, booking_id)
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.OperationalError:
            pass
        raise


def get_booking_by_id(conn: sqlite3.Connection, booking_id: int) -> Optional[dict]:
    cursor = conn.execute(
        """
        SELECT b.id, b.slot_id, b.customer_name, b.notes, b.booked_at, b.user_id, b.status,
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
        "user_id": row["user_id"],
        "status": row["status"] or "CONFIRMED",
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
        SELECT b.id, b.slot_id, b.customer_name, b.notes, b.booked_at, b.user_id, b.status,
               s.slot_date, s.start_time, s.end_time, s.is_booked, s.created_at
        FROM bookings b
        JOIN slots s ON b.slot_id = s.id
        ORDER BY s.slot_date DESC, s.start_time DESC
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
            "user_id": row["user_id"],
            "status": row["status"] or "CONFIRMED",
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


def list_patient_bookings(conn: sqlite3.Connection, user_id: int) -> List[dict]:
    """Retrieve only the bookings belonging to a specific patient."""
    cursor = conn.execute(
        """
        SELECT b.id, b.slot_id, b.customer_name, b.notes, b.booked_at, b.user_id, b.status,
               s.slot_date, s.start_time, s.end_time, s.is_booked, s.created_at
        FROM bookings b
        JOIN slots s ON b.slot_id = s.id
        WHERE b.user_id = ?
        ORDER BY s.slot_date ASC, s.start_time ASC
        """,
        (user_id,)
    )
    rows = cursor.fetchall()
    return [
        {
            "id": row["id"],
            "slot_id": row["slot_id"],
            "customer_name": row["customer_name"],
            "notes": row["notes"],
            "booked_at": row["booked_at"],
            "user_id": row["user_id"],
            "status": row["status"] or "CONFIRMED",
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
