from fastapi import FastAPI
import json
import asyncio

from .nba_stats import get_todays_scoreboard, get_single_game_info, parse_statline

app = FastAPI()

@app.get("/")
async def root():
  scoreboard = await get_todays_scoreboard()
  formatted = json.loads(scoreboard)

  # print(formatted['scoreboard']['games'])

  print(list(map(lambda game: game['gameId'],formatted['scoreboard']['games'])))

  games_stats = await asyncio.gather(*list(map(lambda game: get_single_game_info(game['gameId']),formatted['scoreboard']['games'])))
  formatted_game_stats = list(map(lambda stat: parse_statline(stat), games_stats))

  print(formatted_game_stats)

  # await get_single_game_info('0022400154')
  return {
    'Game Date': formatted['scoreboard']['gameDate'],
    'League': formatted['scoreboard']['leagueName'],
    # 'Games': formatted['scoreboard']['games'],
    # 'GamesIds': list(map(lambda game: game['gameId'],formatted['scoreboard']['games']))
    # 'Games Stats': games_stats,
    'Games Stats': formatted_game_stats
  }
