import json
from pathlib import Path
from urllib.parse import urlparse

from models import ExtractionSettings, SiteExtractionRule


class ExtractionSettingsLoader:
    """Single-responsibility loader: JSON file -> ExtractionSettings."""

    def __init__(self, path: str | Path):
        self._path = Path(path)

    def load(self) -> ExtractionSettings:
        try:
            with self._path.open(encoding="utf-8") as f:
                raw = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed {self._path.name}: {exc}") from exc

        if not isinstance(raw, dict):
            raise ValueError(f"{self._path.name} must be a JSON object")

        urls = self._validate_string_list(raw, "url_scraping")
        if not urls:
            raise ValueError(f"{self._path.name}: 'url_scraping' is empty or missing")

        for url in urls:
            scheme = urlparse(url).scheme
            if scheme not in ("http", "https"):
                raise ValueError(f"Unsupported URL scheme {scheme!r}: {url!r}")

        limitation = self._validate_string_list_map(raw, "limitation_by_class")
        extras_map = self._validate_string_list_map(raw, "extra_data_by_class")

        site_keys = set(limitation) | set(extras_map)
        rules = {
            site: SiteExtractionRule(
                content_classes=tuple(limitation.get(site, [])),
                extra_classes=tuple(extras_map.get(site, [])),
            )
            for site in site_keys
        }

        return ExtractionSettings(urls=tuple(urls), rules=rules)

    @staticmethod
    def _validate_string_list(raw: dict, key: str) -> list[str]:
        value = raw.get(key, [])
        if not isinstance(value, list):
            raise ValueError(f"'{key}' must be a list of strings")
        for i, item in enumerate(value):
            if not isinstance(item, str) or not item:
                raise ValueError(f"'{key}[{i}]' must be a non-empty string")
        return value

    @staticmethod
    def _validate_string_list_map(raw: dict, key: str) -> dict[str, list[str]]:
        value = raw.get(key, {}) or {}
        if not isinstance(value, dict):
            raise ValueError(f"'{key}' must be a JSON object")
        for site, classes in value.items():
            if not isinstance(classes, list):
                raise ValueError(f"'{key}.{site}' must be a list of strings")
            for i, cls in enumerate(classes):
                if not isinstance(cls, str) or not cls:
                    raise ValueError(f"'{key}.{site}[{i}]' must be a non-empty string")
        return value
