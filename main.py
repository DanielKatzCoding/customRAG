"""
Scraper API server entry point.

Adds apps/scraper to sys.path so the scraper package's bare-module imports
(``from models import ...``, ``from config import ...``, etc.) resolve
correctly when the server is launched from the repo root.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRAPER_ROOT = Path(__file__).parent / "apps" / "scraper"
if str(_SCRAPER_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRAPER_ROOT))

import uvicorn  # noqa: E402 — must come after sys.path is patched


def main() -> None:
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        app_dir=str(_SCRAPER_ROOT),
        log_config=None,  # logging is configured inside the app lifespan
    )


if __name__ == "__main__":
    main()
