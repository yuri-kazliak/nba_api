"""Application state helpers."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..domain.enums import NBA_GAME_STATUS
from ..use_cases import players as players_use_case
from ..use_cases import scoreboard as scoreboard_use_case

StateDict = Dict[str, Any]

state: StateDict = {}


def clear_state() -> None:
    state.clear()


def set_todays_boxscore(data: Any, timestamp: Optional[datetime] = None) -> None:
    state["todays_boxscore"] = data
    state["todays_boxscore_datetime"] = timestamp or datetime.now()


def get_todays_boxscore() -> Optional[Any]:
    return state.get("todays_boxscore")


def get_todays_boxscore_timestamp() -> Optional[datetime]:
    return state.get("todays_boxscore_datetime")


def set_all_players_stats(data: Any, timestamp: Optional[datetime] = None) -> None:
    state["all_players_stats"] = data
    state["all_players_stats_datetime"] = timestamp or datetime.now()


def get_all_players_stats() -> Optional[Any]:
    return state.get("all_players_stats")


def get_all_players_stats_timestamp() -> Optional[datetime]:
    return state.get("all_players_stats_datetime")


async def refresh_boxscore() -> None:
    stats = await scoreboard_use_case.get_stats()
    set_todays_boxscore(stats)


async def refresh_players_stats() -> None:
    stats = await players_use_case.get_players_stats()
    set_all_players_stats(stats)


def _get_scoreboard_game_statuses(boxscore: Any) -> List[NBA_GAME_STATUS]:
    statuses: List[NBA_GAME_STATUS] = []

    if not isinstance(boxscore, dict):
        return statuses

    games: Any = boxscore.get("Games Stats")
    if not isinstance(games, list):
        return statuses

    for game in games:
        if not isinstance(game, dict):
            continue

        normalized_status = scoreboard_use_case._normalize_game_status(
            game.get("gameStatus")
        )

        if normalized_status is not None:
            statuses.append(normalized_status)

    return statuses


async def ensure_boxscore_fresh(ttl_minutes: float = 15.0) -> None:
    cached_boxscore = get_todays_boxscore()
    if not cached_boxscore:
        await refresh_boxscore()
        return

    statuses = _get_scoreboard_game_statuses(cached_boxscore)

    if statuses and any(status is NBA_GAME_STATUS.LIVE for status in statuses):
        await refresh_boxscore()
        return

    refresh_interval_minutes = ttl_minutes

    if statuses and all(status is NBA_GAME_STATUS.UPCOMING for status in statuses):
        refresh_interval_minutes = 15.0
    elif statuses and all(status is NBA_GAME_STATUS.FINAL for status in statuses):
        refresh_interval_minutes = 60.0

    timestamp = get_todays_boxscore_timestamp()
    if timestamp and datetime.now() > timestamp + timedelta(
        minutes=refresh_interval_minutes
    ):
        asyncio.create_task(refresh_boxscore())


async def ensure_players_stats_fresh(ttl_hours: float = 1.0) -> None:
    cached_stats = get_all_players_stats()
    if not cached_stats:
        await refresh_players_stats()
        return

    timestamp = get_all_players_stats_timestamp()
    if timestamp and datetime.now() > timestamp + timedelta(hours=ttl_hours):
        asyncio.create_task(refresh_players_stats())


def schedule_full_refresh() -> None:
    asyncio.create_task(refresh_boxscore())
    asyncio.create_task(refresh_players_stats())
