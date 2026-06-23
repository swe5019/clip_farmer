"""Transcribe downloaded media with faster-whisper, producing word-level timestamps."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from faster_whisper import WhisperModel

from clip_farmer.db import repo_episodes
from clip_farmer.db.models import Episode
from clip_farmer.transcribe.transcript_store import Segment, Transcript, Word, save_transcript

_model_cache: dict[tuple[str, str], WhisperModel] = {}


def _get_model(model_size: str, device: str) -> WhisperModel:
    key = (model_size, device)
    if key not in _model_cache:
        compute_type = "int8" if device == "cpu" else "float16"
        _model_cache[key] = WhisperModel(model_size, device=device, compute_type=compute_type)
    return _model_cache[key]


def transcribe_file(local_path: Path, *, model_size: str = "medium", device: str = "cpu") -> Transcript:
    model = _get_model(model_size, device)
    segments_iter, _info = model.transcribe(str(local_path), word_timestamps=True)

    segments: list[Segment] = []
    for seg in segments_iter:
        words = [
            Word(word=w.word.strip(), start=w.start, end=w.end, probability=w.probability)
            for w in (seg.words or [])
        ]
        segments.append(Segment(start=seg.start, end=seg.end, text=seg.text, words=words))
    return Transcript(segments=segments)


def transcribe_episode(
    conn: sqlite3.Connection,
    episode: Episode,
    media_dir: Path,
    *,
    model_size: str = "medium",
    device: str = "cpu",
) -> Path:
    if not episode.local_path:
        raise ValueError(f"Episode {episode.id} has no local_path; download it first")

    repo_episodes.update_status(conn, episode.id, "transcribing")
    try:
        transcript = transcribe_file(Path(episode.local_path), model_size=model_size, device=device)
        dest_path = media_dir / "transcripts" / f"{episode.id}.json"
        save_transcript(transcript, dest_path)
        repo_episodes.set_transcript_path(conn, episode.id, str(dest_path))
        repo_episodes.update_status(conn, episode.id, "transcribed")
        return dest_path
    except Exception as exc:
        repo_episodes.update_status(conn, episode.id, "transcribe_failed", error_message=str(exc))
        raise
