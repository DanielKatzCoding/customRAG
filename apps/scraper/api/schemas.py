"""Pydantic V2 request and response schemas for the scraper API."""

from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl, field_validator

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _validated_urls(urls: list[str]) -> list[str]:
    """Validate that every entry is an http/https URL (reused across schemas)."""
    for url in urls:
        parsed = HttpUrl(url)  # raises ValidationError on bad input
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"URL scheme must be http or https, got: {url!r}")
    return urls


# ---------------------------------------------------------------------------
# Scrape request / response
# ---------------------------------------------------------------------------


class ScrapeRequest(BaseModel):
    """Body for POST /scrape."""

    urls: list[str] = Field(
        min_length=1,
        max_length=50,
        description="One or more http/https URLs to scrape.",
    )

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v: list[str]) -> list[str]:
        return _validated_urls(v)


class ScrapeItemResult(BaseModel):
    """Per-URL result included in a scrape response."""

    url: str
    success: bool
    content: list[str] = Field(default_factory=list)
    extras: dict[str, list[str]] = Field(default_factory=dict)
    error: str | None = None


class ScrapeResponse(BaseModel):
    """Response body for POST /scrape and POST /scrape/all."""

    results: list[ScrapeItemResult]
    total: int
    succeeded: int
    failed: int


# ---------------------------------------------------------------------------
# Settings read
# ---------------------------------------------------------------------------


class SiteExtractionRuleSchema(BaseModel):
    """JSON representation of a per-site extraction rule."""

    content_classes: list[str]
    extra_classes: list[str]


class SettingsResponse(BaseModel):
    """Response body for GET /settings."""

    urls: list[str]
    rules: dict[str, SiteExtractionRuleSchema]


# ---------------------------------------------------------------------------
# Settings mutation requests
# ---------------------------------------------------------------------------


class UrlListRequest(BaseModel):
    """Body for PUT/POST/DELETE /settings/urls."""

    urls: list[str] = Field(
        min_length=1,
        max_length=200,
        description="List of http/https URLs.",
    )

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v: list[str]) -> list[str]:
        return _validated_urls(v)


class UpsertRuleRequest(BaseModel):
    """Body for PUT /settings/rules/{site_key}."""

    content_classes: list[str] = Field(
        default_factory=list,
        description="CSS class names for main content extraction.",
    )
    extra_classes: list[str] = Field(
        default_factory=list,
        description="CSS class names extracted into the extras dict.",
    )

    @field_validator("content_classes", "extra_classes")
    @classmethod
    def no_empty_strings(cls, v: list[str]) -> list[str]:
        for item in v:
            if not item or not item.strip():
                raise ValueError("Class names must be non-empty strings.")
        return v


# ---------------------------------------------------------------------------
# Generic responses
# ---------------------------------------------------------------------------


class MessageResponse(BaseModel):
    """Generic acknowledgement response."""

    message: str


class ErrorDetail(BaseModel):
    """Structured error body returned on 4xx/5xx responses."""

    error: str
    detail: str | None = None
