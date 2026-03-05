"""Parsing helpers for transforming NBA API payloads."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

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

PLAYERS_TO_WATCH: List[str] = ["V. Wembanyama"]


def parse_single_game_statline(stat_line: Optional[str]) -> Optional[ParsedStatline]:
    parsed = parse_to_json(stat_line)
    if not parsed or "boxscore" not in parsed:
        return None

    parsed_boxscore = parsed["boxscore"]

    game_id: Optional[str] = parsed_boxscore.get("gameId")
    if not game_id:
        # ESPN summary payloads sometimes put the id under header
        header: Dict[str, Any] = parsed.get("header", {})  # ESPN summary fallback
        header_id: Any = header.get("id")
        if isinstance(header_id, str) and header_id:
            game_id = header_id

    # identify format: NBA-style has explicit homeTeam/awayTeam keys, ESPN
    # style embeds a list of teams and a separate list of player stat entries.
    home_team_raw: Optional[Dict[str, Any]] = None
    away_team_raw: Optional[Dict[str, Any]] = None

    if "teams" in parsed_boxscore and isinstance(parsed_boxscore.get("teams"), list):
        # convert the ESPN boxscore into the minimal shape expected by
        # format_team_statline(); this includes a `players` list with the
        # simplified statistic structure used by our unit tests.
        home_team_raw, away_team_raw = _convert_espn_boxscore(parsed_boxscore)
    else:
        home_team_raw = parsed_boxscore.get("homeTeam")
        away_team_raw = parsed_boxscore.get("awayTeam")

    if not game_id or not home_team_raw or not away_team_raw:
        return None

    return {
        "gameId": game_id,
        "gameStatus": parsed_boxscore.get("gameStatus"),
        "homeTeam": format_team_statline(home_team_raw),
        "awayTeam": format_team_statline(away_team_raw),
    }


def parse_scoreboard_game(game: Dict[str, Any]) -> Dict[str, Any]:
    game_start_time_raw: Any = game.get("gameStartTimeUtc") or game.get("gameTimeUTC")
    game_start_time_utc: Optional[str] = (
        game_start_time_raw if isinstance(game_start_time_raw, str) else None
    )

    return {
        "gameId": game["gameId"],
        "gameStatus": game.get("gameStatus"),
        "gameStartTimeUtc": game_start_time_utc,
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


def _detect_scoreboard_provider(payload: Dict[str, Any]) -> str:
    """Best-effort detection of scoreboard provider based on payload shape."""
    if "scoreboard" in payload:
        return "nba"

    if "events" in payload:
        return "espn"

    return "unknown"


def _parse_espn_record_summary(summary: str | None) -> Tuple[int, int]:
    """Parse ESPN record summary of form 'W-L' into wins and losses."""
    if not summary or "-" not in summary:
        return (0, 0)

    wins_str, losses_str = summary.split("-", 1)
    try:
        wins = int(wins_str)
    except ValueError:
        wins = 0

    try:
        losses = int(losses_str)
    except ValueError:
        losses = 0

    return (wins, losses)


def _format_espn_team_from_competitor(competitor: Dict[str, Any]) -> Dict[str, Any]:
    """Convert ESPN competitor structure into internal scoreboard team shape."""
    team_info: Dict[str, Any] = competitor.get("team", {})

    records: List[Dict[str, Any]] = competitor.get("records", []) or []
    record_summary: Optional[str] = None

    for record in records:
        if record_summary is None:
            record_summary = record.get("summary")
        if record.get("type") == "total":
            record_summary = record.get("summary")
            break

    wins, losses = _parse_espn_record_summary(record_summary)

    score_raw: Any = competitor.get("score", 0)
    if isinstance(score_raw, str):
        try:
            score = int(score_raw)
        except ValueError:
            score = 0
    elif isinstance(score_raw, int):
        score = score_raw
    else:
        score = 0

    team_id: str = str(team_info.get("id", ""))

    return {
        "score": score,
        "wins": wins,
        "losses": losses,
        "teamCity": team_info.get("location", ""),
        "teamName": team_info.get("name") or team_info.get("shortDisplayName") or "",
        "teamTricode": team_info.get("abbreviation", ""),
        "teamId": team_id,
        # Players list is enriched later from full boxscore stats.
        "players": [],
    }


def normalize_scoreboard_payload(
    raw_payload: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Normalize provider-specific scoreboard payload into internal 'scoreboard' shape.

    - NBA provider already matches the required schema and is returned as-is.
    - ESPN payloads are converted into the NBA-style scoreboard structure:
      {"scoreboard": {"games": [...], "gameDate": str, "leagueName": str}}.
    """
    if not raw_payload:
        return None

    provider = _detect_scoreboard_provider(raw_payload)

    if provider == "nba":
        return raw_payload

    if provider != "espn":
        return raw_payload

    events: List[Dict[str, Any]] = raw_payload.get("events", []) or []
    games: List[Dict[str, Any]] = []

    for event in events:
        competitions: List[Dict[str, Any]] = event.get("competitions", []) or []
        if not competitions:
            continue

        competition: Dict[str, Any] = competitions[0]
        competitors: List[Dict[str, Any]] = competition.get("competitors", []) or []

        home_competitor: Optional[Dict[str, Any]] = next(
            (c for c in competitors if c.get("homeAway") == "home"), None
        )
        away_competitor: Optional[Dict[str, Any]] = next(
            (c for c in competitors if c.get("homeAway") == "away"), None
        )

        if not home_competitor or not away_competitor:
            continue

        status: Dict[str, Any] = competition.get("status", {}) or {}
        status_type: Dict[str, Any] = status.get("type", {}) or {}
        state: str = status_type.get("state", "")

        if state == "in":
            game_status: Any = "LIVE"
        elif state == "post":
            game_status = "FINAL"
        else:
            game_status = "UPCOMING"

        game_id_raw: Any = event.get("id") or competition.get("id") or ""
        game_id: str = str(game_id_raw)

        game_start_time_utc: Optional[str] = None
        event_date: Any = event.get("date")
        if isinstance(event_date, str):
            game_start_time_utc = event_date

        home_team = _format_espn_team_from_competitor(home_competitor)
        away_team = _format_espn_team_from_competitor(away_competitor)

        games.append(
            {
                "gameId": game_id,
                "gameStatus": game_status,
                "gameStartTimeUtc": game_start_time_utc,
                "homeTeam": home_team,
                "awayTeam": away_team,
            }
        )

    game_date: str = ""
    day_info: Optional[Dict[str, Any]] = raw_payload.get("day")
    if isinstance(day_info, dict):
        date_value: Any = day_info.get("date")
        if isinstance(date_value, str):
            game_date = date_value[:10]

    if not game_date and events:
        first_date: Any = events[0].get("date")
        if isinstance(first_date, str):
            game_date = first_date[:10]

    leagues: List[Dict[str, Any]] = raw_payload.get("leagues", []) or []
    league_name: str = "NBA"
    if leagues:
        league_name_candidate: Any = leagues[0].get("name")
        if isinstance(league_name_candidate, str) and league_name_candidate:
            league_name = league_name_candidate

    return {
        "scoreboard": {
            "games": games,
            "gameDate": game_date,
            "leagueName": league_name,
        }
    }


def _convert_espn_boxscore(
    parsed_boxscore: Dict[str, Any],
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Turn an ESPN-style boxscore payload into two team dicts.

    ESPN payloads place team-level stats under ``boxscore['teams']`` and
    player-level information under ``boxscore['players']``.  Each entry in
    ``players`` contains a nested ``statistics`` block that describes the
    various columns (``keys``) and provides a list of ``athletes`` with
    a parallel ``stats`` list.  We build a simplified version of the
    structure consumed by :func:`format_team_statline` so that the existing
    filtering/sorting logic can be reused.
    """

    teams: List[Dict[str, Any]] = parsed_boxscore.get("teams", []) or []
    players_section: List[Dict[str, Any]] = parsed_boxscore.get("players", []) or []

    # build mapping from team id to list of simplified player dicts
    team_players: Dict[str, List[Dict[str, Any]]] = {}

    def safe_int(value: Any) -> int:
        try:
            return int(value)
        except Exception:  # noqa: BLE001
            return 0

    for entry in players_section:
        team_info: Dict[str, Any] = entry.get("team", {}) or {}
        team_id = str(team_info.get("id", ""))
        stats_raw = entry.get("statistics", {}) or {}

        # ESPN occasionally wraps the statistics block in a one-element list
        # (see espn_single_game_example.py).  Normalize to a dict so the
        # downstream code can treat it uniformly.
        if isinstance(stats_raw, list):
            stats_info = {}
            for candidate in stats_raw:
                if isinstance(candidate, dict) and "athletes" in candidate:
                    stats_info = candidate
                    break
            if not stats_info and stats_raw:
                stats_info = stats_raw[0]
        else:
            stats_info = stats_raw

        keys: List[str] = stats_info.get("keys", []) or []
        athletes: List[Dict[str, Any]] = stats_info.get("athletes", []) or []

        for athlete in athletes:
            # skip players who did not log any stats or were inactive
            if athlete.get("didNotPlay"):
                continue

            athlete_info: Dict[str, Any] = athlete.get("athlete", {}) or {}
            name = athlete_info.get("shortName") or athlete_info.get("displayName")
            stats_list: List[Any] = athlete.get("stats", []) or []
            stats_map: Dict[str, Any] = dict(zip(keys, stats_list))

            # convert compatible numeric fields; only the fields that our
            # existing tests/logic care about are extracted here.
            player_dict: Dict[str, Any] = {
                "status": "ACTIVE" if not athlete.get("didNotPlay") else "INACTIVE",
                "nameI": name,
                "statistics": {
                    "points": safe_int(stats_map.get("points", 0)),
                    "reboundsTotal": safe_int(stats_map.get("rebounds", 0)),
                    "assists": safe_int(stats_map.get("assists", 0)),
                    "steals": safe_int(stats_map.get("steals", 0)),
                    "blocks": safe_int(stats_map.get("blocks", 0)),
                },
            }

            team_players.setdefault(team_id, []).append(player_dict)

    home_team: Optional[Dict[str, Any]] = None
    away_team: Optional[Dict[str, Any]] = None

    for team in teams:
        team_entry_info: Dict[str, Any] = team.get("team", {}) or {}
        team_id = str(team_entry_info.get("id", ""))
        tricode = team_entry_info.get("abbreviation", "")
        simple: Dict[str, Any] = {
            "teamTricode": tricode,
            "teamId": team_id,
            "players": team_players.get(team_id, []),
        }
        if team.get("homeAway") == "home":
            home_team = simple
        elif team.get("homeAway") == "away":
            away_team = simple

    return home_team, away_team


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
    league_leaders_json = normalize_players_season_stats_payload(league_leaders_json)

    if not league_leaders_json or "resultSet" not in league_leaders_json:
        logger.debug("missed [resultSet] key in league_leaders_json")
        return None

    categories = league_leaders_json["resultSet"]["headers"]
    all_players_stats = league_leaders_json["resultSet"]["rowSet"]

    return {
        "categories": categories,
        "all_players_stats": all_players_stats,
    }


def normalize_players_season_stats_payload(
    raw_payload: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Normalize provider-specific league/players stats into NBA-style resultSet.

    - NBA stats payloads already contain a 'resultSet' and are returned unchanged.
    - ESPN team payloads are converted into a synthetic resultSet with basic team info.
    """
    if not raw_payload:
        return None

    if "resultSet" in raw_payload:
        return raw_payload

    sports: Any = raw_payload.get("sports")
    if not isinstance(sports, list) or not sports:
        return raw_payload

    leagues: Any = sports[0].get("leagues")
    if not isinstance(leagues, list) or not leagues:
        return raw_payload

    teams: Any = leagues[0].get("teams")
    if not isinstance(teams, list):
        return raw_payload

    headers: List[str] = ["teamId", "teamName", "abbreviation", "location"]
    row_set: List[List[Any]] = []

    for entry in teams:
        team_info: Dict[str, Any] = entry.get("team", {}) or {}
        row_set.append(
            [
                team_info.get("id"),
                team_info.get("displayName") or team_info.get("name"),
                team_info.get("abbreviation"),
                team_info.get("location"),
            ]
        )

    return {
        "resultSet": {
            "headers": headers,
            "rowSet": row_set,
        }
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
