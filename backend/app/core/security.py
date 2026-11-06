"""Password hashing and JWT tokens.

Passwords are hashed with bcrypt (via passlib) and never stored in plain text.
Two kinds of JWT are issued:
- access token: short-lived, sent with every API request;
- refresh token: long-lived, used only to get a new access token. Only its
  SHA-256 hash is stored in the `refresh_tokens` table, so it can be revoked.
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.core import config

if not config.JWT_SECRET:
    raise RuntimeError("JWT_SECRET mungon në backend/.env")

ALGORITHM = "HS256"
ACCESS = "access"
REFRESH = "refresh"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password):
    return pwd_context.hash(password)


def verify_password(password, password_hash):
    return pwd_context.verify(password, password_hash)


def _create_token(user_id, token_type, lifetime, extra=None):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + lifetime,
        "jti": uuid.uuid4().hex,
        **(extra or {}),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=ALGORITHM), payload["exp"]


def create_access_token(user_id, role):
    token, _ = _create_token(
        user_id, ACCESS, timedelta(minutes=config.ACCESS_TOKEN_MINUTES), {"role": role}
    )
    return token


def create_refresh_token(user_id):
    """Return (token, expires_at)."""
    return _create_token(user_id, REFRESH, timedelta(days=config.REFRESH_TOKEN_DAYS))


def decode_token(token, expected_type):
    """Return the payload, or None if the token is invalid, expired or of the wrong type."""
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    return payload


def hash_token(token):
    """SHA-256 of a refresh token: what we store in the database."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
