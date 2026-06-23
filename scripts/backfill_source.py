#!/usr/bin/env python
"""Manually queue a single video/episode URL for testing, bypassing channel/feed discovery.

Usage:
    python scripts/backfill_source.py <source_name> <video_or_episode_url>
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
        if not row:
            print(f"No tracked source named '{source_name}'. Run run-stage discover first or check config.yaml.")
            sys.exit(1)
        source_id = row["id"]
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
