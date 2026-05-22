import logging
from typing import Self

import httpx

from config import StealthConfig
from models.interfaces import BaseScraper

logger = logging.getLogger(__name__)

_MAX_BODY_BYTES = 10 * 1024 * 1024  # 10 MB


class HttpScraper(BaseScraper):
    """Concrete Strategy that fetches HTML via a shared async HTTP/2 client."""

    def __init__(self, config: StealthConfig):
        self._config = config
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0),
            follow_redirects=True,
            verify=True,
            proxy=config.proxy,
            http2=True,
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._client.aclose()

    async def fetch_html(self, url: str) -> str:
        async with self._client.stream(
            "GET", url, headers=self._config.build_headers()
        ) as response:
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if not any(
                ct in content_type
                for ct in ("text/html", "application/xhtml", "text/xml")
            ):
                logger.warning("Unexpected content-type %r for %s", content_type, url)

            chunks: list[bytes] = []
            total = 0
            async for chunk in response.aiter_bytes():
                total += len(chunk)
                if total > _MAX_BODY_BYTES:
                    raise ValueError(
                        f"Response body exceeds {_MAX_BODY_BYTES} bytes for {url}"
                    )
                chunks.append(chunk)

            if response.url != httpx.URL(url):
                logger.info("Redirected: %s -> %s", url, response.url)

            body = b"".join(chunks)
            return body.decode(response.encoding or "utf-8", errors="replace")
