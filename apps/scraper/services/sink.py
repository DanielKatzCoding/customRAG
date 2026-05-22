import json
import logging
from pathlib import Path

import aiofiles

from core.utils import safe_name
from models import BaseSink, ParseResult

logger = logging.getLogger(__name__)


class JsonFileSink(BaseSink):
    """Writes a ParseResult to a JSON file under *output_dir*, atomically."""

    def __init__(self, output_dir: Path):
        self._output_dir = output_dir

    async def save(self, url: str, result: ParseResult) -> None:
        payload = {
            "url": url,
            "content": result.content,
            "extras": result.extras,
        }
        out_path = self._output_dir / f"{safe_name(url)}.json"
        tmp_path = out_path.with_suffix(".tmp")

        async with aiofiles.open(tmp_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(payload, ensure_ascii=False, indent=2))

        tmp_path.replace(out_path)
        logger.info(
            "Saved %d content item(s), %d extra class(es) to %s",
            len(result.content),
            len(result.extras),
            out_path.name,
        )
