"""MySQL database connection.

Opens a connection to the local MySQL database using the settings loaded in
app.core.config (which come from backend/.env).
"""

import mysql.connector

from app.core import config


def get_connection():
    """Return a new MySQL connection to the configured database."""
    return mysql.connector.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
    )
