"""SQLite connection helpers for the project database."""

from __future__ import annotations

import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "database" / "regional_entrepreneurship.sqlite"


def connect_database(database_path: str | Path | None = None) -> sqlite3.Connection:
    """Return a SQLite connection with foreign-key enforcement enabled."""
    path = Path(database_path) if database_path is not None else DEFAULT_DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection
