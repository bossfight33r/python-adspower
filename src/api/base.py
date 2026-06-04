from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from ..exceptions import AdsPowerApiError, AdsPowerConnectionError, AdsPowerStuckError

logger = logging.getLogger(__name__)
_STUCK_MARKERS = ("auth_list", "ETIMEDOUT")
_RATE_LIMIT_MARKER = "Too many request"

def _is_transient(exc: BaseException) -> bool:
    if isinstance(exc, AdsPowerConnectionError): return True
    if isinstance(exc, AdsPowerApiError) and not isinstance(exc, AdsPowerStuckError):
        msg = str(exc)
        if _RATE_LIMIT_MARKER in msg:
            logger.warning("AdsPower rate limit, retrying...")
            return True
        if "HTTP 50" in msg: return True
    return False

_retry = retry(retry=retry_if_exception(_is_transient), stop=stop_after_attempt(4),
               wait=wait_exponential(multiplier=1, min=1, max=10), reraise=True)

def _check(body: dict[str, Any]) -> dict[str, Any]:
    if body.get("code") == 0:
        data = body.get("data")
        return data if isinstance(data, dict) else {}
    code = int(body.get("code") or -1)
    msg = str(body.get("msg") or f"unknown error (code={code})")
    if any(m in msg for m in _STUCK_MARKERS):
        raise AdsPowerStuckError(f"AdsPower appears stuck ({msg}). Try restarting the app.", code=code)
    raise AdsPowerApiError(msg, code=code)

def _parse(r: httpx.Response) -> dict[str, Any]:
    try: r.raise_for_status()
    except httpx.HTTPStatusError as e: raise AdsPowerApiError(f"HTTP {r.status_code}: {r.text[:200]}") from e
    try:
        body: dict[str, Any] = r.json()
        return body
    except Exception as e: raise AdsPowerApiError(f"non-JSON response: {r.text[:200]}") from e

class BaseApi:
    def __init__(self, http: httpx.AsyncClient, base: str, headers: dict[str, str], base_params: dict[str, str] | None = None):
        self.http = http
        self.base = base
        self.headers = headers
        self.base_params = dict(base_params or {})

    @_retry
    async def _get(self, path: str, timeout: float | None = None, **params: Any) -> dict[str, Any]:
        kw: dict[str, Any] = {"timeout": timeout} if timeout is not None else {}
        try:
            r = await self.http.get(f"{self.base}{path}", headers=self.headers, params={**self.base_params, **params}, **kw)
        except httpx.RequestError as e:
            logger.warning("connection error (%s)", path)
            raise AdsPowerConnectionError(str(e)) from e
        return _check(_parse(r))

    @_retry
    async def _post(self, path: str, json: dict[str, Any], timeout: float | None = None) -> dict[str, Any]:
        kw: dict[str, Any] = {"timeout": timeout} if timeout is not None else {}
        try:
            r = await self.http.post(f"{self.base}{path}", headers=self.headers, params=self.base_params, json=json, **kw)
        except httpx.RequestError as e:
            logger.warning("connection error (%s)", path)
            raise AdsPowerConnectionError(str(e)) from e
        return _check(_parse(r))
