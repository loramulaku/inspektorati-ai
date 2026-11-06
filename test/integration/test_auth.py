"""Tests for /auth: login, refresh, logout, me, sektoret (no self-registration)."""

from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import text

from app.core import config
from app.core.security import ALGORITHM
from helpers import PASSWORD


# --- no self-registration ----------------------------------------------------

def test_there_is_no_register_endpoint(client):
    payload = {"emri": "A", "mbiemri": "B", "email": "a@example.com", "password": PASSWORD, "role": "inspektor"}
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 404


# --- login ------------------------------------------------------------------

def test_login_correct_password(client, make_user):
    user = make_user("inspektor")
    response = client.post("/auth/login", json={"email": user.email, "password": PASSWORD})
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == user.email


def test_login_wrong_password(client, make_user):
    user = make_user("inspektor")
    response = client.post("/auth/login", json={"email": user.email, "password": "Gabim!12345"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Email ose fjalëkalim i pasaktë"


def test_login_unknown_email(client):
    response = client.post("/auth/login", json={"email": "askush@example.com", "password": PASSWORD})
    assert response.status_code == 401


def test_login_inactive_user(client, make_user):
    user = make_user("inspektor", aktiv=False)
    response = client.post("/auth/login", json={"email": user.email, "password": PASSWORD})
    assert response.status_code == 403


def test_login_stores_only_hash_of_refresh_token(client, make_user, login, db):
    user = make_user("inspektor")
    refresh_token = login(user.email)["refresh_token"]
    stored = db.execute(text("SELECT token FROM refresh_tokens")).scalars().all()
    assert len(stored) == 1
    assert stored[0] != refresh_token and len(stored[0]) == 64


# --- refresh / logout -------------------------------------------------------

def test_refresh_returns_new_access_token(client, make_user, login, auth_header):
    user = make_user("inspektor")
    tokens = login(user.email)
    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    new_access = response.json()["access_token"]
    assert client.get("/auth/me", headers=auth_header(new_access)).status_code == 200


def test_refresh_with_access_token_is_rejected(client, make_user, login):
    user = make_user("inspektor")
    tokens = login(user.email)
    response = client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert response.status_code == 401


def test_refresh_with_garbage_is_rejected(client):
    response = client.post("/auth/refresh", json={"refresh_token": "not-a-token"})
    assert response.status_code == 401


def test_logout_revokes_refresh_token(client, make_user, login):
    user = make_user("inspektor")
    tokens = login(user.email)
    assert client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]}).status_code == 204
    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 401
    # logging out again is harmless
    assert client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]}).status_code == 204


def test_logout_only_revokes_that_session(client, make_user, login):
    user = make_user("inspektor")
    first = login(user.email)
    second = login(user.email)
    client.post("/auth/logout", json={"refresh_token": first["refresh_token"]})
    response = client.post("/auth/refresh", json={"refresh_token": second["refresh_token"]})
    assert response.status_code == 200


# --- me ---------------------------------------------------------------------

def test_me_with_valid_token(client, make_user, login, auth_header):
    user = make_user("drejtor")
    token = login(user.email)["access_token"]
    response = client.get("/auth/me", headers=auth_header(token))
    assert response.status_code == 200
    assert response.json()["email"] == user.email
    assert response.json()["role"] == "drejtor"


def test_me_without_token(client):
    assert client.get("/auth/me").status_code == 401


def test_me_with_expired_token(client, make_user, auth_header):
    user = make_user("inspektor")
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    expired = jwt.encode(
        {"sub": str(user.id), "type": "access", "role": "inspektor", "exp": past},
        config.JWT_SECRET,
        algorithm=ALGORITHM,
    )
    assert client.get("/auth/me", headers=auth_header(expired)).status_code == 401


def test_me_with_refresh_token_is_rejected(client, make_user, login, auth_header):
    user = make_user("inspektor")
    refresh_token = login(user.email)["refresh_token"]
    assert client.get("/auth/me", headers=auth_header(refresh_token)).status_code == 401


def test_me_with_wrong_signature(client, make_user, auth_header):
    user = make_user("inspektor")
    forged = jwt.encode(
        {"sub": str(user.id), "type": "access", "role": "admin",
         "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "a-different-secret-that-is-long-enough-123",
        algorithm=ALGORITHM,
    )
    assert client.get("/auth/me", headers=auth_header(forged)).status_code == 401


# --- sektoret ---------------------------------------------------------------

def test_sektoret_lists_top_level_categories(client, sector, db):
    from app.db.models import Kategori

    db.add(Kategori(emri="Nënkategori", parent_id=sector.id))
    db.commit()
    response = client.get("/auth/sektoret")
    assert response.status_code == 200
    assert response.json() == [{"id": sector.id, "emri": "Ndërtimi"}]
