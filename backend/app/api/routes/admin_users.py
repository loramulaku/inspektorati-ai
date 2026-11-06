"""Admin-only management of staff users: list, create, edit, deactivate.

Users are never deleted; deactivating sets aktiv = false and revokes all of
their refresh tokens, so they are logged out everywhere.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.models import Perdorues
from app.db.session import get_db
from app.schemas.users import UserCreate, UserOut, UserUpdate
from app.services.users import (
    commit_or_conflict,
    create_user,
    ensure_email_free,
    ensure_sector_exists,
    revoke_all_refresh_tokens,
)

router = APIRouter(prefix="/admin/users", tags=["admin"])

NOT_FOUND = "Përdoruesi nuk u gjet"
CANNOT_DISABLE_SELF = "Nuk mund ta çaktivizoni llogarinë tuaj"
CANNOT_DEMOTE_SELF = "Nuk mund ta hiqni rolin admin nga llogaria juaj"


def _get_user(db, user_id):
    user = db.get(Perdorues, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return user


def _deactivate(db, user, admin):
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=CANNOT_DISABLE_SELF)
    user.aktiv = False
    revoke_all_refresh_tokens(db, user.id)


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), admin: Perdorues = Depends(require_role("admin"))):
    return db.scalars(select(Perdorues).order_by(Perdorues.id)).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create(data: UserCreate, db: Session = Depends(get_db), admin: Perdorues = Depends(require_role("admin"))):
    return create_user(db, data)


@router.patch("/{user_id}", response_model=UserOut)
def edit(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    admin: Perdorues = Depends(require_role("admin")),
):
    user = _get_user(db, user_id)
    changes = data.model_dump(exclude_unset=True)

    if "email" in changes:
        ensure_email_free(db, changes["email"], exclude_id=user.id)
    if "sektori_id" in changes:
        ensure_sector_exists(db, changes["sektori_id"])
    if user.id == admin.id and changes.get("role", "admin") != "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=CANNOT_DEMOTE_SELF)

    aktiv = changes.pop("aktiv", None)
    for field, value in changes.items():
        if value is None and field not in ("sektori_id", "telefoni"):
            continue  # required columns cannot be cleared
        setattr(user, field, value)
    if aktiv is False and user.aktiv:
        _deactivate(db, user, admin)
    elif aktiv is True:
        user.aktiv = True

    commit_or_conflict(db)
    db.refresh(user)
    return user


@router.post("/{user_id}/deactivate", response_model=UserOut)
def deactivate(user_id: int, db: Session = Depends(get_db), admin: Perdorues = Depends(require_role("admin"))):
    user = _get_user(db, user_id)
    _deactivate(db, user, admin)
    db.commit()
    db.refresh(user)
    return user
