"""Application state helpers."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

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


async def ensure_boxscore_fresh(ttl_minutes: float = 15.0) -> None:
    cached_boxscore = get_todays_boxscore()
    if not cached_boxscore:
        await refresh_boxscore()
        return

    timestamp = get_todays_boxscore_timestamp()
    if timestamp and datetime.now() > timestamp + timedelta(minutes=ttl_minutes):
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
