import json
from pathlib import Path

from models import ExtractionSettings, SiteExtractionRule


class ExtractionSettingsLoader:
    """Single-responsibility loader: JSON file -> ExtractionSettings."""

    def __init__(self, path: str | Path):
        self._path = Path(path)

    def load(self) -> ExtractionSettings:
        with self._path.open("r", encoding="utf-8") as f:
            raw = json.load(f)

        urls = tuple(raw.get("url_scraping", []))
        limitation = raw.get("limitation_by_class", {}) or {}
        extras = raw.get("extra_data_by_class", {}) or {}

        site_keys = set(limitation) | set(extras)
        rules = {
            site: SiteExtractionRule(
                content_classes=tuple(limitation.get(site, [])),
                extra_classes=tuple(extras.get(site, [])),
            )
            for site in site_keys
        }

        return ExtractionSettings(urls=urls, rules=rules)
