"""Discover new episodes from a podcast RSS feed using feedparser."""
from __future__ import annotations

import feedparser

from clip_farmer.db.models import TrackedSource
from clip_farmer.ingest.youtube_discovery import EpisodeCandidate


def discover_rss(source: TrackedSource, *, max_episodes: int = 15) -> list[EpisodeCandidate]:
    feed = feedparser.parse(source.url)
    candidates: list[EpisodeCandidate] = []
    for entry in feed.entries[:max_episodes]:
        guid = entry.get("id") or entry.get("link")
        if not guid:
            continue
        enclosure_url = entry.get("link")
        for link in entry.get("links", []):
            if link.get("rel") == "enclosure":
                enclosure_url = link.get("href", enclosure_url)
                break
        candidates.append(
            EpisodeCandidate(
                external_id=guid,
                title=entry.get("title"),
                published_at=entry.get("published"),
                url=enclosure_url,
            )
        )
    return candidates
