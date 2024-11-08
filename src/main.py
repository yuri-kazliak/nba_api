from fastapi import FastAPI

from .nba_stats import get_stats

app = FastAPI()

@app.get("/")
async def root():
  return await get_stats()
