"""Application use case for retrieving and aggregating scoreboard statistics."""

import asyncio
import random
from typing import Any, Dict, List, Optional

from loguru import logger

from ..domain.enums import NBA_GAME_STATUS
from ..domain.parsers import (
    ParsedStatline,
    normalize_scoreboard_payload,
    parse_scoreboard_game,
    parse_single_game_statline,
    parse_to_json,
)
from ..services import stats_client


def _normalize_game_status(status: Any) -> Optional[NBA_GAME_STATUS]:
    if isinstance(status, NBA_GAME_STATUS):
        return status

    if isinstance(status, (list, tuple)):
        status = status[0] if status else None

    if status is None:
        return None

    if isinstance(status, str):
        if status.isdigit():
            return _normalize_game_status(int(status))
        try:
            return NBA_GAME_STATUS[status.upper()]
        except KeyError:
            return None

    if isinstance(status, int):
        try:
            return NBA_GAME_STATUS(status)
        except ValueError:
            return None

    return None


async def get_stats() -> Optional[Dict[str, Any]]:
    try:
        scoreboard = await stats_client.get_todays_scoreboard()

        if "<HTML>" in scoreboard:
            return None

        formatted_scoreboards = parse_to_json(scoreboard)
        formatted_scoreboards = normalize_scoreboard_payload(formatted_scoreboards)

        if not formatted_scoreboards:
            return None

        games: List[Dict[str, Any]] = list(
            map(parse_scoreboard_game, formatted_scoreboards["scoreboard"]["games"])
        )

        filtered_games = [
            game
            for game in games
            if _normalize_game_status(game.get("gameStatus"))
            in {NBA_GAME_STATUS.LIVE, NBA_GAME_STATUS.FINAL}
        ]

        games_full_stats: List[object] = []

        for index, game in enumerate(filtered_games):
            if index > 0:
                delay_seconds: float = random.uniform(0.5, 1.25)
                await asyncio.sleep(delay_seconds)

            try:
                stat_line = await stats_client.get_single_game_full_stats(
                    game["gameId"]
                )
                games_full_stats.append(stat_line)
            except Exception as fetch_err:  # noqa: BLE001
                games_full_stats.append(fetch_err)

        parsed_game_full_stats: List[Optional[ParsedStatline]] = []

        for stat_line in games_full_stats:
            if isinstance(stat_line, Exception):
                logger.exception(stat_line)
                continue

            parsed_game_full_stats.append(
                parse_single_game_statline(
                    stat_line if isinstance(stat_line, str) else None
                )
            )

        combined_full_stats: List[Dict[str, Any]] = []

        for game in games:
            game_to_merge: Dict[str, Any] = next(
                (
                    pgfs
                    for pgfs in parsed_game_full_stats
                    if pgfs
                    and game
                    and "gameId" in pgfs
                    and "gameId" in game
                    and pgfs["gameId"] == game["gameId"]
                ),
                {},
            )

            if "homeTeam" in game_to_merge:
                game["homeTeam"]["players"] = game_to_merge["homeTeam"]["players"]
                game["awayTeam"]["players"] = game_to_merge["awayTeam"]["players"]
            else:
                game["homeTeam"]["players"] = []
                game["awayTeam"]["players"] = []

            combined_full_stats.append(game)

        return {
            "Game Date": formatted_scoreboards["scoreboard"]["gameDate"],
            "League": formatted_scoreboards["scoreboard"]["leagueName"],
            "Games Stats": combined_full_stats,
        }
    except Exception as err:  # noqa: BLE001
        logger.exception(err)
        return None
