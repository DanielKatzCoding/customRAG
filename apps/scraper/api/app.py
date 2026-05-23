"""
FastAPI application factory for the scraper service.

Lifespan contract
-----------------
* On startup : open a single HttpScraper (async context manager), load
  ExtractionSettings from disk, build a SettingsStore, attach it to
  app.state.store so every request dependency can reach it.
* On shutdown: gracefully close the HttpScraper (drains in-flight requests).

Keeping the HttpScraper open for the lifetime of the process allows the
underlying httpx.AsyncClient (HTTP/2 + connection pool) to be reused across
all requests — no per-request TLS handshake overhead.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from config import ScraperSettings, StealthConfig
from core.logging_setup import setup_logging
from core.settings_loader import ExtractionSettingsLoader
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from services import HttpScraper

from api.routes import scrape, settings
from api.settings_store import SettingsStore

logger = logging.getLogger(__name__)

SETTINGS_PATH = Path(__file__).parent.parent / "extraction_settings.json"

_MAX_REQUEST_BODY_BYTES = 1 * 1024 * 1024  # 1 MB


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the HttpScraper lifecycle and wire the dependency graph."""
    scraper_settings = ScraperSettings()
    setup_logging(scraper_settings.log_level)

    logger.info("Loading extraction settings from %s", SETTINGS_PATH)
    initial_settings = ExtractionSettingsLoader(SETTINGS_PATH).load()

    stealth_config = StealthConfig.from_settings(scraper_settings)

    async with HttpScraper(stealth_config) as scraper_engine:
        logger.info("HttpScraper initialised — HTTP/2 client ready")
        app.state.store = SettingsStore(
            settings_path=SETTINGS_PATH,
            initial_settings=initial_settings,
            scraper_engine=scraper_engine,
        )
        yield
        logger.info("Shutting down — closing HttpScraper")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Scraper API",
        description=(
            "REST API for triggering the rule-based web scraper and managing "
            "extraction_settings.json."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------
    # Request size guard middleware
    # ------------------------------------------------------------------

    @app.middleware("http")
    async def limit_request_body(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > _MAX_REQUEST_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "Request body too large",
                    "detail": f"Maximum allowed size is {_MAX_REQUEST_BODY_BYTES} bytes.",
                },
            )
        return await call_next(request)

    # ------------------------------------------------------------------
    # Exception handlers
    # ------------------------------------------------------------------

    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
        logger.warning("Validation error: %s", exc)
        return JSONResponse(
            status_code=422,
            content={"error": "Validation error", "detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(exc)},
        )

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------

    app.include_router(scrape.router)
    app.include_router(settings.router)

    return app


app = create_app()
