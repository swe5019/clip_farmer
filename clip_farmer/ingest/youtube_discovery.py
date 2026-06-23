"""Discover recent uploads on a YouTube channel using yt-dlp, without downloading media."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

from clip_farmer.db.models import TrackedSource


@dataclass
class EpisodeCandidate:
    external_id: str
    title: str | None
    published_at: str | None
    url: str


def discover_youtube(source: TrackedSource, *, max_videos: int = 15) -> list[EpisodeCandidate]:
    """List the most recent uploads for a channel via yt-dlp's flat-playlist mode (metadata only, no download)."""
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        f"--playlist-end={max_videos}",
        source.url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp discovery failed for {source.url}: {result.stderr.strip()}")

    candidates: list[EpisodeCandidate] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        video_id = entry.get("id")
        if not video_id:
            continue
        candidates.append(
            EpisodeCandidate(
                external_id=video_id,
                title=entry.get("title"),
                published_at=entry.get("upload_date"),
                url=f"https://www.youtube.com/watch?v={video_id}",
            )
        )
    return candidates
