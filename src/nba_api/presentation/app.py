from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI

from ..services.http_client import close_http_client, init_http_client
from . import state
from .routes import players, scoreboard

sentry_sdk.init(
    dsn="https://901ada8349b62d0c4ebe34c79816c81c@o4508279705960448.ingest.de.sentry.io/4508279708516432",
    traces_sample_rate=1.0,
    _experiments={
        "continuous_profiling_auto_start": True,
    },
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_http_client()
    yield
    state.clear_state()
    await close_http_client()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(scoreboard.router)
    app.include_router(players.router)
    return app


# @app.get("/players-stats/{player_name}")
# async def player_stat_by_name(player_name):
#     return await get_players_stats()
#     # return app_state['all_stats']
