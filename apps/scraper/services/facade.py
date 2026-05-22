import logging

import httpx

from models import BaseParserProvider, BaseScraper, ParseResult

logger = logging.getLogger(__name__)


class ScrapingFacade:
    """Orchestrates the fetch → parse pipeline. Depends on abstractions (DIP)."""

    def __init__(self, scraper: BaseScraper, parser_provider: BaseParserProvider):
        self._scraper = scraper
        self._parser_provider = parser_provider

    async def scrape(self, url: str) -> ParseResult | None:
        try:
            logger.info("Fetching: %s", url)
            raw_html = await self._scraper.fetch_html(url)
            parser = self._parser_provider.for_url(url)
            return parser.parse(raw_html)
        except httpx.HTTPStatusError as exc:
            logger.error("HTTP %d for %s", exc.response.status_code, url)
        except httpx.TimeoutException:
            logger.error("Timeout fetching %s", url)
        except httpx.RequestError as exc:
            logger.error("Request error for %s: %s", url, exc)
        except Exception:
            logger.exception("Unexpected pipeline failure for %s", url)
        return None
