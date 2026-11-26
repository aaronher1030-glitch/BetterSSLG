"""
saas_backend/tests/test_auth.py
Unit tests for authentication endpoints.
"""


def test_register_new_user(client):
    """A new user can register successfully."""
    resp = client.post("/api/v1/auth/register", json={
        "username": "testuser@school.ph",
        "password": "securepassword",
        "role": "admin",
        "tenant_id": "test-tenant",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert "testuser@school.ph" in data["message"]


def test_register_duplicate_user(client):
    """Registering the same username twice returns 400."""
    payload = {
        "username": "duplicate@school.ph",
        "password": "pass1234",
        "role": "viewer",
        "tenant_id": "test-tenant",
    }
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


def test_login_success(client):
    """Valid credentials return a JWT access token."""
    client.post("/api/v1/auth/register", json={
        "username": "loginuser@school.ph",
        "password": "mypassword",
        "role": "admin",
        "tenant_id": "test-tenant",
    })
    resp = client.post("/api/v1/auth/token", data={
        "username": "loginuser@school.ph",
        "password": "mypassword",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "admin"


def test_login_wrong_password(client):
    """Wrong password returns 401."""
    client.post("/api/v1/auth/register", json={
        "username": "wrongpass@school.ph",
        "password": "correctpass",
        "role": "viewer",
        "tenant_id": "test-tenant",
    })
    resp = client.post("/api/v1/auth/token", data={
        "username": "wrongpass@school.ph",
        "password": "wrongpass",
    })
    assert resp.status_code == 401


def test_me_endpoint(client):
    """Authenticated user can retrieve their own profile."""
    client.post("/api/v1/auth/register", json={
        "username": "me@school.ph",
        "password": "mepass",
        "role": "admin",
        "tenant_id": "test-tenant",
    })
    token_resp = client.post("/api/v1/auth/token", data={
        "username": "me@school.ph",
        "password": "mepass",
    })
    token = token_resp.json()["access_token"]
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["username"] == "me@school.ph"
    assert data["role"] == "admin"


def test_me_without_token(client):
    """Accessing /me without a token returns 401."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_health_endpoint(client):
    """Health check endpoint returns ok."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
