"""SQLAlchemy session for the API.

Uses the same connection settings as app.db.connection (from backend/.env).
Routes get a session through the get_db() dependency, which always closes it.
"""

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker

from app.core import config

DATABASE_URL = URL.create(
    "mysql+mysqlconnector",
    username=config.DB_USER,
    password=config.DB_PASSWORD,
    host=config.DB_HOST,
    port=config.DB_PORT,
    database=config.DB_NAME,
    query={"charset": "utf8mb4", "collation": "utf8mb4_unicode_ci"},
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
