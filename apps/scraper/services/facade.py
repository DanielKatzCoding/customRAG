from models.interfaces import BaseParser, BaseScraper


class Scraper:
    """
    Facade class that simplifies high-level scraping operations.
    Combines the configuration, scraper engine, and parser.
    """
    def __init__(self, scraper: BaseScraper, parser: BaseParser):
        self.scraper = scraper
        self.parser = parser

    async def scrape_to_text(self, url: str) -> str:
        try:
            print(f"Executing stealth fetch for: {url}")
            raw_html = await self.scraper.fetch_html(url)
            clean_text = self.parser.parse(raw_html)
            return clean_text
        except Exception as e:
            print(f"Scraping pipeline failed for {url}: {e}")
            return ""
