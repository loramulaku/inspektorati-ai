"""Shared FastAPI dependencies: the current user and role checks.

Usage in a route:
    user = Depends(get_current_user)            # any logged-in staff user
    user = Depends(require_role("admin"))       # only admins
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import ACCESS, decode_token
from app.db.models import Perdorues
from app.db.session import get_db

bearer = HTTPBearer(auto_error=False)

NOT_AUTHENTICATED = "Nuk jeni të kyçur ose seanca ka skaduar"
FORBIDDEN = "Nuk keni leje për këtë veprim"


def _unauthorized():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=NOT_AUTHENTICATED,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
):
    """The logged-in, active staff user from the Bearer access token; 401 otherwise."""
    if credentials is None:
        raise _unauthorized()
    payload = decode_token(credentials.credentials, ACCESS)
    if payload is None:
        raise _unauthorized()
    user = db.get(Perdorues, int(payload["sub"]))
    if user is None or not user.aktiv:
        raise _unauthorized()
    return user


def require_role(*roles):
    """Dependency that lets through only users whose role is in `roles`."""

    def checker(user: Perdorues = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=FORBIDDEN)
        return user

    return checker
