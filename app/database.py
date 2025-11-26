"""Database configuration and helpers."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def ensure_description_column_exists() -> None:
    """Add the description column for books_of_month if it is missing."""
    try:
        with engine.connect() as conn:
            info = conn.execute("PRAGMA table_info(books_of_month)").fetchall()
            columns = {row[1] for row in info}
            if "description" not in columns:
                conn.execute("ALTER TABLE books_of_month ADD COLUMN description TEXT")
    except Exception:
        # Silently ignore migrations in environments without permissions.
        pass


def init_db() -> None:
    """Initialize database schema and ensure compatibility tweaks."""
    from . import models  # noqa: F401  (needed to register models)

    Base.metadata.create_all(bind=engine)
    ensure_description_column_exists()

