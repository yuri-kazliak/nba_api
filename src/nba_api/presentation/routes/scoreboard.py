"""Scoreboard-related API routes."""

from typing import Any, Dict, Optional

from fastapi import APIRouter

from .. import state

router = APIRouter()


@router.get("/", name="scoreboard:root")
async def root() -> Optional[Dict[str, Any]]:
    await state.ensure_boxscore_fresh()
    todays_boxscore: Optional[Dict[str, Any]] = state.get_todays_boxscore()
    return todays_boxscore


@router.post("/refresh", name="scoreboard:refresh")
async def refresh() -> str:
    state.schedule_full_refresh()
    return "State has been refreshed!"
