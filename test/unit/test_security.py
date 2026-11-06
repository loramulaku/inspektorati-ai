"""Unit tests for app.core.security: password hashing and JWT tokens."""

from datetime import datetime, timedelta, timezone

import jwt

from app.core import config
from app.core.security import (
    ACCESS,
    ALGORITHM,
    REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)


# --- passwords ----------------------------------------------------------------

def test_hash_is_bcrypt_and_not_the_password():
    hashed = hash_password("Sekret!123")
    assert hashed != "Sekret!123"
    assert hashed.startswith("$2b$")


def test_verify_accepts_right_and_rejects_wrong_password():
    hashed = hash_password("Sekret!123")
    assert verify_password("Sekret!123", hashed) is True
    assert verify_password("sekret!123", hashed) is False
    assert verify_password("", hashed) is False


def test_same_password_gets_a_different_salt_each_time():
    assert hash_password("Sekret!123") != hash_password("Sekret!123")


def test_albanian_characters_work():
    hashed = hash_password("Çelës-ëë!2026")
    assert verify_password("Çelës-ëë!2026", hashed)


# --- access token ---------------------------------------------------------------

def test_access_token_carries_user_role_and_type():
    payload = decode_token(create_access_token(7, "drejtor"), ACCESS)
    assert payload["sub"] == "7"
    assert payload["role"] == "drejtor"
    assert payload["type"] == ACCESS


def test_access_token_expires_after_configured_minutes():
    payload = decode_token(create_access_token(1, "inspektor"), ACCESS)
    lifetime = payload["exp"] - payload["iat"]
    assert lifetime == config.ACCESS_TOKEN_MINUTES * 60


def test_access_token_is_not_accepted_as_refresh_token():
    assert decode_token(create_access_token(1, "admin"), REFRESH) is None


# --- refresh token --------------------------------------------------------------

def test_refresh_token_returns_token_and_expiry():
    token, expires_at = create_refresh_token(3)
    payload = decode_token(token, REFRESH)
    assert payload["sub"] == "3"
    assert "role" not in payload
    expected = datetime.now(timezone.utc) + timedelta(days=config.REFRESH_TOKEN_DAYS)
    assert abs((expires_at - expected).total_seconds()) < 5


def test_refresh_token_is_not_accepted_as_access_token():
    token, _ = create_refresh_token(3)
    assert decode_token(token, ACCESS) is None


def test_every_token_is_unique():
    first, _ = create_refresh_token(3)
    second, _ = create_refresh_token(3)
    assert first != second
    assert decode_token(first, REFRESH)["jti"] != decode_token(second, REFRESH)["jti"]


# --- decoding bad tokens --------------------------------------------------------

def test_garbage_is_rejected():
    assert decode_token("jo-një-token", ACCESS) is None
    assert decode_token("", ACCESS) is None


def test_expired_token_is_rejected():
    past = datetime.now(timezone.utc) - timedelta(seconds=1)
    token = jwt.encode({"sub": "1", "type": ACCESS, "exp": past}, config.JWT_SECRET, algorithm=ALGORITHM)
    assert decode_token(token, ACCESS) is None


def test_token_signed_with_another_secret_is_rejected():
    future = datetime.now(timezone.utc) + timedelta(minutes=5)
    token = jwt.encode({"sub": "1", "type": ACCESS, "exp": future}, "x" * 48, algorithm=ALGORITHM)
    assert decode_token(token, ACCESS) is None


def test_unsigned_token_is_rejected():
    token = jwt.encode({"sub": "1", "type": ACCESS}, key=None, algorithm="none")
    assert decode_token(token, ACCESS) is None


# --- stored refresh-token hash ----------------------------------------------------

def test_hash_token_is_sha256_hex_and_stable():
    assert hash_token("abc") == hash_token("abc")
    assert len(hash_token("abc")) == 64
    assert hash_token("abc") != hash_token("abd")
