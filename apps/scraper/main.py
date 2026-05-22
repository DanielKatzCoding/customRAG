import asyncio
import logging
import random
from pathlib import Path

from rich.markup import escape
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
from services import (
    HttpScraper,
    JsonFileSink,
    RuleBasedParserProvider,
    ScrapingFacade,
)

SETTINGS_PATH = Path(__file__).parent / "extraction_settings.json"
OUTPUT_DIR = Path(__file__).parent / "output_scrape"

logger = logging.getLogger(__name__)


async def main() -> None:
    setup_logging()
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 1. Load and validate extraction configuration (URLs + per-site class rules)
    settings = ExtractionSettingsLoader(SETTINGS_PATH).load()

    # 2. Compose dependencies (DIP / Dependency Injection)
    stealth_config = StealthConfig()
    site_resolver = DomainKeywordSiteResolver(known_keys=tuple(settings.rules.keys()))
    parser_provider = RuleBasedParserProvider(settings=settings, resolver=site_resolver)
    sink = JsonFileSink(OUTPUT_DIR)

    # 3. Run pipeline — client is created once and reused across all URLs
    async with HttpScraper(stealth_config) as scraper_engine:
        pipeline = ScrapingFacade(scraper=scraper_engine, parser_provider=parser_provider)

        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("Scraping", total=len(settings.urls))

            for i, url in enumerate(settings.urls):
                progress.update(task, description=f"[bold blue]{escape(url)}[/bold blue]")
                result = await pipeline.scrape(url)

                if result and not result.is_empty:
                    await sink.save(url, result)

                progress.advance(task)

                if i < len(settings.urls) - 1:
                    await asyncio.sleep(random.uniform(3, 6))

    logger.info("Done — scraped %d URL(s)", len(settings.urls))


if __name__ == "__main__":
    asyncio.run(main())
