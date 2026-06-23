# clip_farmer

Automated pipeline that monitors YouTube channels / podcast RSS feeds, transcribes new
episodes, uses an LLM to find highlight-worthy segments, renders vertical clips with
burned-in captions, sends them to a Telegram bot for human approval, and posts approved
clips to TikTok / YouTube Shorts / Instagram Reels / Facebook Reels.

See `/root/.claude/plans/you-are-my-builder-buzzing-waterfall.md` (or your own copy of
the implementation plan) for full architecture, schema, and build-phase details.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # fill in ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, etc. as each phase needs them
python scripts/init_db.py
```

System dependencies required on the host: `ffmpeg`, `ffprobe` (ffmpeg package), and a
working `yt-dlp` install (pulled in as a Python dependency, but relies on ffmpeg for
merging/transcoding).

## Running pipeline stages manually (Phase 1)

```bash
python -m clip_farmer.orchestration.cli run-stage discover    # find new episodes from config.yaml sources
python -m clip_farmer.orchestration.cli run-stage download    # download discovered episodes
python -m clip_farmer.orchestration.cli run-stage transcribe  # transcribe downloaded episodes with faster-whisper
```

Sources are configured in `config/config.yaml` under `sources:`. Currently seeded with
two beta YouTube channels.

## Status

Phase 1 (ingestion + transcription) implemented. Highlight detection, clip rendering,
Telegram review, and platform posting are not yet built — see the plan's build order.
