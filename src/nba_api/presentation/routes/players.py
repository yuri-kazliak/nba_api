"""Players statistics API routes."""

from typing import Any, Dict, Optional

from fastapi import APIRouter

from .. import state

router = APIRouter(prefix="/players-stats")


@router.get("/", name="players:root")
async def players_stats() -> Optional[Dict[str, Any]]:
    await state.ensure_players_stats_fresh()
    stats: Optional[Dict[str, Any]] = state.get_all_players_stats()
    return stats


@router.post("/refresh", name="players:refresh")
async def refresh() -> str:
    state.schedule_full_refresh()
    return "State has been refreshed!"
