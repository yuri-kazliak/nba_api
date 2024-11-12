import json
import asyncio
from loguru import logger

from .nba_api import get_all_players_season_stats, get_single_game_full_stats, get_todays_scoreboard
from .nba_models import parse_players_season_stats, parse_scoreboard_game, parse_single_game_statline

async def get_stats():
  try:
    scoreboard = await get_todays_scoreboard()
    
    formatted_scoreboards = json.loads(scoreboard)

    games = list(map(parse_scoreboard_game ,formatted_scoreboards['scoreboard']['games']))

    games_full_stats = await asyncio.gather(*list(map(lambda game: get_single_game_full_stats(game['gameId']), games)))
    parsed_game_full_stats = list(map(parse_single_game_statline, games_full_stats))

    combined_full_stats = []

    for game in games:
      game_to_merge = next((pgfs for pgfs in parsed_game_full_stats if pgfs['gameId'] == game['gameId']), {})

      game['homeTeam']['players'] = game_to_merge['homeTeam']['players']
      game['awayTeam']['players'] = game_to_merge['awayTeam']['players']
      combined_full_stats.append(game)

    return {
      'Game Date': formatted_scoreboards['scoreboard']['gameDate'],
      'League': formatted_scoreboards['scoreboard']['leagueName'],
      'Games Stats': combined_full_stats,
      # 'formatted_scoreboards': formatted_scoreboards,
      # 'games_full_stats': games_full_stats
    }
  except Exception as err:
    logger.exception(err)
    return None

async def get_players_stats():
  try:
    players_stats = await get_all_players_season_stats()

    return parse_players_season_stats(json.loads(players_stats))
  except Exception as err:
    logger.exception(err)
    return None
