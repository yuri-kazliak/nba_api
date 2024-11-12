from fastapi import FastAPI
import sentry_sdk
from contextlib import asynccontextmanager
import asyncio

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


async def update_app_state_players_stats() -> None:
    app_state["all_players_stats"] = await get_players_stats()


def clear_app_state() -> None:
    app_state.clear()


async def create_interval(func, interval: int) -> None:
    while True:
        asyncio.create_task(func())
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    boxscore_task = asyncio.create_task(
        create_interval(update_app_state_boxscore, 60 * 30)
    )  # Every 30 minutes
    all_stats_task = asyncio.create_task(
        create_interval(update_app_state_players_stats, 60 * 60 * 12)
    )  # Every 12 Hours
    yield
    boxscore_task.cancel()
    all_stats_task.cancel()
    clear_app_state()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return app_state["todays_boxscore"]


@app.get("/players-stats")
async def players_stats():
    return app_state["all_players_stats"]


# @app.get("/players-stats/{player_name}")
# async def player_stat_by_name(player_name):
#     return await get_players_stats()
#     # return app_state['all_stats']
