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
