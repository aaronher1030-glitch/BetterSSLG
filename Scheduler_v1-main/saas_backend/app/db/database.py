"""
saas_backend/app/db/database.py
SQLAlchemy engine + session + declarative Base.

Uses SQLite by default (file: saas_backend/scas.db).
Override with DATABASE_URL env var for PostgreSQL in production.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "sqlite:///./scas.db",
)

# connect_args is only needed for SQLite (check_same_thread=False)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # set True for SQL query logging during dev
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ── FastAPI dependency ───────────────────────────────────────────────────────
def get_db():
    """Yield a DB session and ensure it is closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
