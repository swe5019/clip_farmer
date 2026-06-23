"""Shared ffmpeg/ffprobe subprocess helpers."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


def probe_duration_sec(media_path: Path) -> float | None:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(media_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return None
    data = json.loads(result.stdout)
    duration = data.get("format", {}).get("duration")
    return float(duration) if duration is not None else None


def run_ffmpeg(args: list[str], *, timeout: int = 600) -> subprocess.CompletedProcess:
    """Run an ffmpeg command, raising with captured stderr on failure."""
    cmd = ["ffmpeg", "-y", *args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {' '.join(cmd)}\n{result.stderr[-4000:]}")
    return result
