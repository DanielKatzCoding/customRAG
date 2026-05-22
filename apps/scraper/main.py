import asyncio
import logging
import random
from pathlib import Path

import aiofiles
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from config import StealthConfig
from core.logging_setup import setup_logging
from core.settings_loader import ExtractionSettingsLoader
from core.site_resolver import DomainKeywordSiteResolver
from core.utils import safe_name
from services import (
    HttpScraper,
    RuleBasedParserProvider,
    Scraper,
)

SETTINGS_PATH = Path(__file__).parent / "extraction_settings.json"

logger = logging.getLogger(__name__)


async def main():
    setup_logging()

    # 1. Load extraction configuration (URLs + per-site class rules)
    settings = ExtractionSettingsLoader(SETTINGS_PATH).load()

    # 2. Compose dependencies (DIP / Dependency Injection)
    stealth_config = StealthConfig()
    scraper_engine = HttpScraper(stealth_config)
    site_resolver = DomainKeywordSiteResolver(known_keys=tuple(settings.rules.keys()))
    parser_provider = RuleBasedParserProvider(settings=settings, resolver=site_resolver)

    # 3. Facade orchestrator
    bot = Scraper(scraper=scraper_engine, parser_provider=parser_provider)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("Scraping", total=len(settings.urls))

        for url in settings.urls:
            progress.update(task, description=f"[bold blue]{url}")
            text = await bot.scrape_to_text(url)

            if text:
                logger.info("Extracted %d chars from %s", len(text), url)
                async with aiofiles.open(f"{safe_name(url)}.txt", "w", encoding="utf-8") as f:
                    await f.write(text)

            progress.advance(task)
            await asyncio.sleep(random.uniform(3, 6))

    logger.info("Done — scraped %d URL(s)", len(settings.urls))


if __name__ == "__main__":
    asyncio.run(main())
