import logging

from models import BaseParserProvider, BaseScraper

logger = logging.getLogger(__name__)


class Scraper:
    """
    Facade that orchestrates the scraping pipeline.
    Depends on abstractions (DIP): a scraper engine and a parser provider.
    """
    def __init__(self, scraper: BaseScraper, parser_provider: BaseParserProvider):
        self._scraper = scraper
        self._parser_provider = parser_provider

    async def scrape_to_text(self, url: str) -> str:
        try:
            logger.info("Fetching: %s", url)
            raw_html = await self._scraper.fetch_html(url)
            parser = self._parser_provider.for_url(url)
            return parser.parse(raw_html)
        except Exception as e:
            logger.error("Pipeline failed for %s: %s", url, e)
            return ""
