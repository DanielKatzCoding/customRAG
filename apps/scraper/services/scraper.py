import httpx

from config import StealthConfig
from models.interfaces import BaseScraper


class HttpScraper(BaseScraper):
    """Concrete Strategy that fetches HTML via async HTTP requests."""

    def __init__(self, config: StealthConfig):
        self._config = config

    async def fetch_html(self, url: str) -> str:
        async with httpx.AsyncClient(
            headers=self._config.build_headers(),
            timeout=self._config.timeout_seconds,
            follow_redirects=True,
            proxy=self._config.proxy,
            http2=True,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
