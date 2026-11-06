"""Integration tests for the public citizen portal:
POST /kerkesa, GET /kerkesa/gjurmo/{numri}, GET /attachments/{id}/download.
"""

import re
from datetime import datetime

import pytest
from sqlalchemy import func, select, text

from app.core import config
from app.db.models import Attachment, Kerkese, Lokacion

PDF = b"%PDF-1.4\n%test\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64

VALID = {
    "lloji": "ankese",
    "emri": "Arben",
    "mbiemri": "Krasniqi",
    "numri_personal": "1234567890",
    "email": "arben@example.com",
    "telefoni": "+383 44 123 456",
    "adresa": "Rruga Skënderbeu 12, Vushtrri",
    "lokacioni": "Lagjja e re, afër shkollës",
    "pershkrimi": "Trotuari është i zënë nga një kafene.\nKalimtarët ecin në rrugë.",
    "deklarata_pranuar": "true",
}
PERSONAL_VALUES = ["Arben", "Krasniqi", "1234567890", "arben@example.com", "+383 44 123 456",
                   "Skënderbeu", "Lagjja e re", "kafene"]


def submit(client, files=(), **changes):
    data = {**VALID, **changes}
    data = {k: v for k, v in data.items() if v is not None}
    return client.post("/kerkesa", data=data, files=[("files", f) for f in files])


def count(db, model):
    db.commit()  # fresh snapshot
    return db.scalar(select(func.count()).select_from(model))


def errors(response):
    return {e["loc"][1]: e["msg"].removeprefix("Value error, ") for e in response.json()["detail"]}


# --- valid submission ------------------------------------------------------------------

def test_valid_submission_creates_kerkesa_location_and_files(client, db):
    response = submit(client, files=[("leja.pdf", PDF, "application/pdf"), ("foto.jpg", JPG, "image/jpeg")])
    assert response.status_code == 201, response.text
    body = response.json()
    assert re.fullmatch(rf"VU-{datetime.now().year}-\d{{4}}", body["numri_gjurmimit"])
    assert body["status"] == "e_re"
    assert body["created_at"]

    db.commit()
    kerkese = db.scalar(select(Kerkese).where(Kerkese.numri_gjurmimit == body["numri_gjurmimit"]))
    assert kerkese.lloji == "ankese"
    assert kerkese.kanali == "portal"
    assert kerkese.status == "e_re"
    assert kerkese.aplikuesi_emri == "Arben" and kerkese.aplikuesi_mbiemri == "Krasniqi"
    assert kerkese.aplikuesi_numri_personal == "1234567890"
    assert kerkese.aplikuesi_email == "arben@example.com"
    assert kerkese.aplikuesi_telefoni == "+383 44 123 456"
    assert kerkese.deklarata_pranuar is True
    assert kerkese.deklarata_emri == "Arben Krasniqi"
    assert kerkese.teksti_origjinal.startswith("Trotuari është i zënë")
    assert kerkese.kategori_id is None and kerkese.urgjenca is None  # filled later, not at intake

    location = db.get(Lokacion, kerkese.lokacion_id)
    assert location.pershkrimi == "Lagjja e re, afër shkollës"

    attachments = db.scalars(select(Attachment).where(Attachment.kerkesa_id == kerkese.id)).all()
    assert sorted(a.lloji for a in attachments) == ["dokument", "foto"]
    for attachment in attachments:
        stored = config.UPLOAD_DIR / attachment.path
        assert stored.is_file()
        # never the client's file name: a random name in the kërkesa's folder
        assert re.fullmatch(rf"kerkesat/{kerkese.id}/[0-9a-f]{{32}}\.(pdf|jpg)", attachment.path)
    assert {(config.UPLOAD_DIR / a.path).read_bytes() for a in attachments} == {PDF, JPG}


def test_submission_without_files_and_optional_fields(client, db):
    response = submit(client, email=None, adresa="", lloji="kerkese")
    assert response.status_code == 201, response.text
    db.commit()
    kerkese = db.scalar(select(Kerkese))
    assert kerkese.lloji == "kerkese"
    assert kerkese.aplikuesi_email is None and kerkese.aplikuesi_adresa is None
    assert count(db, Attachment) == 0


def test_two_submissions_get_different_sequential_numbers(client):
    first = submit(client).json()["numri_gjurmimit"]
    second = submit(client).json()["numri_gjurmimit"]
    assert first != second
    assert int(second.rsplit("-", 1)[1]) == int(first.rsplit("-", 1)[1]) + 1


def test_numbering_continues_after_the_highest_number(client, db):
    year = datetime.now().year
    submit(client)
    db.execute(text("UPDATE kerkesat SET numri_gjurmimit = :n"), {"n": f"VU-{year}-0041"})
    db.commit()
    assert submit(client).json()["numri_gjurmimit"] == f"VU-{year}-0042"


def test_input_is_cleaned(client, db):
    response = submit(client, emri="  Arben\u0000  ", lokacioni="Lagjja   e re\t", pershkrimi="  Rresht 1\r\n\r\n\r\n\r\nRresht 2  ")
    assert response.status_code == 201
    db.commit()
    kerkese = db.scalar(select(Kerkese))
    assert kerkese.aplikuesi_emri == "Arben"
    assert db.get(Lokacion, kerkese.lokacion_id).pershkrimi == "Lagjja e re"
    assert kerkese.teksti_origjinal == "Rresht 1\n\nRresht 2"


# --- rejected input --------------------------------------------------------------------------

@pytest.mark.parametrize("field", ["lloji", "emri", "mbiemri", "numri_personal", "telefoni", "lokacioni", "pershkrimi"])
def test_missing_required_field_is_rejected(client, db, field):
    response = submit(client, **{field: None})
    assert response.status_code == 422
    assert field in errors(response)
    assert count(db, Kerkese) == 0


@pytest.mark.parametrize("field", ["emri", "lokacioni", "pershkrimi", "telefoni"])
def test_blank_required_field_is_rejected(client, field):
    response = submit(client, **{field: "   "})
    assert response.status_code == 422
    assert errors(response)[field] == "Kjo fushë është e detyrueshme"


@pytest.mark.parametrize(
    "field, value, message",
    [
        ("numri_personal", "123456789", "Numri personal duhet të ketë saktësisht 10 shifra"),
        ("numri_personal", "12345678901", "Numri personal duhet të ketë saktësisht 10 shifra"),
        ("numri_personal", "12345abcde", "Numri personal duhet të ketë saktësisht 10 shifra"),
        ("email", "jo-email", "Email-i nuk është i vlefshëm"),
        ("telefoni", "abc", "Numri i telefonit nuk është i vlefshëm"),
        ("telefoni", "12345", "Numri i telefonit nuk është i vlefshëm"),
        ("lloji", "tjeter", "Zgjidhni llojin e paraqitjes"),
        ("emri", "12345", "Shkruani një emër të vlefshëm"),
        ("lokacioni", "x" * 256, "Teksti është shumë i gjatë (maksimumi 255 karaktere)"),
        ("pershkrimi", "x" * 5001, "Teksti është shumë i gjatë (maksimumi 5000 karaktere)"),
    ],
)
def test_invalid_field_is_rejected(client, db, field, value, message):
    response = submit(client, **{field: value})
    assert response.status_code == 422
    assert errors(response)[field] == message
    assert count(db, Kerkese) == 0


@pytest.mark.parametrize("value", [None, "false", ""])
def test_declaration_not_accepted_is_rejected(client, db, value):
    response = submit(client, deklarata_pranuar=value)
    assert response.status_code == 422
    assert errors(response)["deklarata_pranuar"] == "Duhet të pajtoheni me deklaratën"
    assert count(db, Kerkese) == 0


# --- rejected files: nothing is saved ---------------------------------------------------------

def no_rows_and_no_files(db):
    return count(db, Kerkese) == 0 and count(db, Lokacion) == 0 and count(db, Attachment) == 0


@pytest.mark.parametrize(
    "upload",
    [
        ("dokument.docx", b"PK\x03\x04 word file", "application/vnd.openxmlformats"),
        ("skript.exe", b"MZ\x90\x00", "application/octet-stream"),
        ("i_rremë.pdf", b"<html>not a pdf</html>", "application/pdf"),  # lies about its type
        ("foto.png", b"GIF89a....", "image/png"),
    ],
)
def test_wrong_file_type_is_rejected(client, db, upload):
    response = submit(client, files=[("leja.pdf", PDF, "application/pdf"), upload])
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Lejohen vetëm skedarë PDF, JPG ose PNG"
    assert response.json()["detail"][0]["loc"] == ["body", "files", 1]
    assert no_rows_and_no_files(db)


def test_file_over_10_mb_is_rejected(client, db):
    big = PDF + b"0" * (10 * 1024 * 1024)
    response = submit(client, files=[("i_madh.pdf", big, "application/pdf")])
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Skedari është më i madh se 10 MB"
    assert no_rows_and_no_files(db)


def test_file_of_exactly_10_mb_is_accepted(client):
    exact = PDF + b"0" * (10 * 1024 * 1024 - len(PDF))
    assert submit(client, files=[("plot.pdf", exact, "application/pdf")]).status_code == 201


def test_empty_file_is_rejected(client):
    response = submit(client, files=[("bosh.pdf", b"", "application/pdf")])
    assert response.status_code == 422


def test_more_than_10_files_is_rejected(client, db):
    response = submit(client, files=[(f"f{i}.png", PNG, "image/png") for i in range(11)])
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Mund të bashkangjitni deri në 10 skedarë"
    assert no_rows_and_no_files(db)


def test_files_are_removed_if_saving_fails(client, db, monkeypatch):
    from app.services import kerkesa as service

    def broken_commit(*args, **kwargs):
        raise RuntimeError("database down")

    monkeypatch.setattr(service.Session, "commit", broken_commit, raising=False)
    folder = config.UPLOAD_DIR / "kerkesat"
    before = set(folder.rglob("*")) if folder.exists() else set()
    with pytest.raises(RuntimeError):
        submit(client, files=[("leja.pdf", PDF, "application/pdf")])
    monkeypatch.undo()
    after = set(folder.rglob("*")) if folder.exists() else set()
    assert after == before
    assert no_rows_and_no_files(db)


# --- tracking ---------------------------------------------------------------------------------

def test_tracking_returns_status_and_timeline_without_personal_data(client):
    numri = submit(client).json()["numri_gjurmimit"]
    response = client.get(f"/kerkesa/gjurmo/{numri}")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"numri_gjurmimit", "lloji", "status", "created_at", "timeline"}
    assert body["numri_gjurmimit"] == numri
    assert body["lloji"] == "ankese"
    assert body["status"] == "e_re"
    assert [step["titulli"] for step in body["timeline"]] == [
        "Kërkesa u pranua", "Kategorizuar nga sistemi", "Caktuar inspektorit", "Inspektim në terren", "Vendimi",
    ]
    assert [step["gjendja"] for step in body["timeline"]] == ["kryer", "aktual", "pritje", "pritje", "pritje"]
    assert body["timeline"][0]["koha"]

    raw = response.text
    for value in PERSONAL_VALUES:
        assert value not in raw


def test_tracking_follows_the_status(client, db):
    numri = submit(client).json()["numri_gjurmimit"]
    db.execute(text("UPDATE kerkesat SET status = 'ne_terren'"))
    db.commit()
    body = client.get(f"/kerkesa/gjurmo/{numri}").json()
    assert body["status"] == "ne_terren"
    assert [s["gjendja"] for s in body["timeline"]] == ["kryer", "kryer", "kryer", "aktual", "pritje"]


def test_tracking_number_is_case_insensitive(client):
    numri = submit(client).json()["numri_gjurmimit"]
    assert client.get(f"/kerkesa/gjurmo/{numri.lower()}").status_code == 200


@pytest.mark.parametrize("numri", ["VU-2026-9999", "abc", "VU-26-1"])
def test_unknown_tracking_number_is_404(client, numri):
    response = client.get(f"/kerkesa/gjurmo/{numri}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Nuk u gjet asnjë kërkesë me këtë numër"


def test_portal_routes_need_no_login(client):
    assert submit(client).status_code == 201  # no Authorization header at all


# --- attachment download (staff only) ------------------------------------------------------------

def test_staff_can_download_attachment(client, db, make_user, login, auth_header):
    submit(client, files=[("leja.pdf", PDF, "application/pdf")])
    db.commit()
    attachment = db.scalar(select(Attachment))
    token = login(make_user("inspektor").email)["access_token"]

    response = client.get(f"/attachments/{attachment.id}/download", headers=auth_header(token))
    assert response.status_code == 200
    assert response.content == PDF
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]


def test_download_needs_login(client, db):
    submit(client, files=[("foto.png", PNG, "image/png")])
    db.commit()
    attachment = db.scalar(select(Attachment))
    assert client.get(f"/attachments/{attachment.id}/download").status_code == 401


def test_download_unknown_attachment_is_404(client, make_user, login, auth_header):
    token = login(make_user("admin").email)["access_token"]
    assert client.get("/attachments/9999/download", headers=auth_header(token)).status_code == 404


def test_download_refuses_paths_outside_upload_folder(client, db, make_user, login, auth_header):
    submit(client, files=[("foto.png", PNG, "image/png")])
    db.execute(text("UPDATE attachments SET path = '../../../windows/win.ini'"))
    db.commit()
    attachment = db.scalar(select(Attachment))
    token = login(make_user("admin").email)["access_token"]
    assert client.get(f"/attachments/{attachment.id}/download", headers=auth_header(token)).status_code == 404
