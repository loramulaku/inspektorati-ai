"""Alembic environment.

Builds the database URL from app.core.config (which reads backend/.env), so the
credentials are never written into alembic.ini. target_metadata points at the
SQLAlchemy models so `alembic check` / autogenerate can compare them to the DB.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import URL, create_engine, pool

from app.core import config as app_config
from app.db.models import Base

# Alembic Config object, gives access to the values in alembic.ini.
config = context.config

# Set up Python logging from the [loggers] sections of alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# URL.create escapes special characters in the password for us.
DATABASE_URL = URL.create(
    "mysql+mysqlconnector",
    username=app_config.DB_USER,
    password=app_config.DB_PASSWORD,
    host=app_config.DB_HOST,
    port=app_config.DB_PORT,
    database=app_config.DB_NAME,
    query={"charset": "utf8mb4", "collation": "utf8mb4_unicode_ci"},
)


def run_migrations_offline() -> None:
    """Print the SQL instead of running it (`alembic upgrade head --sql`)."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to MySQL and run the migrations."""
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
