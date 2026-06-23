"""Typed settings loaded from config/config.yaml + environment variables (.env)."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


class GeneralConfig(BaseModel):
    vps_timezone: str = "UTC"
    whisper_model: str = "medium"
    whisper_device: Literal["cpu", "cuda"] = "cpu"
    max_llm_chunks_per_episode: int = 6
    clip_min_sec: float = 30
    clip_max_sec: float = 90
    review_ttl_hours: int = 48


class PlatformsEnabled(BaseModel):
    youtube_shorts: bool = False
    tiktok: bool = False
    instagram_reels: bool = False
    facebook_reels: bool = False


class FeatureFlags(BaseModel):
    autopost_enabled: bool = False
    platforms_enabled: PlatformsEnabled = Field(default_factory=PlatformsEnabled)


class SourceConfig(BaseModel):
    name: str
    type: Literal["youtube_channel", "rss_podcast"]
    url: str
    active: bool = True


class PlatformAccountConfig(BaseModel):
    platform: Literal["youtube_shorts", "tiktok", "instagram_reels", "facebook_reels"]
    account_label: str
    enabled: bool = False
    daily_quota: int = 1
    credentials_env_prefix: str


class TelegramConfig(BaseModel):
    review_chat_id_env: str = "TELEGRAM_REVIEW_CHAT_ID"


class CaptionsConfig(BaseModel):
    style_template: str = "config/subtitle_styles/default.ass.template"
    font: str = "Montserrat-Bold"
    font_size: int = 64
    highlight_color: str = "&H00FFFF&"


class ReframeConfig(BaseModel):
    strategy: Literal["center_crop_smoothed", "face_biased_crop"] = "center_crop_smoothed"
    smoothing_alpha: float = 0.15


class AppConfig(BaseModel):
    general: GeneralConfig = Field(default_factory=GeneralConfig)
    feature_flags: FeatureFlags = Field(default_factory=FeatureFlags)
    sources: list[SourceConfig] = Field(default_factory=list)
    platform_accounts: list[PlatformAccountConfig] = Field(default_factory=list)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    captions: CaptionsConfig = Field(default_factory=CaptionsConfig)
    reframe: ReframeConfig = Field(default_factory=ReframeConfig)


def load_app_config(path: Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    with open(path) as f:
        raw = yaml.safe_load(f) or {}
    return AppConfig.model_validate(raw)


class Secrets(BaseSettings):
    """Secrets loaded from environment variables / .env. Fields are optional here because
    not every secret is required until the corresponding feature is enabled; modules that
    need a given secret should check for it explicitly and raise PublisherNotConfigured.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str | None = None
    telegram_bot_token: str | None = None
    telegram_review_chat_id: str | None = None


class Settings:
    """Top-level settings object combining config.yaml and .env secrets."""

    def __init__(self, config_path: Path = DEFAULT_CONFIG_PATH):
        self.config: AppConfig = load_app_config(config_path)
        self.secrets: Secrets = Secrets()
        self.db_path: Path = PROJECT_ROOT / "data" / "clip_farmer.db"
        self.media_dir: Path = PROJECT_ROOT / "media"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
