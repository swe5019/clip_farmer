-- Sources being monitored (YouTube channels or RSS podcast feeds)
CREATE TABLE IF NOT EXISTS tracked_sources (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    type            TEXT NOT NULL CHECK (type IN ('youtube_channel','rss_podcast')),
    name            TEXT NOT NULL,
    url             TEXT NOT NULL,
    active          INTEGER NOT NULL DEFAULT 1,
    last_checked_at TEXT,
    last_seen_id    TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Discovered / downloaded / transcribed episodes
CREATE TABLE IF NOT EXISTS episodes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER NOT NULL REFERENCES tracked_sources(id),
    external_id     TEXT NOT NULL,
    title           TEXT,
    published_at    TEXT,
    url             TEXT NOT NULL,
    local_path      TEXT,
    transcript_path TEXT,
    duration_sec    REAL,
    status          TEXT NOT NULL DEFAULT 'discovered'
                      CHECK (status IN ('discovered','downloading','downloaded','download_failed',
                                         'transcribing','transcribed','transcribe_failed',
                                         'highlights_selected','highlights_failed','done','skipped')),
    error_message   TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (source_id, external_id)
);

-- Generated/candidate clips
CREATE TABLE IF NOT EXISTS clips (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id      INTEGER NOT NULL REFERENCES episodes(id),
    start_sec       REAL NOT NULL,
    end_sec         REAL NOT NULL,
    hook_caption    TEXT,
    llm_reason      TEXT,
    llm_score       REAL,
    raw_clip_path   TEXT,
    final_clip_path TEXT,
    status          TEXT NOT NULL DEFAULT 'candidate'
                      CHECK (status IN ('candidate','rendering','rendered','render_failed',
                                         'pending_review','approved','rejected','expired','archived')),
    review_message_id TEXT,
    reviewed_at     TEXT,
    reviewed_by     TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Platform accounts configured for posting (multiple accounts per platform supported)
CREATE TABLE IF NOT EXISTS platform_accounts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    platform        TEXT NOT NULL CHECK (platform IN ('youtube_shorts','tiktok','instagram_reels','facebook_reels')),
    account_label   TEXT NOT NULL,
    enabled         INTEGER NOT NULL DEFAULT 0,
    daily_quota     INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(platform, account_label)
);

-- Per-platform, per-account posting record -- prevents duplicate posting
CREATE TABLE IF NOT EXISTS platform_posts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    clip_id         INTEGER NOT NULL REFERENCES clips(id),
    platform_account_id INTEGER NOT NULL REFERENCES platform_accounts(id),
    status          TEXT NOT NULL DEFAULT 'queued'
                      CHECK (status IN ('queued','posting','posted','failed','skipped')),
    platform_post_id TEXT,
    scheduled_for   TEXT,
    posted_at       TEXT,
    error_message   TEXT,
    attempt_count   INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(clip_id, platform_account_id)
);

-- Simple job lock table to prevent overlapping scheduler runs of the same stage
CREATE TABLE IF NOT EXISTS job_locks (
    job_name        TEXT PRIMARY KEY,
    locked_at       TEXT,
    locked_by       TEXT
);
