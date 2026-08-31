"""
Alembic env.py — MoveIQ
Connects Alembic to the SQLAlchemy engine and models defined in
database/session.py and database/models.py.
"""
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from alembic import context

# ── Make sure project root is on sys.path ─────────────────────────────────────
# (Needed so that `from database.session import ...` works when running alembic)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Load .env so DATABASE_URL env vars are available ─────────────────────────
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# ── Import our engine and models Base ────────────────────────────────────────
from database.session import engine, DATABASE_URL
from database.models import Base

# ── Alembic Config ────────────────────────────────────────────────────────────
config = context.config

# Override sqlalchemy.url from our dynamic DATABASE_URL (ignores alembic.ini value)
# configparser uses % for interpolation, so we must escape any % in the URL
config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point Alembic at our SQLAlchemy metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout without a live DB connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Compare server defaults so Alembic detects all changes
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
