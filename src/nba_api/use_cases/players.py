"""Application use case for retrieving players statistics."""

from typing import Any, Dict, Optional

from loguru import logger

from ..domain.parsers import parse_players_season_stats, parse_to_json
from ..services import stats_client


async def get_players_stats() -> Optional[Dict[str, Any]]:
    try:
        players_stats = await stats_client.get_all_players_season_stats()

        if "<HTML>" in players_stats:
            return None

        players_stats_json = parse_to_json(players_stats)
        parsed_stats: Optional[Dict[str, Any]] = parse_players_season_stats(players_stats_json)
        return parsed_stats
    except Exception as err:  # noqa: BLE001
        logger.exception(err)
        return None
