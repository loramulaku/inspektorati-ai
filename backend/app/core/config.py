"""Application configuration.

Loads settings from the backend/.env file via python-dotenv and exposes them
as simple module-level values used by the rest of the app.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load the .env that sits in the backend/ folder (two levels up from this file).
BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# MySQL database
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "inspektorati")

# Authentication (JWT)
JWT_SECRET = os.getenv("JWT_SECRET", "")
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))

# Folder for files citizens upload with a kërkesë (never inside the code).
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BACKEND_DIR / "uploads"))).resolve()

# Frontend addresses allowed to call the API from the browser (CORS),
# comma-separated. Vite uses 5173, or 5174 when 5173 is already taken.
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGIN", "http://localhost:5173,http://localhost:5174").split(",")
    if origin.strip()
]
