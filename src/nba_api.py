# This file contains everything that relates to getting an info from NBA.com

import httpx
from enum import Enum


TODAYS_SCOREBOARD_URL = "https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/scoreboard/todaysScoreboard_00.json"
SINGLE_GAME_DETAILS_URL = "https://core-api.nba.com/cp/api/v1.8/gameDetails"
LEAGUE_LEADERS_URL = "https://stats.nba.com/stats/leagueLeaders"

SPECIFIC_GAMEDAY_STATS_URL = "https://core-api.nba.com/cp/api/v1.8/feeds/gamecardfeed"
# https://core-api.nba.com/cp/api/v1.8/feeds/gamecardfeed?gamedate=11/10/2024&platform=web


class NBA_GAME_STATUS(Enum):
    Upcoming = (1,)
    Live = (2,)
    Final = 3


async def get_todays_scoreboard():
    r = httpx.get(TODAYS_SCOREBOARD_URL)
    return r.text


async def get_single_game_full_stats(game_id: str):
    params = {"leagueId": "00", "gameId": game_id, "tabs": "all", "platform": "web"}
    headers = {"ocp-apim-subscription-key": "747fa6900c6c4e89a58b81b72f36eb96"}
    r = httpx.get(SINGLE_GAME_DETAILS_URL, params=params, headers=headers)
    return r.text


async def get_all_players_season_stats():
    params = {
        "LeagueID": "00",
        "PerMode": "PerGame",
        "Scope": "S",
        "Season": "2024-25",
        "SeasonType": "Regular Season",
        "StatCategory": "REB",
    }

    r = httpx.get(LEAGUE_LEADERS_URL, params=params)
    return r.text


async def get_specific_gameday_stats(gamedate: str):
    params = {
        "gamedate": gamedate,  # in format 11/10/2024
        "platform": "web",
    }

    r = httpx.get(SPECIFIC_GAMEDAY_STATS_URL, params=params)
    return r.text
