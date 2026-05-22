from bs4 import BeautifulSoup

from models import BaseParser, ParseResult, SiteExtractionRule


class TextContentParser(BaseParser):
    """Fallback strategy: extracts clean text from raw HTML."""

    def parse(self, html: str) -> ParseResult:
        soup = BeautifulSoup(html, "html.parser")
        for element in soup(["script", "style", "nav", "noscript"]):
            element.decompose()

        clean_text = soup.get_text(separator="\n")
        lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
        return ParseResult(content=lines)


class ClassFilteredParser(BaseParser):
    """
    Strategy that extracts only elements matching per-site CSS class rules.
    content_classes form the main body; extra_classes are keyed by class name
    in the extras dict so callers know the origin of each extracted value.
    """

    def __init__(self, rule: SiteExtractionRule):
        self._rule = rule

    def parse(self, html: str) -> ParseResult:
        soup = BeautifulSoup(html, "html.parser")

        content = [text for _, text in self._collect(soup, self._rule.content_classes)]

        extras: dict[str, list[str]] = {}
        for css_class, text in self._collect(soup, self._rule.extra_classes):
            extras.setdefault(css_class, []).append(text)

        return ParseResult(content=content, extras=extras)

    @staticmethod
    def _collect(
        soup: BeautifulSoup, classes: tuple[str, ...]
    ) -> list[tuple[str, str]]:
        results: list[tuple[str, str]] = []
        for css_class in classes:
            for element in soup.find_all(class_=css_class):
                text = element.get_text(separator=" ", strip=True)
                if text:
                    results.append((css_class, text))
        return results
