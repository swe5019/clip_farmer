from __future__ import annotations

import sqlite3

from clip_farmer.db.models import TrackedSource


def _row_to_source(row: sqlite3.Row) -> TrackedSource:
    return TrackedSource(
        id=row["id"],
        type=row["type"],
        name=row["name"],
        url=row["url"],
        active=bool(row["active"]),
        last_checked_at=row["last_checked_at"],
        last_seen_id=row["last_seen_id"],
    )


def list_active_sources(conn: sqlite3.Connection) -> list[TrackedSource]:
    rows = conn.execute("SELECT * FROM tracked_sources WHERE active = 1").fetchall()
    return [_row_to_source(r) for r in rows]


def get_source(conn: sqlite3.Connection, source_id: int) -> TrackedSource | None:
    row = conn.execute("SELECT * FROM tracked_sources WHERE id = ?", (source_id,)).fetchone()
    return _row_to_source(row) if row else None


def upsert_source(conn: sqlite3.Connection, *, type: str, name: str, url: str, active: bool = True) -> int:
    """Insert a source if its URL isn't already tracked, else update name/active. Returns the source id."""
    row = conn.execute("SELECT id FROM tracked_sources WHERE url = ?", (url,)).fetchone()
    if row:
        conn.execute(
            "UPDATE tracked_sources SET name = ?, active = ? WHERE id = ?",
            (name, int(active), row["id"]),
        )
        return row["id"]
    cur = conn.execute(
        "INSERT INTO tracked_sources (type, name, url, active) VALUES (?, ?, ?, ?)",
        (type, name, url, int(active)),
    )
    return cur.lastrowid


def mark_checked(conn: sqlite3.Connection, source_id: int, *, last_seen_id: str | None, checked_at: str) -> None:
    conn.execute(
        "UPDATE tracked_sources SET last_checked_at = ?, last_seen_id = COALESCE(?, last_seen_id) WHERE id = ?",
        (checked_at, last_seen_id, source_id),
    )
