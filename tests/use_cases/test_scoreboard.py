"""Tests for scoreboard use case logic."""

from __future__ import annotations

import json
from typing import Any, Dict, List

import pytest

from nba_api.use_cases import scoreboard


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
