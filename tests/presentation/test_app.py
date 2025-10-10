"""Tests for FastAPI application factory and lifespan hooks."""

from __future__ import annotations

from typing import List

import pytest
from fastapi import FastAPI

from nba_api.presentation import app as app_module


def test_create_app_registers_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    init_calls: List[str] = []
    close_calls: List[str] = []

    async def fake_init_http_client() -> None:
        init_calls.append("init")

    async def fake_close_http_client() -> None:
        close_calls.append("close")

    monkeypatch.setattr("nba_api.presentation.app.init_http_client", fake_init_http_client)

    monkeypatch.setattr("nba_api.presentation.app.close_http_client", fake_close_http_client)

    monkeypatch.setattr("nba_api.presentation.app.state.clear_state", lambda: None)

    created_app = app_module.create_app()

    assert isinstance(created_app, FastAPI)
    routes = {getattr(route, "path", None) for route in created_app.routes}
    routes.discard(None)
    assert "/players-stats/" in routes
    assert "/refresh" in routes or "/" in routes


@pytest.mark.asyncio
async def test_lifespan_calls_init_and_close(monkeypatch: pytest.MonkeyPatch) -> None:
    init_called: List[bool] = []
    close_called: List[bool] = []
    cleared: List[bool] = []

    async def fake_init_http_client() -> None:
        init_called.append(True)

    async def fake_close_http_client() -> None:
        close_called.append(True)

    def fake_clear_state() -> None:
        cleared.append(True)

    monkeypatch.setattr("nba_api.presentation.app.init_http_client", fake_init_http_client)
    monkeypatch.setattr("nba_api.presentation.app.close_http_client", fake_close_http_client)
    monkeypatch.setattr("nba_api.presentation.app.state.clear_state", fake_clear_state)

    test_app = app_module.create_app()

    async with test_app.router.lifespan_context(test_app) as _:
        assert init_called == [True]

    assert close_called == [True]
    assert cleared == [True]
