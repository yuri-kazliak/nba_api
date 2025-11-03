"""NBA-specific HTTP API client functions."""

from typing import Any, Dict

from .http_client import perform_get

TODAYS_SCOREBOARD_URL = "https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/scoreboard/todaysScoreboard_00.json"
SINGLE_GAME_DETAILS_URL = "https://core-api.nba.com/cp/api/v1.8/gameDetails"
LEAGUE_LEADERS_URL = "https://stats.nba.com/stats/leagueLeaders"
SPECIFIC_GAMEDAY_STATS_URL = "https://core-api.nba.com/cp/api/v1.8/feeds/gamecardfeed"


async def get_todays_scoreboard() -> str:
    return await perform_get(
        TODAYS_SCOREBOARD_URL,
        cache_key="todays_scoreboard",
        cache_ttl_seconds=15.0,
    )


async def get_single_game_full_stats(game_id: str) -> str:
    params: Dict[str, Any] = {
        "leagueId": "00",
        "gameId": game_id,
        "tabs": "all",
        "platform": "web",
    }
    headers = {"ocp-apim-subscription-key": "747fa6900c6c4e89a58b81b72f36eb96"}
    return await perform_get(
        SINGLE_GAME_DETAILS_URL,
        params=params,
        headers=headers,
        cache_key=f"single_game_{game_id}",
        cache_ttl_seconds=10.0,
    )


async def get_all_players_season_stats() -> str:
    params: Dict[str, Any] = {
        "LeagueID": "00",
        "PerMode": "PerGame",
        "Scope": "S",
        "Season": "2025-26",
        "SeasonType": "Regular Season",
        "StatCategory": "REB",
    }

    return await perform_get(
        LEAGUE_LEADERS_URL,
        params=params,
        cache_key="all_players_stats",
        cache_ttl_seconds=300.0,
    )


async def get_specific_gameday_stats(gamedate: str) -> str:
    params: Dict[str, Any] = {
        "gamedate": gamedate,
        "platform": "web",
    }

    return await perform_get(
        SPECIFIC_GAMEDAY_STATS_URL,
        params=params,
        cache_key=f"specific_gameday_{gamedate}",
        cache_ttl_seconds=60.0,
    )
