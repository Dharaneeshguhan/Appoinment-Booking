import pytest
from app.database import get_connection
from app.services import create_user


@pytest.fixture
def test_users(temp_db_file):
    conn = get_connection(temp_db_file)
    try:
        doctor = create_user(conn, "doctor_rbac@test.com", "Dr. RBAC", "Doctor123", role="DOCTOR")
        admin = create_user(conn, "admin_rbac@test.com", "Admin RBAC", "Admin123", role="ADMIN")
        patient_1 = create_user(conn, "patient1@test.com", "Patient One", "Pass123", role="PATIENT")
        patient_2 = create_user(conn, "patient2@test.com", "Patient Two", "Pass123", role="PATIENT")
        return {
            "doctor": doctor,
            "admin": admin,
            "patient_1": patient_1,
            "patient_2": patient_2
        }
    finally:
        conn.close()


def get_token(client, email, password):
    res = client.post("/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def test_patient_cannot_create_slot(client, test_users):
    patient_token = get_token(client, "patient1@test.com", "Pass123")
    res = client.post(
        "/slots",
        json={"slot_date": "2026-11-05", "start_time": "09:00", "end_time": "09:30"},
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert res.status_code == 403
    assert "Patients are not authorized" in res.json()["detail"]


def test_doctor_can_create_slot(client, test_users):
    doctor_token = get_token(client, "doctor_rbac@test.com", "Doctor123")
    res = client.post(
        "/slots",
        json={"slot_date": "2026-11-05", "start_time": "09:00", "end_time": "09:30"},
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert res.status_code == 201
    assert res.json()["start_time"] == "09:00"


def test_patient_booking_ownership_and_cancellation(client, test_users):
    # 1. Doctor creates a slot
    doctor_token = get_token(client, "doctor_rbac@test.com", "Doctor123")
    slot_res = client.post(
        "/slots",
        json={"slot_date": "2026-11-05", "start_time": "10:00", "end_time": "10:30"},
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    slot_id = slot_res.json()["id"]

    # 2. Patient 1 books the slot
    p1_token = get_token(client, "patient1@test.com", "Pass123")
    book_res = client.post(
        f"/slots/{slot_id}/book",
        json={"notes": "Checkup"},
        headers={"Authorization": f"Bearer {p1_token}"}
    )
    assert book_res.status_code == 201
    booking_id = book_res.json()["id"]
    assert book_res.json()["user_id"] == test_users["patient_1"]["id"]
    assert book_res.json()["customer_name"] == "Patient One"

    # 3. Patient 1 can view their booking
    my_res = client.get("/my-bookings", headers={"Authorization": f"Bearer {p1_token}"})
    assert my_res.status_code == 200
    assert any(b["id"] == booking_id for b in my_res.json())

    # 4. Patient 2 CANNOT view Patient 1's booking in their personal list
    p2_token = get_token(client, "patient2@test.com", "Pass123")
    p2_my_res = client.get("/my-bookings", headers={"Authorization": f"Bearer {p2_token}"})
    assert p2_my_res.status_code == 200
    assert not any(b["id"] == booking_id for b in p2_my_res.json())

    # 5. Patient 2 CANNOT cancel Patient 1's booking (403 Forbidden)
    p2_cancel_res = client.post(
        f"/my-bookings/{booking_id}/cancel",
        headers={"Authorization": f"Bearer {p2_token}"}
    )
    assert p2_cancel_res.status_code == 403
    assert "only cancel your own" in p2_cancel_res.json()["detail"]

    # 6. Patient 1 cancels their own booking -> slot is freed!
    p1_cancel_res = client.post(
        f"/my-bookings/{booking_id}/cancel",
        headers={"Authorization": f"Bearer {p1_token}"}
    )
    assert p1_cancel_res.status_code == 200
    assert p1_cancel_res.json()["status"] == "CANCELLED"

    # Slot is now available again
    avail_res = client.get("/slots")
    assert any(s["id"] == slot_id for s in avail_res.json())

    # Patient 2 can now book the freed slot!
    p2_book_res = client.post(
        f"/slots/{slot_id}/book",
        json={"notes": "Claiming freed slot"},
        headers={"Authorization": f"Bearer {p2_token}"}
    )
    assert p2_book_res.status_code == 201


def test_doctor_can_update_booking_status(client, test_users):
    doctor_token = get_token(client, "doctor_rbac@test.com", "Doctor123")
    p1_token = get_token(client, "patient1@test.com", "Pass123")

    # Create slot & book
    slot = client.post(
        "/slots",
        json={"slot_date": "2026-11-05", "start_time": "14:00", "end_time": "14:30"},
        headers={"Authorization": f"Bearer {doctor_token}"}
    ).json()
    booking = client.post(
        f"/slots/{slot['id']}/book",
        json={"customer_name": "Patient One"},
        headers={"Authorization": f"Bearer {p1_token}"}
    ).json()

    # Patient cannot update status (403)
    p_status_res = client.patch(
        f"/bookings/{booking['id']}/status",
        json={"status": "COMPLETED"},
        headers={"Authorization": f"Bearer {p1_token}"}
    )
    assert p_status_res.status_code == 403

    # Doctor can mark COMPLETED (200)
    d_status_res = client.patch(
        f"/bookings/{booking['id']}/status",
        json={"status": "COMPLETED"},
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert d_status_res.status_code == 200
    assert d_status_res.json()["status"] == "COMPLETED"


def test_admin_user_management(client, test_users):
    admin_token = get_token(client, "admin_rbac@test.com", "Admin123")
    doctor_token = get_token(client, "doctor_rbac@test.com", "Doctor123")

    # Doctor cannot access admin users endpoint (403)
    d_res = client.get("/admin/users", headers={"Authorization": f"Bearer {doctor_token}"})
    assert d_res.status_code == 403

    # Admin can list users (200)
    a_res = client.get("/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert a_res.status_code == 200
    assert len(a_res.json()) >= 4

    # Admin deactivates patient 1
    p1_id = test_users["patient_1"]["id"]
    deact_res = client.patch(
        f"/admin/users/{p1_id}/status",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert deact_res.status_code == 200
    assert deact_res.json()["is_active"] is False

    # Deactivated patient 1 cannot log in (403)
    login_res = client.post("/auth/login", json={"email": "patient1@test.com", "password": "Pass123"})
    assert login_res.status_code == 403
