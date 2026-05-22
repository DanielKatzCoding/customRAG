from dataclasses import dataclass, field


@dataclass(frozen=True)
class SiteExtractionRule:
    """Per-site extraction configuration."""
    content_classes: tuple[str, ...] = ()
    extra_classes: tuple[str, ...] = ()

    @property
    def is_empty(self) -> bool:
        return not self.content_classes and not self.extra_classes


@dataclass(frozen=True)
class ExtractionSettings:
    """Aggregate root for extraction configuration loaded from JSON."""
    urls: tuple[str, ...] = ()
    rules: dict[str, SiteExtractionRule] = field(default_factory=dict)

    def rule_for(self, site_key: str | None) -> SiteExtractionRule:
        if site_key is None:
            return SiteExtractionRule()
        return self.rules.get(site_key, SiteExtractionRule())
