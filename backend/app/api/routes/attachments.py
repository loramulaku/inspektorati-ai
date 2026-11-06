"""Download a file attached to a kërkesë. Staff only (citizens' personal data)."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core import config
from app.db.models import Attachment, Perdorues
from app.db.session import get_db

router = APIRouter(prefix="/attachments", tags=["attachments"])

NOT_FOUND = "Skedari nuk u gjet"
MEDIA_TYPES = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".png": "image/png"}


@router.get("/{attachment_id}/download")
def download(
    attachment_id: int,
    db: Session = Depends(get_db),
    user: Perdorues = Depends(get_current_user),
):
    attachment = db.get(Attachment, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)

    # Serve only files inside UPLOAD_DIR, even if a stored path were tampered with.
    path = (config.UPLOAD_DIR / attachment.path).resolve()
    if not path.is_relative_to(config.UPLOAD_DIR) or not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)

    return FileResponse(
        path,
        media_type=MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream"),
        filename=path.name,
    )
