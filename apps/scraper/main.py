from core.utils import safe_name
import asyncio
import random
import aiofiles
from config import StealthConfig
from services import PlaywrightStealthScraper, Scraper, TextContentParser


async def main():
    # 1. Setup configurations
    config = StealthConfig()

    # 2. Inject dependencies (DIP / Dependency Injection)
    scraper_engine = PlaywrightStealthScraper(config)
    content_parser = TextContentParser()

    # 3. Instantiate the Facade orchestrator
    bot = Scraper(scraper=scraper_engine, parser=content_parser)

    urls = [
        "https://www.ynet.co.il/news/article/hkfhxptjml"
    ]

    for url in urls:
        text = await bot.scrape_to_text(url)
        if text:
            print(f"\n--- SUCCESSFUL EXTRACTION ---\n{text[:300]}\n...")
            safe_url = safe_name(url)
            async with aiofiles.open(f"{safe_url}.txt", 'w') as f:
                await f.write(text)

        # Throttling between site targets
        await asyncio.sleep(random.uniform(3, 6))

if __name__ == "__main__":
    asyncio.run(main())
