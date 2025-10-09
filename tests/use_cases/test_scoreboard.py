"""Tests for scoreboard use case logic."""

from __future__ import annotations

import json
from typing import Any, Dict, List

import pytest

from nba_api.domain.enums import NBA_GAME_STATUS
from nba_api.use_cases import scoreboard
from nba_api.use_cases.scoreboard import _normalize_game_status


def _scoreboard_payload(games: List[Dict[str, Any]]) -> str:
    return json.dumps(
        {
            "scoreboard": {
                "games": games,
                "gameDate": "2024-10-10",
                "leagueName": "NBA",
            }
        }
    )


@pytest.mark.asyncio
async def test_get_stats_returns_combined_data(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get_todays_scoreboard() -> str:
        return _scoreboard_payload([])

    monkeypatch.setattr(
        "nba_api.services.nba_client.get_todays_scoreboard", fake_get_todays_scoreboard
    )

    result = await scoreboard.get_stats()

    assert result == {
        "Game Date": "2024-10-10",
        "League": "NBA",
        "Games Stats": [],
    }


@pytest.mark.asyncio
async def test_get_stats_filters_only_live_or_final(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get_todays_scoreboard() -> str:
        return _scoreboard_payload(
            [
                {
                    "gameId": "001",
                    "gameStatus": 2,
                    "homeTeam": {
                        "teamTricode": "HOM",
                        "teamId": "001",
                        "teamName": "Home",
                        "teamCity": "City",
                        "wins": 0,
                        "losses": 0,
                        "score": 100,
                        "players": [],
                    },
                    "awayTeam": {
                        "teamTricode": "AWY",
                        "teamId": "002",
                        "teamName": "Away",
                        "teamCity": "City",
                        "wins": 0,
                        "losses": 0,
                        "score": 90,
                        "players": [],
                    },
                },
                {
                    "gameId": "002",
                    "gameStatus": 1,
                    "homeTeam": {
                        "teamTricode": "UP",
                        "teamId": "003",
                        "teamName": "Upcoming",
                        "teamCity": "City",
                        "wins": 0,
                        "losses": 0,
                        "score": 0,
                        "players": [],
                    },
                    "awayTeam": {
                        "teamTricode": "UP2",
                        "teamId": "004",
                        "teamName": "Upcoming 2",
                        "teamCity": "City",
                        "wins": 0,
                        "losses": 0,
                        "score": 0,
                        "players": [],
                    },
                },
            ]
        )

    async def fake_get_single_game_full_stats(game_id: str) -> str:
        return json.dumps(
            {
                "boxscore": {
                    "gameId": game_id,
                    "homeTeam": {
                        "teamTricode": "HOM",
                        "players": [
                            {
                                "status": "ACTIVE",
                                "nameI": "Player",
                                "statistics": {
                                    "points": 20,
                                    "reboundsTotal": 5,
                                    "assists": 3,
                                    "steals": 1,
                                    "blocks": 1,
                                },
                            }
                        ],
                    },
                    "awayTeam": {
                        "teamTricode": "AWY",
                        "players": [],
                    },
                    "gameStatus": 2,
                }
            }
        )

    monkeypatch.setattr(
        "nba_api.services.nba_client.get_todays_scoreboard", fake_get_todays_scoreboard
    )
    monkeypatch.setattr(
        "nba_api.services.nba_client.get_single_game_full_stats",
        fake_get_single_game_full_stats,
    )

    result = await scoreboard.get_stats()

    assert result is not None
    assert len(result["Games Stats"]) == 2
    assert result["Games Stats"][0]["homeTeam"]["players"][0]["points"] == 20


@pytest.mark.asyncio
async def test_get_stats_handles_exception_from_gather(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get_todays_scoreboard() -> str:
        return _scoreboard_payload(
            [
                {
                    "gameId": "001",
                        "gameStatus": NBA_GAME_STATUS.LIVE.value,
                    "homeTeam": {
                        "teamTricode": "HOM",
                        "teamId": "001",
                        "teamName": "Home",
                        "teamCity": "City",
                        "wins": 0,
                        "losses": 0,
                        "score": 100,
                        "players": [],
                    },
                    "awayTeam": {
                        "teamTricode": "AWY",
                        "teamId": "002",
                        "teamName": "Away",
                        "teamCity": "City",
                        "wins": 0,
                        "losses": 0,
                        "score": 95,
                        "players": [],
                    },
                }
            ]
        )

    def fake_logger_exception(err: Exception) -> None:
        captured.append(str(err))

    async def fake_get_single_game_full_stats(game_id: str) -> str:
        raise RuntimeError("fetch failed")

    captured: List[str] = []

    monkeypatch.setattr(
        "nba_api.services.nba_client.get_todays_scoreboard", fake_get_todays_scoreboard
    )
    monkeypatch.setattr(
        "nba_api.services.nba_client.get_single_game_full_stats",
        fake_get_single_game_full_stats,
    )
    monkeypatch.setattr(
        "nba_api.use_cases.scoreboard.logger.exception", fake_logger_exception
    )

    result = await scoreboard.get_stats()

    assert result is not None
    assert result["Games Stats"][0]["homeTeam"]["players"] == []
    assert captured == ["fetch failed"]


@pytest.mark.asyncio
async def test_get_stats_handles_null_statlines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get_todays_scoreboard() -> str:
        return _scoreboard_payload(
            [
                {
                    "gameId": "001",
                    "gameStatus": NBA_GAME_STATUS.FINAL.value,
                    "homeTeam": {
                        "teamTricode": "HOM",
                        "teamId": "001",
                        "teamName": "Home",
                        "teamCity": "City",
                        "wins": 0,
                        "losses": 0,
                        "score": 100,
                        "players": [],
                    },
                    "awayTeam": {
                        "teamTricode": "AWY",
                        "teamId": "002",
                        "teamName": "Away",
                        "teamCity": "City",
                        "wins": 0,
                        "losses": 0,
                        "score": 90,
                        "players": [],
                    },
                }
            ]
        )

    monkeypatch.setattr(
        "nba_api.services.nba_client.get_todays_scoreboard", fake_get_todays_scoreboard
    )
    async def fake_get_single_game_full_stats(game_id: str) -> str:
        return json.dumps({})

    monkeypatch.setattr(
        "nba_api.services.nba_client.get_single_game_full_stats",
        fake_get_single_game_full_stats,
    )
    monkeypatch.setattr(
        "nba_api.use_cases.scoreboard.parse_single_game_statline",
        lambda stat_line: None,
    )

    result = await scoreboard.get_stats()

    assert result is not None
    assert result["Games Stats"][0]["homeTeam"]["players"] == []


@pytest.mark.parametrize(
    "raw_status,expected",
    [
        (NBA_GAME_STATUS.LIVE, NBA_GAME_STATUS.LIVE),
        (NBA_GAME_STATUS.FINAL.value, NBA_GAME_STATUS.FINAL),
        ([NBA_GAME_STATUS.LIVE.value], NBA_GAME_STATUS.LIVE),
        ("LIVE", NBA_GAME_STATUS.LIVE),
        ("2", NBA_GAME_STATUS.LIVE),
        ("UPCOMING", NBA_GAME_STATUS.UPCOMING),
        (0, None),
        ("unexpected", None),
        ([], None),
    ],
)
def test_normalize_game_status_variants(
    raw_status: Any, expected: Optional[NBA_GAME_STATUS]
) -> None:
    assert _normalize_game_status(raw_status) == expected


@pytest.mark.asyncio
async def test_get_stats_returns_none_for_html_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get_todays_scoreboard() -> str:
        return "<HTML>Error"

    monkeypatch.setattr(
        "nba_api.services.nba_client.get_todays_scoreboard", fake_get_todays_scoreboard
    )

    result = await scoreboard.get_stats()

    assert result is None


@pytest.mark.asyncio
async def test_get_stats_handles_parsing_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get_todays_scoreboard() -> str:
        return "{}"

    monkeypatch.setattr(
        "nba_api.services.nba_client.get_todays_scoreboard", fake_get_todays_scoreboard
    )

    result = await scoreboard.get_stats()

    assert result is None


@pytest.mark.asyncio
async def test_get_stats_handles_exceptions(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get_todays_scoreboard() -> str:
        raise RuntimeError("boom")

    captured = []

    def fake_logger_exception(err: Exception) -> None:
        captured.append(str(err))

    monkeypatch.setattr(
        "nba_api.services.nba_client.get_todays_scoreboard", fake_get_todays_scoreboard
    )
    monkeypatch.setattr(
        "nba_api.use_cases.scoreboard.logger.exception", fake_logger_exception
    )

    result = await scoreboard.get_stats()

    assert result is None
    assert captured == ["boom"]
