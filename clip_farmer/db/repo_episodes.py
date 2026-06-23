from __future__ import annotations

import sqlite3

from clip_farmer.db.models import Episode


def _row_to_episode(row: sqlite3.Row) -> Episode:
    return Episode(
        id=row["id"],
        source_id=row["source_id"],
        external_id=row["external_id"],
        title=row["title"],
        published_at=row["published_at"],
        url=row["url"],
        local_path=row["local_path"],
        transcript_path=row["transcript_path"],
        duration_sec=row["duration_sec"],
        status=row["status"],
        error_message=row["error_message"],
    )


def insert_episode_if_new(
    conn: sqlite3.Connection,
    *,
    source_id: int,
    external_id: str,
    title: str | None,
    published_at: str | None,
    url: str,
) -> int | None:
    """Insert a new episode (status=discovered). Returns the new id, or None if it already exists."""
    existing = conn.execute(
        "SELECT id FROM episodes WHERE source_id = ? AND external_id = ?",
        (source_id, external_id),
    ).fetchone()
    if existing:
        return None
    cur = conn.execute(
        "INSERT INTO episodes (source_id, external_id, title, published_at, url) VALUES (?, ?, ?, ?, ?)",
        (source_id, external_id, title, published_at, url),
    )
    return cur.lastrowid


def list_by_status(conn: sqlite3.Connection, status: str) -> list[Episode]:
    rows = conn.execute("SELECT * FROM episodes WHERE status = ?", (status,)).fetchall()
    return [_row_to_episode(r) for r in rows]


def get_episode(conn: sqlite3.Connection, episode_id: int) -> Episode | None:
    row = conn.execute("SELECT * FROM episodes WHERE id = ?", (episode_id,)).fetchone()
    return _row_to_episode(row) if row else None


def update_status(
    conn: sqlite3.Connection,
    episode_id: int,
    status: str,
    *,
    error_message: str | None = None,
) -> None:
    conn.execute(
        "UPDATE episodes SET status = ?, error_message = ?, updated_at = datetime('now') WHERE id = ?",
        (status, error_message, episode_id),
    )


def set_local_path(conn: sqlite3.Connection, episode_id: int, local_path: str, duration_sec: float | None) -> None:
    conn.execute(
        "UPDATE episodes SET local_path = ?, duration_sec = ?, updated_at = datetime('now') WHERE id = ?",
        (local_path, duration_sec, episode_id),
    )


def set_transcript_path(conn: sqlite3.Connection, episode_id: int, transcript_path: str) -> None:
    conn.execute(
        "UPDATE episodes SET transcript_path = ?, updated_at = datetime('now') WHERE id = ?",
        (transcript_path, episode_id),
    )
