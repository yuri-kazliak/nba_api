import asyncio
from loguru import logger

from .nba_api import (
    NBA_GAME_STATUS,
    get_all_players_season_stats,
    get_single_game_full_stats,
    get_todays_scoreboard,
)
from .nba_models import (
    parse_players_season_stats,
    parse_scoreboard_game,
    parse_single_game_statline,
    parse_to_json,
)


async def get_stats():
    try:
        scoreboard = await get_todays_scoreboard()

        formatted_scoreboards = parse_to_json(scoreboard)

        games = list(
            map(parse_scoreboard_game, formatted_scoreboards["scoreboard"]["games"])
        )

        filtered_games = list(
            filter(
                lambda game: game["gameStatus"] == NBA_GAME_STATUS.Live.value
                or game["gameStatus"] == NBA_GAME_STATUS.Final.value,
                games,
            )
        )

        games_full_stats = await asyncio.gather(
            *list(
                map(
                    lambda game: get_single_game_full_stats(game["gameId"]),
                    filtered_games,
                )
            )
        )
        parsed_game_full_stats = list(map(parse_single_game_statline, games_full_stats))

        combined_full_stats = []

        for game in games:
            game_to_merge = next(
                (
                    pgfs
                    for pgfs in parsed_game_full_stats
                    if pgfs["gameId"] == game["gameId"]
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
    except Exception as err:
        logger.exception(err)
        return None


async def get_players_stats():
    try:
        players_stats = await get_all_players_season_stats()

        if "<HTML>" in players_stats:
            return None

        players_stats_json = parse_to_json(players_stats)

        return parse_players_season_stats(players_stats_json)
    except Exception as err:
        logger.exception(err)
        return None
