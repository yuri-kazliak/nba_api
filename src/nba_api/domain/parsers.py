"""Parsing helpers for transforming NBA API payloads."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from loguru import logger

StatisticCriteria = Dict[str, int]
PlayerStatline = Dict[str, Any]
TeamStatline = Dict[str, Any]
ParsedStatline = Dict[str, Any]

STATISTIC_MINIMUM_CRITERIA: StatisticCriteria = {
    "points": 9,
    "reboundsTotal": 5,
    "assists": 3,
    "steals": 2,
    "blocks": 2,
}

PLAYERS_TO_WATCH: List[str] = ["V. Wembanyama", "C. Flagg"]


def parse_single_game_statline(stat_line: Optional[str]) -> Optional[ParsedStatline]:
    parsed = parse_to_json(stat_line)
    if not parsed or "boxscore" not in parsed:
        return None

    parsed_boxscore = parsed["boxscore"]
    return {
        "gameId": parsed_boxscore["gameId"],
        "gameStatus": parsed_boxscore.get("gameStatus"),
        "homeTeam": format_team_statline(parsed_boxscore["homeTeam"]),
        "awayTeam": format_team_statline(parsed_boxscore["awayTeam"]),
    }


def parse_scoreboard_game(game: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "gameId": game["gameId"],
        "gameStatus": game.get("gameStatus"),
        "homeTeam": parse_scoreboard_game_team(game["homeTeam"]),
        "awayTeam": parse_scoreboard_game_team(game["awayTeam"]),
    }


def parse_scoreboard_game_team(team: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "score": team["score"],
        "wins": team["wins"],
        "losses": team["losses"],
        "teamCity": team["teamCity"],
        "teamName": team["teamName"],
        "teamTricode": team["teamTricode"],
        "teamId": team["teamId"],
        "teamLogo": get_team_logo_link(team["teamId"]),
    }


def get_team_logo_link(team_id: str) -> str:
    return f"https://cdn.nba.com/logos/nba/{team_id}/primary/L/logo.svg"


def format_team_statline(team: Dict[str, Any]) -> TeamStatline:
    players: List[PlayerStatline] = []
    formatted_team: TeamStatline = {
        "tricode": team["teamTricode"],
        "players": players,
    }

    team_id = team.get("teamId")
    if team_id:
        formatted_team["teamId"] = team_id
        formatted_team["teamLogo"] = get_team_logo_link(team_id)

    for player in team["players"]:
        if player.get("status") != "ACTIVE":
            continue

        criteria: StatisticCriteria = STATISTIC_MINIMUM_CRITERIA
        player_to_append: PlayerStatline = {"name": player["nameI"]}
        if player_to_append["name"] in PLAYERS_TO_WATCH:
            criteria = {
                "points": 1,
                "reboundsTotal": 0,
                "assists": 0,
                "steals": 0,
                "blocks": 0,
            }

        statistics = player.get("statistics", {})
        points = statistics.get("points", 0)
        if points > criteria["points"]:
            player_to_append["points"] = points

        rebounds_total = statistics.get("reboundsTotal", 0)
        if rebounds_total > criteria["reboundsTotal"]:
            player_to_append["reboundsTotal"] = rebounds_total

        assists = statistics.get("assists", 0)
        if assists > criteria["assists"]:
            player_to_append["assists"] = assists

        steals = statistics.get("steals", 0)
        if steals > criteria["steals"]:
            player_to_append["steals"] = steals

        blocks = statistics.get("blocks", 0)
        if blocks > criteria["blocks"]:
            player_to_append["blocks"] = blocks

        if len(player_to_append) > 1:
            if "points" not in player_to_append:
                player_to_append["points"] = points
            players.append(player_to_append)

    players.sort(reverse=True, key=lambda player: player.get("points", 0))

    return formatted_team


def parse_players_season_stats(
    league_leaders_json: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not league_leaders_json or "resultSet" not in league_leaders_json:
        logger.debug("missed [resultSet] key in league_leaders_json")
        return None

    categories = league_leaders_json["resultSet"]["headers"]
    all_players_stats = league_leaders_json["resultSet"]["rowSet"]

    return {
        "categories": categories,
        "all_players_stats": all_players_stats,
    }


def parse_to_json(value: Optional[str]) -> Optional[Dict[str, Any]]:
    if not value or "<HTML>" in value:
        logger.error("Wrong input for parse_to_json method: {}", value)
        return None

    try:
        parsed: Dict[str, Any] = json.loads(value)
        return parsed
    except json.JSONDecodeError as err:
        logger.exception(err)
        return None
