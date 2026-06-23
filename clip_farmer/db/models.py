from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TrackedSource:
    id: int
    type: str
    name: str
    url: str
    active: bool
    last_checked_at: str | None
    last_seen_id: str | None


@dataclass
class Episode:
    id: int
    source_id: int
    external_id: str
    title: str | None
    published_at: str | None
    url: str
    local_path: str | None
    transcript_path: str | None
    duration_sec: float | None
    status: str
    error_message: str | None


@dataclass
class Clip:
    id: int
    episode_id: int
    start_sec: float
    end_sec: float
    hook_caption: str | None
    llm_reason: str | None
    llm_score: float | None
    raw_clip_path: str | None
    final_clip_path: str | None
    status: str
    review_message_id: str | None
