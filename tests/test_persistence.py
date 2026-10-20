import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, init_db, get_connection


def test_booking_persistence_across_restart():
    """
    Verifies that bookings and slot states persist in SQLite file storage
    after the application/server restarts (i.e. all connections close
    and a fresh client connects to the existing file).
    """
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        # --- PHASE 1: Server Session 1 ---
        # Initialize schema and launch session 1
        init_db(db_path)

        def get_db_session_1():
            conn = get_connection(db_path)
            try:
                yield conn
            finally:
                conn.close()

        app.dependency_overrides[get_db] = get_db_session_1
        with TestClient(app) as client_session_1:
            # 1. Create a slot
            slot_res = client_session_1.post(
                "/slots",
                json={"slot_date": "2026-11-01", "start_time": "10:00", "end_time": "10:30"}
            )
            assert slot_res.status_code == 201
            slot_id = slot_res.json()["id"]

            # 2. Book the slot
            book_res = client_session_1.post(
                f"/slots/{slot_id}/book",
                json={"customer_name": "Persistent Customer", "notes": "Important meeting"}
            )
            assert book_res.status_code == 201
            booking_id = book_res.json()["id"]

        # Session 1 is completely closed here. All connections and TestClient terminated.
        app.dependency_overrides.clear()

        # --- PHASE 2: Server Session 2 (Simulated Restart) ---
        # A completely new application session connects to the existing SQLite DB file on disk.
        def get_db_session_2():
            conn = get_connection(db_path)
            try:
                yield conn
            finally:
                conn.close()

        app.dependency_overrides[get_db] = get_db_session_2
        with TestClient(app) as client_session_2:
            # 1. Verify the booking still exists and data matches
            booking_res = client_session_2.get(f"/bookings/{booking_id}")
            assert booking_res.status_code == 200
            booking_data = booking_res.json()
            assert booking_data["id"] == booking_id
            assert booking_data["customer_name"] == "Persistent Customer"
            assert booking_data["notes"] == "Important meeting"
            assert booking_data["slot_id"] == slot_id

            # 2. Verify the slot remains marked as booked
            slot_check = client_session_2.get(f"/slots/{slot_id}")
            assert slot_check.status_code == 200
            assert slot_check.json()["is_booked"] is True

            # 3. Verify the slot does NOT appear in available slots listing
            avail_res = client_session_2.get("/slots")
            assert not any(s["id"] == slot_id for s in avail_res.json())

            # 4. Verify attempting to book it again in session 2 is rejected
            double_book_res = client_session_2.post(
                f"/slots/{slot_id}/book",
                json={"customer_name": "Intruder"}
            )
            assert double_book_res.status_code == 409

        app.dependency_overrides.clear()

    finally:
        try:
            os.remove(db_path)
        except OSError:
            pass
