"""Tests for NBA client service wrappers."""

from __future__ import annotations

from typing import Any, Dict

import pytest

from nba_api.services import nba_client


@pytest.mark.asyncio
async def test_get_todays_scoreboard_calls_perform_get(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: Dict[str, Any] = {}

    async def fake_perform_get(*args: Any, **kwargs: Any) -> str:
        calls["args"] = args
        calls["kwargs"] = kwargs
        return "payload"

    monkeypatch.setattr("nba_api.services.nba_client.perform_get", fake_perform_get)

    result = await nba_client.get_todays_scoreboard()

    assert result == "payload"
    assert calls["args"][0].endswith("todaysScoreboard_00.json")
    assert calls["kwargs"]["cache_ttl_seconds"] == 15.0


@pytest.mark.asyncio
async def test_get_single_game_full_stats(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: Dict[str, Any] = {}

    async def fake_perform_get(*args: Any, **kwargs: Any) -> str:
        calls["args"] = args
        calls["kwargs"] = kwargs
        return "details"

    monkeypatch.setattr("nba_api.services.nba_client.perform_get", fake_perform_get)

    result = await nba_client.get_single_game_full_stats("002")

    assert result == "details"
    assert calls["kwargs"]["params"]["gameId"] == "002"
    assert "ocp-apim-subscription-key" in calls["kwargs"]["headers"]


@pytest.mark.asyncio
async def test_get_all_players_season_stats(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: Dict[str, Any] = {}

    async def fake_perform_get(*args: Any, **kwargs: Any) -> str:
        calls["kwargs"] = kwargs
        return "stats"

    monkeypatch.setattr("nba_api.services.nba_client.perform_get", fake_perform_get)

    result = await nba_client.get_all_players_season_stats()

    assert result == "stats"
    assert calls["kwargs"]["params"]["StatCategory"] == "REB"


@pytest.mark.asyncio
async def test_get_specific_gameday_stats(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: Dict[str, Any] = {}

    async def fake_perform_get(*args: Any, **kwargs: Any) -> str:
        calls["kwargs"] = kwargs
        return "gameday"

    monkeypatch.setattr("nba_api.services.nba_client.perform_get", fake_perform_get)

    result = await nba_client.get_specific_gameday_stats("11/10/2024")

    assert result == "gameday"
    assert calls["kwargs"]["params"]["gamedate"] == "11/10/2024"
