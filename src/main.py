from fastapi import FastAPI
import httpx

SCOREBOARD_URL = 'https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/scoreboard/todaysScoreboard_00.json'
SINGLE_GAME_URL = 'https://core-api.nba.com/cp/api/v1.8/gameDetails'

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

app = FastAPI()

@app.get("/")
async def root():
    # combine_single_game_link('99999')
    await get_todays_scoreboard()
    await get_single_game_info('0022400154')
    return {"message": f"Hello World"}