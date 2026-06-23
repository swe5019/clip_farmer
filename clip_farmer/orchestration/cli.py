"""Manual/test CLI for running individual pipeline stages in isolation.

Usage:
    python -m clip_farmer.orchestration.cli run-stage discover
    python -m clip_farmer.orchestration.cli run-stage download
    python -m clip_farmer.orchestration.cli run-stage transcribe
"""
from __future__ import annotations

import argparse
import logging

from clip_farmer.db import repo_episodes, repo_sources
from clip_farmer.db.database import connect, init_db
from clip_farmer.ingest.discovery import discover_all
from clip_farmer.ingest.downloader import download_episode
from clip_farmer.settings import get_settings
from clip_farmer.transcribe.whisper_transcriber import transcribe_episode

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def _sync_sources_from_config() -> None:
    settings = get_settings()
    with connect(settings.db_path) as conn:
        for source in settings.config.sources:
            repo_sources.upsert_source(conn, type=source.type, name=source.name, url=source.url, active=source.active)


def run_discover() -> None:
    _sync_sources_from_config()
    settings = get_settings()
    with connect(settings.db_path) as conn:
        new_count = discover_all(conn)
    logger.info("Discovered %d new episode(s)", new_count)


def run_download() -> None:
    settings = get_settings()
    with connect(settings.db_path) as conn:
        pending = repo_episodes.list_by_status(conn, "discovered")
        logger.info("Found %d episode(s) pending download", len(pending))
        for episode in pending:
            source = repo_sources.get_source(conn, episode.source_id)
            logger.info("Downloading episode %d: %s", episode.id, episode.title)
            try:
                download_episode(conn, episode, source, settings.media_dir)
            except Exception:
                logger.exception("Failed to download episode %d", episode.id)


def run_transcribe() -> None:
    settings = get_settings()
    with connect(settings.db_path) as conn:
        pending = repo_episodes.list_by_status(conn, "downloaded")
        logger.info("Found %d episode(s) pending transcription", len(pending))
        for episode in pending:
            logger.info("Transcribing episode %d: %s", episode.id, episode.title)
            try:
                transcribe_episode(
                    conn,
                    episode,
                    settings.media_dir,
                    model_size=settings.config.general.whisper_model,
                    device=settings.config.general.whisper_device,
                )
            except Exception:
                logger.exception("Failed to transcribe episode %d", episode.id)


STAGES = {
    "discover": run_discover,
    "download": run_download,
    "transcribe": run_transcribe,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="clip_farmer manual stage runner")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_stage = subparsers.add_parser("run-stage")
    run_stage.add_argument("stage", choices=list(STAGES.keys()))

    args = parser.parse_args()
    if args.command == "run-stage":
        STAGES[args.stage]()


if __name__ == "__main__":
    main()
