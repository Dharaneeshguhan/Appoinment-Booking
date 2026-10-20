import threading
import concurrent.futures
from app.database import get_connection


def test_concurrent_booking_race_condition_prevention(client, temp_db_file):
    """
    Test that when multiple threads attempt to book the exact same slot concurrently,
    exactly ONE succeeds (201 Created) and all others are rejected (409 Conflict).
    Ensures zero double-booking under race conditions.
    """
    # Create a fresh slot
    create_res = client.post(
        "/slots",
        json={"slot_date": "2026-10-30", "start_time": "15:00", "end_time": "15:30"}
    )
    assert create_res.status_code == 201
    slot_id = create_res.json()["id"]

    num_threads = 10
    barrier = threading.Barrier(num_threads)
    results = []

    def attempt_booking(customer_idx: int):
        # Synchronize all threads so they hit the endpoint at the exact same instant
        barrier.wait()
        res = client.post(
            f"/slots/{slot_id}/book",
            json={"customer_name": f"Competitor {customer_idx}"}
        )
        return res.status_code, res.json()

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(attempt_booking, i) for i in range(num_threads)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    status_codes = [status for status, _ in results]
    success_count = status_codes.count(201)
    conflict_count = status_codes.count(409)

    # Exactly one request must succeed, and all others must fail with 409 Conflict
    assert success_count == 1, f"Expected exactly 1 success, got {success_count}. Status codes: {status_codes}"
    assert conflict_count == num_threads - 1, f"Expected {num_threads - 1} conflicts, got {conflict_count}."

    # Direct database verification: bookings table must contain exactly 1 row for this slot
    conn = get_connection(temp_db_file)
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM bookings WHERE slot_id = ?", (slot_id,))
        count = cursor.fetchone()["cnt"]
        assert count == 1, f"Database has {count} bookings for slot {slot_id}; expected exactly 1."
    finally:
        conn.close()
