"""Tests for the shared HTTP client helper."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any, Dict, List, Optional, Tuple

import httpx
import pytest

from nba_api.services import http_client


class DummyResponse:
    def __init__(self, text: str, error: Optional[Exception] = None) -> None:
        self.text = text
        self._error = error

    def raise_for_status(self) -> None:
        if self._error:
            raise self._error


class MockAsyncClient:
    def __init__(self, responses: List[DummyResponse]) -> None:
        self._responses = responses
        self.calls: List[Tuple[str, Dict[str, Any] | None, Dict[str, str] | None]] = []

    async def get(
        self,
        url: str,
        params: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
    ) -> DummyResponse:
        self.calls.append((url, params, headers))
        return self._responses.pop(0)


@pytest.fixture(autouse=True)
async def reset_http_client_state() -> AsyncGenerator[None, None]:
    http_client._cache.clear()
    http_client._client = None
    yield
    http_client._cache.clear()
    http_client._client = None


@pytest.mark.asyncio
async def test_perform_get_returns_cached_value() -> None:
    future_expiry = http_client.monotonic() + 10.0
    http_client._cache["cached_key"] = (future_expiry, "cached-response")

    result = await http_client.perform_get(
        "https://example.com/data",
        cache_key="cached_key",
        cache_ttl_seconds=60.0,
    )

    assert result == "cached-response"
    assert http_client._client is None


@pytest.mark.asyncio
async def test_perform_get_fetches_and_caches(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_client: httpx.AsyncClient = MockAsyncClient([DummyResponse("fresh-data")])  # type: ignore[assignment]
    http_client._client = mock_client  # type: ignore[assignment]

    result = await http_client.perform_get(
        "https://example.com/data",
        params={"foo": "bar"},
        headers={"X-Test": "1"},
        cache_key="fresh_key",
        cache_ttl_seconds=30.0,
    )

    assert result == "fresh-data"
    assert getattr(http_client._client, "calls") == [
        ("https://example.com/data", {"foo": "bar"}, {"X-Test": "1"})
    ]

    cached_entry = http_client._cache.get("fresh_key")
    assert cached_entry is not None
    expiry, cached_text = cached_entry
    assert cached_text == "fresh-data"
    assert expiry > http_client.monotonic()


@pytest.mark.asyncio
async def test_perform_get_retries_on_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleep_calls: List[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    monkeypatch.setattr(http_client.asyncio, "sleep", fake_sleep)

    error = httpx.HTTPError("boom")
    mock_client: httpx.AsyncClient = MockAsyncClient(
        [DummyResponse("", error=error), DummyResponse("recovered-data")]
    )  # type: ignore[assignment]
    http_client._client = mock_client  # type: ignore[assignment]

    result = await http_client.perform_get(
        "https://example.com/retry",
        cache_key="retry_key",
        cache_ttl_seconds=10.0,
    )

    assert result == "recovered-data"
    assert getattr(http_client._client, "calls") is not None
    assert len(getattr(http_client._client, "calls")) == 2
    assert sleep_calls == [0.5]

    cached_entry = http_client._cache.get("retry_key")
    assert cached_entry is not None
    _, cached_text = cached_entry
    assert cached_text == "recovered-data"


@pytest.mark.asyncio
async def test_perform_get_raises_after_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def failing_sleep(delay: float) -> None:
        pass

    monkeypatch.setattr(http_client.asyncio, "sleep", failing_sleep)
    http_client._client = MockAsyncClient([DummyResponse("", error=httpx.HTTPError("fail"))])  # type: ignore[assignment]

    with pytest.raises(httpx.HTTPError):
        await http_client.perform_get("https://example.com/fail", retries=1)


@pytest.mark.asyncio
async def test_perform_get_raises_runtime_error_when_no_exception() -> None:
    class BrokenClient(MockAsyncClient):
        async def get(
            self,
            url: str,
            params: Dict[str, Any] | None = None,
            headers: Dict[str, str] | None = None,
        ) -> DummyResponse:
            raise RuntimeError("unexpected")

    http_client._client = BrokenClient([])  # type: ignore[assignment]

    with pytest.raises(RuntimeError, match="unexpected"):
        await http_client.perform_get("https://example.com/broken", retries=1)


def test_init_and_close_http_client() -> None:
    assert http_client._client is None

    http_client._cache.clear()

    async def runner() -> None:
        await http_client.init_http_client()
        assert http_client._client is not None
        await http_client.close_http_client()
        assert http_client._client is None

    http_client.asyncio.run(runner())
