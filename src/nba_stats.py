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

async def get_single_game_full_stats(game_id):
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
    'gameId': parsed['gameId'],
    'homeTeam': format_team_statline(parsed['homeTeam']),
    'awayTeam': format_team_statline(parsed['awayTeam'])
  }

def parse_scoreboard_game(game):
  return {
    'gameId': game['gameId'],
    'homeTeam': parse_scoreboard_game_team(game['homeTeam']),
    'awayTeam': parse_scoreboard_game_team(game['awayTeam'])
  }

def parse_scoreboard_game_team(team):
  return {
    'score': team['score'],
    'wins': team['wins'],
    'losses': team['losses'],
    'teamCity': team['teamCity'],
    'teamName': team['teamName'],
    'teamTricode': team['teamTricode']
  }

def format_team_statline(team):
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
    'tricode': team['teamTricode'],
    'players': players
  }

async def get_stats():
  scoreboard = await get_todays_scoreboard()
  formatted_scoreboards = json.loads(scoreboard)

  games = list(map(parse_scoreboard_game ,formatted_scoreboards['scoreboard']['games']))

  games_full_stats = await asyncio.gather(*list(map(lambda game: get_single_game_full_stats(game['gameId']), games)))
  parsed_game_full_stats = list(map(parse_statline, games_full_stats))

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
    'formatted_scoreboards': formatted_scoreboards,
    'games_full_stats': games_full_stats
  }
