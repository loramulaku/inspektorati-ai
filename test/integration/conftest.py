"""Fixtures for the integration tests: the real FastAPI app (TestClient) on the
MySQL test database. The tables the tests write to are emptied before each test.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.models import Kategori, Perdorues
from app.db.session import SessionLocal, engine
from app.main import app
from helpers import PASSWORD

TABLES_TO_EMPTY = ["attachments", "kerkesat", "lokacionet", "refresh_tokens", "perdoruesit", "kategorite"]


@pytest.fixture(autouse=True)
def empty_tables(test_database):
    with engine.begin() as conn:
        conn.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 0")
        for table in TABLES_TO_EMPTY:
            conn.exec_driver_sql(f"TRUNCATE TABLE `{table}`")
        conn.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 1")


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def make_user(db):
    """Insert a user straight into the DB and return it."""
    counter = {"n": 0}

    def _make(role="inspektor", aktiv=True, email=None):
        counter["n"] += 1
        user = Perdorues(
            emri="Test",
            mbiemri=role.capitalize(),
            email=email or f"{role}{counter['n']}@example.com",
            password_hash=hash_password(PASSWORD),
            role=role,
            aktiv=aktiv,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        # End the transaction so later reads in the test see what the API wrote.
        db.commit()
        return user

    return _make


@pytest.fixture
def login(client):
    """Log a user in and return the token response as a dict."""

    def _login(email, password=PASSWORD):
        response = client.post("/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        return response.json()

    return _login


@pytest.fixture
def auth_header():
    def _header(token):
        return {"Authorization": f"Bearer {token}"}

    return _header


@pytest.fixture
def sector(db):
    sector = Kategori(emri="Ndërtimi")
    db.add(sector)
    db.commit()
    db.refresh(sector)
    db.commit()
    return sector
