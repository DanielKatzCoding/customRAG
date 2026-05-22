from bs4 import BeautifulSoup

from models import BaseParser, SiteExtractionRule


class TextContentParser(BaseParser):
    """Fallback strategy: parses pure, clean text from raw HTML."""
    def parse(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        clean_text = soup.get_text(separator="\n")
        return "\n".join(line.strip() for line in clean_text.splitlines() if line.strip())


class ClassFilteredParser(BaseParser):
    """
    Strategy that extracts only elements whose CSS class matches the
    site-specific rule. `content_classes` form the main body; `extra_classes`
    are appended as labeled metadata.
    """

    def __init__(self, rule: SiteExtractionRule):
        self._rule = rule

    def parse(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        body = [text for _, text in self._collect(soup, self._rule.content_classes)]
        extras = [f"[{cls}] {text}" for cls, text in self._collect(soup, self._rule.extra_classes)]

        sections: list[str] = []
        if body:
            sections.append("\n".join(body))
        if extras:
            sections.append("\n".join(extras))

        return "\n\n".join(sections)

    @staticmethod
    def _collect(soup: BeautifulSoup, classes: tuple[str, ...]) -> list[tuple[str, str]]:
        results: list[tuple[str, str]] = []
        for css_class in classes:
            for element in soup.find_all(class_=css_class):
                text = element.get_text(separator=" ", strip=True)
                if text:
                    results.append((css_class, text))
        return results
