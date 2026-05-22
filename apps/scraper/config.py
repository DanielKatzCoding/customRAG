import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

DEFAULT_ACCEPT_LANGUAGE = "en-US,en;q=0.9,he;q=0.8"


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
