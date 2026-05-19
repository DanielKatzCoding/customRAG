from bs4 import BeautifulSoup
from models.interfaces import BaseParser


class TextContentParser(BaseParser):
    """Parses pure, clean text from raw HTML."""
    def parse(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        clean_text = soup.get_text(separator="\n")
        return "\n".join([line.strip() for line in clean_text.splitlines() if line.strip()])
