from __future__ import annotations

import inspect
import os
import random
import time
from typing import Any

import httpx


class WMError(Exception):
    pass


class WMAuthError(WMError):
    pass


class WMRateLimitError(WMError):
    pass


class WorldMonitorClient:
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(
        self,
        http_client: httpx.AsyncClient | Any | None = None,
        sleeper: Any = None,
        jitter_fn: Any = None,
    ) -> None:
        self.base_url = os.getenv('WM_BASE_URL', '').strip().rstrip('/')
        self.api_key = os.getenv('WORLDMONITOR_API_KEY', '').strip()
        self._http = http_client or httpx.AsyncClient(timeout=15)
        self._sleep = sleeper or time.sleep
        self._jitter = jitter_fn or random.random

    async def _sleep_async(self, seconds: float) -> None:
        result = self._sleep(seconds)
        if inspect.isawaitable(result):
            await result

    def _headers(self) -> dict[str, str]:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        if self.api_key:
            headers['X-WorldMonitor-Key'] = self.api_key
        return headers

    async def request(self, method: str, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.base_url:
            raise WMError('WorldMonitor is unavailable: WM_BASE_URL is not configured.')
        url = f'{self.base_url}/{path.lstrip("/")}'
        max_retries = 3
        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                response = await self._http.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    headers=self._headers(),
                )
                if response.status_code in {401, 403}:
                    raise WMAuthError(f'WorldMonitor auth failed with status {response.status_code}')
                if response.status_code == 429:
                    if attempt < max_retries:
                        delay = min(8.0, 0.5 * (2 ** attempt))
                        delay *= 1 + ((self._jitter() * 0.4) - 0.2)
                        await self._sleep_async(delay)
                        continue
                    raise WMRateLimitError('WorldMonitor rate limit exceeded')
                if response.status_code in {500, 502, 503, 504}:
                    if attempt < max_retries:
                        delay = min(8.0, 0.5 * (2 ** attempt))
                        delay *= 1 + ((self._jitter() * 0.4) - 0.2)
                        await self._sleep_async(delay)
                        continue
                    raise WMError(f'WorldMonitor upstream error {response.status_code}')
                if response.status_code >= 400:
                    raise WMError(f'WorldMonitor request failed with status {response.status_code}')
                if not response.text:
                    return {}
                payload = response.json()
                return payload if isinstance(payload, dict) else {'data': payload}
            except (httpx.RequestError, WMError) as exc:
                last_error = exc
                if isinstance(exc, (WMAuthError, WMRateLimitError)):
                    raise
                if isinstance(exc, httpx.RequestError):
                    if attempt < max_retries:
                        delay = min(8.0, 0.5 * (2 ** attempt))
                        delay *= 1 + ((self._jitter() * 0.4) - 0.2)
                        await self._sleep_async(delay)
                        continue
                    raise WMError(str(exc)) from exc
                if attempt >= max_retries:
                    raise
        raise WMError(f'WorldMonitor request failed: {last_error}')

    async def close(self) -> None:
        close_method = getattr(self._http, 'aclose', None) or getattr(self._http, 'close', None)
        if close_method is None:
            return
        result = close_method()
        if inspect.isawaitable(result):
            await result
