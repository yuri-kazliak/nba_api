"""Tests for players use case logic."""

from __future__ import annotations

import json

import pytest

from nba_api.use_cases import players


@pytest.mark.asyncio
async def test_get_players_stats_returns_parsed_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get_all_players_season_stats() -> str:
        return json.dumps(
            {
                "resultSet": {
                    "headers": ["PLAYER"],
                    "rowSet": [["Player 1"]],
                }
            }
        )

    monkeypatch.setattr(
        "nba_api.services.nba_client.get_all_players_season_stats",
        fake_get_all_players_season_stats,
    )

    stats = await players.get_players_stats()
    assert stats == {"categories": ["PLAYER"], "all_players_stats": [["Player 1"]]}


@pytest.mark.asyncio
async def test_get_players_stats_returns_none_for_html(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get_all_players_season_stats() -> str:
        return "<HTML>Error"

    monkeypatch.setattr(
        "nba_api.services.nba_client.get_all_players_season_stats",
        fake_get_all_players_season_stats,
    )

    stats = await players.get_players_stats()
    assert stats is None


@pytest.mark.asyncio
async def test_get_players_stats_handles_parsing_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get_all_players_season_stats() -> str:
        return "{}"

    monkeypatch.setattr(
        "nba_api.services.nba_client.get_all_players_season_stats",
        fake_get_all_players_season_stats,
    )

    stats = await players.get_players_stats()
    assert stats is None
