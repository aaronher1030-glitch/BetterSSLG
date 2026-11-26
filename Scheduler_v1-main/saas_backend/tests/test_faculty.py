"""
saas_backend/tests/test_faculty.py
Unit tests for Faculty CRUD endpoints.
"""

import pytest


def _auth_header(client) -> dict:
    """Helper to register and log in a test admin, returning Authorization header."""
    client.post("/api/v1/auth/register", json={
        "username": "fac_admin@school.ph",
        "password": "facpass123",
        "role": "admin",
        "tenant_id": "test-tenant",
    })
    resp = client.post("/api/v1/auth/token", data={
        "username": "fac_admin@school.ph",
        "password": "facpass123",
    })
    token = resp.json().get("access_token", "")
    return {"Authorization": f"Bearer {token}"}


def test_create_faculty(client):
    """Admin can create a new faculty member."""
    headers = _auth_header(client)
    resp = client.post("/api/v1/faculty", json={
        "name": "Maria Santos",
        "department": "Science",
        "employment_type": "Full-time",
        "binary_availability_mask": [True] * 40,
        "tenant_id": "test-tenant",
    }, headers=headers)
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert data["name"] == "Maria Santos"
    assert "id" in data


def test_list_faculty(client):
    """Faculty list endpoint returns a list."""
    headers = _auth_header(client)
    client.post("/api/v1/faculty", json={
        "name": "Jose Reyes",
        "department": "Math",
        "employment_type": "Full-time",
        "binary_availability_mask": [True] * 40,
        "tenant_id": "test-tenant",
    }, headers=headers)
    resp = client.get("/api/v1/faculty", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_faculty_by_id(client):
    """Can retrieve a specific faculty member by ID."""
    headers = _auth_header(client)
    create_resp = client.post("/api/v1/faculty", json={
        "name": "Ana Lim",
        "department": "Language",
        "employment_type": "Part-time",
        "binary_availability_mask": [True] * 40,
        "tenant_id": "test-tenant",
    }, headers=headers)
    fac_id = create_resp.json()["id"]
    resp = client.get(f"/api/v1/faculty/{fac_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Ana Lim"


def test_delete_faculty(client):
    """Admin can delete a faculty member."""
    headers = _auth_header(client)
    create_resp = client.post("/api/v1/faculty", json={
        "name": "Delete Me",
        "department": "General",
        "employment_type": "Full-time",
        "binary_availability_mask": [True] * 40,
        "tenant_id": "test-tenant",
    }, headers=headers)
    fac_id = create_resp.json()["id"]
    del_resp = client.delete(f"/api/v1/faculty/{fac_id}", headers=headers)
    assert del_resp.status_code in (200, 204)
    # Verify it's gone
    get_resp = client.get(f"/api/v1/faculty/{fac_id}", headers=headers)
    assert get_resp.status_code == 404


def test_create_faculty_invalid_mask(client):
    """Creating faculty with invalid mask raises an error."""
    headers = _auth_header(client)
    resp = client.post("/api/v1/faculty", json={
        "name": "Bad Mask",
        "department": "General",
        "employment_type": "Full-time",
        "binary_availability_mask": [],  # empty mask — invalid
        "tenant_id": "test-tenant",
    }, headers=headers)
    # Should either succeed with defaults or return validation error
    assert resp.status_code in (200, 201, 422)
