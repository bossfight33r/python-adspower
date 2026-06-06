from __future__ import annotations

import asyncio
import logging

from ..api import BrowserApi
from ..models import ActiveProfile

logger = logging.getLogger(__name__)

class Manager:
    def __init__(self, browser: BrowserApi, sem: asyncio.Semaphore | None = None):
        self.browser = browser
        self._sem = sem or asyncio.Semaphore(3)

    async def open_all(self, profile_ids: list[str]) -> list[ActiveProfile]:  # noqa: E501
        results = await asyncio.gather(*[self._open_guarded(pid) for pid in profile_ids], return_exceptions=True)
        opened = [r for r in results if isinstance(r, ActiveProfile)]
        failed = len(results) - len(opened)
        if failed: logger.error("failed to open %d profiles", failed)
        logger.info("opened %d/%d", len(opened), len(results))
        return opened

    async def close_all(self, profile_ids: list[str]) -> int:
        results = await asyncio.gather(*[self.browser.close(pid) for pid in profile_ids], return_exceptions=True)
        closed = sum(1 for r in results if not isinstance(r, Exception))
        logger.info("closed %d/%d", closed, len(results))
        return closed

    async def restart(self, profile_id: str) -> ActiveProfile:
        return await self.browser.restart(profile_id)

    async def _open_guarded(self, profile_id: str) -> ActiveProfile:
        async with self._sem: return await self.browser.open(profile_id)
