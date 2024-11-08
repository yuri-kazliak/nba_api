import httpx
import json
import asyncio

SCOREBOARD_URL = 'https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/scoreboard/todaysScoreboard_00.json'
SINGLE_GAME_URL = 'https://core-api.nba.com/cp/api/v1.8/gameDetails'

statistic_minumum_criteria = {
  'points': 9,
  'reboundsTotal': 5,
  'assists': 3,
  'steals': 2,
  'blocks': 2
}

players_to_watch = [
  "V. Wembanyama"
]

async def get_todays_scoreboard():
  r = httpx.get(SCOREBOARD_URL)
  return r.text

async def get_single_game_info(game_id):
  params = {
    'leagueId': '00',
    'gameId': game_id,
    'tabs': 'all',
    'platform': 'web'
  }
  headers = {
    "ocp-apim-subscription-key":"747fa6900c6c4e89a58b81b72f36eb96"
  }
  r = httpx.get(SINGLE_GAME_URL, params=params, headers=headers)
  return r.text

def parse_statline(stat_line):
  parsed = json.loads(stat_line)['boxscore']
  return {
    'homeTeam': format_team_statline(parsed['homeTeam']),
    'awayTeam': format_team_statline(parsed['awayTeam'])
  }

def format_team_statline(team):
  team_title = f'{team['teamCity']} {team['teamName']}'
  players = []
  for player in team['players']:
    if player['status'] == 'ACTIVE':
      criterias = statistic_minumum_criteria
      player_to_append = {
        'name': player['nameI']
      }
      if player_to_append['name'] in players_to_watch:
        criterias = {
          'points': 1,
          'reboundsTotal': 0,
          'assists': 0,
          'steals': 0,
          'blocks': 0
        }

      if player['statistics']['points'] > criterias['points']:
        player_to_append['points'] = player['statistics']['points']
      if player['statistics']['reboundsTotal'] > criterias['reboundsTotal']:
        player_to_append['reboundsTotal'] = player['statistics']['reboundsTotal']
      if player['statistics']['assists'] > criterias['assists']:
        player_to_append['assists'] = player['statistics']['assists']
      if player['statistics']['steals'] > criterias['steals']:
        player_to_append['steals'] = player['statistics']['steals']
      if player['statistics']['blocks'] > criterias['blocks']:
        player_to_append['blocks'] = player['statistics']['blocks']

      if len(player_to_append) > 1:
        if not 'points' in player_to_append:
          player_to_append['points'] = player['statistics']['points']
        players.append(player_to_append)

  return {
    'team': team_title,
    'points': team['statistics']['points'],
    'players': players
  }

async def get_stats():
  scoreboard = await get_todays_scoreboard()
  formatted = json.loads(scoreboard)

  # print(formatted['scoreboard']['games'])

  # print(list(map(lambda game: game['gameId'],formatted['scoreboard']['games'])))

  games_stats = await asyncio.gather(*list(map(lambda game: get_single_game_info(game['gameId']),formatted['scoreboard']['games'])))
  formatted_game_stats = list(map(lambda stat: parse_statline(stat), games_stats))

  # print(formatted_game_stats)

  # await get_single_game_info('0022400154')
  return {
    'Game Date': formatted['scoreboard']['gameDate'],
    'League': formatted['scoreboard']['leagueName'],
    # 'Games': formatted['scoreboard']['games'],
    # 'GamesIds': list(map(lambda game: game['gameId'],formatted['scoreboard']['games']))
    'Games Stats': formatted_game_stats,
    # 'formatted': formatted
  }
