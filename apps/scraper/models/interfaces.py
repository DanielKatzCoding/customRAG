from abc import ABC, abstractmethod


class BaseParser(ABC):
    """Interface for processing content (SRP)."""
    @abstractmethod
    def parse(self, html: str) -> str:
        pass


class BaseScraper(ABC):
    """Abstract Strategy interface for all scrapers."""
    @abstractmethod
    async def fetch_html(self, url: str) -> str:
        pass


class BaseSiteResolver(ABC):
    """Resolves a URL to a site key used to look up extraction rules."""
    @abstractmethod
    def resolve(self, url: str) -> str | None:
        pass


class BaseParserProvider(ABC):
    """Factory abstraction: yields the right parser strategy for a given URL."""
    @abstractmethod
    def for_url(self, url: str) -> BaseParser:
        pass
