"""User operations used by the admin endpoints."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import Kategori, Perdorues, RefreshToken

EMAIL_TAKEN = "Ky email është tashmë i regjistruar"
SECTOR_NOT_FOUND = "Sektori i zgjedhur nuk ekziston"


def utcnow():
    """Current UTC time without tzinfo, matching MySQL DATETIME columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ensure_email_free(db: Session, email, exclude_id=None):
    query = select(Perdorues.id).where(Perdorues.email == email)
    if exclude_id is not None:
        query = query.where(Perdorues.id != exclude_id)
    if db.scalar(query) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=EMAIL_TAKEN)


def ensure_sector_exists(db: Session, sektori_id):
    """A sector is a top-level category (parent_id NULL)."""
    if sektori_id is None:
        return
    sector = db.get(Kategori, sektori_id)
    if sector is None or sector.parent_id is not None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=SECTOR_NOT_FOUND)


def commit_or_conflict(db: Session):
    # Two requests with the same email at the same time: the UNIQUE index decides.
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=EMAIL_TAKEN)


def create_user(db: Session, data):
    ensure_email_free(db, data.email)
    ensure_sector_exists(db, data.sektori_id)
    user = Perdorues(
        emri=data.emri,
        mbiemri=data.mbiemri,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        sektori_id=data.sektori_id,
        telefoni=data.telefoni,
        aktiv=True,
    )
    db.add(user)
    commit_or_conflict(db)
    db.refresh(user)
    return user


def revoke_all_refresh_tokens(db: Session, user_id):
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.perdoruesi_id == user_id, RefreshToken.revoked.is_(False))
        .values(revoked=True)
    )
