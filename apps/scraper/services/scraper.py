# scrapers.py
import asyncio
import random

from config import StealthConfig
from models.interfaces import BaseScraper
from playwright.async_api import async_playwright


class PlaywrightStealthScraper(BaseScraper):
    """Concrete Strategy implementing human-like Playwright scraping."""
    def __init__(self, config: StealthConfig):
        self.config = config

    async def fetch_html(self, url: str) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context_options = self.config.get_browser_context_options()
            context = await browser.new_context(**context_options)
            page = await context.new_page()

            # Hide automation footprints
            await page.add_init_script("delete navigator.__proto__.webdriver;")

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # Simulate human interaction (random scroll)
                await page.evaluate("window.scrollBy(0, window.innerHeight);")
                await asyncio.sleep(random.uniform(2, 5))

                return await page.content()
            finally:
                await context.close()
                await browser.close()
