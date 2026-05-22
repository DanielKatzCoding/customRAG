from __future__ import annotations

from abc import ABC, abstractmethod

from .result import ParseResult


class BaseParser(ABC):
    """Interface for processing HTML content."""

    @abstractmethod
    def parse(self, html: str) -> ParseResult:
        ...


class BaseScraper(ABC):
    """Abstract Strategy interface for all HTTP fetchers."""

    @abstractmethod
    async def fetch_html(self, url: str) -> str:
        ...


class BaseSiteResolver(ABC):
    """Resolves a URL to a site key used to look up extraction rules."""

    @abstractmethod
    def resolve(self, url: str) -> str | None:
        ...


class BaseParserProvider(ABC):
    """Factory abstraction: yields the right parser strategy for a given URL."""

    @abstractmethod
    def for_url(self, url: str) -> BaseParser:
        ...


class BaseSink(ABC):
    """Persists a scrape result for a given URL."""

    @abstractmethod
    async def save(self, url: str, result: ParseResult) -> None:
        ...
