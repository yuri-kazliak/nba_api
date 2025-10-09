"""Unit tests for domain parsing helpers."""

from __future__ import annotations

import json

from nba_api.domain import parsers


def test_parse_to_json_returns_dict() -> None:
    payload = {"key": "value"}
    result = parsers.parse_to_json(json.dumps(payload))
    assert result == payload


def test_parse_to_json_handles_invalid_input() -> None:
    assert parsers.parse_to_json("<HTML>Error") is None
    assert parsers.parse_to_json("not-json") is None


def test_parse_single_game_statline_formats_players() -> None:
    stat_line = json.dumps(
        {
            "boxscore": {
                "gameId": "001",
                "gameStatus": 2,
                "homeTeam": {
                    "teamTricode": "HOM",
                    "players": [
                        {
                            "status": "ACTIVE",
                            "nameI": "A.Player",
                            "statistics": {
                                "points": 15,
                                "reboundsTotal": 7,
                                "assists": 5,
                                "steals": 2,
                                "blocks": 1,
                            },
                        }
                    ],
                },
                "awayTeam": {
                    "teamTricode": "AWY",
                    "players": [
                        {
                            "status": "ACTIVE",
                            "nameI": "B.Player",
                            "statistics": {
                                "points": 10,
                                "reboundsTotal": 5,
                                "assists": 4,
                                "steals": 1,
                                "blocks": 0,
                            },
                        }
                    ],
                },
            }
        }
    )

    result = parsers.parse_single_game_statline(stat_line)

    assert result is not None
    assert result["gameId"] == "001"
    assert result["homeTeam"]["players"][0]["points"] == 15
    assert result["awayTeam"]["players"][0]["points"] == 10


def test_parse_single_game_statline_returns_none_for_missing_boxscore() -> None:
    assert parsers.parse_single_game_statline(json.dumps({})) is None


def test_format_team_statline_includes_watch_player() -> None:
    team = {
        "teamTricode": "SA",
        "players": [
            {
                "status": "ACTIVE",
                "nameI": "V. Wembanyama",
                "statistics": {
                    "points": 2,
                    "reboundsTotal": 0,
                    "assists": 0,
                    "steals": 0,
                    "blocks": 0,
                },
            }
        ],
    }

    result = parsers.format_team_statline(team)
    assert result["players"][0]["name"] == "V. Wembanyama"


def test_parse_scoreboard_game_team_adds_logo() -> None:
    team = {
        "score": 100,
        "wins": 10,
        "losses": 5,
        "teamCity": "City",
        "teamName": "Name",
        "teamTricode": "ABC",
        "teamId": "123",
    }

    result = parsers.parse_scoreboard_game_team(team)
    assert result["teamLogo"].endswith("123/primary/L/logo.svg")


def test_parse_players_season_stats_returns_expected_structure() -> None:
    payload = {
        "resultSet": {
            "headers": ["PLAYER", "TEAM"],
            "rowSet": [["Player 1", "Team"]],
        }
    }

    result = parsers.parse_players_season_stats(payload)
    assert result == {
        "categories": ["PLAYER", "TEAM"],
        "all_players_stats": [["Player 1", "Team"]],
    }


def test_parse_players_season_stats_missing_result_set_returns_none() -> None:
    assert parsers.parse_players_season_stats({}) is None
