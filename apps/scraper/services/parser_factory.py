from models import (
    BaseParser,
    BaseParserProvider,
    BaseSiteResolver,
    ExtractionSettings,
)

from .parser import ClassFilteredParser, TextContentParser


class RuleBasedParserProvider(BaseParserProvider):
    """
    Factory + Strategy selector.
    Picks ClassFilteredParser when the URL maps to a known site rule,
    otherwise falls back to TextContentParser.
    """

    def __init__(
        self,
        settings: ExtractionSettings,
        resolver: BaseSiteResolver,
        fallback: BaseParser | None = None,
    ):
        self._settings = settings
        self._resolver = resolver
        self._fallback = fallback or TextContentParser()

    def for_url(self, url: str) -> BaseParser:
        site_key = self._resolver.resolve(url)
        rule = self._settings.rule_for(site_key)
        if rule.is_empty:
            return self._fallback
        return ClassFilteredParser(rule)
