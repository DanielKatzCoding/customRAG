"""Routes for reading and mutating extraction_settings.json."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from models import SiteExtractionRule

from api.dependencies import StoreDep
from api.schemas import (
    SettingsResponse,
    SiteExtractionRuleSchema,
    UpsertRuleRequest,
    UrlListRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


def _settings_response(store: StoreDep) -> SettingsResponse:
    s = store.settings
    return SettingsResponse(
        urls=list(s.urls),
        rules={
            site_key: SiteExtractionRuleSchema(
                content_classes=list(rule.content_classes),
                extra_classes=list(rule.extra_classes),
            )
            for site_key, rule in s.rules.items()
        },
    )


# ---------------------------------------------------------------------------
# GET /settings
# ---------------------------------------------------------------------------


@router.get("", response_model=SettingsResponse, summary="Return current extraction settings")
async def get_settings(store: StoreDep) -> SettingsResponse:
    """Return the in-memory view of extraction_settings.json (always up to date)."""
    return _settings_response(store)


# ---------------------------------------------------------------------------
# URL management
# ---------------------------------------------------------------------------


@router.put(
    "/urls",
    response_model=SettingsResponse,
    summary="Replace the full url_scraping list",
)
async def replace_urls(body: UrlListRequest, store: StoreDep) -> SettingsResponse:
    """Overwrite url_scraping with exactly the URLs provided."""
    await store.replace_urls(body.urls)
    logger.info("Replaced url_scraping list (%d URL(s))", len(body.urls))
    return _settings_response(store)


@router.post(
    "/urls",
    response_model=SettingsResponse,
    summary="Append URLs to url_scraping",
)
async def append_urls(body: UrlListRequest, store: StoreDep) -> SettingsResponse:
    """Append the supplied URLs to url_scraping (duplicates are silently ignored)."""
    await store.append_urls(body.urls)
    logger.info("Appended URL(s) to url_scraping")
    return _settings_response(store)


@router.delete(
    "/urls",
    response_model=SettingsResponse,
    summary="Remove specific URLs from url_scraping",
)
async def remove_urls(body: UrlListRequest, store: StoreDep) -> SettingsResponse:
    """Remove the supplied URLs from url_scraping (unknown URLs are silently ignored)."""
    await store.remove_urls(body.urls)
    logger.info("Removed URL(s) from url_scraping")
    return _settings_response(store)


# ---------------------------------------------------------------------------
# Rule management
# ---------------------------------------------------------------------------


@router.put(
    "/rules/{site_key}",
    response_model=SettingsResponse,
    summary="Upsert extraction rule for a site",
)
async def upsert_rule(
    site_key: str,
    body: UpsertRuleRequest,
    store: StoreDep,
) -> SettingsResponse:
    """
    Create or replace the extraction rule for *site_key*.

    The site key is matched case-sensitively against URL hostname tokens by
    DomainKeywordSiteResolver (e.g. ``ynet`` matches ``www.ynet.co.il``).
    """
    if not site_key or not site_key.strip():
        raise HTTPException(status_code=422, detail="site_key must be a non-empty string.")

    rule = SiteExtractionRule(
        content_classes=tuple(body.content_classes),
        extra_classes=tuple(body.extra_classes),
    )
    await store.upsert_rule(site_key, rule)
    logger.info("Upserted rule for site_key=%r", site_key)
    return _settings_response(store)


@router.delete(
    "/rules/{site_key}",
    response_model=SettingsResponse,
    summary="Remove extraction rule for a site",
)
async def delete_rule(site_key: str, store: StoreDep) -> SettingsResponse:
    """Remove the extraction rule for *site_key*. Returns 404 if it does not exist."""
    removed = await store.delete_rule(site_key)
    if not removed:
        raise HTTPException(
            status_code=404,
            detail=f"No extraction rule found for site_key={site_key!r}.",
        )
    logger.info("Deleted rule for site_key=%r", site_key)
    return _settings_response(store)
