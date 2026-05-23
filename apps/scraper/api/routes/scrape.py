"""Routes for triggering scrape operations."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter

from api.dependencies import StoreDep
from api.schemas import ScrapeItemResult, ScrapeRequest, ScrapeResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scrape", tags=["scrape"])


async def _run_single(store: StoreDep, url: str) -> ScrapeItemResult:
    """Execute the scraping pipeline for a single URL and return a structured result."""
    result = await store.facade.scrape(url)
    if result is None:
        logger.warning("Scrape returned no result for %s", url)
        return ScrapeItemResult(
            url=url,
            success=False,
            error="Scrape failed — check server logs for details.",
        )
    return ScrapeItemResult(
        url=url,
        success=not result.is_empty,
        content=result.content,
        extras=result.extras,
        error=None if not result.is_empty else "Scrape succeeded but returned empty content.",
    )


def _build_response(results: list[ScrapeItemResult]) -> ScrapeResponse:
    succeeded = sum(1 for r in results if r.success)
    return ScrapeResponse(
        results=results,
        total=len(results),
        succeeded=succeeded,
        failed=len(results) - succeeded,
    )


@router.post("", response_model=ScrapeResponse, summary="Scrape one or more URLs")
async def scrape_urls(body: ScrapeRequest, store: StoreDep) -> ScrapeResponse:
    """
    Trigger scraping of the URLs supplied in the request body.
    All URLs are fetched concurrently; results are returned in the same order.
    """
    tasks = [_run_single(store, url) for url in body.urls]
    results: list[ScrapeItemResult] = await asyncio.gather(*tasks)
    return _build_response(list(results))


@router.post(
    "/all",
    response_model=ScrapeResponse,
    summary="Scrape all URLs from extraction_settings.json",
)
async def scrape_all(store: StoreDep) -> ScrapeResponse:
    """
    Trigger scraping of every URL currently configured in extraction_settings.json.
    All URLs are fetched concurrently.
    """
    urls = list(store.settings.urls)
    if not urls:
        return ScrapeResponse(results=[], total=0, succeeded=0, failed=0)

    tasks = [_run_single(store, url) for url in urls]
    results: list[ScrapeItemResult] = await asyncio.gather(*tasks)
    return _build_response(list(results))
