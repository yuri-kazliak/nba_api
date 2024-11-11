from fastapi import FastAPI
import sentry_sdk

from .nba_stats import get_stats

sentry_sdk.init(
    dsn="https://901ada8349b62d0c4ebe34c79816c81c@o4508279705960448.ingest.de.sentry.io/4508279708516432",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    _experiments={
        # Set continuous_profiling_auto_start to True
        # to automatically start the profiler on when
        # possible.
        "continuous_profiling_auto_start": True,
    },
)

app = FastAPI()

@app.get("/")
async def root():
  return await get_stats()
