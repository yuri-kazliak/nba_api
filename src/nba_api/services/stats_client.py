"""Stats provider selector that routes calls to NBA.com or ESPN clients."""

import os
from enum import Enum

from . import espn_client, nba_client


class StatsProvider(str, Enum):
    NBA = "nba"
    ESPN = "espn"


def _get_active_provider() -> StatsProvider:
    """Determine which stats provider to use based on environment variable."""
    env_value: str = os.getenv("NBA_API_PROVIDER", StatsProvider.ESPN.value).lower()

    if env_value == StatsProvider.ESPN.value:
        return StatsProvider.ESPN

    return StatsProvider.NBA


async def get_todays_scoreboard() -> str:
    provider: StatsProvider = _get_active_provider()

    if provider is StatsProvider.ESPN:
        return await espn_client.get_todays_scoreboard()

    return await nba_client.get_todays_scoreboard()


async def get_single_game_full_stats(game_id: str) -> str:
    provider: StatsProvider = _get_active_provider()

    if provider is StatsProvider.ESPN:
        return await espn_client.get_single_game_full_stats(game_id)

    return await nba_client.get_single_game_full_stats(game_id)


async def get_all_players_season_stats() -> str:
    provider: StatsProvider = _get_active_provider()

    if provider is StatsProvider.ESPN:
        return await espn_client.get_all_players_season_stats()

    return await nba_client.get_all_players_season_stats()


async def get_specific_gameday_stats(gamedate: str) -> str:
    provider: StatsProvider = _get_active_provider()

    if provider is StatsProvider.ESPN:
        return await espn_client.get_specific_gameday_stats(gamedate)

    return await nba_client.get_specific_gameday_stats(gamedate)
