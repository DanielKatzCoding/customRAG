"""
Thread-safe in-memory store for ExtractionSettings with atomic file persistence.

Keeping this as a distinct module (not inside dependencies.py) isolates the
mutation + persistence logic from FastAPI plumbing, making it independently
testable.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from core.site_resolver import DomainKeywordSiteResolver
from models import ExtractionSettings, SiteExtractionRule
from services import RuleBasedParserProvider, ScrapingFacade

logger = logging.getLogger(__name__)


def _build_raw_json(settings: ExtractionSettings) -> dict:
    """Serialize ExtractionSettings back to the extraction_settings.json shape."""
    limitation: dict[str, list[str]] = {}
    extra_data: dict[str, list[str]] = {}

    for site_key, rule in settings.rules.items():
        if rule.content_classes:
            limitation[site_key] = list(rule.content_classes)
        if rule.extra_classes:
            extra_data[site_key] = list(rule.extra_classes)

    return {
        "url_scraping": list(settings.urls),
        "limitation_by_class": limitation,
        "extra_data_by_class": extra_data,
    }


def _build_settings(urls: list[str], rules: dict[str, SiteExtractionRule]) -> ExtractionSettings:
    return ExtractionSettings(urls=tuple(urls), rules=rules)


def _build_provider(settings: ExtractionSettings) -> RuleBasedParserProvider:
    resolver = DomainKeywordSiteResolver(known_keys=tuple(settings.rules.keys()))
    return RuleBasedParserProvider(settings=settings, resolver=resolver)


class SettingsStore:
    """
    Single source of truth for the current ExtractionSettings.

    Mutations atomically:
      1. Produce the new ExtractionSettings in memory.
      2. Persist the canonical JSON file (write-to-temp then rename).
      3. Rebuild RuleBasedParserProvider so the live facade uses updated rules.

    An asyncio.Lock serialises concurrent mutation calls. Reads are lock-free
    (Python GIL + immutable dataclasses make snapshot reads safe).
    """

    def __init__(
        self,
        settings_path: Path,
        initial_settings: ExtractionSettings,
        scraper_engine,  # HttpScraper — injected, not imported, to avoid circular deps
    ) -> None:
        self._path = settings_path
        self._settings = initial_settings
        self._scraper_engine = scraper_engine
        self._provider = _build_provider(initial_settings)
        self._facade = ScrapingFacade(scraper=scraper_engine, parser_provider=self._provider)
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Read access (no lock needed — immutable dataclasses + GIL)
    # ------------------------------------------------------------------

    @property
    def settings(self) -> ExtractionSettings:
        return self._settings

    @property
    def facade(self) -> ScrapingFacade:
        return self._facade

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _persist_and_reload(self, new_settings: ExtractionSettings) -> None:
        """Write new_settings to disk (atomically) then hot-swap in-memory state."""
        raw = _build_raw_json(new_settings)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=4), encoding="utf-8")
        tmp.replace(self._path)
        logger.info("Persisted extraction_settings.json")

        self._settings = new_settings
        self._provider = _build_provider(new_settings)
        self._facade = ScrapingFacade(scraper=self._scraper_engine, parser_provider=self._provider)
        logger.debug("Hot-reloaded in-memory settings and pipeline provider")

    # ------------------------------------------------------------------
    # Mutation operations (all serialised through _lock)
    # ------------------------------------------------------------------

    async def replace_urls(self, urls: list[str]) -> None:
        async with self._lock:
            new_settings = _build_settings(
                urls=urls,
                rules=dict(self._settings.rules),
            )
            await self._persist_and_reload(new_settings)

    async def append_urls(self, urls: list[str]) -> None:
        async with self._lock:
            existing = list(self._settings.urls)
            # Deduplicate while preserving order
            seen = set(existing)
            added = [u for u in urls if u not in seen]
            new_settings = _build_settings(
                urls=existing + added,
                rules=dict(self._settings.rules),
            )
            await self._persist_and_reload(new_settings)

    async def remove_urls(self, urls: list[str]) -> None:
        async with self._lock:
            to_remove = set(urls)
            remaining = [u for u in self._settings.urls if u not in to_remove]
            new_settings = _build_settings(
                urls=remaining,
                rules=dict(self._settings.rules),
            )
            await self._persist_and_reload(new_settings)

    async def upsert_rule(self, site_key: str, rule: SiteExtractionRule) -> None:
        async with self._lock:
            rules = dict(self._settings.rules)
            rules[site_key] = rule
            new_settings = _build_settings(
                urls=list(self._settings.urls),
                rules=rules,
            )
            await self._persist_and_reload(new_settings)

    async def delete_rule(self, site_key: str) -> bool:
        """Returns True if the rule existed and was removed, False otherwise."""
        async with self._lock:
            rules = dict(self._settings.rules)
            if site_key not in rules:
                return False
            del rules[site_key]
            new_settings = _build_settings(
                urls=list(self._settings.urls),
                rules=rules,
            )
            await self._persist_and_reload(new_settings)
            return True
