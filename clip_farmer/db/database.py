"""SQLite connection management and schema initialization."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path) -> None:
    """Apply schema.sql. Idempotent thanks to CREATE TABLE IF NOT EXISTS."""
    conn = get_connection(db_path)
    try:
        with open(SCHEMA_PATH) as f:
            conn.executescript(f.read())
        conn.commit()
    finally:
        conn.close()


@contextmanager
def connect(db_path: Path):
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
