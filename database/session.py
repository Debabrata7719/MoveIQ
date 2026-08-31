"""
SQLAlchemy Session Factory — MoveIQ

Provides a thread-safe SessionLocal for use in both FastAPI endpoints
and Celery workers (synchronous). Reads USE_LOCAL_DB to auto-select
MySQL (local/Docker) or PostgreSQL (Supabase cloud).
"""
import os
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

USE_LOCAL_DB = os.getenv("USE_LOCAL_DB", "true").lower() == "true"

# ── Build database URL ────────────────────────────────────────────────────────
if USE_LOCAL_DB:
    # MySQL via PyMySQL driver
    DB_HOST     = os.getenv("DB_HOST", "localhost")
    DB_USER     = os.getenv("DB_USER", "root")
    DB_PASSWORD = urllib.parse.quote_plus(os.getenv("DB_PASSWORD", ""))
    DB_NAME     = os.getenv("DB_NAME", "sports_injury_detection")
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"
else:
    # PostgreSQL (Supabase) via psycopg2
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    # SQLAlchemy requires 'postgresql://' not 'postgres://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,          # Recycle stale connections automatically
    pool_recycle=1800,           # Recycle connections every 30 min
    echo=False,
)

# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    """
    FastAPI dependency that yields a DB session and ensures it is always closed.

    Usage in a router:
        from database.session import get_db
        from sqlalchemy.orm import Session
        from fastapi import Depends

        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
