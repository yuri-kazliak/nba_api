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
    assert parsers.parse_to_json(None) is None


def test_parse_single_game_statline_formats_players() -> None:
    def build_player(
        name: str,
        points: int,
        rebounds: int,
        assists: int,
        steals: int,
        blocks: int,
    ) -> dict[str, object]:
        return {
            "status": "ACTIVE",
            "nameI": name,
            "statistics": {
                "points": points,
                "reboundsTotal": rebounds,
                "assists": assists,
                "steals": steals,
                "blocks": blocks,
            },
        }

    home_players = [
        build_player("A.Player1", 26, 8, 9, 4, 3),
        build_player("A.Player2", 11, 3, 2, 1, 0),
        build_player("A.Player3", 30, 10, 7, 4, 5),
        build_player("A.Player4", 12, 1, 1, 0, 0),
        build_player("A.Player5", 7, 6, 4, 1, 2),
        build_player("A.Player6", 4, 1, 1, 0, 0),
        build_player("A.Player7", 17, 6, 2, 2, 3),
        build_player("A.Player8", 25, 12, 10, 5, 4),
        build_player("A.Player9", 14, 4, 3, 1, 1),
        build_player("V. Wembanyama", 22, 9, 2, 1, 7),
    ]

    away_players = [
        build_player("B.Player1", 20, 8, 6, 4, 3),
        build_player("B.Player2", 8, 3, 5, 1, 0),
        build_player("B.Player3", 16, 5, 4, 2, 1),
        build_player("B.Player4", 10, 7, 3, 3, 4),
        build_player("B.Player5", 4, 2, 1, 0, 0),
        build_player("B.Player6", 18, 10, 2, 1, 2),
        build_player("B.Player7", 15, 4, 8, 3, 1),
        build_player("B.Player8", 21, 11, 9, 5, 5),
        build_player("B.Player9", 13, 7, 2, 2, 3),
        build_player("C. Flagg", 8, 7, 1, 1, 1),
    ]

    stat_line = json.dumps(
        {
            "boxscore": {
                "gameId": "001",
                "gameStatus": 2,
                "homeTeam": {
                    "teamTricode": "HOM",
                    "teamId": "100",
                    "players": home_players,
                },
                "awayTeam": {
                    "teamTricode": "AWY",
                    "teamId": "200",
                    "players": away_players,
                },
            }
        }
    )

    result = parsers.parse_single_game_statline(stat_line)

    assert result is not None
    assert result["gameId"] == "001"

    home_team = result["homeTeam"]
    away_team = result["awayTeam"]

    assert home_team["tricode"] == "HOM"
    assert home_team["teamId"] == "100"
    assert home_team["teamLogo"].endswith("100/primary/L/logo.svg")
    assert away_team["tricode"] == "AWY"
    assert away_team["teamId"] == "200"
    assert away_team["teamLogo"].endswith("200/primary/L/logo.svg")

    home_players_parsed = {
        player["name"]: {k: v for k, v in player.items() if k != "name"}
        for player in home_team["players"]
    }
    away_players_parsed = {
        player["name"]: {k: v for k, v in player.items() if k != "name"}
        for player in away_team["players"]
    }

    expected_home = {
        "A.Player1": {
            "points": 26,
            "reboundsTotal": 8,
            "assists": 9,
            "steals": 4,
            "blocks": 3,
        },
        "A.Player2": {"points": 11},
        "A.Player3": {
            "points": 30,
            "reboundsTotal": 10,
            "assists": 7,
            "steals": 4,
            "blocks": 5,
        },
        "A.Player4": {"points": 12},
        "A.Player5": {
            "points": 7,
            "reboundsTotal": 6,
            "assists": 4,
        },
        "A.Player7": {
            "points": 17,
            "reboundsTotal": 6,
            "blocks": 3,
        },
        "A.Player8": {
            "points": 25,
            "reboundsTotal": 12,
            "assists": 10,
            "steals": 5,
            "blocks": 4,
        },
        "A.Player9": {"points": 14},
        "V. Wembanyama": {
            "points": 22,
            "reboundsTotal": 9,
            "assists": 2,
            "steals": 1,
            "blocks": 7,
        },
    }

    expected_away = {
        "B.Player1": {
            "points": 20,
            "reboundsTotal": 8,
            "assists": 6,
            "steals": 4,
            "blocks": 3,
        },
        "B.Player2": {
            "points": 8,
            "assists": 5,
        },
        "B.Player3": {
            "points": 16,
            "assists": 4,
        },
        "B.Player4": {
            "points": 10,
            "reboundsTotal": 7,
            "steals": 3,
            "blocks": 4,
        },
        "B.Player6": {
            "points": 18,
            "reboundsTotal": 10,
        },
        "B.Player7": {
            "points": 15,
            "assists": 8,
            "steals": 3,
        },
        "B.Player8": {
            "points": 21,
            "reboundsTotal": 11,
            "assists": 9,
            "steals": 5,
            "blocks": 5,
        },
        "B.Player9": {
            "points": 13,
            "reboundsTotal": 7,
            "blocks": 3,
        },
        "C. Flagg": {
            "points": 8,
            "reboundsTotal": 7,
        },
    }

    assert set(home_players_parsed.keys()) == set(expected_home.keys())
    assert set(away_players_parsed.keys()) == set(expected_away.keys())

    assert "A.Player6" not in home_players_parsed
    assert "B.Player5" not in away_players_parsed

    for name, stats in expected_home.items():
        assert home_players_parsed[name] == stats

    for name, stats in expected_away.items():
        assert away_players_parsed[name] == stats


# def test_parse_single_game_statline_handles_espn_example() -> None:
#     # load the real ESPN game payload that lives in the repository
#     import pathlib

#     path = (
#         pathlib.Path(__file__).parent.parent.parent
#         / "data-examples"
#         / "espn_single_game_example.json"
#     )
#     raw = path.read_text()
#     payload = json.loads(raw)
#     result = parsers.parse_single_game_statline(json.dumps(payload))

#     assert result is not None
#     # make sure we still return the same high‑level keys
#     assert "homeTeam" in result and "awayTeam" in result

#     # verify that a few well‑known players from the sample are present and
#     # that their numeric statistics were pulled correctly.
#     home_names = {p["name"] for p in result["homeTeam"]["players"]}
#     away_names = {p["name"] for p in result["awayTeam"]["players"]}

#     # Chet Holmgren played for the Thunder (away team) and scored 28 points
#     assert "C. Holmgren" in away_names
#     holmgren = next(
#         p for p in result["awayTeam"]["players"] if p["name"] == "C. Holmgren"
#     )
#     assert holmgren["points"] == 28
#     assert holmgren["reboundsTotal"] == 8
#     # assists were below the inclusion threshold so might be absent
#     if "assists" in holmgren:
#         assert holmgren["assists"] == 2

#     # Jalen Brunson is on the Knicks (home team) with 16 points & 15 assists
#     assert "J. Brunson" in home_names
#     brunson = next(
#         p for p in result["homeTeam"]["players"] if p["name"] == "J. Brunson"
#     )
#     assert brunson["points"] == 16
#     # rebounds fell below the threshold and may not be present
#     assert "reboundsTotal" not in brunson or brunson["reboundsTotal"] == 3
#     assert brunson["assists"] == 15


def test_parse_single_game_statline_returns_none_for_missing_boxscore() -> None:
    assert parsers.parse_single_game_statline(json.dumps({})) is None


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
