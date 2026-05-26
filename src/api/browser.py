from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from ..exceptions import AdsPowerApiError, AdsPowerError
from ..models import ActiveProfile
from .base import BaseApi

logger = logging.getLogger(__name__)
_OPEN_TIMEOUT = 120.0

class BrowserApi(BaseApi):
    async def open(self, profile_id: str) -> ActiveProfile:
        data = await self._get("/api/v1/browser/start", timeout=_OPEN_TIMEOUT, user_id=profile_id)
        ws_url = data.get("ws", {}).get("puppeteer", "")
        if not ws_url: raise AdsPowerApiError(f"no websocket URL returned for {profile_id!r}")
        return ActiveProfile(id=profile_id, name=profile_id, websocket_url=ws_url, debug_port=int(data.get("debug_port") or 0))

    async def close(self, profile_id: str) -> None:
        await self._get("/api/v1/browser/stop", user_id=profile_id)

    @asynccontextmanager
    async def session(self, profile_id: str) -> AsyncIterator[ActiveProfile]:
        active = await self.open(profile_id)
        try:
            yield active
        finally:
            try: await self.close(profile_id)
            except AdsPowerError: pass

    async def active(self, profile_id: str) -> bool:
        try: return (await self._active_data(profile_id)).get("status") == "Active"
        except AdsPowerApiError: return False

    async def websocket_url(self, profile_id: str) -> str:
        try:
            ws_data: dict[str, Any] = (await self._active_data(profile_id)).get("ws") or {}
            return str(ws_data.get("puppeteer", ""))
        except AdsPowerApiError: return ""

    async def _active_data(self, profile_id: str) -> dict[str, Any]:
        return await self._get("/api/v1/browser/active", user_id=profile_id)

    async def restart(self, profile_id: str, delay: float = 2.0) -> ActiveProfile:
        try: await self.close(profile_id)
        except AdsPowerError: pass
        await asyncio.sleep(delay)
        return await self.open(profile_id)
