"""Integration-style tests for FastAPI routes."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pytest
from fastapi.testclient import TestClient

from nba_api.presentation.app import create_app


class DummyState:
    def __init__(self) -> None:
        self.boxscore: Optional[Dict[str, Any]] = None
        self.players: Optional[Dict[str, Any]] = None
        self.refreshed = False


@pytest.fixture
def app_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    dummy_state = DummyState()

    async def fake_ensure_boxscore_fresh() -> None:
        if dummy_state.boxscore is None:
            dummy_state.boxscore = {"game": "data"}

    async def fake_ensure_players_stats_fresh() -> None:
        if dummy_state.players is None:
            dummy_state.players = {"players": "data"}

    monkeypatch.setattr(
        "nba_api.presentation.state.ensure_boxscore_fresh",
        fake_ensure_boxscore_fresh,
    )
    monkeypatch.setattr(
        "nba_api.presentation.state.ensure_players_stats_fresh",
        fake_ensure_players_stats_fresh,
    )
    monkeypatch.setattr(
        "nba_api.presentation.state.get_todays_boxscore",
        lambda: dummy_state.boxscore,
    )
    monkeypatch.setattr(
        "nba_api.presentation.state.get_all_players_stats",
        lambda: dummy_state.players,
    )
    monkeypatch.setattr(
        "nba_api.presentation.state.schedule_full_refresh",
        lambda: setattr(dummy_state, "refreshed", True),
    )

    app = create_app()
    return TestClient(app)


def test_scoreboard_route_returns_data(app_client: TestClient) -> None:
    response = app_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"game": "data"}


def test_players_stats_route_returns_data(app_client: TestClient) -> None:
    response = app_client.get("/players-stats/")
    assert response.status_code == 200
    assert response.json() == {"players": "data"}


def test_refresh_endpoints_schedule_state_update(app_client: TestClient) -> None:
    resp_scoreboard = app_client.post("/refresh")
    assert resp_scoreboard.status_code == 200
    assert resp_scoreboard.json() == "State has been refreshed!"

    resp_players = app_client.post("/players-stats/refresh")
    assert resp_players.status_code == 200
    assert resp_players.json() == "State has been refreshed!"


def test_missing_routes_return_404(app_client: TestClient) -> None:
    response = app_client.get("/unknown")
    assert response.status_code == 404
