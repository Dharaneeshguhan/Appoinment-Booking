import pytest


def test_patient_signup_success(client):
    res = client.post("/auth/signup", json={
        "email": "newpatient@test.com",
        "full_name": "New Patient",
        "password": "Password123"
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newpatient@test.com"
    assert data["user"]["role"] == "PATIENT"
    assert data["user"]["full_name"] == "New Patient"


def test_signup_duplicate_email_rejected_409(client):
    payload = {
        "email": "duplicate@test.com",
        "full_name": "User One",
        "password": "Password123"
    }
    res1 = client.post("/auth/signup", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/auth/signup", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_login_success(client):
    client.post("/auth/signup", json={
        "email": "loginuser@test.com",
        "full_name": "Login User",
        "password": "MySecretPassword"
    })

    res = client.post("/auth/login", json={
        "email": "loginuser@test.com",
        "password": "MySecretPassword"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "loginuser@test.com"


def test_login_invalid_password_returns_401(client):
    client.post("/auth/signup", json={
        "email": "user401@test.com",
        "full_name": "User 401",
        "password": "CorrectPassword"
    })

    res = client.post("/auth/login", json={
        "email": "user401@test.com",
        "password": "WrongPassword"
    })
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


def test_get_current_user_profile(client):
    signup_res = client.post("/auth/signup", json={
        "email": "profileuser@test.com",
        "full_name": "Profile User",
        "password": "Password123"
    })
    token = signup_res.json()["access_token"]

    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "profileuser@test.com"
    assert data["full_name"] == "Profile User"
    assert data["role"] == "PATIENT"


def test_unauthenticated_profile_returns_401(client):
    res = client.get("/auth/me")
    assert res.status_code == 401
