"""Saving a citizen's kërkesë: tracking number, location, files, timeline.

The whole submission is all-or-nothing: files are checked before anything is
written; if saving to the database fails, the files written so far are removed.
"""

import re
import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import Integer, cast, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import config
from app.db.models import Attachment, Kerkese, Lokacion

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_FILES = 10
CHUNK = 1024 * 1024

FILE_TYPE_INVALID = "Lejohen vetëm skedarë PDF, JPG ose PNG"
FILE_TOO_BIG = "Skedari është më i madh se 10 MB"
FILE_EMPTY = "Skedari është bosh"
TOO_MANY_FILES = f"Mund të bashkangjitni deri në {MAX_FILES} skedarë"

TRACKING_PATTERN = re.compile(r"^VU-(\d{4})-(\d{4,})$")

# The file's first bytes decide its type; the name and browser-sent type are ignored.
SIGNATURES = [
    (b"%PDF-", "pdf", "dokument"),
    (b"\x89PNG\r\n\x1a\n", "png", "foto"),
    (b"\xff\xd8\xff", "jpg", "foto"),
]

# Public timeline (the 5 steps of the design) and where each status stands in it.
TIMELINE_STEPS = [
    "Kërkesa u pranua",
    "Kategorizuar nga sistemi",
    "Caktuar inspektorit",
    "Inspektim në terren",
    "Vendimi",
]
CURRENT_STEP = {
    "e_re": 1,
    "kategorizuar": 2,
    "caktuar": 3,
    "ne_terren": 3,
    "procesverbal": 3,
    "vendim_propozuar": 4,
    "vendim_miratuar": 4,
    "mase_aktive": 4,
    "riinspektim": 4,
    "ankese": 4,
    "mbyllur": len(TIMELINE_STEPS),  # everything done
}


# --- tracking number ----------------------------------------------------------------

def format_tracking_number(year, sequence):
    return f"VU-{year}-{sequence:04d}"


def next_tracking_number(db: Session, year):
    """The year's highest sequence + 1 (VU-2026-0001, VU-2026-0002, …)."""
    prefix = f"VU-{year}-"
    sequence = cast(func.substring(Kerkese.numri_gjurmimit, len(prefix) + 1), Integer)
    highest = db.scalar(select(func.max(sequence)).where(Kerkese.numri_gjurmimit.like(prefix + "%")))
    return format_tracking_number(year, (highest or 0) + 1)


def normalize_tracking_number(value):
    """Upper-case, trimmed tracking number, or None if it is not VU-YYYY-NNNN."""
    text = (value or "").strip().upper()
    return text if TRACKING_PATTERN.fullmatch(text) else None


# --- files ----------------------------------------------------------------------------

def detect_file_type(head):
    """(extension, attachments.lloji) from the first bytes, or None if not allowed."""
    for signature, extension, kind in SIGNATURES:
        if head.startswith(signature):
            return extension, kind
    return None


def _file_error(index, message):
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=[{"type": "value_error", "loc": ["body", "files", index], "msg": message}],
    )


def check_uploads(uploads):
    """Validate every file before anything is saved. Returns [(upload, ext, kind)]."""
    uploads = [u for u in uploads if u is not None and (u.filename or u.size)]
    if len(uploads) > MAX_FILES:
        raise _file_error(MAX_FILES, TOO_MANY_FILES)
    checked = []
    for index, upload in enumerate(uploads):
        handle = upload.file
        handle.seek(0, 2)
        size = handle.tell()
        handle.seek(0)
        if size == 0:
            raise _file_error(index, FILE_EMPTY)
        if size > MAX_FILE_BYTES:
            raise _file_error(index, FILE_TOO_BIG)
        detected = detect_file_type(handle.read(8))
        handle.seek(0)
        if detected is None:
            raise _file_error(index, FILE_TYPE_INVALID)
        checked.append((upload, *detected))
    return checked


def _write_file(upload, destination):
    with destination.open("wb") as out:
        while chunk := upload.file.read(CHUNK):
            out.write(chunk)


# --- saving ----------------------------------------------------------------------------

def create_kerkesa(db: Session, form, uploads, attempts=5):
    """Insert the kërkesë, its location and its files. Returns the Kerkese row."""
    files = check_uploads(uploads)
    written = []
    try:
        for attempt in range(attempts):
            location = Lokacion(pershkrimi=form.lokacioni)
            db.add(location)
            db.flush()
            kerkese = Kerkese(
                numri_gjurmimit=next_tracking_number(db, datetime.now().year),
                lloji=form.lloji,
                teksti_origjinal=form.pershkrimi,
                kanali="portal",
                status="e_re",
                lokacion_id=location.id,
                aplikuesi_emri=form.emri,
                aplikuesi_mbiemri=form.mbiemri,
                aplikuesi_numri_personal=form.numri_personal,
                aplikuesi_email=form.email,
                aplikuesi_telefoni=form.telefoni,
                aplikuesi_adresa=form.adresa,
                deklarata_pranuar=True,
                deklarata_emri=form.deklarata_emri,
            )
            db.add(kerkese)
            try:
                db.flush()
                break
            except IntegrityError:
                # Someone took the same number at the same moment: try the next one.
                db.rollback()
                if attempt == attempts - 1:
                    raise

        if files:
            folder = config.UPLOAD_DIR / "kerkesat" / str(kerkese.id)
            folder.mkdir(parents=True, exist_ok=True)
            for upload, extension, kind in files:
                name = f"{uuid.uuid4().hex}.{extension}"
                written.append(folder / name)
                _write_file(upload, folder / name)
                db.add(Attachment(
                    lloji=kind,
                    path=f"kerkesat/{kerkese.id}/{name}",
                    kerkesa_id=kerkese.id,
                ))
        db.commit()
    except Exception:
        db.rollback()
        # Remove only the files this submission wrote, then the folder if it is empty.
        for path in written:
            path.unlink(missing_ok=True)
        if written:
            try:
                written[0].parent.rmdir()
            except OSError:
                pass  # not empty: it holds other files
        raise
    db.refresh(kerkese)
    return kerkese


# --- public status ------------------------------------------------------------------------

def public_timeline(status_value, created_at):
    """The 5 public steps with their state: kryer (done), aktual (current), pritje (waiting)."""
    current = CURRENT_STEP.get(status_value, 1)
    steps = []
    for index, title in enumerate(TIMELINE_STEPS):
        state = "kryer" if index < current else "aktual" if index == current else "pritje"
        steps.append({"titulli": title, "gjendja": state, "koha": created_at if index == 0 else None})
    return steps
