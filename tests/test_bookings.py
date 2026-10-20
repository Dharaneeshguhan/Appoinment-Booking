import pytest


def test_book_slot_via_slots_endpoint(client):
    create_res = client.post("/slots", json={"slot_date": "2026-10-25", "start_time": "09:00", "end_time": "09:30"})
    slot_id = create_res.json()["id"]

    book_res = client.post(
        f"/slots/{slot_id}/book",
        json={"customer_name": "Alice Cooper", "notes": "Checkup"}
    )
    assert book_res.status_code == 201
    booking = book_res.json()
    assert booking["slot_id"] == slot_id
    assert booking["customer_name"] == "Alice Cooper"
    assert booking["notes"] == "Checkup"
    assert booking["slot"]["is_booked"] is True

    # Slot should no longer appear in available slots list
    avail_res = client.get("/slots")
    assert not any(s["id"] == slot_id for s in avail_res.json())

    # Slot should show is_booked = True when queried with available_only=false
    all_res = client.get("/slots?available_only=false")
    booked_slot = next(s for s in all_res.json() if s["id"] == slot_id)
    assert booked_slot["is_booked"] is True


def test_book_slot_via_bookings_endpoint(client):
    create_res = client.post("/slots", json={"slot_date": "2026-10-25", "start_time": "10:00", "end_time": "10:30"})
    slot_id = create_res.json()["id"]

    book_res = client.post(
        "/bookings",
        json={"slot_id": slot_id, "customer_name": "Bob Dylan", "notes": "Guitar lesson"}
    )
    assert book_res.status_code == 201
    booking = book_res.json()
    assert booking["slot_id"] == slot_id
    assert booking["customer_name"] == "Bob Dylan"


def test_double_booking_rejected_with_409(client):
    create_res = client.post("/slots", json={"slot_date": "2026-10-25", "start_time": "11:00", "end_time": "11:30"})
    slot_id = create_res.json()["id"]

    # First booking succeeds
    res1 = client.post(f"/slots/{slot_id}/book", json={"customer_name": "First Customer"})
    assert res1.status_code == 201

    # Second booking must be rejected with 409 Conflict
    res2 = client.post(f"/slots/{slot_id}/book", json={"customer_name": "Second Customer"})
    assert res2.status_code == 409
    assert "already been booked" in res2.json()["detail"]

    # Also rejected via /bookings endpoint
    res3 = client.post("/bookings", json={"slot_id": slot_id, "customer_name": "Third Customer"})
    assert res3.status_code == 409
    assert "already been booked" in res3.json()["detail"]


def test_booking_non_existent_slot_returns_404(client):
    res = client.post("/slots/9999/book", json={"customer_name": "Ghost"})
    assert res.status_code == 404
    assert "does not exist" in res.json()["detail"]

    res2 = client.post("/bookings", json={"slot_id": 9999, "customer_name": "Ghost"})
    assert res2.status_code == 404
    assert "does not exist" in res2.json()["detail"]


def test_booking_empty_customer_name_validation(client):
    create_res = client.post("/slots", json={"slot_date": "2026-10-25", "start_time": "12:00", "end_time": "12:30"})
    slot_id = create_res.json()["id"]

    # Empty string
    res = client.post(f"/slots/{slot_id}/book", json={"customer_name": "   "})
    assert res.status_code == 422

    # Missing customer name
    res2 = client.post(f"/slots/{slot_id}/book", json={})
    assert res2.status_code == 422


def test_list_and_get_bookings(client):
    # Book two slots
    s1 = client.post("/slots", json={"slot_date": "2026-10-25", "start_time": "13:00", "end_time": "13:30"}).json()["id"]
    s2 = client.post("/slots", json={"slot_date": "2026-10-25", "start_time": "14:00", "end_time": "14:30"}).json()["id"]

    b1 = client.post(f"/slots/{s1}/book", json={"customer_name": "Client One"}).json()
    b2 = client.post(f"/slots/{s2}/book", json={"customer_name": "Client Two"}).json()

    # List bookings
    list_res = client.get("/bookings")
    assert list_res.status_code == 200
    bookings = list_res.json()
    assert len(bookings) == 2

    # Get single booking
    b1_res = client.get(f"/bookings/{b1['id']}")
    assert b1_res.status_code == 200
    assert b1_res.json()["customer_name"] == "Client One"

    # Non-existent booking ID
    b_none = client.get("/bookings/8888")
    assert b_none.status_code == 404
