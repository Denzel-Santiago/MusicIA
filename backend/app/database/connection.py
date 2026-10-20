"""Compatibility imports for SQLAlchemy database configuration."""

from app.adapters.persistence.sqlalchemy.database import (
    BASE_DIR, DATA_DIR, DATABASE_PATH, DATABASE_URL, engine, SessionLocal, Base, get_db,
)

__all__ = ["BASE_DIR", "DATA_DIR", "DATABASE_PATH", "DATABASE_URL", "engine", "SessionLocal", "Base", "get_db"]
