#!/usr/bin/env python
"""Manually queue a single video/episode URL for testing, bypassing channel/feed discovery.

Usage:
    python scripts/backfill_source.py <source_name> <video_or_episode_url>

If <source_name> doesn't match anything in the DB or config.yaml, it is created
on the fly as an ad-hoc youtube_channel source (useful for one-off test videos
that aren't from one of your configured channels).
"""
from __future__ import annotations

import sys

from clip_farmer.db import repo_episodes, repo_sources
from clip_farmer.db.database import connect
from clip_farmer.settings import get_settings


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    source_name, url = sys.argv[1], sys.argv[2]

    settings = get_settings()
    with connect(settings.db_path) as conn:
        row = conn.execute("SELECT * FROM tracked_sources WHERE name = ?", (source_name,)).fetchone()
        if row:
            source_id = row["id"]
        else:
            config_source = next((s for s in settings.config.sources if s.name == source_name), None)
            if config_source is not None:
                source_id = repo_sources.upsert_source(
                    conn, type=config_source.type, name=config_source.name, url=config_source.url, active=config_source.active
                )
                print(f"Registered source '{source_name}' from config.yaml (id={source_id}).")
            else:
                source_id = repo_sources.upsert_source(
                    conn, type="youtube_channel", name=source_name, url=url, active=True
                )
                print(f"Created ad-hoc test source '{source_name}' (id={source_id}).")
        external_id = url.split("v=")[-1].split("&")[0] if "v=" in url else url
        new_id = repo_episodes.insert_episode_if_new(
            conn,
            source_id=source_id,
            external_id=external_id,
            title=f"Manual backfill: {url}",
            published_at=None,
            url=url,
        )
        if new_id is None:
            print("Episode already exists for this source/url.")
        else:
            print(f"Queued episode id={new_id} for download.")


if __name__ == "__main__":
    main()
