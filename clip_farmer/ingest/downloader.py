"""Download an episode's media to media/raw/<episode_id>.<ext>."""
from __future__ import annotations

import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path

import httpx

from clip_farmer.common.ffmpeg_utils import probe_duration_sec
from clip_farmer.db import repo_episodes
from clip_farmer.db.models import Episode, TrackedSource


@dataclass
class DownloadResult:
    local_path: Path
    duration_sec: float | None


def _download_youtube(episode: Episode, dest_dir: Path) -> Path:
    output_template = str(dest_dir / f"{episode.id}.%(ext)s")
    cmd = [
        "yt-dlp",
        "-f", "bestaudio+bestvideo/best",
        "--merge-output-format", "mp4",
        "-o", output_template,
        episode.url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp download failed for {episode.url}: {result.stderr.strip()}")
    matches = list(dest_dir.glob(f"{episode.id}.*"))
    if not matches:
        raise RuntimeError(f"yt-dlp reported success but no output file found for episode {episode.id}")
    return matches[0]


def _download_rss(episode: Episode, dest_dir: Path) -> Path:
    suffix = Path(episode.url.split("?")[0]).suffix or ".mp3"
    dest = dest_dir / f"{episode.id}{suffix}"
    with httpx.stream("GET", episode.url, follow_redirects=True, timeout=120) as response:
        response.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)
    return dest


def download_episode(conn: sqlite3.Connection, episode: Episode, source: TrackedSource, media_dir: Path) -> DownloadResult:
    dest_dir = media_dir / "raw"
    dest_dir.mkdir(parents=True, exist_ok=True)

    repo_episodes.update_status(conn, episode.id, "downloading")
    try:
        if source.type == "youtube_channel":
            local_path = _download_youtube(episode, dest_dir)
        elif source.type == "rss_podcast":
            local_path = _download_rss(episode, dest_dir)
        else:
            raise ValueError(f"Unknown source type: {source.type}")

        duration_sec = probe_duration_sec(local_path)
        repo_episodes.set_local_path(conn, episode.id, str(local_path), duration_sec)
        repo_episodes.update_status(conn, episode.id, "downloaded")
        return DownloadResult(local_path=local_path, duration_sec=duration_sec)
    except Exception as exc:
        repo_episodes.update_status(conn, episode.id, "download_failed", error_message=str(exc))
        raise
