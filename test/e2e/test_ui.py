"""Selenium end-to-end tests: a real browser clicking through the real app.

Covers the public pages, login, the welcome message, role-based routing,
session restore and logout, and the admin user management page.
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

ROLE_HOME = {"inspektor": "/inspektor", "drejtor": "/drejtor", "admin": "/admin"}
ROLE_LABEL = {"inspektor": "Inspektor", "drejtor": "Drejtor", "admin": "Admin"}
ROLE_TITLE = {"inspektor": "Inspektor komunal", "drejtor": "Drejtor", "admin": "Administrator"}
ADMIN_NOTE = "Llogaritë krijohen nga administratori i inspektoratit."


def stema_loaded(app):
    return app.driver.execute_script(
        "return [...document.images].some(i => i.src.endsWith('/stema.svg') && i.complete && i.naturalWidth > 0)"
    )


def row_for(app, email):
    """The users-table row that contains `email`."""
    return app.wait(lambda d: d.find_element(By.XPATH, f"//tr[td[normalize-space()='{email}']]"))


# --- public pages --------------------------------------------------------------------

def test_landing_page(app):
    app.open("/")
    app.wait_text("Raporto problemin.")
    text = app.text()
    assert "Inspektorati AI" in app.driver.title
    for expected in ["Inspektorati vepron.", "Paraqit kërkesë / ankesë si qytetar", "Kyçu si zyrtar",
                     "Mbështetje nga AI për kategorizim dhe propozim vendimi", ADMIN_NOTE]:
        assert expected in text
    assert "krijo llogari" not in text.lower()
    assert stema_loaded(app)


def test_citizen_button_opens_request_page_without_login(app):
    app.open("/")
    app.click_text("Paraqit kërkesë / ankesë si qytetar →", "a")
    app.wait_path("/kerkese")
    app.wait_text("Paraqit kërkesë ose ankesë")
    assert "Shërbim publik · pa llogari" in app.text()
    app.click_text("Kreu", "a")
    app.wait_path("/")


@pytest.mark.parametrize("where", ["header", "main"])
def test_staff_button_opens_login(app, where):
    app.open("/")
    app.wait(lambda d: d.find_element(By.XPATH, f"//{where}//a[normalize-space()='Kyçu si zyrtar']")).click()
    app.wait_path("/kycu")


def test_login_page_content(app):
    app.open("/kycu")
    app.wait_text("Mirë se vini")
    text = app.text()
    for expected in ["Prano kërkesën.", "Inspekto.", "Vendos me ligj.", "Kyçuni në llogarinë tuaj të stafit",
                     "Kategorizim i asistuar nga AI", "Lidhje me bazën ligjore", ADMIN_NOTE]:
        assert expected in text
    assert "krijo llogari" not in text.lower()
    assert stema_loaded(app)
    app.click_text("← Kthehu te faqja kryesore", "a")
    app.wait_path("/")


def test_register_page_does_not_exist(app):
    app.open("/regjistrohu")
    app.wait_path("/")


def test_unknown_page_goes_home(app):
    app.open("/kjo-faqe-nuk-ekziston")
    app.wait_path("/")


# --- login form ----------------------------------------------------------------------

def test_login_with_empty_fields_shows_error(app):
    app.open("/kycu")
    app.find("button[type=submit]").click()
    app.wait_text("Shkruani email-in dhe fjalëkalimin.")
    assert app.path == "/kycu"


def test_login_with_wrong_password_shows_error(app, seed_users):
    app.login(seed_users["admin"]["email"], "Gabim!12345")
    app.wait_text("Email ose fjalëkalim i pasaktë")
    assert app.path == "/kycu"


def test_login_with_unknown_email_shows_same_error(app):
    app.login("askush@example.com", "Gabim!12345")
    app.wait_text("Email ose fjalëkalim i pasaktë")


def test_password_can_be_shown_and_hidden(app):
    app.open("/kycu")
    password = app.find("#password")
    password.send_keys("Sekret!1")
    assert password.get_attribute("type") == "password"
    app.find("button[aria-label='Shfaq fjalëkalimin']").click()
    assert password.get_attribute("type") == "text"
    app.find("button[aria-label='Fshih fjalëkalimin']").click()
    assert password.get_attribute("type") == "password"


def test_login_with_enter_key(app, seed_users):
    inspektor = seed_users["inspektor"]
    app.open("/kycu")
    app.type("#email", inspektor["email"])
    app.type("#password", inspektor["password"] + Keys.ENTER)
    app.wait_path("/inspektor")


# --- logged out: protected pages -------------------------------------------------------

@pytest.mark.parametrize("path", ["/inspektor", "/drejtor", "/admin", "/admin/perdoruesit"])
def test_protected_pages_need_login(app, path):
    app.open(path)
    app.wait_path("/kycu")


# --- each role ---------------------------------------------------------------------------

@pytest.mark.parametrize("role", ["inspektor", "drejtor", "admin"])
def test_role_logs_in_to_own_dashboard_with_welcome(app, seed_users, role):
    user = seed_users[role]
    app.login(user["email"], user["password"], expect_path=ROLE_HOME[role])

    app.wait_text(f"Mirë se erdhe, {user['emri']}! Roli juaj është {ROLE_LABEL[role]}.")
    app.wait_text("LEJUAR")  # the role's protected API route answered 200
    text = app.text()
    assert f"GET /{role}/paneli" in text
    assert f"{user['emri']} {user['mbiemri']}" in text
    assert ROLE_TITLE[role] in text
    assert stema_loaded(app)


@pytest.mark.parametrize(
    "role, forbidden",
    [("inspektor", "/admin/perdoruesit"), ("inspektor", "/drejtor"), ("drejtor", "/admin"), ("admin", "/inspektor")],
)
def test_wrong_role_is_sent_to_own_dashboard(app, seed_users, role, forbidden):
    user = seed_users[role]
    app.login(user["email"], user["password"], expect_path=ROLE_HOME[role])
    app.open(forbidden)
    app.wait_path(ROLE_HOME[role])


def test_logged_in_user_opening_login_goes_to_dashboard(app, seed_users):
    drejtor = seed_users["drejtor"]
    app.login(drejtor["email"], drejtor["password"], expect_path="/drejtor")
    app.open("/kycu")
    app.wait_path("/drejtor")


def test_only_admin_sees_user_management_menu(app, seed_users):
    inspektor = seed_users["inspektor"]
    app.login(inspektor["email"], inspektor["password"], expect_path="/inspektor")
    app.wait_text("LEJUAR")
    assert "Përdoruesit & rolet" not in app.text()


# --- welcome message, session, logout ------------------------------------------------------

def test_welcome_can_be_closed_and_shows_only_once(app, seed_users):
    inspektor = seed_users["inspektor"]
    welcome = f"Mirë se erdhe, {inspektor['emri']}!"
    app.login(inspektor["email"], inspektor["password"], expect_path="/inspektor")
    app.wait_text(welcome)

    app.find("button[aria-label='Mbyll']").click()
    app.wait_text_gone(welcome)

    app.driver.refresh()
    app.wait_text("LEJUAR")
    assert welcome not in app.text()


def test_session_survives_page_reload(app, seed_users):
    drejtor = seed_users["drejtor"]
    app.login(drejtor["email"], drejtor["password"], expect_path="/drejtor")
    assert app.local_storage("inspektorati.refreshToken")

    app.driver.refresh()
    app.wait_text("LEJUAR")
    assert app.path == "/drejtor"
    assert f"{drejtor['emri']} {drejtor['mbiemri']}" in app.text()


def test_logout_ends_the_session(app, seed_users):
    inspektor = seed_users["inspektor"]
    app.login(inspektor["email"], inspektor["password"], expect_path="/inspektor")
    app.logout()

    assert app.local_storage("inspektorati.refreshToken") is None
    app.open("/inspektor")
    app.wait_path("/kycu")


# --- admin: user management -------------------------------------------------------------------

def test_admin_dashboard_links_to_user_management(app, seed_users):
    admin = seed_users["admin"]
    app.login(admin["email"], admin["password"], expect_path="/admin")
    app.click_text("Menaxho përdoruesit →", "a")
    app.wait_path("/admin/perdoruesit")
    app.wait_text(admin["email"])


def test_admin_creates_user_who_can_then_log_in(app, seed_users):
    admin = seed_users["admin"]
    email = "selenium.i.ri@example.com"
    app.login(admin["email"], admin["password"], expect_path="/admin")
    app.open("/admin/perdoruesit")
    app.click_text("+ Shto përdorues", "button")

    app.type("#u-emri", "Besa")
    app.type("#u-mbiemri", "Selenium")
    app.type("#u-email", email)
    app.type("#u-password", "Besa!12345")
    app.click_text("Krijo llogarinë", "button")

    app.wait_text("Llogaria për Besa Selenium u krijua.")
    row = row_for(app, email)
    assert "Inspektor" in row.text and "Aktiv" in row.text

    app.logout()
    app.login(email, "Besa!12345", expect_path="/inspektor")
    app.wait_text("Mirë se erdhe, Besa! Roli juaj është Inspektor.")


def test_admin_cannot_create_user_with_taken_email(app, seed_users):
    admin = seed_users["admin"]
    app.login(admin["email"], admin["password"], expect_path="/admin")
    app.open("/admin/perdoruesit")
    app.click_text("+ Shto përdorues", "button")
    app.type("#u-emri", "Dyfish")
    app.type("#u-mbiemri", "Email")
    app.type("#u-email", seed_users["inspektor"]["email"])
    app.type("#u-password", "Dyfish!123")
    app.click_text("Krijo llogarinë", "button")
    app.wait_text("Ky email është tashmë i regjistruar")


def test_admin_edits_user(app, seed_users, api):
    user = api.create_user("inspektor", emri="Vjeter")
    admin = seed_users["admin"]
    app.login(admin["email"], admin["password"], expect_path="/admin")
    app.open("/admin/perdoruesit")

    row_for(app, user["email"]).find_element(By.XPATH, ".//button[normalize-space()='Modifiko']").click()
    name = app.find("#u-emri")
    assert name.get_attribute("value") == "Vjeter"
    name.send_keys(Keys.CONTROL, "a")
    name.send_keys("Ndryshuar")
    app.click_text("Ruaj ndryshimet", "button")

    app.wait_text("Ndryshimet u ruajtën.")
    assert "Ndryshuar Selenium" in row_for(app, user["email"]).text


def test_admin_deactivates_and_reactivates_user(app, seed_users, api):
    user = api.create_user("drejtor")
    admin = seed_users["admin"]
    app.login(admin["email"], admin["password"], expect_path="/admin")
    app.open("/admin/perdoruesit")

    row_for(app, user["email"]).find_element(By.XPATH, ".//button[normalize-space()='Çaktivizo']").click()
    app.wait(lambda d: d.switch_to.alert).accept()  # the "are you sure?" dialog
    app.wait_text(f"Llogaria e {user['emri']} {user['mbiemri']} u çaktivizua.")
    assert "Joaktiv" in row_for(app, user["email"]).text

    # the deactivated user is locked out
    app.logout()
    app.login(user["email"], user["password"])
    app.wait_text("Llogaria juaj është çaktivizuar")

    # reactivate, then the user can log in again
    app.login(admin["email"], admin["password"], expect_path="/admin")
    app.open("/admin/perdoruesit")
    row_for(app, user["email"]).find_element(By.XPATH, ".//button[normalize-space()='Aktivizo']").click()
    app.wait_text(f"Llogaria e {user['emri']} {user['mbiemri']} u aktivizua.")
    app.logout()
    app.login(user["email"], user["password"], expect_path="/drejtor")


def test_admin_cannot_deactivate_own_account(app, seed_users):
    admin = seed_users["admin"]
    app.login(admin["email"], admin["password"], expect_path="/admin")
    app.open("/admin/perdoruesit")
    own_row = row_for(app, admin["email"])
    assert "(ju)" in own_row.text
    assert own_row.find_elements(By.XPATH, ".//button[normalize-space()='Çaktivizo']") == []


def test_cancel_closes_the_user_form(app, seed_users):
    admin = seed_users["admin"]
    app.login(admin["email"], admin["password"], expect_path="/admin")
    app.open("/admin/perdoruesit")
    app.click_text("+ Shto përdorues", "button")
    app.find("#u-emri")
    app.click_text("Anulo", "button")
    app.wait(lambda d: not d.find_elements(By.CSS_SELECTOR, "#u-emri"), "form did not close")
