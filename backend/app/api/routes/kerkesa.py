"""Public citizen portal: submit a kërkesë / ankesë and track it by number.

These two routes need NO login: citizens have no account. Everything else in
the API stays JWT-protected.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Kerkese
from app.db.session import get_db
from app.schemas.kerkesa import KerkesaCreated, KerkesaForm, KerkesaPublic
from app.services.kerkesa import create_kerkesa, normalize_tracking_number, public_timeline

router = APIRouter(prefix="/kerkesa", tags=["portali"])

NOT_FOUND = "Nuk u gjet asnjë kërkesë me këtë numër"

FormText = Annotated[str, Form()]


@router.post("", response_model=KerkesaCreated, status_code=status.HTTP_201_CREATED)
def submit(
    lloji: FormText = "",
    emri: FormText = "",
    mbiemri: FormText = "",
    numri_personal: FormText = "",
    email: FormText = "",
    telefoni: FormText = "",
    adresa: FormText = "",
    lokacioni: FormText = "",
    pershkrimi: FormText = "",
    deklarata_pranuar: FormText = "",
    files: Annotated[list[UploadFile], File()] = [],
    db: Session = Depends(get_db),
):
    """Fields and files in one multipart/form-data request: all saved, or nothing.

    The fields arrive as plain text and are cleaned and checked by KerkesaForm,
    which reports every problem at once with Albanian messages (422).
    """
    try:
        form = KerkesaForm(
            lloji=lloji,
            emri=emri,
            mbiemri=mbiemri,
            numri_personal=numri_personal,
            email=email,
            telefoni=telefoni,
            adresa=adresa,
            lokacioni=lokacioni,
            pershkrimi=pershkrimi,
            deklarata_pranuar=deklarata_pranuar or False,
        )
    except ValidationError as error:
        raise RequestValidationError(
            [{**e, "loc": ("body", *e["loc"])} for e in error.errors(include_url=False, include_context=False)]
        ) from None

    kerkese = create_kerkesa(db, form, files)
    return KerkesaCreated(
        numri_gjurmimit=kerkese.numri_gjurmimit, status=kerkese.status, created_at=kerkese.created_at
    )


@router.get("/gjurmo/{numri}", response_model=KerkesaPublic)
def track(numri: str, db: Session = Depends(get_db)):
    """Status of a kërkesë. Only public fields, never the applicant's data."""
    numri = normalize_tracking_number(numri)
    kerkese = numri and db.scalar(select(Kerkese).where(Kerkese.numri_gjurmimit == numri))
    if not kerkese:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return KerkesaPublic(
        numri_gjurmimit=kerkese.numri_gjurmimit,
        lloji=kerkese.lloji,
        status=kerkese.status,
        created_at=kerkese.created_at,
        timeline=public_timeline(kerkese.status, kerkese.created_at),
    )
