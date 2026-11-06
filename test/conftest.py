"""Shared pytest setup for all backend tests.

Three layers, each in its own folder (and marked automatically):
    test/unit/         unit tests: single functions, no database, no server
    test/integration/  API + real MySQL test database (FastAPI TestClient)
    test/e2e/          Selenium: real browser, real backend and frontend servers

Every layer that needs a database uses `inspektorati_test`, never the real
`inspektorati`. It is dropped, recreated and migrated with Alembic once per
test run.

Run from the project root:
    backend\\venv\\Scripts\\python.exe -m pytest                  (everything)
    backend\\venv\\Scripts\\python.exe -m pytest test\\unit       (one layer)
"""

import os
import sys
import tempfile

from helpers import BACKEND_DIR, TEST_DB_NAME

# Must be set before any app module is imported: app.core.config reads them.
os.environ["DB_NAME"] = TEST_DB_NAME
# Uploaded test files go to a throw-away folder, never to backend/uploads.
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="inspektorati-test-uploads-")
sys.path.insert(0, str(BACKEND_DIR))

import mysql.connector
import pytest
from alembic import command
from alembic.config import Config

from app.core import config
from app.db.session import engine

LAYERS = ("unit", "integration", "e2e")


def pytest_collection_modifyitems(items):
    """Mark each test with its layer (folder name), so `-m unit` etc. works."""
    for item in items:
        for layer in LAYERS:
            if layer in item.path.parts:
                item.add_marker(getattr(pytest.mark, layer))


@pytest.fixture(scope="session")
def test_database():
    """A fresh, fully migrated `inspektorati_test` database for this test run."""
    assert config.DB_NAME == TEST_DB_NAME, "Tests must never run on the real database"
    server = mysql.connector.connect(
        host=config.DB_HOST, port=config.DB_PORT, user=config.DB_USER, password=config.DB_PASSWORD
    )
    cursor = server.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS `{TEST_DB_NAME}`")
    cursor.execute(
        f"CREATE DATABASE `{TEST_DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    server.close()

    command.upgrade(Config(str(BACKEND_DIR / "alembic.ini")), "head")
    yield TEST_DB_NAME
    engine.dispose()
