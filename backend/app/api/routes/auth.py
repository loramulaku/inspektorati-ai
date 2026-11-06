"""Staff authentication: login, refresh, logout, me.

There is no self-registration: staff accounts are created only by an admin
(POST /admin/users) or by the seed script. Citizens never use these
endpoints; they stay anonymous.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import (
    REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.models import Kategori, Perdorues, RefreshToken
from app.db.session import get_db
from app.schemas.users import AccessToken, LoginIn, RefreshIn, Sektor, TokenPair, UserOut
from app.services.users import utcnow

router = APIRouter(prefix="/auth", tags=["auth"])

WRONG_CREDENTIALS = "Email ose fjalëkalim i pasaktë"
ACCOUNT_DISABLED = "Llogaria juaj është çaktivizuar. Kontaktoni administratorin."
INVALID_REFRESH = "Seanca ka skaduar. Ju lutemi kyçuni përsëri."

# Checked against when the email does not exist, so a wrong email takes as long
# as a wrong password and does not reveal which emails are registered.
_DUMMY_HASH = hash_password("dummy-password-for-timing")


@router.post("/login", response_model=TokenPair)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(Perdorues).where(Perdorues.email == data.email))
    password_ok = verify_password(data.password, user.password_hash if user else _DUMMY_HASH)
    if user is None or not password_ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=WRONG_CREDENTIALS)
    if not user.aktiv:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=ACCOUNT_DISABLED)

    refresh_token, expires_at = create_refresh_token(user.id)
    db.add(
        RefreshToken(
            perdoruesi_id=user.id,
            token=hash_token(refresh_token),
            expires_at=expires_at.replace(tzinfo=None),
        )
    )
    db.commit()
    return TokenPair(
        access_token=create_access_token(user.id, user.role),
        refresh_token=refresh_token,
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=AccessToken)
def refresh(data: RefreshIn, db: Session = Depends(get_db)):
    payload = decode_token(data.refresh_token, REFRESH)
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token == hash_token(data.refresh_token)))
    if payload is None or stored is None or stored.revoked or stored.expires_at <= utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_REFRESH)

    user = db.get(Perdorues, stored.perdoruesi_id)
    if user is None or not user.aktiv:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_REFRESH)
    return AccessToken(access_token=create_access_token(user.id, user.role))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: RefreshIn, db: Session = Depends(get_db)):
    """Revoke the refresh token. Always 204, so logging out twice is harmless."""
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token == hash_token(data.refresh_token)))
    if stored is not None and not stored.revoked:
        stored.revoked = True
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserOut)
def me(user: Perdorues = Depends(get_current_user)):
    return user


@router.get("/sektoret", response_model=list[Sektor])
def sektoret(db: Session = Depends(get_db)):
    """Sectors for the user forms: the top-level categories."""
    return db.scalars(select(Kategori).where(Kategori.parent_id.is_(None)).order_by(Kategori.emri)).all()
