"""Tiny DB connectivity check.

Connects to the local MySQL `inspektorati` database using the backend's
connection module and prints "DB OK" on success.

Run with the backend venv:
    backend/venv/Scripts/python.exe test/test_db.py
"""

import sys
from pathlib import Path

# Make the backend package importable when running this script directly.
BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.connection import get_connection


def main():
    try:
        conn = get_connection()
        conn.close()
        print("DB OK")
    except Exception as exc:
        print(f"DB FAILED: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
