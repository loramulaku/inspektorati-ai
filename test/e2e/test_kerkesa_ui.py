"""Selenium tests for the citizen portal: the public form, the confirmation
page and the tracking page. No login anywhere: citizens have no account."""

import re

import pytest
from selenium.webdriver.common.by import By
from sqlalchemy import func, select

from app.db.models import Attachment, Kerkese
from app.db.session import SessionLocal

PDF = b"%PDF-1.4\n%selenium\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 2048
TRACKING = re.compile(r"^VU-\d{4}-\d{4,}$")


@pytest.fixture
def sample_files(tmp_path):
    files = {
        "pdf": tmp_path / "leja_e_ndertimit.pdf",
        "jpg": tmp_path / "foto_trotuari.jpg",
        "txt": tmp_path / "shenime.txt",
        "fake_pdf": tmp_path / "i_rreme.pdf",
    }
    files["pdf"].write_bytes(PDF)
    files["jpg"].write_bytes(JPG)
    files["txt"].write_text("jo dokument")
    files["fake_pdf"].write_bytes(b"<html>not really a pdf</html>")
    return {key: str(path) for key, path in files.items()}


def kerkesa_count():
    with SessionLocal() as db:
        return db.scalar(select(func.count()).select_from(Kerkese))


def open_form(app):
    app.open("/kerkese")
    app.wait_text("Paraqit kërkesë ose ankesë")


def attach(app, *paths):
    app.find("#files").send_keys("\n".join(paths))


def fill_valid(app, lloji="Ankesë"):
    app.by_text(lloji, "span").click()  # the radio card
    app.type("#emri", "Arben")
    app.type("#mbiemri", "Krasniqi")
    app.type("#numri_personal", "1234567890")
    app.type("#email", "arben@example.com")
    app.type("#telefoni", "+383 44 123 456")
    app.type("#adresa", "Rruga Skënderbeu 12, Vushtrri")
    app.type("#lokacioni", "Lagjja e re, afër shkollës")
    app.type("#pershkrimi", "Trotuari është i zënë nga tavolinat e një kafeneje.")


def accept_declaration(app):
    app.by_text("Pajtohem me deklaratën e mësipërme dhe konfirmoj saktësinë e të dhënave.", "span").click()


def submit(app):
    app.by_text("Konfirmo dhe dërgo", "button").click()


# --- the page ------------------------------------------------------------------------

def test_form_shows_the_five_sections(app):
    open_form(app)
    text = app.text()
    for expected in [
        "Shërbim publik · pa llogari",
        "1. Lloji i paraqitjes", "2. Të dhënat e aplikuesit", "3. Detajet e rastit",
        "4. Dokumente dhe foto shtesë", "5. Dëshmia e aplikuesit për vërtetësi",
        "Kërkesë", "Ankesë", "Data e paraqitjes", "automatik",
        "Tërhiq skedarët këtu ose kliko për të ngarkuar",
        "Konfirmo dhe dërgo", "Pastro formularin",
        "Të dhënat tuaja përdoren vetëm për trajtimin e kësaj paraqitjeje.",
    ]:
        assert expected in text, expected
    # the submission date is filled automatically: DD.MM.YYYY · HH:mm
    assert re.fullmatch(r"\d{2}\.\d{2}\.\d{4} · \d{2}:\d{2}", app.find("[data-testid=data-paraqitjes]").text)
    # line icons (SVG), no emoji
    assert app.driver.find_elements(By.CSS_SELECTOR, "main svg")


def test_no_login_is_needed(app):
    open_form(app)
    assert app.path == "/kerkese"


# --- validation blocks the submit ------------------------------------------------------

def test_empty_form_shows_errors_and_sends_nothing(app):
    before = kerkesa_count()
    open_form(app)
    submit(app)

    app.wait_text("Kontrolloni fushat e shënuara me të kuqe dhe provoni përsëri.")
    text = app.text()
    assert "Zgjidhni llojin e paraqitjes" in text
    assert text.count("Kjo fushë është e detyrueshme") == 6  # emri, mbiemri, nr. personal, telefoni, lokacioni, përshkrimi
    assert "Duhet të pajtoheni me deklaratën" in text
    assert app.path == "/kerkese"
    assert kerkesa_count() == before


def test_invalid_values_show_their_own_messages(app):
    open_form(app)
    fill_valid(app)
    accept_declaration(app)
    app.find("#numri_personal").clear()
    app.type("#numri_personal", "12345")
    app.type("#email", "@@")
    app.find("#telefoni").clear()
    app.type("#telefoni", "abc")
    submit(app)

    app.wait_text("Numri personal duhet të ketë saktësisht 10 shifra")
    assert "Email-i nuk është i vlefshëm" in app.text()
    assert "Numri i telefonit nuk është i vlefshëm" in app.text()
    assert app.path == "/kerkese"


def test_declaration_is_required_even_when_everything_else_is_valid(app):
    before = kerkesa_count()
    open_form(app)
    fill_valid(app)
    submit(app)
    app.wait_text("Duhet të pajtoheni me deklaratën")
    assert app.path == "/kerkese"
    assert kerkesa_count() == before


def test_name_in_declaration_and_chosen_type_fill_in_live(app):
    open_form(app)
    assert "Lloji i zgjedhur: —" in app.find("[data-testid=lloji-zgjedhur]").text
    app.by_text("Kërkesë", "span").click()
    app.wait(lambda d: "Kërkesë" in d.find_element(By.CSS_SELECTOR, "[data-testid=lloji-zgjedhur]").text)

    app.type("#emri", "Arben")
    app.type("#mbiemri", "Krasniqi")
    app.wait(lambda d: "Unë, Arben Krasniqi," in d.find_element(By.CSS_SELECTOR, "[data-testid=deklarata]").text)


# --- files ------------------------------------------------------------------------------

def test_wrong_file_type_is_refused_in_the_browser(app, sample_files):
    open_form(app)
    attach(app, sample_files["txt"])
    app.wait_text("shenime.txt: Lejohen vetëm skedarë PDF, JPG ose PNG")
    assert "SKEDARËT E BASHKANGJITUR" not in app.text()


def test_attached_files_can_be_downloaded_and_removed(app, sample_files):
    open_form(app)
    # record what the "Shkarko" button hands to the browser
    app.driver.execute_script(
        "window.__downloads = []; const original = URL.createObjectURL;"
        "URL.createObjectURL = (blob) => { window.__downloads.push(blob.size); return original(blob); };"
    )
    attach(app, sample_files["pdf"], sample_files["jpg"])
    app.wait_text("SKEDARËT E BASHKANGJITUR (2)")
    text = app.text()
    assert "leja_e_ndertimit.pdf" in text and "foto_trotuari.jpg" in text
    assert "Dokument ·" in text and "Foto ·" in text

    pdf_row = app.find("li")  # first file row
    pdf_row.find_element(By.XPATH, ".//button[normalize-space()='Shkarko']").click()
    assert app.driver.execute_script("return window.__downloads") == [len(PDF)]

    app.find("button[aria-label='Hiq leja_e_ndertimit.pdf']").click()
    app.wait_text("SKEDARËT E BASHKANGJITUR (1)")
    assert "leja_e_ndertimit.pdf" not in app.text()


def test_server_rejects_a_fake_pdf_and_the_form_shows_it(app, sample_files):
    before = kerkesa_count()
    open_form(app)
    fill_valid(app)
    attach(app, sample_files["fake_pdf"])  # name says .pdf, content is not
    accept_declaration(app)
    submit(app)
    app.wait_text("Lejohen vetëm skedarë PDF, JPG ose PNG")
    assert app.path == "/kerkese"
    assert kerkesa_count() == before


# --- happy path -------------------------------------------------------------------------

def test_happy_path_submits_and_shows_the_tracking_number(app, sample_files):
    before = kerkesa_count()
    open_form(app)
    fill_valid(app, "Ankesë")
    attach(app, sample_files["pdf"], sample_files["jpg"])
    app.wait_text("SKEDARËT E BASHKANGJITUR (2)")
    accept_declaration(app)
    submit(app)

    app.wait(lambda d: "/kerkese/konfirmim/" in d.current_url, "no confirmation page")
    app.wait_text("Ankesa u dërgua me sukses")
    numri = app.find("[data-testid=numri-gjurmimit]").text
    assert TRACKING.fullmatch(numri), numri
    assert "Çfarë ndodh më pas" in app.text()

    # saved in the database with its two files
    assert kerkesa_count() == before + 1
    with SessionLocal() as db:
        kerkese = db.scalar(select(Kerkese).where(Kerkese.numri_gjurmimit == numri))
        assert kerkese.deklarata_emri == "Arben Krasniqi"
        assert kerkese.status == "e_re" and kerkese.kanali == "portal"
        assert db.scalar(select(func.count()).select_from(Attachment).where(Attachment.kerkesa_id == kerkese.id)) == 2

    # follow it on the tracking page
    app.click_text("Gjurmo statusin tani", "a")
    app.wait_path(f"/gjurmo/{numri}")
    app.wait_text(f"Ankesë {numri}")
    result = app.find("[data-testid=rezultati]").text
    assert "E RE" in result
    for step in ["Kërkesa u pranua", "Kategorizuar nga sistemi", "Caktuar inspektorit", "Inspektim në terren", "Vendimi"]:
        assert step in result
    assert "në proces" in result and "në pritje" in result
    # no personal data on the public page
    for private in ["Arben", "Krasniqi", "1234567890", "+383 44 123 456", "Lagjja e re"]:
        assert private not in app.text()


def test_clear_button_empties_the_form(app, sample_files):
    open_form(app)
    fill_valid(app)
    attach(app, sample_files["pdf"])
    accept_declaration(app)
    app.wait_text("SKEDARËT E BASHKANGJITUR (1)")

    app.click_text("Pastro formularin", "button")
    for field in ["emri", "mbiemri", "numri_personal", "email", "telefoni", "adresa", "lokacioni", "pershkrimi"]:
        assert app.find(f"#{field}").get_attribute("value") == ""
    assert "SKEDARËT E BASHKANGJITUR" not in app.text()
    assert not app.find("#deklarata_pranuar").is_selected()
    assert "Lloji i zgjedhur: —" in app.find("[data-testid=lloji-zgjedhur]").text


# --- tracking page ---------------------------------------------------------------------

def test_tracking_unknown_number_shows_error(app):
    app.open("/gjurmo")
    app.wait_text("Gjurmo kërkesën tënde")
    app.type("#numri", "vu-2026-9999")
    app.click_text("Gjurmo", "button")
    app.wait_path("/gjurmo/VU-2026-9999")
    app.wait_text("Nuk u gjet asnjë kërkesë me këtë numër")


def test_tracking_with_a_wrong_format_explains_it(app):
    app.open("/gjurmo/abc")
    app.wait_text("Shkruani numrin në formatin VU-2026-0001")


def test_landing_and_header_link_to_tracking(app):
    app.open("/")
    app.click_text("Gjurmo kërkesën", "a")
    app.wait_path("/gjurmo")
    app.click_text("Kreu", "a")
    app.wait_path("/")
