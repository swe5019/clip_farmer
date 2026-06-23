"""Read/write transcript JSON files."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Word:
    word: str
    start: float
    end: float
    probability: float


@dataclass
class Segment:
    start: float
    end: float
    text: str
    words: list[Word]


@dataclass
class Transcript:
    segments: list[Segment]

    def words_in_range(self, start_sec: float, end_sec: float) -> list[Word]:
        result: list[Word] = []
        for segment in self.segments:
            for word in segment.words:
                if word.start >= start_sec and word.end <= end_sec:
                    result.append(word)
        return result

    def full_text(self) -> str:
        return " ".join(segment.text.strip() for segment in self.segments)


def save_transcript(transcript: Transcript, dest_path: Path) -> None:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "segments": [
            {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
                "words": [asdict(w) for w in seg.words],
            }
            for seg in transcript.segments
        ]
    }
    with open(dest_path, "w") as f:
        json.dump(payload, f, indent=2)


def load_transcript(path: Path) -> Transcript:
    with open(path) as f:
        payload = json.load(f)
    segments = [
        Segment(
            start=seg["start"],
            end=seg["end"],
            text=seg["text"],
            words=[Word(**w) for w in seg["words"]],
        )
        for seg in payload["segments"]
    ]
    return Transcript(segments=segments)
