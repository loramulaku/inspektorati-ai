"""Schemas for the public citizen form (kërkesë / ankesë) and the tracking page.

KerkesaForm cleans and validates every field the same way the frontend does,
with Albanian error messages. Required fields default to "" so that a missing
field gets our Albanian message instead of Pydantic's English one.
"""

import re
import unicodedata
from datetime import datetime
from typing import Literal

from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, ConfigDict, field_validator

REQUIRED = "Kjo fushë është e detyrueshme"
NAME_INVALID = "Shkruani një emër të vlefshëm"
NUMRI_PERSONAL_INVALID = "Numri personal duhet të ketë saktësisht 10 shifra"
EMAIL_INVALID = "Email-i nuk është i vlefshëm"
TELEFONI_INVALID = "Numri i telefonit nuk është i vlefshëm"
LLOJI_INVALID = "Zgjidhni llojin e paraqitjes"
DEKLARATA_REQUIRED = "Duhet të pajtoheni me deklaratën"

LLOJET = ("kerkese", "ankese")
PHONE_CHARS = re.compile(r"^\+?[0-9 ()\-]+$")


def too_long(limit):
    return f"Teksti është shumë i gjatë (maksimumi {limit} karaktere)"


def clean_text(value, multiline=False):
    """Normalise user text: NFC, no control characters, trimmed.

    Single-line fields also collapse runs of whitespace into one space;
    the description keeps its line breaks.
    """
    if value is None:
        return ""
    text = unicodedata.normalize("NFC", str(value)).replace("\r\n", "\n").replace("\r", "\n")
    kept = []
    for char in text:
        if char == "\n" and multiline:
            kept.append(char)
        elif char in "\t\n":
            kept.append(" ")
        elif unicodedata.category(char) not in ("Cc", "Cf"):
            kept.append(char)
    text = "".join(kept)
    if multiline:
        lines = [re.sub(r"[ ]{2,}", " ", line).strip() for line in text.split("\n")]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return re.sub(r"\s+", " ", text).strip()


def _required(value, limit, multiline=False):
    text = clean_text(value, multiline)
    if not text:
        raise ValueError(REQUIRED)
    if len(text) > limit:
        raise ValueError(too_long(limit))
    return text


def _optional(value, limit):
    text = clean_text(value)
    if len(text) > limit:
        raise ValueError(too_long(limit))
    return text or None


class KerkesaForm(BaseModel):
    """The fields of the public form (sent as multipart/form-data)."""

    # Run the validators on missing fields too, so a missing field is rejected.
    model_config = ConfigDict(validate_default=True)

    lloji: str = ""
    emri: str = ""
    mbiemri: str = ""
    numri_personal: str = ""
    email: str = ""
    telefoni: str = ""
    adresa: str = ""
    lokacioni: str = ""
    pershkrimi: str = ""
    deklarata_pranuar: bool = False

    @field_validator("lloji")
    @classmethod
    def _lloji(cls, value):
        value = clean_text(value).lower()
        if value not in LLOJET:
            raise ValueError(LLOJI_INVALID)
        return value

    @field_validator("emri", "mbiemri")
    @classmethod
    def _name(cls, value):
        text = _required(value, 80)
        if not any(char.isalpha() for char in text):
            raise ValueError(NAME_INVALID)
        return text

    @field_validator("numri_personal")
    @classmethod
    def _numri_personal(cls, value):
        text = clean_text(value).replace(" ", "")
        if not text:
            raise ValueError(REQUIRED)
        if not re.fullmatch(r"[0-9]{10}", text):
            raise ValueError(NUMRI_PERSONAL_INVALID)
        return text

    @field_validator("email")
    @classmethod
    def _email(cls, value):
        text = _optional(value, 120)
        if text is None:
            return None
        try:
            return validate_email(text, check_deliverability=False).normalized.lower()
        except EmailNotValidError:
            raise ValueError(EMAIL_INVALID) from None

    @field_validator("telefoni")
    @classmethod
    def _telefoni(cls, value):
        text = _required(value, 30)
        digits = sum(char.isdigit() for char in text)
        if not PHONE_CHARS.fullmatch(text) or not 6 <= digits <= 15:
            raise ValueError(TELEFONI_INVALID)
        return text

    @field_validator("adresa")
    @classmethod
    def _adresa(cls, value):
        return _optional(value, 255)

    @field_validator("lokacioni")
    @classmethod
    def _lokacioni(cls, value):
        return _required(value, 255)

    @field_validator("pershkrimi")
    @classmethod
    def _pershkrimi(cls, value):
        return _required(value, 5000, multiline=True)

    @field_validator("deklarata_pranuar", mode="before")
    @classmethod
    def _deklarata(cls, value):
        # Checkbox values from a form: only an explicit "yes" counts as accepted.
        if value is True or str(value).strip().lower() in ("true", "on", "1", "yes"):
            return True
        raise ValueError(DEKLARATA_REQUIRED)

    @property
    def deklarata_emri(self):
        """The name in "Unë, {emri mbiemri}, vërtetoj…", built by the server."""
        return f"{self.emri} {self.mbiemri}"


class KerkesaCreated(BaseModel):
    numri_gjurmimit: str
    status: str
    created_at: datetime | None


class TimelineStep(BaseModel):
    titulli: str
    gjendja: Literal["kryer", "aktual", "pritje"]
    koha: datetime | None = None


class KerkesaPublic(BaseModel):
    """What anyone with the tracking number may see. No personal data."""

    numri_gjurmimit: str
    lloji: str
    status: str
    created_at: datetime | None
    timeline: list[TimelineStep]
