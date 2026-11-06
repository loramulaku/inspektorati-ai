"""Fixtures for the Selenium (end-to-end) tests.

The tests start their OWN servers, so they never touch your real database or
the servers you run while developing:
    backend   http://localhost:8001  (uvicorn, database `inspektorati_test`)
    frontend  http://localhost:5180  (Vite, calls the backend on 8001)
The three seed users (admin / inspektor / drejtor) are created in the test
database first. Every test gets a fresh browser (empty localStorage).

Browser: Microsoft Edge, headless. Selenium downloads the matching driver
by itself on the first run (needs internet once).
    E2E_BROWSER=chrome   use Chrome instead of Edge
    E2E_HEADED=1         show the browser window while the tests run
"""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from urllib.parse import urlparse

import pytest
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from helpers import BACKEND_DIR, FRONTEND_DIR, PASSWORD, TEST_DB_NAME

API_PORT = 8001
WEB_PORT = 5180
API_URL = f"http://localhost:{API_PORT}"
WEB_URL = f"http://localhost:{WEB_PORT}"
# Generous: on a first run Vite may still be pre-bundling packages.
WAIT_SECONDS = 30


def _port_in_use(port):
    with socket.socket() as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _wait_until_up(url, process, log_path, name):
    deadline = time.time() + 60
    while time.time() < deadline:
        if process.poll() is not None:
            break
        try:
            urllib.request.urlopen(url, timeout=2)
            return
        except Exception:
            time.sleep(0.5)
    log = log_path.read_text(encoding="utf-8", errors="replace")[-2000:]
    pytest.fail(f"{name} did not start at {url}. Last log lines:\n{log}")


def _warm_up_frontend():
    """Load the app once in a browser before the tests, so Vite finishes
    pre-bundling its packages (which can briefly reload the page) up front."""
    browser = _new_driver()
    try:
        browser.get(f"{WEB_URL}/kerkese")
        WebDriverWait(browser, 60).until(
            lambda d: "Paraqit kërkesë ose ankesë" in d.find_element(By.TAG_NAME, "body").text
        )
    finally:
        browser.quit()


def _stop(process):
    if process.poll() is None:
        if os.name == "nt":
            # npm / uvicorn start child processes; /T stops the whole tree.
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
        else:
            process.terminate()
        process.wait(timeout=15)


@pytest.fixture(scope="session")
def seed_users(test_database):
    """Create the seed accounts in the test database; returns them by role."""
    from scripts.seed_users import TEST_USERS, main as seed

    seed()
    return {user["role"]: user for user in TEST_USERS}


@pytest.fixture(scope="session")
def servers(seed_users, tmp_path_factory):
    for port in (API_PORT, WEB_PORT):
        if _port_in_use(port):
            pytest.fail(f"Port {port} is already in use; the Selenium tests need it free.")

    logs = tmp_path_factory.mktemp("server-logs")
    api_log, web_log = logs / "backend.log", logs / "frontend.log"

    api_env = {**os.environ, "DB_NAME": TEST_DB_NAME, "FRONTEND_ORIGIN": WEB_URL}
    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(API_PORT)],
        cwd=BACKEND_DIR, env=api_env, stdout=api_log.open("w"), stderr=subprocess.STDOUT,
    )
    web_env = {**os.environ, "VITE_API_URL": API_URL}
    npm = "npm.cmd" if os.name == "nt" else "npm"
    web = subprocess.Popen(
        [npm, "run", "dev", "--", "--port", str(WEB_PORT), "--strictPort"],
        cwd=FRONTEND_DIR, env=web_env, stdout=web_log.open("w"), stderr=subprocess.STDOUT,
    )
    try:
        _wait_until_up(f"{API_URL}/docs", api, api_log, "Backend")
        _wait_until_up(f"{WEB_URL}/", web, web_log, "Frontend")
        _warm_up_frontend()
        yield {"api": API_URL, "web": WEB_URL}
    finally:
        _stop(web)
        _stop(api)


def _new_driver():
    headed = os.getenv("E2E_HEADED") == "1"
    if os.getenv("E2E_BROWSER", "edge").lower() == "chrome":
        options = webdriver.ChromeOptions()
        factory = webdriver.Chrome
    else:
        options = webdriver.EdgeOptions()
        factory = webdriver.Edge
    if not headed:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1024")
    options.add_argument("--disable-gpu")
    return factory(options=options)


@pytest.fixture
def driver(servers):
    browser = _new_driver()
    yield browser
    browser.quit()


class App:
    """Small helper around the WebDriver so the tests read like user steps."""

    def __init__(self, driver, base_url):
        self.driver = driver
        self.base = base_url

    # navigation -------------------------------------------------------------
    def open(self, path):
        self.driver.get(self.base + path)

    @property
    def path(self):
        return urlparse(self.driver.current_url).path

    def wait(self, condition, message=""):
        return WebDriverWait(self.driver, WAIT_SECONDS).until(condition, message)

    def wait_path(self, path):
        self.wait(lambda d: urlparse(d.current_url).path == path, f"URL path never became {path}")

    # page content -----------------------------------------------------------
    def text(self):
        return self.driver.find_element(By.TAG_NAME, "body").text

    def wait_text(self, text):
        self.wait(lambda d: text in d.find_element(By.TAG_NAME, "body").text, f"Text never appeared: {text}")

    def wait_text_gone(self, text):
        self.wait(lambda d: text not in d.find_element(By.TAG_NAME, "body").text, f"Text never went away: {text}")

    def find(self, css):
        return self.wait(lambda d: d.find_element(By.CSS_SELECTOR, css))

    def by_text(self, text, tag="*"):
        """The element whose visible text is exactly `text`."""
        xpath = f"//{tag}[normalize-space()={json.dumps(text, ensure_ascii=False)}]"
        return self.wait(lambda d: d.find_element(By.XPATH, xpath))

    def click_text(self, text, tag="*"):
        """Click the element with this text. If React re-renders it right at that
        moment (stale element / covered), look it up again and retry."""
        xpath = f"//{tag}[normalize-space()={json.dumps(text, ensure_ascii=False)}]"

        def click(d):
            try:
                d.find_element(By.XPATH, xpath).click()
                return True
            except (StaleElementReferenceException, ElementClickInterceptedException, NoSuchElementException):
                return False

        self.wait(click, f"Could not click: {text}")

    def type(self, css, value):
        self.find(css).send_keys(value)

    def local_storage(self, key):
        return self.driver.execute_script("return window.localStorage.getItem(arguments[0])", key)

    # user actions -----------------------------------------------------------
    def login(self, email, password, expect_path=None):
        self.open("/kycu")
        self.type("#email", email)
        self.type("#password", password)
        self.find("button[type=submit]").click()
        if expect_path:
            self.wait_path(expect_path)

    def logout(self):
        self.click_text("Dil", "button")
        self.wait_path("/kycu")


@pytest.fixture
def app(driver, servers):
    return App(driver, servers["web"])


class Api:
    """Direct calls to the test backend, to prepare data quickly."""

    def __init__(self, base_url, admin):
        self.base = base_url
        self.admin = admin

    def _call(self, method, path, body=None, token=None):
        request = urllib.request.Request(
            self.base + path, data=json.dumps(body).encode() if body is not None else None, method=method
        )
        request.add_header("Content-Type", "application/json")
        if token:
            request.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.loads(response.read() or "null")
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read() or "null")

    def admin_token(self):
        status, body = self._call("POST", "/auth/login", {"email": self.admin["email"], "password": self.admin["password"]})
        assert status == 200, body
        return body["access_token"]

    def create_user(self, role="inspektor", emri="Test"):
        """Create a staff user through the admin API; returns its data + password."""
        email = f"e2e.{role}.{uuid.uuid4().hex[:8]}@example.com"
        status, body = self._call(
            "POST", "/admin/users",
            {"emri": emri, "mbiemri": "Selenium", "email": email, "password": PASSWORD, "role": role},
            token=self.admin_token(),
        )
        assert status == 201, body
        return {**body, "password": PASSWORD}


@pytest.fixture
def api(servers, seed_users):
    return Api(servers["api"], seed_users["admin"])
