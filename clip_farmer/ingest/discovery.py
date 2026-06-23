"""Poll all active tracked sources and insert new episode rows."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from clip_farmer.db import repo_episodes, repo_sources
from clip_farmer.db.models import TrackedSource
from clip_farmer.ingest.rss_discovery import discover_rss
from clip_farmer.ingest.youtube_discovery import discover_youtube


def discover_source(conn: sqlite3.Connection, source: TrackedSource) -> int:
    """Discover new episodes for a single source. Returns count of newly inserted episodes."""
    if source.type == "youtube_channel":
        candidates = discover_youtube(source)
    elif source.type == "rss_podcast":
        candidates = discover_rss(source)
    else:
        raise ValueError(f"Unknown source type: {source.type}")

    inserted = 0
    for candidate in candidates:
        new_id = repo_episodes.insert_episode_if_new(
            conn,
            source_id=source.id,
            external_id=candidate.external_id,
            title=candidate.title,
            published_at=candidate.published_at,
            url=candidate.url,
        )
        if new_id is not None:
            inserted += 1

    last_seen = candidates[0].external_id if candidates else None
    repo_sources.mark_checked(
        conn,
        source.id,
        last_seen_id=last_seen,
        checked_at=datetime.now(timezone.utc).isoformat(),
    )
    return inserted


def discover_all(conn: sqlite3.Connection) -> int:
    """Discover new episodes across every active tracked source. Returns total new episodes inserted."""
    total = 0
    for source in repo_sources.list_active_sources(conn):
        total += discover_source(conn, source)
    return total
