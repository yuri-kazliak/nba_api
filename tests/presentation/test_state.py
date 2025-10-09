"""Tests for presentation state helpers."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Awaitable, Coroutine, Generator, cast

import pytest

from nba_api.presentation import state


@pytest.fixture(autouse=True)
def reset_state() -> Generator[None, None, None]:
    state.clear_state()
    yield
    state.clear_state()


@pytest.mark.asyncio
async def test_refresh_boxscore_invokes_use_case(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get_stats() -> str:
        return "stats"

    monkeypatch.setattr(state.scoreboard_use_case, "get_stats", fake_get_stats)

    await state.refresh_boxscore()

    assert state.get_todays_boxscore() == "stats"


@pytest.mark.asyncio
async def test_refresh_players_stats_invokes_use_case(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get_stats() -> str:
        return "players"

    monkeypatch.setattr(state.players_use_case, "get_players_stats", fake_get_stats)

    await state.refresh_players_stats()

    assert state.get_all_players_stats() == "players"


@pytest.mark.asyncio
async def test_ensure_boxscore_fresh_refreshes_when_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    async def fake_refresh() -> None:
        calls.append("refresh")

    monkeypatch.setattr(state, "refresh_boxscore", fake_refresh)

    await state.ensure_boxscore_fresh()

    assert calls == ["refresh"]


@pytest.mark.asyncio
async def test_ensure_boxscore_fresh_schedules_when_stale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scheduled: list[str] = []

    async def fake_refresh() -> None:
        scheduled.append("refresh")

    original_create_task = asyncio.create_task

    def fake_create_task(coro: Awaitable[Any]) -> asyncio.Task[Any]:
        scheduled.append("scheduled")
        coroutine = cast(Coroutine[Any, Any, Any], coro)
        return original_create_task(coroutine)

    monkeypatch.setattr(state.asyncio, "create_task", fake_create_task)
    monkeypatch.setattr(state, "refresh_boxscore", fake_refresh)

    state.set_todays_boxscore(
        {"foo": "bar"}, timestamp=datetime.now() - timedelta(minutes=16)
    )

    await state.ensure_boxscore_fresh()
    await asyncio.sleep(0)

    assert scheduled[0] == "scheduled"


@pytest.mark.asyncio
async def test_players_stats_refreshes_when_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    async def fake_refresh() -> None:
        calls.append("refresh")

    monkeypatch.setattr(state, "refresh_players_stats", fake_refresh)

    await state.ensure_players_stats_fresh()

    assert calls == ["refresh"]


@pytest.mark.asyncio
async def test_players_stats_schedules_when_stale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scheduled: list[str] = []

    async def fake_refresh() -> None:
        scheduled.append("refresh")

    original_create_task = asyncio.create_task

    def fake_create_task(coro: Awaitable[Any]) -> asyncio.Task[Any]:
        scheduled.append("scheduled")
        coroutine = cast(Coroutine[Any, Any, Any], coro)
        return original_create_task(coroutine)

    monkeypatch.setattr(state.asyncio, "create_task", fake_create_task)
    monkeypatch.setattr(state, "refresh_players_stats", fake_refresh)

    state.set_all_players_stats(
        {"foo": "bar"}, timestamp=datetime.now() - timedelta(hours=2)
    )

    await state.ensure_players_stats_fresh()
    await asyncio.sleep(0)

    assert scheduled[0] == "scheduled"
