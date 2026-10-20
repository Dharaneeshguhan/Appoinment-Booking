import pytest


def test_list_slots_empty(client):
    response = client.get("/slots")
    assert response.status_code == 200
    assert response.json() == []


def test_create_slot_success(client):
    payload = {
        "slot_date": "2026-10-25",
        "start_time": "10:00",
        "end_time": "10:30"
    }
    response = client.post("/slots", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["slot_date"] == "2026-10-25"
    assert data["start_time"] == "10:00"
    assert data["end_time"] == "10:30"
    assert data["is_booked"] is False


def test_create_duplicate_slot_rejected(client):
    payload = {
        "slot_date": "2026-10-25",
        "start_time": "10:00",
        "end_time": "10:30"
    }
    res1 = client.post("/slots", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/slots", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_create_slot_invalid_time_range(client):
    payload = {
        "slot_date": "2026-10-25",
        "start_time": "11:00",
        "end_time": "10:00"  # end time before start time
    }
    response = client.post("/slots", json=payload)
    assert response.status_code == 422


def test_create_slot_invalid_date_format(client):
    payload = {
        "slot_date": "25-10-2026",
        "start_time": "10:00",
        "end_time": "10:30"
    }
    response = client.post("/slots", json=payload)
    assert response.status_code == 422


def test_filter_slots_by_date(client):
    client.post("/slots", json={"slot_date": "2026-10-25", "start_time": "09:00", "end_time": "09:30"})
    client.post("/slots", json={"slot_date": "2026-10-25", "start_time": "10:00", "end_time": "10:30"})
    client.post("/slots", json={"slot_date": "2026-10-26", "start_time": "11:00", "end_time": "11:30"})

    # Filter for 2026-10-25
    res = client.get("/slots?date=2026-10-25")
    assert res.status_code == 200
    slots = res.json()
    assert len(slots) == 2
    assert all(s["slot_date"] == "2026-10-25" for s in slots)

    # Filter for 2026-10-26
    res2 = client.get("/slots?date=2026-10-26")
    assert res2.status_code == 200
    slots2 = res2.json()
    assert len(slots2) == 1
    assert slots2[0]["start_time"] == "11:00"

    # Filter for date with no slots
    res3 = client.get("/slots?date=2026-10-27")
    assert res3.status_code == 200
    assert res3.json() == []


def test_filter_slots_invalid_date_query_param(client):
    res = client.get("/slots?date=not-a-date")
    assert res.status_code == 400


def test_get_slot_by_id(client):
    create_res = client.post("/slots", json={"slot_date": "2026-10-25", "start_time": "14:00", "end_time": "14:30"})
    slot_id = create_res.json()["id"]

    get_res = client.get(f"/slots/{slot_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == slot_id

    # Non-existent ID
    res404 = client.get("/slots/99999")
    assert res404.status_code == 404
