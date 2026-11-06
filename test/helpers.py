"""Values shared by several test files."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

# The tests' own database; the real `inspektorati` is never used by tests.
TEST_DB_NAME = "inspektorati_test"

# Password given to every user the tests create.
PASSWORD = "Fjalekalim!1"
