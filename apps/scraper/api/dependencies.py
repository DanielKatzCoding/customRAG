"""
FastAPI dependency functions that expose the shared SettingsStore to routes.

The store is attached to app.state during lifespan startup so that each
request dependency resolves it via a single attribute lookup — no globals.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from api.settings_store import SettingsStore


def get_store(request: Request) -> SettingsStore:
    """Return the application-scoped SettingsStore from app state."""
    return request.app.state.store


StoreDep = Annotated[SettingsStore, Depends(get_store)]
