import httpx
import json

SCOREBOARD_URL = 'https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/scoreboard/todaysScoreboard_00.json'
SINGLE_GAME_URL = 'https://core-api.nba.com/cp/api/v1.8/gameDetails'

statistic_minumum_criteria = {
  'assists': 3,
  'blocks': 2,
  'points': 9,
  'reboundsTotal': 5,
  'steals': 2
}

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
  team_title = team['teamCity'] + ' ' + team['teamName']
  players = []
  for player in team['players']:
    if player['status'] == 'ACTIVE':
      player_to_append = {
        'name': player['nameI']
      }
      if player['statistics']['assists'] > statistic_minumum_criteria['assists']:
        player_to_append['assists'] = player['statistics']['assists']
      if player['statistics']['blocks'] > statistic_minumum_criteria['blocks']:
        player_to_append['blocks'] = player['statistics']['blocks']
      if player['statistics']['points'] > statistic_minumum_criteria['points']:
        player_to_append['points'] = player['statistics']['points']
      if player['statistics']['reboundsTotal'] > statistic_minumum_criteria['reboundsTotal']:
        player_to_append['reboundsTotal'] = player['statistics']['reboundsTotal']
      if player['statistics']['steals'] > statistic_minumum_criteria['steals']:
        player_to_append['steals'] = player['statistics']['steals']

      if len(player_to_append) > 1:
        if not 'points' in player_to_append:
          player_to_append['points'] = player['statistics']['points']
        players.append(player_to_append)

  return {
    'team': team_title,
    'points': team['statistics']['points'],
    'players': players
  }
