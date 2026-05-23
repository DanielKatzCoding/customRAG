import json
import logging
from pathlib import Path

from models.document import RawDocument
from models.interfaces import BaseLoader

logger = logging.getLogger(__name__)


class JsonLoader(BaseLoader):
    def load(self, file_path: Path) -> RawDocument:
        with file_path.open(encoding="utf-8") as fh:
            data = json.load(fh)

        url = data.get("url", "")
        content: list[str] = [s for s in data.get("content", []) if isinstance(s, str) and s.strip()]
        raw_extras = data.get("extras", {})
        extras: dict[str, list[str]] = {
            k: [s for s in v if isinstance(s, str) and s.strip()]
            for k, v in raw_extras.items()
            if isinstance(v, list)
        }

        logger.debug("Loaded %d paragraphs from %s", len(content), file_path.name)
        return RawDocument(url=url, content=content, extras=extras)
