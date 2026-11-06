"""Unit tests for the citizen-portal helpers: text cleaning, form rules,
file-type detection, tracking numbers and the public timeline."""

from datetime import datetime
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.kerkesa import KerkesaForm, clean_text
from app.services.kerkesa import (
    MAX_FILE_BYTES,
    check_uploads,
    detect_file_type,
    format_tracking_number,
    normalize_tracking_number,
    public_timeline,
)

VALID = dict(
    lloji="kerkese", emri="Arta", mbiemri="Gashi", numri_personal="1234567890",
    email="", telefoni="044 123 456", adresa="", lokacioni="Qendra", pershkrimi="Përshkrim",
    deklarata_pranuar=True,
)


def form_errors(**changes):
    with pytest.raises(ValidationError) as error:
        KerkesaForm(**{**VALID, **changes})
    return {e["loc"][0]: e["msg"].removeprefix("Value error, ") for e in error.value.errors()}


# --- clean_text ------------------------------------------------------------------------

def test_clean_text_trims_and_collapses_spaces():
    assert clean_text("  Lagjja   e\tre  ") == "Lagjja e re"


def test_clean_text_removes_control_characters():
    assert clean_text("Ar\u0000ben​") == "Arben"


def test_clean_text_keeps_line_breaks_only_when_multiline():
    assert clean_text("a\r\nb") == "a b"
    assert clean_text(" a \r\n\r\n\r\n b ", multiline=True) == "a\n\nb"


def test_clean_text_normalises_albanian_letters():
    decomposed = "ë"  # "ë" written as e + combining diaeresis
    assert clean_text(decomposed) == "ë"


def test_clean_text_of_none_is_empty():
    assert clean_text(None) == ""


# --- KerkesaForm rules -------------------------------------------------------------------

def test_valid_form_and_declaration_name():
    form = KerkesaForm(**VALID)
    assert form.deklarata_emri == "Arta Gashi"
    assert form.email is None and form.adresa is None


def test_missing_fields_get_albanian_messages():
    with pytest.raises(ValidationError) as error:
        KerkesaForm()
    messages = {e["loc"][0]: e["msg"].removeprefix("Value error, ") for e in error.value.errors()}
    assert messages["emri"] == "Kjo fushë është e detyrueshme"
    assert messages["lloji"] == "Zgjidhni llojin e paraqitjes"
    assert messages["deklarata_pranuar"] == "Duhet të pajtoheni me deklaratën"


@pytest.mark.parametrize("value", ["12345 67890", " 1234567890 "])
def test_personal_number_spaces_are_ignored(value):
    assert KerkesaForm(**{**VALID, "numri_personal": value}).numri_personal == "1234567890"


@pytest.mark.parametrize("value", ["123456789", "١٢٣٤٥٦٧٨٩٠", "12345678a0"])
def test_personal_number_must_be_10_ascii_digits(value):
    assert form_errors(numri_personal=value)["numri_personal"] == "Numri personal duhet të ketë saktësisht 10 shifra"


@pytest.mark.parametrize("value", ["+383 44 123 456", "044-123-456", "(044) 123456"])
def test_phone_numbers_accepted(value):
    assert KerkesaForm(**{**VALID, "telefoni": value}).telefoni == value


@pytest.mark.parametrize("value", ["12345", "044 abc", "+" + "1" * 16])
def test_phone_numbers_rejected(value):
    assert "telefoni" in form_errors(telefoni=value)


def test_email_is_optional_but_must_be_valid():
    assert KerkesaForm(**{**VALID, "email": "Arta@Example.com"}).email == "arta@example.com"
    assert form_errors(email="arta@")["email"] == "Email-i nuk është i vlefshëm"


def test_type_is_case_insensitive_but_limited():
    assert KerkesaForm(**{**VALID, "lloji": "ANKESE"}).lloji == "ankese"
    assert "lloji" in form_errors(lloji="leje")


@pytest.mark.parametrize("value", ["false", "", False])
def test_declaration_must_be_accepted(value):
    assert form_errors(deklarata_pranuar=value)["deklarata_pranuar"] == "Duhet të pajtoheni me deklaratën"


def test_length_limits():
    assert form_errors(emri="a" * 81)["emri"] == "Teksti është shumë i gjatë (maksimumi 80 karaktere)"
    assert "pershkrimi" in form_errors(pershkrimi="a" * 5001)
    assert KerkesaForm(**{**VALID, "pershkrimi": "a" * 5000}).pershkrimi == "a" * 5000


# --- files -----------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "head, expected",
    [
        (b"%PDF-1.7", ("pdf", "dokument")),
        (b"\x89PNG\r\n\x1a\n", ("png", "foto")),
        (b"\xff\xd8\xff\xe0", ("jpg", "foto")),
        (b"GIF89a", None),
        (b"PK\x03\x04", None),
        (b"", None),
    ],
)
def test_detect_file_type_by_content(head, expected):
    assert detect_file_type(head) == expected


def fake_upload(content, name="skedar.pdf"):
    return SimpleNamespace(filename=name, size=len(content), file=BytesIO(content))


def test_check_uploads_accepts_valid_files_and_ignores_empty_slots():
    checked = check_uploads([fake_upload(b"%PDF-1.4 x"), fake_upload(b"", name=""), None])
    assert [(ext, kind) for _, ext, kind in checked] == [("pdf", "dokument")]


def test_check_uploads_rejects_bad_type_with_the_file_position():
    with pytest.raises(HTTPException) as error:
        check_uploads([fake_upload(b"%PDF-1.4 x"), fake_upload(b"MZ exe", "a.pdf")])
    assert error.value.status_code == 422
    assert error.value.detail[0]["loc"] == ["body", "files", 1]


def test_check_uploads_size_limit():
    exact = b"%PDF-" + b"0" * (MAX_FILE_BYTES - 5)
    assert check_uploads([fake_upload(exact)])
    with pytest.raises(HTTPException):
        check_uploads([fake_upload(exact + b"0")])


def test_check_uploads_rewinds_files_for_saving():
    upload = fake_upload(b"%PDF-1.4 content")
    check_uploads([upload])
    assert upload.file.tell() == 0


# --- tracking numbers ----------------------------------------------------------------------------

def test_format_tracking_number():
    assert format_tracking_number(2026, 1) == "VU-2026-0001"
    assert format_tracking_number(2026, 412) == "VU-2026-0412"
    assert format_tracking_number(2026, 12345) == "VU-2026-12345"


@pytest.mark.parametrize("value, expected", [
    ("VU-2026-0001", "VU-2026-0001"),
    (" vu-2026-0412 ", "VU-2026-0412"),
    ("VU-2026-12345", "VU-2026-12345"),
    ("VU-26-1", None),
    ("VU-2026-01", None),
    ("'; DROP TABLE kerkesat; --", None),
    ("", None),
])
def test_normalize_tracking_number(value, expected):
    assert normalize_tracking_number(value) == expected


# --- public timeline --------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "status, states",
    [
        ("e_re", ["kryer", "aktual", "pritje", "pritje", "pritje"]),
        ("kategorizuar", ["kryer", "kryer", "aktual", "pritje", "pritje"]),
        ("caktuar", ["kryer", "kryer", "kryer", "aktual", "pritje"]),
        ("procesverbal", ["kryer", "kryer", "kryer", "aktual", "pritje"]),
        ("vendim_miratuar", ["kryer", "kryer", "kryer", "kryer", "aktual"]),
        ("mbyllur", ["kryer", "kryer", "kryer", "kryer", "kryer"]),
    ],
)
def test_timeline_states(status, states):
    assert [step["gjendja"] for step in public_timeline(status, None)] == states


def test_only_the_first_step_has_a_time():
    created = datetime(2026, 11, 2, 10, 24)
    steps = public_timeline("e_re", created)
    assert steps[0]["koha"] == created
    assert all(step["koha"] is None for step in steps[1:])
