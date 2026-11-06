"""Unit tests for the role check, the token check and the CORS setting,
called directly as plain functions (no database, no HTTP)."""

import importlib
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.deps import get_current_user, require_role
from app.core import config
from app.core.security import create_refresh_token
from app.services.users import ensure_sector_exists, utcnow


def user(role):
    return SimpleNamespace(id=1, role=role, aktiv=True)


# --- require_role ------------------------------------------------------------------

def test_require_role_lets_the_right_role_through():
    checker = require_role("admin")
    me = user("admin")
    assert checker(user=me) is me


def test_require_role_accepts_any_of_several_roles():
    checker = require_role("drejtor", "admin")
    assert checker(user=user("drejtor")).role == "drejtor"


@pytest.mark.parametrize("role", ["inspektor", "drejtor"])
def test_require_role_refuses_other_roles_with_403(role):
    with pytest.raises(HTTPException) as error:
        require_role("admin")(user=user(role))
    assert error.value.status_code == 403
    assert error.value.detail == "Nuk keni leje për këtë veprim"


# --- get_current_user (the parts that never reach the database) ------------------

def test_no_token_is_401():
    with pytest.raises(HTTPException) as error:
        get_current_user(credentials=None, db=None)
    assert error.value.status_code == 401


def test_refresh_token_used_as_access_token_is_401():
    token, _ = create_refresh_token(1)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as error:
        get_current_user(credentials=credentials, db=None)
    assert error.value.status_code == 401


# --- small service helpers ---------------------------------------------------------

def test_no_sector_needs_no_database_check():
    assert ensure_sector_exists(db=None, sektori_id=None) is None


def test_utcnow_has_no_timezone_like_mysql_datetime():
    assert utcnow().tzinfo is None


# --- FRONTEND_ORIGIN (CORS) parsing -------------------------------------------------

def test_frontend_origins_is_a_trimmed_comma_separated_list(monkeypatch):
    monkeypatch.setenv("FRONTEND_ORIGIN", " http://localhost:5173 , http://localhost:5174,, ")
    try:
        reloaded = importlib.reload(config)
        assert reloaded.FRONTEND_ORIGINS == ["http://localhost:5173", "http://localhost:5174"]
    finally:
        monkeypatch.undo()
        importlib.reload(config)
