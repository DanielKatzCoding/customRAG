import random
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

_REPO_ROOT = Path(__file__).parent.parent.parent


class ScraperSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SCRAPER_",
        env_file=_REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str
    port: int
    log_level: str
    output_dir: str

    proxy: str | None = Field(default=None)
    timeout_seconds: float
    accept_language: str


class StealthConfig:
    """Builds request-time options that mimic a real browser."""

    def __init__(
        self,
        proxy: str | None = None,
        timeout_seconds: float = 30.0,
        accept_language: str = "en-US,en;q=0.9,he;q=0.8",
    ):
        self.proxy = proxy
        self.timeout_seconds = timeout_seconds
        self.accept_language = accept_language

    @classmethod
    def from_settings(cls, settings: ScraperSettings) -> "StealthConfig":
        return cls(
            proxy=settings.proxy,
            timeout_seconds=settings.timeout_seconds,
            accept_language=settings.accept_language,
        )

    def build_headers(self) -> dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": self.accept_language,
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
