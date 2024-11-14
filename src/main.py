from fastapi import FastAPI
import sentry_sdk
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime, timedelta

from .nba_controllers import get_stats, get_players_stats

sentry_sdk.init(
    dsn="https://901ada8349b62d0c4ebe34c79816c81c@o4508279705960448.ingest.de.sentry.io/4508279708516432",
    traces_sample_rate=1.0,
    _experiments={
        "continuous_profiling_auto_start": True,
    },
)

app_state = {}


async def update_app_state_boxscore() -> None:
    app_state["todays_boxscore"] = await get_stats()
    app_state["todays_boxscore_datetime"] = datetime.now()


async def update_app_state_players_stats() -> None:
    app_state["all_players_stats"] = await get_players_stats()
    app_state["all_players_stats_datetime"] = datetime.now()


def clear_app_state() -> None:
    app_state.clear()


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.gather(update_app_state_boxscore(), update_app_state_players_stats())
    yield
    clear_app_state()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    if not "todays_boxscore" in app_state or not app_state["todays_boxscore"]:
        await update_app_state_boxscore()
    else:
        if datetime.now() > app_state["todays_boxscore_datetime"] + timedelta(hours=1):
            asyncio.gather(update_app_state_boxscore())

    return app_state["todays_boxscore"]


@app.get("/players-stats")
async def players_stats():
    if not "all_players_stats" in app_state or not app_state["all_players_stats"]:
        await update_app_state_players_stats()
    else:
        if datetime.now() > app_state["all_players_stats_datetime"] + timedelta(
            hours=1
        ):
            asyncio.gather(update_app_state_players_stats())

    return app_state["all_players_stats"]


@app.get("/refresh")
async def players_stats():
    try:
        asyncio.gather(update_app_state_boxscore(), update_app_state_players_stats())
        return "State has been refreshed!"
    except Exception as err:
        return err


# @app.get("/players-stats/{player_name}")
# async def player_stat_by_name(player_name):
#     return await get_players_stats()
#     # return app_state['all_stats']
