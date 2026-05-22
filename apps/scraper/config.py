import random
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

DEFAULT_ACCEPT_LANGUAGE = "en-US,en;q=0.9,he;q=0.8"

# Resolve the repo root regardless of the working directory from which the
# scraper is launched (apps/scraper/ is two levels below the repo root).
_REPO_ROOT = Path(__file__).parent.parent.parent


class ScraperSettings(BaseSettings):
    """Environment-driven settings for the scraper.

    All variables are prefixed with ``SCRAPER_`` in the environment / .env
    file (e.g. ``SCRAPER_TIMEOUT_SECONDS=45``).  Unset variables fall back to
    the defaults declared below.
    """

    model_config = SettingsConfigDict(
        env_prefix="SCRAPER_",
        env_file=_REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        # Extra fields in the env file (e.g. INGEST_* vars) are silently ignored.
        extra="ignore",
    )

    proxy: str | None = Field(
        default=None,
        description="Optional HTTP/SOCKS proxy URL (e.g. http://user:pass@host:port).",
    )
    timeout_seconds: float = Field(
        default=30.0,
        description="Per-request timeout in seconds.",
    )
    accept_language: str = Field(
        default=DEFAULT_ACCEPT_LANGUAGE,
        description="Value sent in the Accept-Language request header.",
    )


class StealthConfig:
    """Builds request-time options that mimic a real browser."""

    def __init__(
        self,
        proxy: str | None = None,
        timeout_seconds: float = 30.0,
        accept_language: str = DEFAULT_ACCEPT_LANGUAGE,
    ):
        self.proxy = proxy
        self.timeout_seconds = timeout_seconds
        self.accept_language = accept_language

    @classmethod
    def from_settings(cls, settings: ScraperSettings) -> "StealthConfig":
        """Construct a ``StealthConfig`` from a ``ScraperSettings`` instance."""
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
