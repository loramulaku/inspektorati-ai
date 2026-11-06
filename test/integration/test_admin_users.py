"""Admin user management: list, create, edit, deactivate (admin only).

POST /admin/users is the only way (besides the seed script) to create staff users.
"""

import pytest
from sqlalchemy import text

from helpers import PASSWORD


@pytest.fixture
def admin_headers(make_user, login, auth_header):
    admin = make_user("admin", email="admin@example.com")
    return auth_header(login(admin.email)["access_token"])


def new_user(role="drejtor", email="drejtor.ri@example.com", **extra):
    return {"emri": "Vjosa", "mbiemri": "Rexhepi", "email": email, "password": PASSWORD, "role": role, **extra}


def test_admin_creates_user_who_can_log_in(client, admin_headers):
    response = client.post("/admin/users", json=new_user(telefoni="044 123 456"), headers=admin_headers)
    assert response.status_code == 201
    assert response.json()["telefoni"] == "044 123 456"

    login = client.post("/auth/login", json={"email": "drejtor.ri@example.com", "password": PASSWORD})
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "drejtor"


@pytest.mark.parametrize("role", ["inspektor", "drejtor", "admin"])
def test_admin_creates_every_role(role, client, admin_headers):
    response = client.post("/admin/users", json=new_user(role=role, email=f"{role}.ri@example.com"), headers=admin_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["role"] == role and body["aktiv"] is True
    assert "password" not in body and "password_hash" not in body


def test_create_stores_bcrypt_hash_not_plain_password(client, admin_headers, db):
    client.post("/admin/users", json=new_user(), headers=admin_headers)
    stored = db.execute(text("SELECT password_hash FROM perdoruesit WHERE email = 'drejtor.ri@example.com'")).scalar()
    assert stored != PASSWORD
    assert stored.startswith("$2b$")


def test_create_with_sector(client, admin_headers, sector):
    response = client.post("/admin/users", json=new_user(role="inspektor", sektori_id=sector.id), headers=admin_headers)
    assert response.status_code == 201
    assert response.json()["sektori_id"] == sector.id


def test_create_with_unknown_sector_is_rejected(client, admin_headers):
    response = client.post("/admin/users", json=new_user(sektori_id=999), headers=admin_headers)
    assert response.status_code == 422


def test_create_duplicate_email_is_case_insensitive(client, admin_headers):
    assert client.post("/admin/users", json=new_user(email="Rasti@Example.com"), headers=admin_headers).status_code == 201
    response = client.post("/admin/users", json=new_user(email="rasti@example.com"), headers=admin_headers)
    assert response.status_code == 409


def test_create_short_password_rejected(client, admin_headers):
    response = client.post("/admin/users", json=new_user(password="short"), headers=admin_headers)
    assert response.status_code == 422


def test_admin_lists_users(client, admin_headers, make_user):
    make_user("inspektor")
    response = client.get("/admin/users", headers=admin_headers)
    assert response.status_code == 200
    assert {u["role"] for u in response.json()} == {"admin", "inspektor"}


def test_admin_edits_user(client, admin_headers, make_user, sector):
    user = make_user("inspektor")
    response = client.patch(
        f"/admin/users/{user.id}",
        json={"emri": "Emër i ri", "role": "drejtor", "sektori_id": sector.id, "email": "Ri@Example.com"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert (body["emri"], body["role"], body["sektori_id"], body["email"]) == (
        "Emër i ri", "drejtor", sector.id, "ri@example.com"
    )


def test_edit_to_taken_email_conflicts(client, admin_headers, make_user):
    first = make_user("inspektor")
    second = make_user("inspektor")
    response = client.patch(f"/admin/users/{second.id}", json={"email": first.email}, headers=admin_headers)
    assert response.status_code == 409


def test_edit_unknown_user(client, admin_headers):
    assert client.patch("/admin/users/9999", json={"emri": "X"}, headers=admin_headers).status_code == 404


def test_deactivate_locks_user_out(client, admin_headers, make_user, login, auth_header):
    user = make_user("inspektor")
    tokens = login(user.email)

    response = client.post(f"/admin/users/{user.id}/deactivate", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["aktiv"] is False

    # old access token, old refresh token and a new login all fail
    assert client.get("/auth/me", headers=auth_header(tokens["access_token"])).status_code == 401
    assert client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
    assert client.post("/auth/login", json={"email": user.email, "password": PASSWORD}).status_code == 403


def test_reactivate_with_patch(client, admin_headers, make_user):
    user = make_user("inspektor", aktiv=False)
    response = client.patch(f"/admin/users/{user.id}", json={"aktiv": True}, headers=admin_headers)
    assert response.status_code == 200 and response.json()["aktiv"] is True
    assert client.post("/auth/login", json={"email": user.email, "password": PASSWORD}).status_code == 200


def test_admin_cannot_deactivate_or_demote_self(client, admin_headers):
    me = client.get("/auth/me", headers=admin_headers).json()
    assert client.post(f"/admin/users/{me['id']}/deactivate", headers=admin_headers).status_code == 400
    assert client.patch(f"/admin/users/{me['id']}", json={"aktiv": False}, headers=admin_headers).status_code == 400
    assert client.patch(f"/admin/users/{me['id']}", json={"role": "inspektor"}, headers=admin_headers).status_code == 400


@pytest.mark.parametrize("role", ["inspektor", "drejtor"])
def test_non_admin_cannot_manage_users(role, client, make_user, login, auth_header):
    user = make_user(role)
    headers = auth_header(login(user.email)["access_token"])
    assert client.get("/admin/users", headers=headers).status_code == 403
    assert client.post("/admin/users", json=new_user(), headers=headers).status_code == 403
    assert client.patch(f"/admin/users/{user.id}", json={"emri": "X"}, headers=headers).status_code == 403
    assert client.post(f"/admin/users/{user.id}/deactivate", headers=headers).status_code == 403


def test_user_management_needs_login(client):
    assert client.get("/admin/users").status_code == 401
