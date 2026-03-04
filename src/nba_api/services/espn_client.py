"""ESPN-specific HTTP API client functions."""

from typing import Any, Dict

from .http_client import perform_get

ESPN_TODAYS_SCOREBOARD_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
)
ESPN_SINGLE_GAME_DETAILS_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary"
)
ESPN_TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"


async def get_todays_scoreboard() -> str:
    return await perform_get(
        ESPN_TODAYS_SCOREBOARD_URL,
        cache_key="espn_todays_scoreboard",
        cache_ttl_seconds=15.0,
    )


async def get_single_game_full_stats(game_id: str) -> str:
    params: Dict[str, Any] = {
        "event": game_id,
    }

    return await perform_get(
        ESPN_SINGLE_GAME_DETAILS_URL,
        params=params,
        cache_key=f"espn_single_game_{game_id}",
        cache_ttl_seconds=10.0,
    )


async def get_all_players_season_stats() -> str:
    params: Dict[str, Any] = {
        "limit": 1000,
    }

    return await perform_get(
        ESPN_TEAMS_URL,
        params=params,
        cache_key="espn_all_players_stats",
        cache_ttl_seconds=300.0,
    )


def _format_espn_date(gamedate: str) -> str:
    """Convert YYYY-MM-DD to YYYYMMDD for ESPN scoreboard dates."""
    if "-" in gamedate and len(gamedate) == 10:
        year, month, day = gamedate.split("-")
        if len(year) == 4 and len(month) == 2 and len(day) == 2:
            return f"{year}{month}{day}"
    return gamedate


async def get_specific_gameday_stats(gamedate: str) -> str:
    formatted_date: str = _format_espn_date(gamedate)
    params: Dict[str, Any] = {
        "dates": formatted_date,
    }

    return await perform_get(
        ESPN_TODAYS_SCOREBOARD_URL,
        params=params,
        cache_key=f"espn_specific_gameday_{formatted_date}",
        cache_ttl_seconds=60.0,
    )

