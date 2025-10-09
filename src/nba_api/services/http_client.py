"""Shared HTTP client with retry and caching support."""

import asyncio
from time import monotonic
from typing import Any, Dict, Optional, Tuple

import httpx

CACHE_ENTRY = Tuple[float, str]
_client: Optional[httpx.AsyncClient] = None
_cache: Dict[str, CACHE_ENTRY] = {}


async def init_http_client() -> None:
    """Initialise the shared AsyncClient if not already created."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))


async def close_http_client() -> None:
    """Close the shared AsyncClient and clear cache."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
    _cache.clear()


async def perform_get(
    url: str,
    params: Dict[str, Any] | None = None,
    headers: Dict[str, str] | None = None,
    *,
    cache_key: Optional[str] = None,
    cache_ttl_seconds: Optional[float] = None,
    retries: int = 3,
    retry_delay_seconds: float = 0.5,
) -> str:
    """Execute GET request with optional caching and retries."""

    if cache_key and cache_ttl_seconds:
        cached = _cache.get(cache_key)
        if cached and cached[0] > monotonic():
            return cached[1]

    if _client is None:
        await init_http_client()

    assert _client is not None

    last_exception: Optional[Exception] = None
    delay = retry_delay_seconds

    for attempt in range(retries):
        try:
            response = await _client.get(url, params=params, headers=headers)
            response.raise_for_status()
            result = response.text
            if cache_key and cache_ttl_seconds:
                _cache[cache_key] = (monotonic() + cache_ttl_seconds, result)
            return result
        except httpx.HTTPError as err:
            last_exception = err
            if attempt == retries - 1:
                break
            await asyncio.sleep(delay)
            delay *= 2

    if last_exception is not None:
        raise last_exception

    raise RuntimeError("Failed to perform HTTP GET request without exception")
