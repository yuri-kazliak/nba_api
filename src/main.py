from fastapi import FastAPI
import sentry_sdk
from contextlib import asynccontextmanager
import asyncio

from .nba_stats import get_stats

sentry_sdk.init(
    dsn="https://901ada8349b62d0c4ebe34c79816c81c@o4508279705960448.ingest.de.sentry.io/4508279708516432",
    traces_sample_rate=1.0,
    _experiments={
        "continuous_profiling_auto_start": True,
    },
)

app_state = {}

async def update_app_state() -> None:
    app_state['today'] = await get_stats()

def clear_app_state() -> None:
    app_state.clear()

async def create_interval(interval: int) -> None:
    while True:
        asyncio.create_task(update_app_state())
        await asyncio.sleep(interval)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(create_interval(60 * 10))
    yield
    task.cancel()
    clear_app_state()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return app_state['today']
