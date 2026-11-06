"""One protected example route per role, to prove role-based access works.

Each role's placeholder dashboard in the frontend calls its own route.
"""

from fastapi import APIRouter, Depends

from app.api.deps import require_role
from app.db.models import Perdorues

router = APIRouter(tags=["role"])


def _welcome(user, panel):
    return {"paneli": panel, "mesazh": f"Mirë se vini, {user.emri} {user.mbiemri}", "role": user.role}


@router.get("/inspektor/paneli")
def inspektor_panel(user: Perdorues = Depends(require_role("inspektor"))):
    return _welcome(user, "Paneli i inspektorit")


@router.get("/drejtor/paneli")
def drejtor_panel(user: Perdorues = Depends(require_role("drejtor"))):
    return _welcome(user, "Paneli i drejtorit")


@router.get("/admin/paneli")
def admin_panel(user: Perdorues = Depends(require_role("admin"))):
    return _welcome(user, "Paneli i administratorit")
